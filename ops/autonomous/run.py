#!/usr/bin/env python3
"""
Entry point for the autonomous loop.
Usage:
    python3 run.py cycle       # Run one cycle
    python3 run.py dry-run     # Dry run (no dispatch, no reports)
    python3 run.py status      # Show loop status
    python3 run.py reindex     # Force codebase reindex
    python3 run.py search <q>  # Search codebase
    python3 run.py state       # Show project state
    python3 run.py queue       # Show priority queue
    python3 run.py assess      # Self-assessment
"""
import sys
import os
from pathlib import Path

# Add lib to path
SCRIPT_DIR = Path(__file__).resolve().parent
LIB_DIR = SCRIPT_DIR / "lib"
sys.path.insert(0, str(LIB_DIR))

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd in ('cycle', 'dry-run', 'status'):
        from autonomous_loop import AutonomousLoop
        loop = AutonomousLoop()
        if cmd == 'cycle':
            result = loop.run_cycle(dry_run=False)
            print(loop._build_cycle_summary(result))
        elif cmd == 'dry-run':
            result = loop.run_cycle(dry_run=True)
            print(loop._build_cycle_summary(result))
        elif cmd == 'status':
            state = loop.loop_state
            print(f"Cycle count: {state.get('cycle_count', 0)}")
            print(f"Last cycle: {state.get('last_cycle', 'never')}")
            print(f"Dispatched tasks: {len(state.get('dispatched_tasks', []))}")
            print(f"Paused: {state.get('autonomous_dispatch_paused', False)}")

    elif cmd == 'reindex':
        from codebase_brain import CodebaseBrain
        brain = CodebaseBrain()
        result = brain.index(force=True)
        brain.close()
        print(f"Indexed: {result['files']} files, {result['symbols']} symbols, "
              f"{result['deps']} deps in {result['elapsed_s']}s")

    elif cmd == 'search':
        if not args:
            print("Usage: search <query>")
            sys.exit(1)
        from codebase_brain import CodebaseBrain
        brain = CodebaseBrain()
        results = brain.search(' '.join(args))
        for r in results:
            print(f"  {r.get('score', 0):.2f}  {r['package']}:{r['file_path']}:{r['start_line']}  "
                  f"{r['kind']}  {r['name']}")
        brain.close()

    elif cmd == 'semantic':
        if not args:
            print("Usage: semantic <query>")
            sys.exit(1)
        from codebase_brain import CodebaseBrain
        brain = CodebaseBrain()
        results = brain.semantic_search(' '.join(args))
        for r in results:
            print(f"  {r['similarity']:.3f}  {r['package']}:{r['file_path']}:{r['start_line']}  "
                  f"{r['kind']}  {r['name']}")
        brain.close()

    elif cmd == 'state':
        from state_awareness import StateAwareness
        sa = StateAwareness()
        state = sa.scan_all()
        print(f"Git: {state['git']['branch']}, dirty={state['git']['dirty']}")
        print(f"Deploys: " + ', '.join(
            f"{k}={'✅' if v.get('healthy') else '❌'}" for k, v in state['deploys'].items()))
        print(f"Backlog: {len(state['backlog'])} items")
        for item in state['backlog'][:5]:
            print(f"  [{item['priority_score']:>3}] {item['title']}")

    elif cmd == 'queue':
        from decision_engine import DecisionEngine
        engine = DecisionEngine()
        queue = engine.run()
        for item in queue:
            ready = '⚡' if item.get('dispatch_ready') else '  '
            print(f"  {ready} [{item['priority_score']:>5}] {item['category']:<10} {item['title']}")

    elif cmd == 'assess':
        from self_improvement import SelfImprovement
        si = SelfImprovement()
        analysis = si.analyze_trends()
        print(f"Success rate: {analysis.get('overall_success_rate', 0):.1%}")
        print(f"Trend: {analysis.get('trend', '?')}")
        for r in analysis.get('recommendations', []):
            print(f"  [{r['priority']}] {r['message']}")

    elif cmd == 'map':
        from codebase_brain import CodebaseBrain
        brain = CodebaseBrain()
        print(brain.get_repo_map())
        brain.close()

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
