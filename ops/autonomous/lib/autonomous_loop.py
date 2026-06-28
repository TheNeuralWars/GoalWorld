#!/usr/bin/env python3
"""
Layer 5: Continuous Operation Loop (Autonomous Heartbeat)
==========================================================
The master orchestrator that ties all layers together.

Cycle:
1. Reindex codebase (Layer 1) — if git changed since last index
2. Scan project state (Layer 2)
3. Build priority queue + decisions (Layer 3)
4. Pick top dispatch-ready task → decompose → dispatch to Hermes CEO
5. Monitor dispatched task
6. Record outcome (Layer 4)
7. Analyze trends + self-assess
8. Report to Discord/WhatsApp
9. Sleep and repeat

Runs every 30 minutes via systemd timer.
Escalates to Nico only when truly blocked (3 consecutive failures on same task).
"""

import os
import sys
import json
from collections import defaultdict, Counter
import subprocess
from pathlib import Path
from datetime import datetime, timezone

# Add lib to path
SCRIPT_DIR = Path(__file__).resolve().parent
LIB_DIR = SCRIPT_DIR / "lib"
sys.path.insert(0, str(LIB_DIR))

REPO_ROOT = Path(os.environ.get("GOALWORLD_REPO_PATH", "/data/apps/GoalWorld"))
DATA_DIR = Path(os.environ.get("AUTONOMOUS_DATA_DIR",
    str(REPO_ROOT / "ops" / "autonomous" / "data")))
LOG_DIR = Path(os.environ.get("AUTONOMOUS_LOG_DIR",
    str(REPO_ROOT / "ops" / "autonomous" / "logs")))
LOOP_STATE = DATA_DIR / "loop_state.json"

# Import layers
from codebase_brain import CodebaseBrain
from state_awareness import StateAwareness
from decision_engine import DecisionEngine
from self_improvement import SelfImprovement


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg, level="INFO"):
    msg = f"[{now_iso()}] [AUTONOMOUS-LOOP] [{level}] {msg}"
    print(msg, flush=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_DIR / "loop.log", 'a') as f:
        f.write(msg + '\n')


def run_cmd(args, cwd=None, timeout=60):
    try:
        res = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return res.returncode == 0, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return False, "", str(e)


def run_cmd_with_env(args, cwd=None, env=None, timeout=60):
    try:
        res = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                             timeout=timeout, env=env)
        return res.returncode == 0, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return False, "", str(e)


