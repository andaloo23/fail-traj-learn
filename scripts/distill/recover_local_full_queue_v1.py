"""Explicit, one-shot recovery of the approved local queue after the PC reboot.

Frozen launch/trainer files and pre-reboot training artifacts remain unchanged.
Only binary is resumed; untouched later recipes use the original frozen worker.
"""
import argparse
import copy
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import local_full_recipe_queue as queue
import qwen_binary_resume_v1 as resume

ROOT = queue.ROOT
RECOVERY = ROOT / 'recovery_reboot_v1'
TRAIN_OUT = ROOT / 'runs/binary/recovery_v1'
CHILD = None


def prepare():
    plan, folder = queue.approved()
    state = queue.frozen.read(ROOT / 'queue.json')
    if state.get('current_recipe') != 'binary' or state['arms']['base']['status'] != 'completed':
        raise ValueError('Unexpected interruption; this plan recovers binary after the completed baseline')
    if (RECOVERY / 'launch.json').exists():
        raise ValueError('Recovery was already launched; inspect its receipts instead of retrying')
    saved, logged = resume.inspect_checkpoint(folder, ROOT / 'runs/binary', plan['optimizer_updates'], plan['train_max_hours_per_recipe'])
    for recipe in plan['recipes'][2:]:
        if recipe in state['arms'] or (ROOT / 'runs' / recipe).exists() or (ROOT / 'predictions' / recipe).exists():
            raise ValueError('Later recipe has already started: ' + recipe)
    paths = [ROOT / 'runs/binary/training_state.pt', ROOT / 'runs/binary/run.json', ROOT / 'runs/binary/train.jsonl',
             ROOT / 'arm_states/base.json', ROOT / 'arm_scores/base.json']
    paths += list(Path(saved['adapter']).iterdir())
    paths += [p for p in (ROOT / 'predictions/base').iterdir() if p.is_file()]
    paths += list((ROOT / 'logs').iterdir())
    queue.freeze(RECOVERY / 'queue_before.json', state)
    snapshot = RECOVERY / 'status_before.md'
    if not snapshot.exists():
        snapshot.write_bytes((ROOT / 'status.md').read_bytes())
    paths += [RECOVERY / 'queue_before.json', snapshot]
    execution = [Path(__file__), Path(resume.__file__)]
    recovery = dict(protocol='local_reboot_recovery_v1', parent_plan_sha256=queue.frozen.digest(ROOT / 'plan.json'),
        user_instruction='recover the local ones.', checkpoint_step=saved['step'], last_logged_step=logged['step'],
        replayed_updates=logged['step'] - saved['step'], updates=plan['optimizer_updates'],
        train_max_hours=plan['train_max_hours_per_recipe'], prior_consumed_seconds=logged['elapsed_seconds'],
        recipes=plan['recipes'], baseline_skipped=True, restore_optimizer_and_rng=True,
        automatic_retry=False, new_teacher_calls=0, test_used=False,
        source_sha256={str(p.relative_to(ROOT)): queue.frozen.digest(p) for p in paths if p.is_file()},
        execution_sha256={str(p.relative_to(queue.frozen.REPO)): queue.frozen.digest(p) for p in execution})
    queue.freeze(RECOVERY / 'plan.json', recovery)
    queue.freeze(RECOVERY / 'approval.json', dict(approved=True, user_instruction='recover the local ones.',
        plan_sha256=queue.frozen.digest(RECOVERY / 'plan.json'),
        scope='Recover the already approved local sequential queue; unchanged recipe/data/update and time budgets.'))
    print(json.dumps(dict(prepared=True, checkpoint_step=saved['step'], replayed_updates=recovery['replayed_updates'])), flush=True)


def approved():
    plan, folder = queue.approved()
    recovery = queue.frozen.read(RECOVERY / 'plan.json')
    approval = queue.frozen.read(RECOVERY / 'approval.json')
    if approval.get('approved') is not True or approval['plan_sha256'] != queue.frozen.digest(RECOVERY / 'plan.json'):
        raise ValueError('Recovery approval mismatch')
    if recovery['parent_plan_sha256'] != queue.frozen.digest(ROOT / 'plan.json'):
        raise ValueError('Original local plan changed')
    for rel, expected in recovery['execution_sha256'].items():
        if queue.frozen.digest(queue.frozen.REPO / rel) != expected:
            raise ValueError('Recovery code changed: ' + rel)
    return plan, folder, recovery


