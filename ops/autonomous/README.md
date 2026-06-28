# GoalWorld Autonomous Agent — 5-Layer Architecture

## Overview

A fully autonomous 24/7 agent system that understands the codebase, decides what to build,
self-improves, and operates continuously without human intervention.

## Layers

### Layer 1: Codebase Brain (codebase_brain.py)
- AST-based repo indexing via tree-sitter (Rust, TypeScript, JavaScript, Python)
- SQLite FTS5 full-text search over all symbols
- TF-IDF vector similarity for semantic code search (numpy + sklearn)
- Cross-package dependency graph (Rust program → SDK → API → Webapp → Scripts)
- Auto-reindex on git push via post-commit hook
- Queryable: "where is place_bet implemented?" → exact file:line

### Layer 2: Project State Awareness (state_awareness.py)
- Continuous monitoring: tests, builds, deploys, API health, on-chain program health
- Backlog autogeneration: TODOs, FIXMEs, failing tests, stale PRs, open issues
- Priority matrix: impact × effort × strategic alignment (Mundial 2026)

### Layer 3: Decision Engine (decision_engine.py)
- Autonomous goal decomposition: project vision → milestones → tasks
- Dynamic priority queue that reorders based on: blockers, dependencies, strategic value, resources
- Decision log: every autonomous decision recorded with rationale (auditable)

### Layer 4: Self-Improvement Loop (self_improvement.py)
- Post-task evaluation: did tests pass? deploy work? review clean?
- Failure analysis: root cause + what to do differently
- Auto-skill generation: successful patterns → new skills
- Episodic memory: "when I tried X, Y happened" — queryable

### Layer 5: Continuous Operation Loop (autonomous_loop.py)
- Heartbeat cycle: scan state → update queue → pick task → decompose → dispatch → monitor → review → merge/reject → update memory → self-assess
- Runs every 30 minutes via systemd timer
- Escalates to Nico only when truly blocked

## Data Storage

All state in `data/`:
- `codebase.db` — SQLite: symbols, FTS5 index, dependency graph
- `state.json` — current project state snapshot
- `decision_log.jsonl` — append-only decision history
- `episodic_memory.jsonl` — append-only episodic memory
- `priority_queue.json` — current task queue
- `metrics.json` — performance metrics over time

## Integration

- Uses existing `create-task.sh` for dispatching to Hermes CEO
- Uses existing `healthcheck.sh` for health data
- Uses existing `local-issue-queue.sh` for task tracking
- Posts to Discord #hermes-reports via `hermes_reporter.py`
- GBrain integration for institutional memory
