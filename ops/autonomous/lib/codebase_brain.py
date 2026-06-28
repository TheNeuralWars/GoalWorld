#!/usr/bin/env python3
"""
Layer 1: Codebase Brain
=======================
AST-based repo indexing + semantic search + dependency graph.

Indexes all source files via tree-sitter, builds:
1. SQLite FTS5 full-text search over symbols
2. TF-IDF vector similarity for semantic search
3. Cross-package dependency graph

Queryable API:
    brain = CodebaseBrain(repo_root)
    brain.index()                          # full reindex
    brain.search("place_bet")              # FTS5 keyword search
    brain.semantic_search("how bets are placed on-chain")  # TF-IDF similarity
    brain.get_symbol("place_bet")          # exact symbol lookup
    brain.get_dependencies("goalworld_program/lib.rs")  # dependency graph
    brain.get_repo_map()                   # Aider-style repo map
"""

import os
import sys
import json
import sqlite3
import hashlib
import re
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# tree-sitter
import tree_sitter_python
import tree_sitter_typescript
import tree_sitter_rust
import tree_sitter_javascript
from tree_sitter import Language, Parser

# ─── Config ───────────────────────────────────────────────────────────────────

REPO_ROOT = Path(os.environ.get("GOALWORLD_REPO_PATH", "/data/apps/GoalWorld"))
DB_PATH = Path(os.environ.get("AUTONOMOUS_DATA_DIR",
    str(REPO_ROOT / "ops" / "autonomous" / "data" / "codebase.db")))

# Languages and their tree-sitter modules
LANGUAGES = {
    '.py':  ('python',     tree_sitter_python.language()),
    '.ts':  ('typescript', tree_sitter_typescript.language_typescript()),
    '.tsx': ('typescript', tree_sitter_typescript.language_typescript()),
    '.rs':  ('rust',       tree_sitter_rust.language()),
    '.js':  ('javascript', tree_sitter_javascript.language()),
    '.jsx': ('javascript', tree_sitter_javascript.language()),
}

# Node types that represent "symbols" we want to index
SYMBOL_NODE_TYPES = {
    'python':     {'function_definition', 'class_definition', 'decorated_definition',
                   'assignment'},
    'typescript': {'function_declaration', 'class_declaration', 'interface_declaration',
                   'type_alias_declaration', 'enum_declaration', 'method_definition',
                   'variable_declaration', 'export_statement', 'import_statement'},
    'rust':       {'function_item', 'struct_item', 'enum_item', 'impl_item',
                   'trait_item', 'macro_definition', 'const_item', 'static_item',
                   'module_declaration', 'use_declaration'},
    'javascript': {'function_declaration', 'class_declaration', 'method_definition',
                   'variable_declaration', 'export_statement', 'import_statement'},
}

# Directories to skip
SKIP_DIRS = {
    'node_modules', '.git', 'target', 'dist', '__pycache__', '.next', 'build',
    '.cache', 'coverage', '.turbo', '.vercel', 'vendor', 'third_party',
    '.docusaurus', '.parcel-cache', 'out',
}

# File patterns to skip
SKIP_PATTERNS = {'.min.js', '.min.css', '.map', '.lock', '.svg', '.png', '.jpg',
                 '.jpeg', '.gif', '.ico', '.woff', '.woff2', '.ttf', '.eot',
                 '.mp4', '.webm', '.webp', '.pdf'}

# Packages in the monorepo and their entry points
PACKAGES = {
    'contracts':  {'path': 'contracts',         'lang': 'rust',       'desc': 'Solana program (Anchor)'},
    'sdk':        {'path': 'sdk',               'lang': 'typescript', 'desc': 'TypeScript SDK'},
    'oracle':     {'path': 'oracle',            'lang': 'typescript', 'desc': 'Oracle (Node.js)'},
    'api':        {'path': 'api',               'lang': 'typescript', 'desc': 'API (Express)'},
    'webapp':     {'path': 'webapp',            'lang': 'typescript', 'desc': 'Webapp (React/Vite)'},
    'scripts':    {'path': 'scripts',           'lang': 'python',     'desc': 'Automation scripts'},
    'ops':        {'path': 'ops',               'lang': 'python',     'desc': 'Ops & automation'},
    'docs':       {'path': 'docs',              'lang': None,         'desc': 'Documentation'},
    'ai_context': {'path': 'ai_context',        'lang': None,         'desc': 'AI context / economy docs'},
}


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg, level="INFO"):
    print(f"[{now_iso()}] [CODEBASE-BRAIN] [{level}] {msg}", flush=True)