def status(state):
    state['updated_utc'] = queue.now()
    queue.save(ROOT / 'queue.json', state)
    lines = ['# Local distillation queue', '', f"**{state['status']}** · updated {state['updated_utc']}", '',
        'RTX 3090 · one recipe at a time · 400 train / 50 development · 50 test sealed · no new teacher calls.', '',
        'Recovered after the PC reboot. Binary resumes from checkpoint 1,500; the pre-reboot logs and checkpoints are preserved.', '',
        '| Recipe | Status | Training updates | Development windows returned |', '|---|---|---:|---:|']
    for recipe in queue.RECIPES:
        arm = state['arms'].get(recipe, {})
        log = TRAIN_OUT / 'train.jsonl' if recipe == 'binary' else ROOT / 'runs' / recipe / 'train.jsonl'
        step = arm.get('resumed_from_step', 0)
        if log.exists():
            try:
                step = resume.last_entry(log)['step']
            except ValueError:
                pass  # The first update may still be computing in a new log.
        returned = len(list((ROOT / 'predictions' / recipe).glob('*_binary.json')))
        lines.append(f"| {recipe} | {arm.get('status', 'queued')} | {'—' if recipe == 'base' else str(step) + '/2688'} | {returned}/279 |")
    if state.get('error'):
        lines += ['', 'Error: ' + state['error']]
    lines += ['', 'Recovery phase logs: `recovery_reboot_v1/logs/`. Original artifacts and the pre-reboot status snapshot remain preserved.', '']
    (ROOT / 'status.md').write_text('\n'.join(lines), encoding='utf-8')


def worker(recipe, phase):
    plan, folder, _ = approved()
    if recipe == 'binary' and phase == 'train':
        result = resume.train(folder, ROOT / 'runs/binary', TRAIN_OUT, plan['optimizer_updates'], plan['train_max_hours_per_recipe'])
        # The original generator follows this new receipt to the recovered adapter.
        queue.freeze(ROOT / 'runs/binary/completion.json', result)
        print(json.dumps(result), flush=True)
    else:
        queue.worker(recipe, phase)


def interrupt(signum, frame):
    if CHILD is not None and CHILD.poll() is None:
        CHILD.terminate()
    raise InterruptedError('Recovery controller received signal ' + str(signum))


def phase(recipe, name, state):
    global CHILD
    plan, _, recovery = approved()
    hours = plan['train_max_hours_per_recipe'] if name == 'train' else plan['evaluation_max_hours_per_recipe']
    if recipe == 'binary' and name == 'train':
        hours -= recovery['prior_consumed_seconds'] / 3600
    logs = RECOVERY / 'logs'; logs.mkdir(exist_ok=True)
    arm = state['arms'][recipe]
    arm.update(status=name, phase_started_utc=queue.now())
    status(state)
    command = [sys.executable, '-u', str(Path(__file__).resolve()), 'worker', '--recipe', recipe, '--phase', name]
    with (logs / f'{recipe}_{name}.out').open('x') as out, (logs / f'{recipe}_{name}.err').open('x') as err:
        CHILD = subprocess.Popen(command, cwd=str(queue.frozen.REPO), stdout=out, stderr=err)
        arm['child_pid'] = CHILD.pid; status(state); started = time.monotonic()
        while CHILD.poll() is None:
            try:
                CHILD.wait(timeout=30)
            except subprocess.TimeoutExpired:
                status(state)
                if time.monotonic() - started > hours * 3600 + 1800:
                    raise TimeoutError(recipe + ' ' + name + ' exceeded its remaining ceiling')
        code = CHILD.returncode; CHILD = None
    if code:
        raise RuntimeError(f'{recipe} {name} exited {code}; see {logs / (recipe + "_" + name + ".err")}')