class AutonomousLoop:
    def __init__(self):
        self.repo_root = REPO_ROOT
        self.cycle_count = 0
        self.loop_state = self._load_loop_state()

    def _load_loop_state(self):
        if LOOP_STATE.exists():
            return json.loads(LOOP_STATE.read_text())
        return {
            'cycle_count': 0,
            'last_cycle': None,
            'last_index': None,
            'dispatched_tasks': [],
            'consecutive_failures': defaultdict(int),
            'paused_tasks': [],
        }

    def _save_loop_state(self):
        state = dict(self.loop_state)
        # Convert defaultdict
        state['consecutive_failures'] = dict(state.get('consecutive_failures', {}))
        with open(LOOP_STATE, 'w') as f:
            json.dump(state, f, indent=2)

    def run_cycle(self, dry_run=False):
        """Run one complete autonomous cycle."""
        self.cycle_count = self.loop_state.get('cycle_count', 0) + 1
        log(f"═══ Starting cycle #{self.cycle_count} ═══")

        cycle_result = {
            'cycle': self.cycle_count,
            'timestamp': now_iso(),
            'steps': {},
        }

        # Step 1: Reindex codebase if needed
        step1 = self._step_reindex(dry_run)
        cycle_result['steps']['reindex'] = step1

        # Step 2: Scan project state
        step2 = self._step_scan_state(dry_run)
        cycle_result['steps']['scan_state'] = step2

        # Step 3: Build priority queue
        step3 = self._step_build_queue(dry_run)
        cycle_result['steps']['build_queue'] = step3

        # Step 4: Dispatch top task (if not dry run)
        step4 = self._step_dispatch(dry_run)
        cycle_result['steps']['dispatch'] = step4

        # Step 5: Check on previously dispatched tasks
        step5 = self._step_monitor_dispatched(dry_run)
        cycle_result['steps']['monitor'] = step5

        # Step 6: Self-assessment
        step6 = self._step_self_assess(dry_run)
        cycle_result['steps']['self_assess'] = step6

        # Step 7: Report
        step7 = self._step_report(cycle_result, dry_run)
        cycle_result['steps']['report'] = step7

        # Update loop state
        self.loop_state['cycle_count'] = self.cycle_count
        self.loop_state['last_cycle'] = now_iso()
        self._save_loop_state()

        log(f"═══ Cycle #{self.cycle_count} complete ═══")
        return cycle_result

    def _step_reindex(self, dry_run):
        """Step 1: Reindex codebase if git changed since last index."""
        log("Step 1: Checking if reindex needed...")

        # Check if git HEAD changed since last index
        ok, head, _ = run_cmd(['git', 'rev-parse', 'HEAD'], cwd=self.repo_root)
        last_indexed_head = self.loop_state.get('last_indexed_head')

        if head == last_indexed_head and not dry_run:
            log("  No git changes since last index. Skipping reindex.")
            return {'action': 'skip', 'reason': 'no_changes'}

        if dry_run:
            log("  [DRY RUN] Would reindex codebase")
            return {'action': 'dry_run'}

        try:
            brain = CodebaseBrain()
            result = brain.index()
            brain.close()
            self.loop_state['last_indexed_head'] = head
            self.loop_state['last_index'] = now_iso()
            log(f"  Reindexed: {result['files']} files, {result['symbols']} symbols")
            return {'action': 'reindex', 'result': result}
        except Exception as e:
            log(f"  Reindex failed: {e}", "ERROR")
            return {'action': 'error', 'error': str(e)}

    def _step_scan_state(self, dry_run):
        """Step 2: Scan project state."""
        log("Step 2: Scanning project state...")
        if dry_run:
            log("  [DRY RUN] Would scan state")
            return {'action': 'dry_run'}

        try:
            sa = StateAwareness()
            state = sa.scan_all()
            backlog_count = len(state.get('backlog', []))
            log(f"  State scanned: {backlog_count} backlog items")
            return {
                'action': 'scan',
                'backlog_items': backlog_count,
                'deploys_healthy': {k: v.get('healthy') for k, v in state.get('deploys', {}).items()},
                'open_issues': len(state.get('issues', {}).get('open_issues', [])),
            }
        except Exception as e:
            log(f"  State scan failed: {e}", "ERROR")
            return {'action': 'error', 'error': str(e)}

    def _step_build_queue(self, dry_run):
        """Step 3: Build priority queue."""
        log("Step 3: Building priority queue...")
        if dry_run:
            log("  [DRY RUN] Would build queue")
            return {'action': 'dry_run'}

        try:
            engine = DecisionEngine()
            queue = engine.run()
            dispatchable = [q for q in queue if q.get('dispatch_ready')]
            log(f"  Queue built: {len(queue)} items, {len(dispatchable)} dispatchable")
            return {
                'action': 'build',
                'total_items': len(queue),
                'dispatchable': len(dispatchable),
                'top_task': queue[0] if queue else None,
            }
        except Exception as e:
            log(f"  Queue build failed: {e}", "ERROR")
            return {'action': 'error', 'error': str(e)}

    def _step_dispatch(self, dry_run):
        """Step 4: Dispatch top task to Hermes CEO."""
        log("Step 4: Checking for dispatchable tasks...")

        try:
            engine = DecisionEngine()
            task = engine.get_next_dispatchable()
        except Exception as e:
            log(f"  Failed to get next task: {e}", "ERROR")
            return {'action': 'error', 'error': str(e)}

        if not task:
            log("  No dispatchable tasks in queue")
            return {'action': 'none', 'reason': 'no_dispatchable_tasks'}

        # Check if this task has failed too many times
        task_id = task.get('id', '')
        failures = self.loop_state.get('consecutive_failures', {}).get(task_id, 0)
        if failures >= 3:
            log(f"  Task {task_id} has failed {failures} times. Escalating to Nico.", "WARN")
            self._escalate_to_nico(task, failures)
            self.loop_state.setdefault('paused_tasks', []).append(task_id)
            return {'action': 'escalated', 'task_id': task_id, 'failures': failures}

        # Check if already dispatched and pending
        already_dispatched = any(
            d.get('task_id') == task_id and d.get('status') == 'pending'
            for d in self.loop_state.get('dispatched_tasks', [])
        )
        if already_dispatched:
            log(f"  Task {task_id} already dispatched and pending. Skipping.")
            return {'action': 'skip', 'reason': 'already_dispatched', 'task_id': task_id}

        if dry_run:
            log(f"  [DRY RUN] Would dispatch: {task['title']}")
            return {'action': 'dry_run', 'task': task}

        # Decompose the task
        try:
            decomposition = engine.decompose_task(
                task['title'],
                task.get('rationale', ''),
                task.get('source', '')
            )
        except Exception as e:
            log(f"  Decomposition failed: {e}", "WARN")
            decomposition = {'subtasks': []}

        # Dispatch to Hermes CEO via GitHub issue (direct gh, no legacy script dependency)
        priority = 'P0' if task.get('priority_score', 0) >= 80 else \
                   'P1' if task.get('priority_score', 0) >= 50 else 'P2'

        # Build detailed prompt
        prompt = self._build_dispatch_prompt(task, decomposition)

        # Use gh directly — more robust than create-task.sh which needs config.env
        ok, out, err = run_cmd([
            'gh', 'issue', 'create',
            '--title', f"[AUTO] {task['title']}",
            '--body', prompt,
            '--label', 'agent:hermes',
            '--label', f'priority:{priority}',
            '--label', 'status:ready',
            '--label', 'autonomous',
        ], cwd=self.repo_root, timeout=30)

        if ok:
            # Extract issue URL from output
            issue_url = None
            for line in (out + '\n' + err).split('\n'):
                if 'https://github.com' in line:
                    issue_url = line.strip()
                    break

            dispatch_record = {
                'task_id': task_id,
                'title': task['title'],
                'priority': priority,
                'issue_url': issue_url,
                'dispatched_at': now_iso(),
                'status': 'pending',
                'decomposition': decomposition,
            }
            self.loop_state.setdefault('dispatched_tasks', []).append(dispatch_record)
            log(f"  Dispatched: {task['title']} → {issue_url or 'issue created'}")
            return {'action': 'dispatched', 'task': task, 'issue_url': issue_url}
        else:
            log(f"  Dispatch failed: {err}", "ERROR")
            return {'action': 'error', 'error': err, 'stdout': out}

    def _build_dispatch_prompt(self, task, decomposition):
        """Build a detailed prompt for Hermes CEO."""
        lines = [
            f"# Autonomous Task: {task['title']}",
            f"",
            f"## Rationale",
            f"{task.get('rationale', 'Autonomously generated by the decision engine.')}",
            f"",
            f"## Context",
            f"- Category: {task.get('category', 'unknown')}",
            f"- Priority score: {task.get('priority_score', 0)}",
            f"- Strategic objectives: {', '.join(task.get('strategic_objectives', []))}",
            f"- Source: {task.get('source', 'autonomous')}",
            f"",
            f"## Decomposition",
        ]

        for sub in decomposition.get('subtasks', []):
            lines.append(f"{sub['step']}. {sub['action']}: {sub['detail']}")

        lines.extend([
            f"",
            f"## Relevant Codebase Context",
        ])

        for sym in decomposition.get('relevant_symbols', [])[:5]:
            lines.append(f"- `{sym['name']}` ({sym['kind']}) — {sym['file_path']}:{sym['start_line']}")

        lines.extend([
            f"",
            f"## Verification",
            f"After implementation:",
            f"1. Run relevant tests",
            f"2. Verify no regressions",
            f"3. Update docs/IMPLEMENTATION_STATUS.md if needed",
            f"",
            f"## Constraints",
            f"- Follow existing code conventions",
            f"- Minimal changes — don't refactor unrelated code",
            f"- All work on branch exp/hermes-issue-*",
            f"- Open draft PR",
        ])

        return '\n'.join(lines)

    def _step_monitor_dispatched(self, dry_run):
        """Step 5: Monitor previously dispatched tasks."""
        log("Step 5: Monitoring dispatched tasks...")
        if dry_run:
            log("  [DRY RUN] Would monitor dispatched tasks")
            return {'action': 'dry_run'}

        dispatched = self.loop_state.get('dispatched_tasks', [])
        pending = [d for d in dispatched if d.get('status') == 'pending']
        results = []

        for task in pending:
            task_id = task['task_id']
            issue_url = task.get('issue_url', '')

            # Check if the GitHub issue was closed (merged or done)
            if issue_url:
                # Extract issue number from URL
                import re
                match = re.search(r'/issues/(\d+)', issue_url)
                if match:
                    issue_num = match.group(1)
                    ok, out, _ = run_cmd(
                        ['gh', 'issue', 'view', issue_num, '--json', 'state,closed'],
                        cwd=self.repo_root)
                    if ok and out:
                        try:
                            issue_data = json.loads(out)
                            if issue_data.get('state') == 'CLOSED':
                                task['status'] = 'completed'
                                task['completed_at'] = now_iso()
                                log(f"  Task {task_id}: COMPLETED (issue #{issue_num} closed)")

                                # Record outcome
                                si = SelfImprovement()
                                si.record_outcome(
                                    task_id, task['title'],
                                    task.get('category', 'unknown'),
                                    True,
                                    {'issue_url': issue_url}
                                )
                                results.append({'task_id': task_id, 'status': 'completed'})
                                continue
                        except json.JSONDecodeError:
                            pass

            # Check if it's been pending too long (>24h)
            dispatched_at = task.get('dispatched_at')
            if dispatched_at:
                try:
                    dt = datetime.fromisoformat(dispatched_at.replace('Z', '+00:00'))
                    age_hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
                    if age_hours > 24:
                        task['status'] = 'stale'
                        task['stale_at'] = now_iso()
                        log(f"  Task {task_id}: STALE (pending {age_hours:.0f}h)", "WARN")
                        results.append({'task_id': task_id, 'status': 'stale'})
                        continue
                except Exception:
                    pass

            results.append({'task_id': task_id, 'status': 'pending'})

        # Clean up old completed/stale tasks (keep last 20)
        active = [d for d in dispatched if d.get('status') == 'pending']
        completed = [d for d in dispatched if d.get('status') != 'pending'][-20:]
        self.loop_state['dispatched_tasks'] = active + completed

        return {'action': 'monitor', 'results': results}

    def _step_self_assess(self, dry_run):
        """Step 6: Self-assessment and trend analysis."""
        log("Step 6: Self-assessment...")
        if dry_run:
            log("  [DRY RUN] Would self-assess")
            return {'action': 'dry_run'}

        try:
            si = SelfImprovement()
            analysis = si.analyze_trends()
            metrics = si.get_metrics()

            log(f"  Success rate: {metrics.get('success_rate', 0):.1%} "
                f"({metrics.get('successful', 0)}/{metrics.get('total_tasks', 0)})")
            log(f"  Trend: {analysis.get('trend', 'unknown')}")

            # Check for declining trend → pause autonomous dispatch
            if analysis.get('trend') == 'declining' and \
               analysis.get('recent_success_rate', 1) < 0.3:
                log("  ⚠️  Success rate critically low. Pausing autonomous dispatch.", "WARN")
                self.loop_state['autonomous_dispatch_paused'] = True
                self.loop_state['pause_reason'] = 'low_success_rate'
            elif analysis.get('trend') == 'improving':
                self.loop_state['autonomous_dispatch_paused'] = False

            return {
                'action': 'assess',
                'success_rate': metrics.get('success_rate', 0),
                'trend': analysis.get('trend'),
                'recommendations': analysis.get('recommendations', []),
            }
        except Exception as e:
            log(f"  Self-assessment failed: {e}", "ERROR")
            return {'action': 'error', 'error': str(e)}

    def _step_report(self, cycle_result, dry_run):
        """Step 7: Report cycle results."""
        log("Step 7: Reporting...")

        # Build summary
        summary = self._build_cycle_summary(cycle_result)

        # Save cycle result
        with open(DATA_DIR / f"cycle_{self.cycle_count}.json", 'w') as f:
            json.dump(cycle_result, f, indent=2)

        # Try to post to Discord via hermes_reporter
        if not dry_run:
            try:
                reporter = self.repo_root / "ops" / "hermes" / "hermes_reporter.py"
                if reporter.exists():
                    ok, out, err = run_cmd([
                        '/home/ubuntu/.hermes/hermes-agent/venv/bin/python3',
                        str(reporter), '--custom', summary
                    ], timeout=15)
                    if ok:
                        log("  Reported to Discord #hermes-reports")
                    else:
                        log(f"  Discord report failed: {err}", "WARN")
            except Exception as e:
                log(f"  Report failed: {e}", "WARN")

        return {'action': 'report', 'summary': summary[:200]}

    def _build_cycle_summary(self, cycle_result):
        """Build a human-readable cycle summary."""
        lines = [
            f"🤖 **Autonomous Cycle #{self.cycle_count}** — {now_iso()}",
            f"",
        ]

        # Reindex
        reindex = cycle_result['steps'].get('reindex', {})
        if reindex.get('action') == 'reindex':
            r = reindex.get('result', {})
            lines.append(f"📚 Codebase: {r.get('files', 0)} files, {r.get('symbols', 0)} symbols indexed")

        # State
        state = cycle_result['steps'].get('scan_state', {})
        deploys = state.get('deploys_healthy', {})
        deploy_str = ' '.join(f"{k}={'✅' if v else '❌'}" for k, v in deploys.items())
        lines.append(f"🏥 Deploys: {deploy_str}")
        lines.append(f"📋 Backlog: {state.get('backlog_items', 0)} items")

        # Queue
        queue = cycle_result['steps'].get('build_queue', {})
        lines.append(f"🎯 Queue: {queue.get('total_items', 0)} items, "
                     f"{queue.get('dispatchable', 0)} dispatchable")

        # Dispatch
        dispatch = cycle_result['steps'].get('dispatch', {})
        if dispatch.get('action') == 'dispatched':
            lines.append(f"⚡ Dispatched: {dispatch.get('task', {}).get('title', '?')}")
        elif dispatch.get('action') == 'escalated':
            lines.append(f"⚠️ Escalated: {dispatch.get('task_id')} ({dispatch.get('failures')} failures)")

        # Monitor
        monitor = cycle_result['steps'].get('monitor', {})
        for r in monitor.get('results', []):
            if r.get('status') == 'completed':
                lines.append(f"✅ Completed: {r['task_id']}")
            elif r.get('status') == 'stale':
                lines.append(f"⏰ Stale: {r['task_id']}")

        # Self-assess
        assess = cycle_result['steps'].get('self_assess', {})
        lines.append(f"📊 Success rate: {assess.get('success_rate', 0):.0%} ({assess.get('trend', '?')})")

        return '\n'.join(lines)

    def _escalate_to_nico(self, task, failures):
        """Escalate a repeatedly failing task to Nico."""
        log(f"Escalating to Nico: {task.get('title')} ({failures} failures)", "WARN")
        # This would send a WhatsApp/Discord message to Nico
        # For now, just log it prominently
        try:
            reporter = self.repo_root / "ops" / "hermes" / "hermes_reporter.py"
            if reporter.exists():
                msg = (f"⚠️ **AUTONOMOUS ESCALATION**\n"
                       f"Task: {task.get('title')}\n"
                       f"Failures: {failures}\n"
                       f"Needs human intervention.")
                run_cmd([
                    '/home/ubuntu/.hermes/hermes-agent/venv/bin/python3',
                    str(reporter), '--custom', msg
                ], timeout=15)
        except Exception:
            pass


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Autonomous Loop — Layer 5")
    parser.add_argument('command', choices=['cycle', 'status', 'dry-run'])
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()

    loop = AutonomousLoop()

    if args.command in ('cycle', 'dry-run'):
        result = loop.run_cycle(dry_run=(args.command == 'dry-run'))
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print(f"\n{loop._build_cycle_summary(result)}")

    elif args.command == 'status':
        state = loop.loop_state
        print(json.dumps(state, indent=2, default=str) if args.json else
              f"Cycle count: {state.get('cycle_count', 0)}\n"
              f"Last cycle: {state.get('last_cycle', 'never')}\n"
              f"Dispatched tasks: {len(state.get('dispatched_tasks', []))}\n"
              f"Paused tasks: {state.get('paused_tasks', [])}\n"
              f"Dispatch paused: {state.get('autonomous_dispatch_paused', False)}")


if __name__ == '__main__':
    main()
