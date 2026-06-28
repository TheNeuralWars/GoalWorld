#!/usr/bin/env python3
"""
Layer 3: Decision Engine
=========================
Autonomous decision-making: what to work on, in what order, and why.

Consumes:
- Project state (Layer 2)
- Codebase brain (Layer 1) for context
- Episodic memory (Layer 4) for past outcomes
- Strategic objectives

Produces:
- Decision log (auditable rationale for each decision)
- Priority queue (ordered task list)
- Task decomposition (objectives → subtasks)
- Dispatch instructions (ready for Hermes CEO)
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

REPO_ROOT = Path(os.environ.get("GOALWORLD_REPO_PATH", "/data/apps/GoalWorld"))
DATA_DIR = Path(os.environ.get("AUTONOMOUS_DATA_DIR",
    str(REPO_ROOT / "ops" / "autonomous" / "data")))
STATE_FILE = DATA_DIR / "state.json"
BACKLOG_FILE = DATA_DIR / "backlog.json"
CODEBASE_DB = DATA_DIR / "codebase.db"
DECISION_LOG = DATA_DIR / "decision_log.jsonl"
PRIORITY_QUEUE = DATA_DIR / "priority_queue.json"
EPISODIC_MEMORY = DATA_DIR / "episodic_memory.jsonl"

# Strategic objectives with weights
STRATEGIC_OBJECTIVES = [
    {'id': 'mundial-mvp', 'name': 'Mundial 2026 MVP', 'weight': 1.0,
     'keywords': ['fixture', 'bet', 'claim', 'payout', 'devnet', 'wallet', 'oracle', 'match',
                  'place_bet', 'claim_bet', 'refund', 'complete']},
    {'id': 'economy', 'name': 'Economy/On-chain', 'weight': 0.9,
     'keywords': ['economy', 'token', 'vault', 'yield', 'fee', 'split', 'rarity', 'program',
                  'solana', 'anchor', 'instruction']},
    {'id': 'merge-stack', 'name': 'Merge Stack Convergence', 'weight': 0.8,
     'keywords': ['pr', 'merge', 'refactor', 'cleanup', 'archive', 'stale', 'branch']},
    {'id': 'webapp', 'name': 'Webapp Polish', 'weight': 0.7,
     'keywords': ['webapp', 'ui', 'react', 'frontend', 'css', 'component', 'vite', 'tailwind']},
    {'id': 'automation', 'name': 'Automation & Ops', 'weight': 0.6,
     'keywords': ['script', 'cron', 'daemon', 'pipeline', 'automation', 'ops', 'systemd',
                  'healthcheck']},
    {'id': 'marketing', 'name': 'Marketing & Content', 'weight': 0.5,
     'keywords': ['video', 'social', 'buffer', 'tiktok', 'youtube', 'content', 'marketing']},
]

# Category base priorities
CATEGORY_BASE = {
    'bug': 80,
    'ops': 70,
    'review': 60,
    'triage': 50,
    'tech-debt': 35,
    'hygiene': 25,
    'feature': 55,
    'refactor': 45,
}


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg, level="INFO"):
    print(f"[{now_iso()}] [DECISION-ENGINE] [{level}] {msg}", flush=True)


class DecisionEngine:
    def __init__(self):
        self.repo_root = REPO_ROOT
        self.state = self._load_state()
        self.episodic = self._load_episodic_memory()
        self.decisions = []

    def _load_state(self):
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text())
        return {}

    def _load_episodic_memory(self):
        """Load episodic memory for past outcomes."""
        memories = []
        if EPISODIC_MEMORY.exists():
            for line in EPISODIC_MEMORY.read_text().strip().split('\n'):
                if line:
                    try:
                        memories.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return memories

    def _log_decision(self, decision_type, rationale, action, context=None):
        """Log a decision to the decision log."""
        entry = {
            'timestamp': now_iso(),
            'type': decision_type,
            'rationale': rationale,
            'action': action,
            'context': context or {},
        }
        self.decisions.append(entry)
        with open(DECISION_LOG, 'a') as f:
            f.write(json.dumps(entry) + '\n')
        return entry

    def run(self):
        """Main decision engine cycle."""
        log("Starting decision engine cycle...")
        queue = self._build_priority_queue()
        self._save_queue(queue)
        log(f"Priority queue built: {len(queue)} items")
        return queue

    def _score_backlog_item(self, item):
        """Score a backlog item considering strategic alignment and past outcomes."""
        base = CATEGORY_BASE.get(item.get('category', 'tech-debt'), 40)
        title = (item.get('title', '') + ' ' + item.get('rationale', '')).lower()

        # Strategic alignment bonus
        strategic_bonus = 0
        aligned_objectives = []
        for obj in STRATEGIC_OBJECTIVES:
            for kw in obj['keywords']:
                if kw in title:
                    strategic_bonus += obj['weight'] * 10
                    aligned_objectives.append(obj['id'])
                    break

        # Past outcome penalty: if we've failed at similar tasks before, lower priority
        past_penalty = 0
        for mem in self.episodic[-50:]:  # Last 50 memories
            if not mem.get('success', True) and mem.get('category') == item.get('category'):
                past_penalty += 5

        # Urgency: bugs and ops issues get boosted
        urgency = 0
        if item.get('category') == 'bug':
            urgency = 20
        elif item.get('category') == 'ops':
            urgency = 15

        # Original priority from Layer 2
        original = item.get('priority_score', 50)

        score = base + strategic_bonus + urgency + (original * 0.3) - past_penalty
        return min(score, 100), aligned_objectives

    def _build_priority_queue(self):
        """Build the priority queue from backlog + strategic objectives."""
        backlog = []
        if BACKLOG_FILE.exists():
            backlog = json.loads(BACKLOG_FILE.read_text())

        queue = []
        for item in backlog:
            score, objectives = self._score_backlog_item(item)
            queue.append({
                'id': item['id'],
                'title': item['title'],
                'category': item['category'],
                'rationale': item.get('rationale', ''),
                'priority_score': round(score, 1),
                'strategic_objectives': objectives,
                'source': item.get('source', ''),
                'dispatch_ready': self._is_dispatch_ready(item),
            })

        # Add strategic objectives that have no corresponding backlog items
        # (proactive task generation)
        proactive = self._generate_proactive_tasks()
        queue.extend(proactive)

        # Sort by priority score
        queue.sort(key=lambda x: x['priority_score'], reverse=True)

        # Log top decisions
        for item in queue[:5]:
            self._log_decision(
                'priority_assignment',
                f"Priority {item['priority_score']}: {item['title']} "
                f"(objectives: {item['strategic_objectives']})",
                f"Queued as {item['category']} with score {item['priority_score']}",
                {'item_id': item['id'], 'objectives': item['strategic_objectives']}
            )

        return queue

    def _is_dispatch_ready(self, item):
        """Check if a backlog item is ready to be dispatched to Hermes CEO."""
        cat = item.get('category', '')
        # Bugs and ops issues are immediately dispatchable
        if cat in ('bug', 'ops'):
            return True
        # Reviews need human or agent attention
        if cat == 'review':
            return False
        # Triage needs analysis first
        if cat == 'triage':
            return False
        # Tech debt and hygiene are dispatchable
        return True

    def _generate_proactive_tasks(self):
        """Generate proactive tasks based on strategic objectives and current state."""
        proactive = []

        # Check if API is down → generate fix task
        deploys = self.state.get('deploys', {})
        if not deploys.get('api', {}).get('healthy', True):
            proactive.append({
                'id': 'proactive-api-fix',
                'title': 'Fix API deploy health',
                'category': 'bug',
                'rationale': 'API is down — critical for webapp and ops',
                'priority_score': 95,
                'strategic_objectives': ['mundial-mvp', 'automation'],
                'source': 'proactive',
                'dispatch_ready': True,
            })

        # Check for uncommitted changes → suggest commit
        git = self.state.get('git', {})
        if git.get('uncommitted', 0) > 5:
            proactive.append({
                'id': 'proactive-commit',
                'title': 'Commit and push uncommitted changes',
                'category': 'hygiene',
                'rationale': f'{git["uncommitted"]} uncommitted changes on {git["branch"]}',
                'priority_score': 45,
                'strategic_objectives': ['merge-stack'],
                'source': 'proactive',
                'dispatch_ready': False,
            })

        # Check for high TODO count → suggest cleanup sprint
        code_health = self.state.get('code_health', {})
        if code_health.get('total_todos', 0) > 20:
            proactive.append({
                'id': 'proactive-todo-cleanup',
                'title': 'Tech debt sprint: resolve TODOs in codebase',
                'category': 'tech-debt',
                'rationale': f'{code_health["total_todos"]} TODOs accumulated',
                'priority_score': 30,
                'strategic_objectives': ['merge-stack'],
                'source': 'proactive',
                'dispatch_ready': True,
            })

        # Check for stale branches → suggest cleanup
        stale = git.get('stale_branches', [])
        if len(stale) > 3:
            proactive.append({
                'id': 'proactive-branch-cleanup',
                'title': f'Clean up {len(stale)} stale branches',
                'category': 'hygiene',
                'rationale': 'Stale branches accumulating in repo',
                'priority_score': 25,
                'strategic_objectives': ['merge-stack'],
                'source': 'proactive',
                'dispatch_ready': False,
            })

        return proactive

    def _save_queue(self, queue):
        """Save priority queue to file."""
        with open(PRIORITY_QUEUE, 'w') as f:
            json.dump(queue, f, indent=2)

    def decompose_task(self, task_title, task_rationale, context=""):
        """
        Decompose a high-level task into subtasks using codebase context.
        This is the 'prefrontal cortex' — it thinks about HOW to approach a task.
        """
        log(f"Decomposing task: {task_title}")

        # Query codebase brain for relevant context
        context_symbols = self._query_codebase(task_title)

        # Build decomposition prompt (this would be sent to an LLM in production)
        decomposition = {
            'task': task_title,
            'rationale': task_rationale,
            'context': context,
            'relevant_symbols': context_symbols[:10],
            'subtasks': self._auto_decompose(task_title, task_rationale, context_symbols),
            'timestamp': now_iso(),
        }

        self._log_decision(
            'task_decomposition',
            f"Decomposed '{task_title}' into {len(decomposition['subtasks'])} subtasks",
            f"Created decomposition plan",
            decomposition
        )

        return decomposition

    def _query_codebase(self, query):
        """Query the codebase brain for symbols relevant to a task."""
        if not CODEBASE_DB.exists():
            return []

        db = sqlite3.connect(str(CODEBASE_DB))
        db.row_factory = sqlite3.Row
        symbols = []

        # FTS search
        try:
            safe = query.replace("'", " ").replace('"', ' ')
            rows = db.execute(
                "SELECT s.name, s.kind, s.file_path, s.start_line, s.package, s.docstring "
                "FROM symbols_fts f JOIN symbols s ON f.rowid = s.id "
                "WHERE symbols_fts MATCH ? "
                "ORDER BY bm25(symbols_fts) LIMIT 10",
                (safe,)
            ).fetchall()
            symbols = [dict(r) for r in rows]
        except Exception:
            pass
        finally:
            db.close()

        return symbols

    def _auto_decompose(self, title, rationale, context_symbols):
        """
        Auto-decompose a task into subtasks based on patterns.
        This uses heuristics — in production, an LLM would do this.
        """
        subtasks = []
        title_lower = title.lower()

        # Pattern: bug fix
        if any(w in title_lower for w in ['fix', 'broken', 'down', 'fail', 'error', 'unhealthy']):
            subtasks = [
                {'step': 1, 'action': 'Investigate root cause',
                 'detail': f'Examine {", ".join(s["file_path"] for s in context_symbols[:3])}'},
                {'step': 2, 'action': 'Implement fix',
                 'detail': 'Minimal change to resolve the issue'},
                {'step': 3, 'action': 'Add/update test',
                 'detail': 'Prevent regression'},
                {'step': 4, 'action': 'Verify fix',
                 'detail': 'Run tests and check deploy health'},
            ]

        # Pattern: feature implementation
        elif any(w in title_lower for w in ['add', 'implement', 'create', 'build']):
            subtasks = [
                {'step': 1, 'action': 'Design approach',
                 'detail': f'Review existing patterns in {", ".join(s["name"] for s in context_symbols[:3])}'},
                {'step': 2, 'action': 'Implement core logic',
                 'detail': 'Follow existing code conventions'},
                {'step': 3, 'action': 'Add tests',
                 'detail': 'Unit + integration tests'},
                {'step': 4, 'action': 'Update documentation',
                 'detail': 'Update IMPLEMENTATION_STATUS.md if needed'},
            ]

        # Pattern: refactor / cleanup
        elif any(w in title_lower for w in ['refactor', 'cleanup', 'clean up', 'archive']):
            subtasks = [
                {'step': 1, 'action': 'Identify all affected files',
                 'detail': 'Use codebase brain to map dependencies'},
                {'step': 2, 'action': 'Make changes incrementally',
                 'detail': 'One package at a time'},
                {'step': 3, 'action': 'Verify no regressions',
                 'detail': 'Run all tests'},
            ]

        # Default
        else:
            subtasks = [
                {'step': 1, 'action': 'Analyze requirements',
                 'detail': 'Understand what needs to be done'},
                {'step': 2, 'action': 'Implement solution',
                 'detail': 'Follow existing patterns'},
                {'step': 3, 'action': 'Verify result',
                 'detail': 'Test and validate'},
            ]

        return subtasks

    def get_next_dispatchable(self):
        """Get the next dispatch-ready task from the priority queue."""
        if not PRIORITY_QUEUE.exists():
            return None
        queue = json.loads(PRIORITY_QUEUE.read_text())
        for item in queue:
            if item.get('dispatch_ready', False):
                return item
        return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Decision Engine — Layer 3")
    parser.add_argument('command', choices=['run', 'queue', 'decompose', 'next', 'decisions'])
    parser.add_argument('--title', '-t', help="Task title for decomposition")
    parser.add_argument('--rationale', '-r', help="Task rationale")
    parser.add_argument('--limit', '-l', type=int, default=20)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()

    engine = DecisionEngine()

    if args.command == 'run':
        queue = engine.run()
        if args.json:
            print(json.dumps(queue, indent=2))
        else:
            print(f"=== Priority Queue ({len(queue)} items) ===")
            for item in queue[:args.limit]:
                ready = '⚡' if item.get('dispatch_ready') else '  '
                print(f"  {ready} [{item['priority_score']:>5}] {item['category']:<10} "
                      f"{item['title']}")
                if item.get('strategic_objectives'):
                    print(f"         objectives: {', '.join(item['strategic_objectives'])}")

    elif args.command == 'queue':
        if PRIORITY_QUEUE.exists():
            queue = json.loads(PRIORITY_QUEUE.read_text())
            if args.json:
                print(json.dumps(queue, indent=2))
            else:
                for item in queue[:args.limit]:
                    ready = '⚡' if item.get('dispatch_ready') else '  '
                    print(f"  {ready} [{item['priority_score']:>5}] {item['category']:<10} "
                          f"{item['title']}")

    elif args.command == 'decompose':
        if not args.title:
            print("Error: --title required for decompose")
            sys.exit(1)
        result = engine.decompose_task(args.title, args.rationale or '')
        print(json.dumps(result, indent=2) if args.json else
              f"Task: {result['task']}\nSubtasks:\n" +
              '\n'.join(f"  {s['step']}. {s['action']}: {s['detail']}" for s in result['subtasks']))

    elif args.command == 'next':
        item = engine.get_next_dispatchable()
        if item:
            print(json.dumps(item, indent=2) if args.json else
                  f"Next dispatchable: [{item['priority_score']}] {item['title']}\n"
                  f"Category: {item['category']}\nRationale: {item.get('rationale', '')}")
        else:
            print("No dispatchable tasks in queue")

    elif args.command == 'decisions':
        if DECISION_LOG.exists():
            lines = DECISION_LOG.read_text().strip().split('\n')
            for line in lines[-args.limit:]:
                entry = json.loads(line)
                print(f"[{entry['timestamp']}] {entry['type']}: {entry['rationale']}")


if __name__ == '__main__':
    main()