# ─── CodebaseBrain ────────────────────────────────────────────────────────────

class CodebaseBrain:
    def __init__(self, repo_root=None, db_path=None):
        self.repo_root = Path(repo_root or REPO_ROOT)
        self.db_path = Path(db_path or DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._parsers = {}
        self._init_parsers()
        self._init_db()
        self._tfidf = None
        self._tfidf_matrix = None
        self._symbol_ids = None

    def _init_parsers(self):
        for ext, (lang_name, lang_obj) in LANGUAGES.items():
            try:
                lang = Language(lang_obj)
                parser = Parser(lang)
                self._parsers[ext] = (lang_name, parser)
            except Exception as e:
                log(f"Failed to init parser for {ext}: {e}", "WARN")

    def _init_db(self):
        self.db = sqlite3.connect(str(self.db_path))
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=NORMAL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS files (
                path TEXT PRIMARY KEY,
                package TEXT,
                language TEXT,
                line_count INTEGER,
                symbol_count INTEGER,
                file_hash TEXT,
                indexed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                qualified_name TEXT,
                kind TEXT,
                file_path TEXT NOT NULL,
                start_line INTEGER,
                end_line INTEGER,
                package TEXT,
                language TEXT,
                docstring TEXT,
                body_preview TEXT,
                FOREIGN KEY (file_path) REFERENCES files(path)
            );

            CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);
            CREATE INDEX IF NOT EXISTS idx_symbols_file ON symbols(file_path);
            CREATE INDEX IF NOT EXISTS idx_symbols_kind ON symbols(kind);
            CREATE INDEX IF NOT EXISTS idx_symbols_package ON symbols(package);

            CREATE VIRTUAL TABLE IF NOT EXISTS symbols_fts USING fts5(
                name, qualified_name, kind, docstring, body_preview, package,
                content='symbols', content_rowid='id'
            );

            CREATE TABLE IF NOT EXISTS dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT NOT NULL,
                source_symbol TEXT,
                target TEXT NOT NULL,
                target_kind TEXT,
                dep_type TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_deps_source ON dependencies(source_file);
            CREATE INDEX IF NOT EXISTS idx_deps_target ON dependencies(target);

            CREATE TABLE IF NOT EXISTS index_meta (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        """)
        self.db.commit()

    # ─── Indexing ─────────────────────────────────────────────────────────────

    def index(self, force=False):
        """Full reindex of the repository."""
        log(f"Starting {'forced ' if force else ''}reindex of {self.repo_root}")
        start = datetime.now(timezone.utc)

        # Clear existing data
        self.db.executescript("DELETE FROM symbols; DELETE FROM files; DELETE FROM dependencies;")
        self.db.execute("DELETE FROM symbols_fts;")
        self.db.commit()

        total_files = 0
        total_symbols = 0
        total_deps = 0

        for file_path, ext, lang_name, rel_path in self._walk_repo():
            total_files += 1
            try:
                syms, deps = self._index_file(file_path, ext, lang_name)
                total_symbols += syms
                total_deps += deps
            except Exception as e:
                log(f"Error indexing {file_path}: {e}", "WARN")

        # Update FTS index
        self._rebuild_fts()

        # Build TF-IDF for semantic search
        self._build_tfidf()

        # Record metadata
        self.db.execute(
            "INSERT OR REPLACE INTO index_meta(key, value) VALUES('last_index', ?)",
            (now_iso(),))
        self.db.execute(
            "INSERT OR REPLACE INTO index_meta(key, value) VALUES('total_files', ?)",
            (str(total_files),))
        self.db.execute(
            "INSERT OR REPLACE INTO index_meta(key, value) VALUES('total_symbols', ?)",
            (str(total_symbols),))
        self.db.commit()

        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        log(f"Index complete: {total_files} files, {total_symbols} symbols, "
            f"{total_deps} deps in {elapsed:.1f}s")
        return {'files': total_files, 'symbols': total_symbols, 'deps': total_deps,
                'elapsed_s': round(elapsed, 1)}

    def _walk_repo(self):
        """Walk the repo, yielding (file_path, ext, lang_name) for indexable files."""
        for root, dirs, files in os.walk(self.repo_root):
            # Skip excluded dirs in-place
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
            for fname in files:
                if any(fname.endswith(p) for p in SKIP_PATTERNS):
                    continue
                ext = os.path.splitext(fname)[1].lower()
                if ext not in LANGUAGES:
                    continue
                fpath = os.path.join(root, fname)
                rel_path = os.path.relpath(fpath, self.repo_root)
                lang_name = LANGUAGES[ext][0]
                yield fpath, ext, lang_name, rel_path

    def _index_file(self, fpath, ext, lang_name):
        """Index a single file: parse AST, extract symbols and dependencies."""
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                source = f.read()
        except Exception:
            return 0, 0

        if not source.strip():
            return 0, 0

        rel_path = os.path.relpath(fpath, self.repo_root)
        file_hash = hashlib.md5(source.encode()).hexdigest()
        line_count = source.count('\n') + 1
        package = self._detect_package(rel_path)

        # Parse with tree-sitter
        _, parser = self._parsers[ext]
        try:
            tree = parser.parse(source.encode())
        except Exception:
            return 0, 0

        # Extract symbols
        symbol_nodes = SYMBOL_NODE_TYPES.get(lang_name, set())
        symbols = []
        deps = []

        def walk(node):
            # Check if this node is a symbol we want
            if node.type in symbol_nodes:
                sym = self._extract_symbol(node, source, rel_path, lang_name, package)
                if sym:
                    symbols.append(sym)
                    # Extract dependencies from this symbol's body
                    sym_deps = self._extract_deps_from_node(node, source, lang_name)
                    for d in sym_deps:
                        deps.append((rel_path, sym['name'], d[0], d[1], d[2]))

            for child in node.children:
                walk(child)

        walk(tree.root_node)

        # Also extract file-level imports/dependencies
        file_deps = self._extract_file_deps(tree.root_node, source, lang_name)
        for d in file_deps:
            deps.append((rel_path, None, d[0], d[1], 'import'))

        # Insert file record
        self.db.execute(
            "INSERT OR REPLACE INTO files(path, package, language, line_count, symbol_count, file_hash, indexed_at) "
            "VALUES(?, ?, ?, ?, ?, ?, ?)",
            (rel_path, package, lang_name, line_count, len(symbols), file_hash, now_iso()))

        # Insert symbols
        for sym in symbols:
            cursor = self.db.execute(
                "INSERT INTO symbols(name, qualified_name, kind, file_path, start_line, end_line, "
                "package, language, docstring, body_preview) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (sym['name'], sym.get('qualified_name'), sym['kind'], rel_path,
                 sym['start_line'], sym['end_line'], package, lang_name,
                 sym.get('docstring'), sym.get('body_preview', '')[:500]))
            sym_id = cursor.lastrowid
            # Insert into FTS
            self.db.execute(
                "INSERT INTO symbols_fts(rowid, name, qualified_name, kind, docstring, body_preview, package) "
                "VALUES(?, ?, ?, ?, ?, ?, ?)",
                (sym_id, sym['name'], sym.get('qualified_name', ''), sym['kind'],
                 sym.get('docstring', ''), sym.get('body_preview', '')[:500], package))

        # Insert dependencies
        for dep in deps:
            self.db.execute(
                "INSERT INTO dependencies(source_file, source_symbol, target, target_kind, dep_type) "
                "VALUES(?, ?, ?, ?, ?)",
                dep)

        self.db.commit()
        return len(symbols), len(deps)

    def _detect_package(self, rel_path):
        """Detect which monorepo package a file belongs to."""
        parts = rel_path.split('/')
        for pkg_name, pkg_info in PACKAGES.items():
            pkg_path = pkg_info['path']
            if parts[0] == pkg_path or rel_path.startswith(pkg_path + '/'):
                return pkg_name
        return 'root'

    def _extract_symbol(self, node, source, file_path, lang_name, package):
        """Extract a symbol definition from an AST node."""
        try:
            name = self._get_symbol_name(node, source, lang_name)
            if not name:
                return None

            kind = node.type
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1

            # Get body preview (first ~500 chars of the symbol body)
            body_text = source[node.start_byte:node.end_byte]
            body_preview = body_text[:500]

            # Try to get docstring
            docstring = self._get_docstring(node, source, lang_name)

            return {
                'name': name,
                'qualified_name': f"{package}:{file_path}:{name}",
                'kind': kind,
                'start_line': start_line,
                'end_line': end_line,
                'docstring': docstring,
                'body_preview': body_preview,
            }
        except Exception:
            return None

    def _get_symbol_name(self, node, source, lang_name):
        """Extract the name of a symbol from its AST node."""
        # For most languages, the name is in a child node of type 'identifier' or 'type_identifier'
        for child in node.children:
            if child.type in ('identifier', 'type_identifier', 'property_identifier'):
                return source[child.start_byte:child.end_byte]

        # For decorated definitions, look inside
        if node.type == 'decorated_definition':
            for child in node.children:
                if child.type not in ('decorator', 'comment', 'newline'):
                    return self._get_symbol_name(child, source, lang_name)

        # For Rust impl_item, the name is in function_item children
        if node.type == 'impl_item':
            for child in node.children:
                if child.type == 'function_item':
                    return self._get_symbol_name(child, source, lang_name)

        # For variable declarations, get the name from the declarator
        if node.type in ('variable_declaration', 'assignment'):
            for child in node.children:
                if child.type in ('identifier', 'variable_declarator'):
                    if child.type == 'variable_declarator':
                        for sub in child.children:
                            if sub.type == 'identifier':
                                return source[sub.start_byte:sub.end_byte]
                    return source[child.start_byte:child.end_byte]

        return None

    def _get_docstring(self, node, source, lang_name):
        """Try to extract a docstring/comment for a symbol."""
        # Check for preceding comment
        if hasattr(node, 'prev_sibling') and node.prev_sibling:
            prev = node.prev_sibling
            if prev.type in ('comment', 'line_comment', 'block_comment', 'documentation'):
                return source[prev.start_byte:prev.end_byte].strip()

        # Check for first child comment (docstring style)
        for child in node.children:
            if child.type in ('comment', 'line_comment', 'block_comment', 'documentation'):
                return source[child.start_byte:child.end_byte].strip()
            if child.type == 'block':
                # Python docstring is usually first statement in block
                for sub in child.children:
                    if sub.type == 'expression_statement':
                        for expr in sub.children:
                            if expr.type == 'string':
                                return source[expr.start_byte:expr.end_byte].strip()
                    if sub.type in ('comment', 'line_comment', 'block_comment'):
                        return source[sub.start_byte:sub.end_byte].strip()
            break
        return None

    def _extract_deps_from_node(self, node, source, lang_name):
        """Extract dependencies (calls, references) from a symbol's body."""
        deps = []
        # Look for function calls and type references
        def walk_deps(n):
            if n.type in ('call_expression', 'macro_invocation'):
                # Get the function/macro being called
                func_node = n.children[0] if n.children else None
                if func_node:
                    name = source[func_node.start_byte:func_node.end_byte]
                    deps.append((name, 'call', 'call'))
            elif n.type == 'field_access' or n.type == 'member_expression':
                # Could be a cross-package reference
                pass
            for child in n.children:
                walk_deps(child)
        walk_deps(node)
        return deps

    def _extract_file_deps(self, root_node, source, lang_name):
        """Extract file-level dependencies (imports, use statements)."""
        deps = []
        def walk_imports(n):
            if n.type in ('import_statement', 'use_declaration', 'import_declaration',
                          'export_statement'):
                text = source[n.start_byte:n.end_byte]
                # Extract module names from import statements
                imports = re.findall(r'["\']([^"\']+)["\']', text)
                for imp in imports:
                    deps.append((imp, 'import', 'import'))
                # Also extract from/from clauses
                froms = re.findall(r'from\s+["\']([^"\']+)["\']', text)
                for f in froms:
                    deps.append((f, 'import', 'import'))
                # Rust use statements: use foo::bar::baz
                uses = re.findall(r'use\s+([\w:]+)', text)
                for u in uses:
                    deps.append((u, 'import', 'import'))
            for child in n.children:
                walk_imports(child)
        walk_imports(root_node)
        return deps

    def _rebuild_fts(self):
        """Rebuild the FTS5 index from the symbols table."""
        self.db.execute("DELETE FROM symbols_fts;")
        rows = self.db.execute(
            "SELECT id, name, qualified_name, kind, docstring, body_preview, package FROM symbols"
        ).fetchall()
        for row in rows:
            self.db.execute(
                "INSERT INTO symbols_fts(rowid, name, qualified_name, kind, docstring, body_preview, package) "
                "VALUES(?, ?, ?, ?, ?, ?, ?)",
                (row['id'], row['name'], row['qualified_name'] or '', row['kind'],
                 row['docstring'] or '', row['body_preview'] or '', row['package'] or ''))
        self.db.commit()

    def _build_tfidf(self):
        """Build TF-IDF matrix for semantic search."""
        rows = self.db.execute(
            "SELECT id, name, docstring, body_preview FROM symbols ORDER BY id"
        ).fetchall()
        if not rows:
            self._tfidf = None
            self._tfidf_matrix = None
            self._symbol_ids = None
            return

        docs = []
        ids = []
        for row in rows:
            text = f"{row['name']} {row['docstring'] or ''} {row['body_preview'] or ''}"
            docs.append(text)
            ids.append(row['id'])

        self._tfidf = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 2),
            stop_words='english',
            sublinear_tf=True,
        )
        self._tfidf_matrix = self._tfidf.fit_transform(docs)
        self._symbol_ids = np.array(ids)
        log(f"TF-IDF built: {self._tfidf_matrix.shape[0]} docs, {self._tfidf_matrix.shape[1]} features")

    # ─── Querying ─────────────────────────────────────────────────────────────

    def search(self, query, limit=20):
        """FTS5 keyword search over symbols."""
        # Escape FTS5 special chars
        safe_query = re.sub(r'[^\w\s]', ' ', query).strip()
        if not safe_query:
            return []
        # Use OR for multi-word queries to maximize recall
        fts_query = ' OR '.join(safe_query.split())
        rows = self.db.execute(
            "SELECT s.id, s.name, s.qualified_name, s.kind, s.file_path, s.start_line, "
            "s.end_line, s.package, s.docstring, bm25(symbols_fts) as score "
            "FROM symbols_fts f JOIN symbols s ON f.rowid = s.id "
            "WHERE symbols_fts MATCH ? "
            "ORDER BY score LIMIT ?",
            (fts_query, limit)
        ).fetchall()
        return [dict(r) for r in rows]

    def semantic_search(self, query, limit=10):
        """TF-IDF cosine similarity search."""
        if self._tfidf is None or self._tfidf_matrix is None:
            self._build_tfidf()
        if self._tfidf is None:
            return []

        query_vec = self._tfidf.transform([query])
        sims = cosine_similarity(query_vec, self._tfidf_matrix).flatten()
        top_indices = np.argsort(sims)[::-1][:limit]

        results = []
        for idx in top_indices:
            if sims[idx] < 0.001:
                continue
            sym_id = self._symbol_ids[idx]
            row = self.db.execute(
                "SELECT name, qualified_name, kind, file_path, start_line, end_line, "
                "package, docstring FROM symbols WHERE id = ?",
                (sym_id,)
            ).fetchone()
            if row:
                r = dict(row)
                r['similarity'] = float(sims[idx])
                results.append(r)
        return results

    def get_symbol(self, name):
        """Exact symbol lookup by name."""
        rows = self.db.execute(
            "SELECT * FROM symbols WHERE name = ? ORDER BY package, file_path",
            (name,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_dependencies(self, file_path):
        """Get dependencies for a file."""
        outgoing = self.db.execute(
            "SELECT * FROM dependencies WHERE source_file = ?",
            (file_path,)
        ).fetchall()
        incoming = self.db.execute(
            "SELECT * FROM dependencies WHERE target LIKE ?",
            (f"%{os.path.basename(file_path)}%",)
        ).fetchall()
        return {'outgoing': [dict(r) for r in outgoing],
                'incoming': [dict(r) for r in incoming]}

    def get_repo_map(self):
        """Generate an Aider-style repo map: package → files → symbols."""
        packages = defaultdict(lambda: defaultdict(list))
        rows = self.db.execute(
            "SELECT package, file_path, name, kind, start_line FROM symbols "
            "ORDER BY package, file_path, start_line"
        ).fetchall()
        for row in rows:
            packages[row['package']][row['file_path']].append({
                'name': row['name'],
                'kind': row['kind'],
                'line': row['start_line'],
            })

        # Build compact text representation
        lines = []
        for pkg in sorted(packages.keys()):
            files = packages[pkg]
            pkg_info = PACKAGES.get(pkg, {})
            lines.append(f"\n## {pkg} ({pkg_info.get('desc', 'unknown')})")
            for fpath in sorted(files.keys()):
                syms = files[fpath]
                lines.append(f"  {fpath} ({len(syms)} symbols)")
                for sym in syms[:20]:  # Limit per file
                    lines.append(f"    L{sym['line']:>4} {sym['kind']:<30} {sym['name']}")
                if len(syms) > 20:
                    lines.append(f"    ... +{len(syms) - 20} more")
        return '\n'.join(lines)

    def get_stats(self):
        """Get index statistics."""
        total_files = self.db.execute("SELECT COUNT(*) as c FROM files").fetchone()['c']
        total_symbols = self.db.execute("SELECT COUNT(*) as c FROM symbols").fetchone()['c']
        total_deps = self.db.execute("SELECT COUNT(*) as c FROM dependencies").fetchone()['c']
        by_package = self.db.execute(
            "SELECT package, COUNT(*) as c FROM symbols GROUP BY package ORDER BY c DESC"
        ).fetchall()
        by_kind = self.db.execute(
            "SELECT kind, COUNT(*) as c FROM symbols GROUP BY kind ORDER BY c DESC LIMIT 10"
        ).fetchall()
        last_index = self.db.execute(
            "SELECT value FROM index_meta WHERE key = 'last_index'"
        ).fetchone()
        return {
            'total_files': total_files,
            'total_symbols': total_symbols,
            'total_deps': total_deps,
            'by_package': {r['package']: r['c'] for r in by_package},
            'by_kind': {r['kind']: r['c'] for r in by_kind},
            'last_index': last_index['value'] if last_index else None,
        }

    def close(self):
        self.db.close()


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Codebase Brain — Layer 1")
    parser.add_argument('command', choices=['index', 'search', 'semantic', 'symbol',
                                            'deps', 'map', 'stats'])
    parser.add_argument('--query', '-q', help="Search query")
    parser.add_argument('--limit', '-l', type=int, default=20)
    parser.add_argument('--force', '-f', action='store_true', help="Force reindex")
    parser.add_argument('--json', action='store_true', help="Output as JSON")
    args = parser.parse_args()

    brain = CodebaseBrain()

    if args.command == 'index':
        result = brain.index(force=args.force)
        print(json.dumps(result, indent=2) if args.json else
              f"Indexed: {result['files']} files, {result['symbols']} symbols, "
              f"{result['deps']} deps in {result['elapsed_s']}s")

    elif args.command == 'search':
        results = brain.search(args.query, limit=args.limit)
        print(json.dumps(results, indent=2) if args.json else
              '\n'.join(f"{r['score']:.2f}  {r['package']}:{r['file_path']}:{r['start_line']}  "
                        f"{r['kind']}  {r['name']}" for r in results) or "No results")

    elif args.command == 'semantic':
        results = brain.semantic_search(args.query, limit=args.limit)
        print(json.dumps(results, indent=2) if args.json else
              '\n'.join(f"{r['similarity']:.3f}  {r['package']}:{r['file_path']}:{r['start_line']}  "
                        f"{r['kind']}  {r['name']}" for r in results) or "No results")

    elif args.command == 'symbol':
        results = brain.get_symbol(args.query)
        print(json.dumps(results, indent=2) if args.json else
              '\n'.join(f"{r['package']}:{r['file_path']}:{r['start_line']}-{r['end_line']}  "
                        f"{r['kind']}  {r['name']}" for r in results) or "Not found")

    elif args.command == 'deps':
        results = brain.get_dependencies(args.query)
        print(json.dumps(results, indent=2) if args.json else
              f"Outgoing ({len(results['outgoing'])}):\n" +
              '\n'.join(f"  {d['target']} ({d['dep_type']})" for d in results['outgoing']) +
              f"\nIncoming ({len(results['incoming'])}):\n" +
              '\n'.join(f"  {d['source_file']} ({d['dep_type']})" for d in results['incoming']))

    elif args.command == 'map':
        repo_map = brain.get_repo_map()
        print(repo_map)

    elif args.command == 'stats':
        stats = brain.get_stats()
        print(json.dumps(stats, indent=2) if args.json else
              f"Files: {stats['total_files']}\nSymbols: {stats['total_symbols']}\n"
              f"Deps: {stats['total_deps']}\nLast index: {stats['last_index']}\n"
              f"By package: {stats['by_package']}\nBy kind: {stats['by_kind']}")

    brain.close()


if __name__ == '__main__':
    main()