def continue_recipes(state, plan, folder):
    import score_recipe_suite as scoring
    for recipe in plan['recipes']:
        if state['arms'].get(recipe, {}).get('status') == 'completed':
            continue
        if (ROOT / 'STOP_AFTER_CURRENT').exists():
            state['status'] = 'stopped_after_current'; return
        state['current_recipe'] = recipe
        arm = state['arms'].setdefault(recipe, dict(status='starting', started_utc=queue.now()))
        if recipe == 'binary':
            arm['resumed_from_step'] = queue.frozen.read(RECOVERY / 'plan.json')['checkpoint_step']
        status(state)
        if recipe != 'base':
            phase(recipe, 'train', state)
        phase(recipe, 'generate', state)
        generated = queue.frozen.read(ROOT / 'predictions' / recipe / 'completion.json')
        trained = None if recipe == 'base' else queue.frozen.read(ROOT / 'runs' / recipe / 'completion.json')
        scored = scoring.score(folder, ROOT / 'predictions' / recipe)
        queue.freeze(ROOT / 'arm_scores' / (recipe + '.json'), scored)
        scores = {p.stem: queue.frozen.read(p) for p in (ROOT / 'arm_scores').glob('*.json')}
        scoring.write_report(ROOT, scores)
        complete = generated['complete'] and (recipe == 'base' or trained['completed_schedule'])
        arm.update(status='completed' if complete else 'time_capped', finished_utc=queue.now(), training=trained, generation=generated)
        queue.freeze(ROOT / 'arm_states' / (recipe + '.json'), arm)
        status(state)
    state['status'] = 'completed' if all(a['status'] == 'completed' for a in state['arms'].values()) else 'finished_with_incomplete_arms'


def run():
    plan, folder, recovery = approved()
    lock = Path('/home/aliu/.cache/ftl-local-recipe-gpu.lock')
    with lock.open('a+') as guard:
        fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (RECOVERY / 'launch.json').exists() or TRAIN_OUT.exists():
            raise ValueError('Recovery already attempted; reconcile instead of automatically retrying')
        before = queue.frozen.read(RECOVERY / 'queue_before.json')
        for pid in [before['pid'], before['arms']['binary']['child_pid']]:
            process = Path('/proc') / str(pid) / 'cmdline'
            if process.exists() and b'local_full_recipe_queue.py' in process.read_bytes():
                raise ValueError('Original queue process is still alive')
        for rel, expected in recovery['source_sha256'].items():
            if queue.frozen.digest(ROOT / rel) != expected:
                raise ValueError('Pre-reboot source artifact changed: ' + rel)
        if queue.frozen.read(ROOT / 'queue.json') != before:
            raise ValueError('Queue changed after recovery preparation')
        state = copy.deepcopy(before)
        state.update(status='running', pid=os.getpid(), recovered_utc=queue.now(), recovery='recovery_reboot_v1')
        state['arms']['binary'].update(status='recovering', resumed_from_step=recovery['checkpoint_step'])
        for key in ('error', 'finished_utc'):
            state.pop(key, None)
        queue.freeze(RECOVERY / 'launch.json', dict(pid=os.getpid(), started_utc=queue.now(), plan_sha256=queue.frozen.digest(RECOVERY / 'plan.json')))
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, interrupt)
        try:
            continue_recipes(state, plan, folder)
        except BaseException as exc:
            state.update(status='interrupted' if isinstance(exc, InterruptedError) else 'failed', error=type(exc).__name__ + ': ' + str(exc))
            state['arms'][state['current_recipe']]['status'] = state['status']
            raise
        finally:
            if CHILD is not None and CHILD.poll() is None:
                CHILD.terminate()
                try:
                    CHILD.wait(timeout=120)
                except subprocess.TimeoutExpired:
                    CHILD.kill(); CHILD.wait()
            state['finished_utc'] = queue.now()
            status(state)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'check', 'run', 'worker'])
    parser.add_argument('--recipe', choices=queue.RECIPES)
    parser.add_argument('--phase', choices=['train', 'generate'])
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare()
    elif args.command == 'check':
        approved(); print('Original approval and versioned recovery code verified.')
    elif args.command == 'run':
        run()
    else:
        worker(args.recipe, args.phase)
