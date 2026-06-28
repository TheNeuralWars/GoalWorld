#!/usr/bin/env python3
"""
Layer 4: Self-Improvement Loop
================================
Metacognition: evaluate own work, learn from failures, auto-generate skills.

Consumes:
- Task outcomes (from Layer 5 dispatch results)
- Decision log (from Layer 3)
- Codebase changes (git diff after task completion)

Produces:
- Episodic memory entries (what was tried, what happened)
- Failure analysis with root causes
- Skill suggestions (patterns that worked → reusable skills)
- Prompt refinement suggestions
- Performance metrics over time
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict, Counter

REPO_ROOT = Path(os.environ.get("GOALWORLD_REPO_PATH", "/data/apps/GoalWorld"))
DATA_DIR = Path(os.environ.get("AUTONOMOUS_DATA_DIR",
    str(REPO_ROOT / "ops" / "autonomous" / "data")))
EPISODIC_MEMORY = DATA_DIR / "episodic_memory.jsonl"
DECISION_LOG = DATA_DIR / "decision_log.jsonl"
METRICS_FILE = DATA_DIR / "metrics.json"
SKILL_SUGGESTIONS = DATA_DIR / "skill_suggestions.jsonl"
PRIORITY_QUEUE = DATA_DIR / "priority_queue.json"

# Skills directory (Hermes CEO profile)
SKILLS_DIR = Path(os.environ.get("HERMES_CEO_SKILLS_DIR",
    "/home/ubuntu/.hermes/profiles/hermes-ceo/skills"))


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg, level="INFO"):
    print(f"[{now_iso()}] [SELF-IMPROVEMENT] [{level}] {msg}", flush=True)


def run_cmd(args, cwd=None, timeout=30):
    try:
        res = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return res.returncode == 0, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return False, "", str(e)


class SelfImprovement:
    def __init__(self):
        self.repo_root = REPO_ROOT
        self.memories = self._load_memories()
        self.metrics = self._load_metrics()

    def _load_memories(self):
        memories = []
        if EPISODIC_MEMORY.exists():
            for line in EPISODIC_MEMORY.read_text().strip().split('\n'):
                if line:
                    try:
                        memories.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return memories

    def _load_metrics(self):
        if METRICS_FILE.exists():
            return json.loads(METRICS_FILE.read_text())
        return {
            'total_tasks': 0,
            'successful': 0,
            'failed': 0,
            'success_rate': 0.0,
            'by_category': defaultdict(int),
            'by_category_success': defaultdict(int),
            'common_failures': [],
            'skill_suggestions_generated': 0,
            'history': [],
        }

    def _save_metrics(self):
        # Convert defaultdicts to regular dicts for JSON
        m = dict(self.metrics)
        m['by_category'] = dict(m.get('by_category', {}))
        m['by_category_success'] = dict(m.get('by_category_success', {}))
        with open(METRICS_FILE, 'w') as f:
            json.dump(m, f, indent=2)

    def record_outcome(self, task_id, task_title, category, success, details=None):
        """Record the outcome of a completed task."""
        entry = {
            'timestamp': now_iso(),
            'task_id': task_id,
            'task_title': task_title,
            'category': category,
            'success': success,
            'details': details or {},
        }

        # Append to episodic memory
        with open(EPISODIC_MEMORY, 'a') as f:
            f.write(json.dumps(entry) + '\n')
        self.memories.append(entry)

        # Update metrics
        self.metrics['total_tasks'] += 1
        if success:
            self.metrics['successful'] += 1
            self.metrics['by_category_success'][category] = \
                self.metrics['by_category_success'].get(category, 0) + 1
        else:
            self.metrics['failed'] += 1
            # Analyze failure
            analysis = self._analyze_failure(entry)
            entry['failure_analysis'] = analysis
            if analysis:
                self.metrics['common_failures'].append({
                    'task_id': task_id,
                    'category': category,
                    'root_cause': analysis.get('root_cause'),
                    'timestamp': now_iso(),
                })

        self.metrics['by_category'][category] = \
            self.metrics['by_category'].get(category, 0) + 1
        total = self.metrics['total_tasks']
        self.metrics['success_rate'] = round(self.metrics['successful'] / total, 3) if total else 0

        # Record in history (keep last 100)
        self.metrics['history'].append({
            'timestamp': now_iso(),
            'task_id': task_id,
            'success': success,
            'category': category,
        })
        self.metrics['history'] = self.metrics['history'][-100:]

        self._save_metrics()
        log(f"Recorded outcome: {task_id} → {'SUCCESS' if success else 'FAILURE'} "
            f"(rate: {self.metrics['success_rate']:.1%})")

        # If successful, check for skill-worthy patterns
        if success:
            self._check_skill_worthy(entry)

        return entry

    def _analyze_failure(self, entry):
        """Analyze a failure to find root cause."""
        details = entry.get('details', {})
        analysis = {'root_cause': None, 'pattern': None, 'suggestion': None}

        error_text = details.get('error', '') + ' ' + details.get('stderr', '')
        error_lower = error_text.lower()

        # Common failure patterns
        patterns = [
            ('compile_error', ['error:', 'cannot find', 'expected', 'mismatched types',
                               'cargo: error', 'tsc: error'],
             'Compilation error — check syntax and types'),
            ('test_failure', ['test failed', 'assert', 'expect', 'failed:'],
             'Test failure — check test assertions and logic'),
            ('dependency_error', ['module not found', 'cannot resolve', 'no such file',
                                  'package not found'],
             'Dependency error — check imports and package.json/Cargo.toml'),
            ('timeout', ['timeout', 'timed out', 'deadline exceeded'],
             'Timeout — operation took too long, may need optimization'),
            ('permission_error', ['permission denied', 'unauthorized', 'forbidden'],
             'Permission error — check credentials and access control'),
            ('network_error', ['connection refused', 'econnrefused', 'enotfound',
                               'network error'],
             'Network error — check connectivity and endpoints'),
            ('merge_conflict', ['conflict', 'merge conflict', 'CONFLICT'],
             'Merge conflict — resolve manually or rebase'),
        ]

        for pattern_name, keywords, suggestion in patterns:
            if any(kw in error_lower for kw in keywords):
                analysis['root_cause'] = pattern_name
                analysis['pattern'] = suggestion
                analysis['suggestion'] = f"Next time: {suggestion}. " \
                    f"Consider adding a pre-check step."
                break

        if not analysis['root_cause']:
            analysis['root_cause'] = 'unknown'
            analysis['suggestion'] = 'No pattern matched — manual investigation needed'

        return analysis

    def _check_skill_worthy(self, entry):
        """Check if a successful task contains a pattern worth turning into a skill."""
        details = entry.get('details', {})
        title = entry.get('task_title', '').lower()
        category = entry.get('category', '')

        # Heuristics for skill-worthy tasks
        skill_worthy = False
        skill_name = None
        skill_description = None

        # Pattern: successfully fixed a recurring issue
        similar_failures = [m for m in self.memories[-20:]
                           if m.get('category') == category and not m.get('success', True)]
        if len(similar_failures) >= 2:
            skill_worthy = True
            skill_name = f"fix-{category}-pattern"
            skill_description = f"Pattern for resolving {category} issues: " \
                f"based on {len(similar_failures)} past failures"

        # Pattern: successfully implemented a feature with specific approach
        if any(w in title for w in ['implement', 'add', 'create', 'build']):
            if details.get('approach'):
                skill_worthy = True
                skill_name = f"build-{category}-feature"
                skill_description = f"Approach for building {category} features"

        if skill_worthy:
            suggestion = {
                'timestamp': now_iso(),
                'task_id': entry['task_id'],
                'suggested_skill_name': skill_name,
                'description': skill_description,
                'evidence': f"Successful task in category '{category}'",
                'auto_generated': True,
            }
            with open(SKILL_SUGGESTIONS, 'a') as f:
                f.write(json.dumps(suggestion) + '\n')
            self.metrics['skill_suggestions_generated'] += 1
            log(f"Skill suggestion generated: {skill_name}")

    def analyze_trends(self):
        """Analyze trends in episodic memory to find improvement opportunities."""
        log("Analyzing trends in episodic memory...")

        if len(self.memories) < 5:
            log("Not enough data for trend analysis (need 5+ memories)")
            return {'status': 'insufficient_data', 'memories': len(self.memories)}

        # Success rate by category
        by_cat = defaultdict(lambda: {'total': 0, 'success': 0})
        for m in self.memories:
            cat = m.get('category', 'unknown')
            by_cat[cat]['total'] += 1
            if m.get('success'):
                by_cat[cat]['success'] += 1

        # Find worst-performing categories
        worst = []
        for cat, stats in by_cat.items():
            if stats['total'] >= 2:
                rate = stats['success'] / stats['total']
                worst.append((cat, rate, stats['total']))
        worst.sort(key=lambda x: x[1])

        # Common failure root causes
        failure_causes = Counter()
        for m in self.memories:
            if not m.get('success') and m.get('failure_analysis'):
                failure_causes[m['failure_analysis'].get('root_cause', 'unknown')] += 1

        # Recent trend (last 10 vs previous 10)
        recent = self.memories[-10:]
        previous = self.memories[-20:-10] if len(self.memories) >= 20 else []
        recent_rate = sum(1 for m in recent if m.get('success')) / len(recent) if recent else 0
        previous_rate = sum(1 for m in previous if m.get('success')) / len(previous) if previous else 0
        trend = 'improving' if recent_rate > previous_rate else \
                'declining' if recent_rate < previous_rate else 'stable'

        analysis = {
            'timestamp': now_iso(),
            'total_memories': len(self.memories),
            'overall_success_rate': round(
                sum(1 for m in self.memories if m.get('success')) / len(self.memories), 3),
            'recent_success_rate': round(recent_rate, 3),
            'previous_success_rate': round(previous_rate, 3),
            'trend': trend,
            'by_category': {cat: {'rate': round(s['success']/s['total'], 3),
                                  'total': s['total']}
                           for cat, s in by_cat.items()},
            'worst_categories': [{'category': w[0], 'rate': round(w[1], 3),
                                  'count': w[2]} for w in worst[:3]],
            'common_failure_causes': failure_causes.most_common(5),
            'recommendations': self._generate_recommendations(worst, failure_causes, trend),
        }

        return analysis

    def _generate_recommendations(self, worst_categories, failure_causes, trend):
        """Generate actionable recommendations based on trends."""
        recs = []

        # Recommend focusing on worst categories
        for cat, rate, count in worst_categories[:2]:
            if rate < 0.5:
                recs.append({
                    'type': 'focus_area',
                    'priority': 'high',
                    'message': f"Category '{cat}' has {rate:.0%} success rate ({count} tasks). "
                               f"Consider adding pre-checks or a dedicated skill.",
                })

        # Recommend addressing common failure causes
        for cause, count in failure_causes.most_common(3):
            if count >= 2:
                recs.append({
                    'type': 'failure_pattern',
                    'priority': 'medium',
                    'message': f"Failure pattern '{cause}' occurred {count} times. "
                               f"Add a validation step before dispatching similar tasks.",
                })

        # Trend-based recommendation
        if trend == 'declining':
            recs.append({
                'type': 'trend_alert',
                'priority': 'high',
                'message': "Success rate is declining. Review recent failures and "
                           "consider pausing autonomous dispatch until pattern is identified.",
            })
        elif trend == 'improving':
            recs.append({
                'type': 'positive',
                'priority': 'low',
                'message': "Success rate is improving. Current approach is working well.",
            })

        return recs

    def get_skill_suggestions(self):
        """Get pending skill suggestions."""
        suggestions = []
        if SKILL_SUGGESTIONS.exists():
            for line in SKILL_SUGGESTIONS.read_text().strip().split('\n'):
                if line:
                    try:
                        suggestions.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return suggestions

    def get_metrics(self):
        """Get current performance metrics."""
        return self.metrics


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Self-Improvement Loop — Layer 4")
    parser.add_argument('command', choices=['record', 'analyze', 'metrics', 'suggestions'])
    parser.add_argument('--task-id', required=False)
    parser.add_argument('--title', required=False)
    parser.add_argument('--category', default='unknown')
    parser.add_argument('--success', choices=['true', 'false'], default='true')
    parser.add_argument('--error', help="Error message for failures")
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()

    si = SelfImprovement()

    if args.command == 'record':
        result = si.record_outcome(
            args.task_id or f"task-{now_iso()}",
            args.title or "Untitled task",
            args.category,
            args.success == 'true',
            {'error': args.error or ''} if args.error else {}
        )
        print(json.dumps(result, indent=2) if args.json else
              f"Recorded: {result['task_id']} → {'SUCCESS' if result['success'] else 'FAILURE'}")

    elif args.command == 'analyze':
        analysis = si.analyze_trends()
        if args.json:
            print(json.dumps(analysis, indent=2))
        else:
            print(f"=== Trend Analysis ({analysis.get('total_memories', 0)} memories) ===")
            print(f"Overall success rate: {analysis.get('overall_success_rate', 0):.1%}")
            print(f"Recent trend: {analysis.get('trend', '?')}")
            print(f"Recent rate: {analysis.get('recent_success_rate', 0):.1%} vs "
                  f"previous: {analysis.get('previous_success_rate', 0):.1%}")
            if analysis.get('worst_categories'):
                print("\nWorst categories:")
                for w in analysis['worst_categories']:
                    print(f"  {w['category']}: {w['rate']:.0%} ({w['count']} tasks)")
            if analysis.get('recommendations'):
                print("\nRecommendations:")
                for r in analysis['recommendations']:
                    print(f"  [{r['priority']}] {r['message']}")

    elif args.command == 'metrics':
        m = si.get_metrics()
        print(json.dumps(m, indent=2) if args.json else
              f"Total tasks: {m['total_tasks']}\nSuccessful: {m['successful']}\n"
              f"Failed: {m['failed']}\nSuccess rate: {m['success_rate']:.1%}\n"
              f"Skill suggestions: {m.get('skill_suggestions_generated', 0)}")

    elif args.command == 'suggestions':
        suggestions = si.get_skill_suggestions()
        if args.json:
            print(json.dumps(suggestions, indent=2))
        else:
            for s in suggestions:
                print(f"[{s['timestamp']}] {s['suggested_skill_name']}: {s['description']}")


if __name__ == '__main__':
    main()
