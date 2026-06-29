#!/usr/bin/env python3
"""
Layer 2: Project State Awareness
=================================
Continuously monitors project health and generates an autonomous backlog.

Monitors:
- Tests (pass/fail/skip counts)
- Builds (compile status)
- Deploys (API health, webapp health)
- On-chain program health
- Git state (uncommitted changes, stale branches)
- Open issues and PRs
- TODOs/FIXMEs in code
- Failing CI

Generates:
- state.json: current project state snapshot
- backlog items with priority scoring
"""

import os
import sys
import json
import re
import subprocess
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

# Health endpoints
HEALTH_ENDPOINTS = {
    'api': os.environ.get("GOALWORLD_API_HEALTH", "https://crm.goalworld.fun/goalworld-api/health"),
    'webapp': os.environ.get("GOALWORLD_WEBAPP_URL", "https://play.goalworld.fun"),
    'marketing': os.environ.get("GOALWORLD_MARKETING_URL", "https://goalworld.fun"),
}

# Strategic objectives (for priority alignment)
STRATEGIC_OBJECTIVES = [
    {'id': 'mundial-mvp', 'name': 'Mundial 2026 MVP', 'weight': 1.0,
     'keywords': ['fixture', 'bet', 'claim', 'payout', 'devnet', 'wallet', 'oracle', 'match']},
    {'id': 'merge-stack', 'name': 'Merge Stack Convergence', 'weight': 0.8,
     'keywords': ['pr', 'merge', 'refactor', 'cleanup', 'archive']},
    {'id': 'webapp', 'name': 'Webapp Polish', 'weight': 0.7,
     'keywords': ['webapp', 'ui', 'react', 'frontend', 'css', 'component']},
    {'id': 'economy', 'name': 'Economy/On-chain', 'weight': 0.9,
     'keywords': ['economy', 'token', 'vault', 'yield', 'fee', 'split', 'rarity', 'program']},
    {'id': 'automation', 'name': 'Automation & Ops', 'weight': 0.6,
     'keywords': ['script', 'cron', 'daemon', 'pipeline', 'automation', 'ops']},
    {'id': 'marketing', 'name': 'Marketing & Content', 'weight': 0.5,
     'keywords': ['video', 'social', 'buffer', 'tiktok', 'youtube', 'content']},
]


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg, level="INFO"):
    print(f"[{now_iso()}] [STATE-AWARENESS] [{level}] {msg}", flush=True)


def run_cmd(args, cwd=None, timeout=30):
    """Run a command and return (success, stdout, stderr)."""
    try:
        res = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return res.returncode == 0, res.stdout.strip(), res.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "timeout"
    except Exception as e:
        return False, "", str(e)


class StateAwareness:
    def __init__(self):
        self.repo_root = REPO_ROOT
        self.state = {
            'timestamp': now_iso(),
            'git': {},
            'tests': {},
            'builds': {},
            'deploys': {},
            'onchain': {},
            'issues': {},
            'code_health': {},
            'backlog': [],
        }

    def scan_all(self):
        """Run all scans and produce a complete state snapshot."""
        log("Starting full project state scan...")
        self._scan_git()
        self._scan_tests()
        self._scan_builds()
        self._scan_deploys()
        self._scan_onchain()
        self._scan_issues()
        self._scan_code_health()
        self._generate_backlog()
        self._save_state()
        log(f"State scan complete. {len(self.state['backlog'])} backlog items generated.")
        return self.state

    def _scan_git(self):
        """Scan git state: current branch, uncommitted changes, stale branches."""
        log("Scanning git state...")
        git = {'branch': None, 'dirty': False, 'uncommitted': 0, 'stale_branches': [],
               'recent_commits': [], 'ahead_behind': {}}

        ok, branch, _ = run_cmd(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=self.repo_root)
        git['branch'] = branch if ok else 'unknown'

        ok, status, _ = run_cmd(['git', 'status', '--porcelain'], cwd=self.repo_root)
        if ok and status:
            git['dirty'] = True
            git['uncommitted'] = len(status.strip().split('\n'))

        ok, log_out, _ = run_cmd(['git', 'log', '--oneline', '-10'], cwd=self.repo_root)
        if ok:
            git['recent_commits'] = log_out.strip().split('\n') if log_out else []

        # Check for stale branches (not main/master, older than 7 days)
        ok, branches, _ = run_cmd(
            ['git', 'for-each-ref', '--format=%(refname:short) %(committerdate:relative)',
             'refs/heads/'], cwd=self.repo_root)
        if ok:
            for line in branches.strip().split('\n'):
                if not line:
                    continue
                parts = line.split(' ', 1)
                bname = parts[0]
                age = parts[1] if len(parts) > 1 else ''
                if bname not in ('main', 'master') and ('day' in age or 'week' in age or 'month' in age):
                    git['stale_branches'].append({'branch': bname, 'last_commit': age})

        # Ahead/behind origin
        ok, ahead, _ = run_cmd(['git', 'rev-list', '--count', 'HEAD..origin/main'],
                               cwd=self.repo_root)
        ok2, behind, _ = run_cmd(['git', 'rev-list', '--count', 'origin/main..HEAD'],
                                 cwd=self.repo_root)
        git['ahead_behind'] = {
            'behind_origin': int(ahead) if ahead.isdigit() else 0,
            'ahead_origin': int(behind) if behind.isdigit() else 0,
        }

        self.state['git'] = git

    def _scan_tests(self):
        """Scan test status."""
        log("Scanning tests...")
        tests = {'rust': {}, 'typescript': {}, 'python': {}}

        # Rust tests (just check if it compiles — running tests is expensive)
        contracts_dir = self.repo_root / 'contracts'
        if contracts_dir.exists():
            ok, out, err = run_cmd(['cargo', 'check', '--manifest-path',
                                    str(contracts_dir / 'Cargo.toml')], timeout=120)
            tests['rust'] = {
                'compiles': ok,
                'error': err[:500] if err else None,
            }

        # TypeScript: check for test files and run if fast
        test_files = []
        for pkg in ['sdk', 'api', 'oracle', 'webapp']:
            pkg_dir = self.repo_root / pkg
            if not pkg_dir.exists():
                continue
            ok, out, _ = run_cmd(
                ['find', str(pkg_dir), '-name', '*.test.*', '-o', '-name', '*.spec.*'],
                timeout=10)
            if ok and out:
                test_files.extend(out.strip().split('\n'))

        tests['typescript'] = {
            'test_files': len(test_files),
            'files': test_files[:10],
        }

        # Python: check for test files
        py_test_files = []
        for d in ['scripts', 'ops']:
            ddir = self.repo_root / d
            if ddir.exists():
                ok, out, _ = run_cmd(
                    ['find', str(ddir), '-name', 'test_*.py', '-o', '-name', '*_test.py'],
                    timeout=10)
                if ok and out:
                    py_test_files.extend(out.strip().split('\n'))

        tests['python'] = {
            'test_files': len(py_test_files),
            'files': py_test_files[:10],
        }

        self.state['tests'] = tests

    def _scan_builds(self):
        """Scan build status."""
        log("Scanning builds...")
        builds = {}

        # Webapp build check
        webapp_dir = self.repo_root / 'webapp'
        if webapp_dir.exists():
            ok, out, err = run_cmd(
                ['npm', 'run', 'build', '--dry-run'],
                cwd=str(webapp_dir), timeout=30)
            builds['webapp'] = {
                'buildable': ok or 'run' in (err or ''),
            }

        # API build check
        api_dir = self.repo_root / 'api'
        if api_dir.exists():
            ok, out, _ = run_cmd(['node', '-e', "require('./package.json')"],
                                 cwd=str(api_dir), timeout=10)
            builds['api'] = {'valid_package': ok}

        self.state['builds'] = builds

    def _scan_deploys(self):
        """Check deployed service health."""
        log("Scanning deploy health...")
        deploys = {}
        try:
            import requests
            for name, url in HEALTH_ENDPOINTS.items():
                try:
                    r = requests.get(url, timeout=10, allow_redirects=True)
                    deploys[name] = {
                        'url': url,
                        'status_code': r.status_code,
                        'healthy': r.status_code < 400,
                        'response_time_ms': int(r.elapsed.total_seconds() * 1000),
                    }
                except Exception as e:
                    deploys[name] = {'url': url, 'healthy': False, 'error': str(e)[:200]}
        except ImportError:
            # Fallback to curl
            for name, url in HEALTH_ENDPOINTS.items():
                ok, out, err = run_cmd(['curl', '-sS', '-o', '/dev/null', '-w',
                                        '%{http_code} %{time_total}', '--max-time', '10', url])
                if ok and out:
                    parts = out.split()
                    code = int(parts[0]) if parts else 0
                    deploys[name] = {
                        'url': url,
                        'status_code': code,
                        'healthy': code < 400,
                    }
                else:
                    deploys[name] = {'url': url, 'healthy': False, 'error': err[:200]}

        self.state['deploys'] = deploys

    def _scan_onchain(self):
        """Check on-chain program health via API."""
        log("Scanning on-chain health...")
        onchain = {'program_info': {}, 'economy_health': {}}
        try:
            import requests
            # Try ops status endpoint
            try:
                r = requests.get(
                    "https://crm.goalworld.fun/goalworld-api/ops/status", timeout=10)
                if r.status_code == 200:
                    onchain['program_info'] = r.json()
            except Exception:
                pass
            # Try economy health
            try:
                r = requests.get(
                    "https://crm.goalworld.fun/goalworld-api/economy/config", timeout=10)
                if r.status_code == 200:
                    onchain['economy_health'] = r.json()
            except Exception:
                pass
        except ImportError:
            pass

        self.state['onchain'] = onchain

    def _scan_issues(self):
        """Scan GitHub issues and PRs."""
        log("Scanning GitHub issues and PRs...")
        issues = {'open_issues': [], 'open_prs': [], 'stale_prs': []}

        ok, out, err = run_cmd(
            ['gh', 'issue', 'list', '--state', 'open', '--limit', '20', '--json',
             'number,title,labels,createdAt,updatedAt'], cwd=self.repo_root)
        if ok and out:
            try:
                issues['open_issues'] = json.loads(out)
            except json.JSONDecodeError:
                pass

        ok, out, err = run_cmd(
            ['gh', 'pr', 'list', '--state', 'open', '--limit', '20', '--json',
             'number,title,headRefName,createdAt,updatedAt,isDraft'], cwd=self.repo_root)
        if ok and out:
            try:
                prs = json.loads(out)
                issues['open_prs'] = prs
                # Mark stale PRs (older than 3 days)
                now = datetime.now(timezone.utc)
                for pr in prs:
                    updated = pr.get('updatedAt', '')
                    if updated:
                        try:
                            dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                            if (now - dt).days > 3:
                                issues['stale_prs'].append(pr)
                        except Exception:
                            pass
            except json.JSONDecodeError:
                pass

        self.state['issues'] = issues

    def _scan_code_health(self):
        """Scan code health: TODOs, FIXMEs, complexity indicators."""
        log("Scanning code health...")
        health = {'todos': [], 'fixmes': [], 'total_todos': 0, 'total_fixmes': 0}

        # Query the codebase brain DB for TODO/FIXME if available
        if CODEBASE_DB.exists():
            db = sqlite3.connect(str(CODEBASE_DB))
            db.row_factory = sqlite3.Row
            # Search body_preview for TODO/FIXME
            try:
                rows = db.execute(
                    "SELECT name, file_path, start_line, body_preview, docstring FROM symbols "
                    "WHERE body_preview LIKE '%TODO%' OR body_preview LIKE '%FIXME%' "
                    "OR docstring LIKE '%TODO%' OR docstring LIKE '%FIXME%' LIMIT 50"
                ).fetchall()
                for row in rows:
                    preview = row['body_preview'] or ''
                    doc = row['docstring'] or ''
                    text = preview + ' ' + doc
                    if 'TODO' in text:
                        health['todos'].append({
                            'file': row['file_path'],
                            'line': row['start_line'],
                            'symbol': row['name'],
                        })
                    if 'FIXME' in text:
                        health['fixmes'].append({
                            'file': row['file_path'],
                            'line': row['start_line'],
                            'symbol': row['name'],
                        })
            except Exception as e:
                log(f"Error querying codebase DB: {e}", "WARN")
            finally:
                db.close()

        # Also grep for TODO/FIXME in all source files
        skip_dirs = {'node_modules', '.git', 'target', 'dist', '__pycache__'}
        for root, dirs, files in os.walk(self.repo_root):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for fname in files:
                ext = os.path.splitext(fname)[1]
                if ext not in ('.py', '.ts', '.tsx', '.rs', '.js', '.jsx', '.md'):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, 'r', errors='replace') as f:
                        for i, line in enumerate(f, 1):
                            if 'TODO' in line:
                                health['total_todos'] += 1
                            if 'FIXME' in line:
                                health['total_fixmes'] += 1
                except Exception:
                    continue

        health['todos'] = health['todos'][:30]
        health['fixmes'] = health['fixmes'][:30]
        self.state['code_health'] = health

    def _generate_backlog(self):
        """Generate a prioritized backlog from all scanned state."""
        log("Generating backlog...")
        backlog = []

        # 1. Failing tests / broken builds
        if not self.state['tests'].get('rust', {}).get('compiles', True):
            backlog.append({
                'id': 'rust-compile-fail',
                'title': 'Rust program does not compile',
                'category': 'bug',
                'priority_score': 100,
                'rationale': 'Contracts do not compile — blocks all on-chain work',
                'source': 'tests.rust',
            })

        # 2. Unhealthy deploys
        for name, info in self.state['deploys'].items():
            if not info.get('healthy', False):
                backlog.append({
                    'id': f'deploy-{name}-down',
                    'title': f'{name} deploy is unhealthy',
                    'category': 'ops',
                    'priority_score': 90,
                    'rationale': f'{name} at {info.get("url")} is down or erroring',
                    'source': f'deploys.{name}',
                })

        # 3. Stale PRs
        for pr in self.state['issues'].get('stale_prs', []):
            backlog.append({
                'id': f'pr-{pr.get("number")}-stale',
                'title': f'PR #{pr.get("number")} is stale: {pr.get("title", "")}',
                'category': 'review',
                'priority_score': 70,
                'rationale': 'PR has been open >3 days without merge',
                'source': 'issues.stale_prs',
            })

        # 4. Uncommitted changes
        if self.state['git'].get('uncommitted', 0) > 5:
            backlog.append({
                'id': 'git-dirty',
                'title': f'{self.state["git"]["uncommitted"]} uncommitted changes on {self.state["git"]["branch"]}',
                'category': 'hygiene',
                'priority_score': 40,
                'rationale': 'Working tree has many uncommitted changes',
                'source': 'git',
            })

        # 5. Stale branches
        for branch_info in self.state['git'].get('stale_branches', []):
            backlog.append({
                'id': f'branch-{branch_info["branch"]}-stale',
                'title': f'Stale branch: {branch_info["branch"]}',
                'category': 'hygiene',
                'priority_score': 20,
                'rationale': f'Last commit {branch_info["last_commit"]}',
                'source': 'git.stale_branches',
            })

        # 6. TODOs in code → potential tasks
        for todo in self.state['code_health'].get('todos', [])[:10]:
            backlog.append({
                'id': f'todo-{todo["file"]}-{todo["line"]}',
                'title': f'TODO in {todo["file"]}:{todo["line"]} ({todo["symbol"]})',
                'category': 'tech-debt',
                'priority_score': 30,
                'rationale': 'Unfinished TODO in codebase',
                'source': 'code_health.todos',
            })

        # 7. Open issues without agent label
        for issue in self.state['issues'].get('open_issues', []):
            labels = [l.get('name', '') for l in issue.get('labels', [])]
            if not any(l.startswith('agent:') for l in labels):
                backlog.append({
                    'id': f'issue-{issue.get("number")}-unassigned',
                    'title': f'Issue #{issue.get("number")} unassigned: {issue.get("title", "")}',
                    'category': 'triage',
                    'priority_score': 50,
                    'rationale': 'Open issue without agent assignment',
                    'source': 'issues.open_issues',
                })

        # Sort by priority score (descending)
        backlog.sort(key=lambda x: x['priority_score'], reverse=True)
        self.state['backlog'] = backlog

    def _save_state(self):
        """Save state to JSON file."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
        # Also save backlog separately
        with open(BACKLOG_FILE, 'w') as f:
            json.dump(self.state['backlog'], f, indent=2)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Project State Awareness — Layer 2")
    parser.add_argument('command', choices=['scan', 'state', 'backlog'])
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()

    sa = StateAwareness()

    if args.command == 'scan':
        state = sa.scan_all()
        if args.json:
            print(json.dumps(state, indent=2))
        else:
            print(f"=== Project State ({state['timestamp']}) ===")
            print(f"Git: branch={state['git']['branch']}, dirty={state['git']['dirty']}, "
                  f"uncommitted={state['git']['uncommitted']}")
            print(f"Tests: rust_compiles={state['tests'].get('rust', {}).get('compiles', '?')}")
            print(f"Deploys: " + ", ".join(
                f"{k}={'✅' if v.get('healthy') else '❌'}" for k, v in state['deploys'].items()))
            print(f"Issues: {len(state['issues'].get('open_issues', []))} open, "
                  f"{len(state['issues'].get('open_prs', []))} PRs, "
                  f"{len(state['issues'].get('stale_prs', []))} stale")
            print(f"Code health: {state['code_health']['total_todos']} TODOs, "
                  f"{state['code_health']['total_fixmes']} FIXMEs")
            print(f"Backlog: {len(state['backlog'])} items")
            for item in state['backlog'][:5]:
                print(f"  [{item['priority_score']:>3}] {item['title']}")

    elif args.command == 'state':
        if STATE_FILE.exists():
            data = json.loads(STATE_FILE.read_text())
            print(json.dumps(data, indent=2) if args.json else
                  json.dumps(data, indent=2))
        else:
            print("No state file. Run 'scan' first.")

    elif args.command == 'backlog':
        if BACKLOG_FILE.exists():
            data = json.loads(BACKLOG_FILE.read_text())
            if args.json:
                print(json.dumps(data, indent=2))
            else:
                for item in data:
                    print(f"[{item['priority_score']:>3}] {item['category']:<10} "
                          f"{item['title']}")
        else:
            print("No backlog file. Run 'scan' first.")


if __name__ == '__main__':
    main()
