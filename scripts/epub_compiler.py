#!/usr/bin/env python3
"""Compile Markdown chapter files into a KDP-friendly EPUB.

Expected input layout:
- One or more Markdown chapter files, passed explicitly or discovered in a directory.
- A title file and optional metadata file can be provided for richer EPUB metadata.

The script keeps dependencies light and only uses the Python standard library.
It supports a small, pragmatic Markdown subset suitable for narrative chapters:
- # / ## headings
- paragraphs
- bullet and numbered lists
- blockquotes
- horizontal rules
- fenced code blocks
- inline emphasis, strong, code, and links

Example:
    python3 scripts/epub_compiler.py \
        --input ai_context/lore/chapters \
        --output dist/my_book.epub \
        --title "My Book" \
        --author "GoalWorld"
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import textwrap
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Sequence, Tuple
from xml.etree import ElementTree as ET


EPUB_NAMESPACE = "urn:oasis:names:tc:opendocument:xmlns:container"
DC_NAMESPACE = "http://purl.org/dc/elements/1.1/"
OPF_NAMESPACE = "http://www.idpf.org/2007/opf"

ET.register_namespace("", OPF_NAMESPACE)
ET.register_namespace("dc", DC_NAMESPACE)
ET.register_namespace("container", EPUB_NAMESPACE)


@dataclass
class Chapter:
    source_path: Path
    title: str
    html_body: str
    filename: str


@dataclass
class BookMetadata:
    title: str
    author: str = "GoalWorld"
    language: str = "en"
    identifier: str = "goalworld-epub-compiler"
    description: str = ""
    publisher: str = "GoalWorld"
    subject: str = "Fiction"
    date: str = ""


INLINE_TAG_REPLACEMENTS = [
    (re.compile(r"`([^`]+)`"), r"<code>\1</code>"),
    (re.compile(r"\*\*([^*]+)\*\*"), r"<strong>\1</strong>"),
    (re.compile(r"__([^_]+)__"), r"<strong>\1</strong>"),
    (re.compile(r"\*([^*]+)\*"), r"<em>\1</em>"),
    (re.compile(r"_([^_]+)_"), r"<em>\1</em>"),
    (re.compile(r"\[([^\]]+)\]\(([^)]+)\)"), r'<a href="\2">\1</a>'),
]


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Markdown file or directory containing chapter files")
    parser.add_argument("--output", required=True, help="Output EPUB path")
    parser.add_argument("--title", required=True, help="Book title")
    parser.add_argument("--author", default="GoalWorld", help="Book author")
    parser.add_argument("--language", default="en", help="EPUB language code")
    parser.add_argument("--identifier", default="goalworld-epub-compiler", help="EPUB identifier")
    parser.add_argument("--description", default="", help="Book description")
    parser.add_argument("--publisher", default="GoalWorld", help="Publisher name")
    parser.add_argument("--subject", default="Fiction", help="Book subject")
    parser.add_argument("--metadata", help="Optional JSON file with metadata overrides")
    parser.add_argument("--chapter-glob", default="*.md", help="Glob for discovering chapters in a directory")
    parser.add_argument("--sort", choices=("name", "mtime"), default="name", help="Chapter ordering when input is a directory")
    return parser.parse_args(argv)


def load_metadata(args: argparse.Namespace) -> BookMetadata:
    meta = BookMetadata(
        title=args.title,
        author=args.author,
        language=args.language,
        identifier=args.identifier,
        description=args.description,
        publisher=args.publisher,
        subject=args.subject,
        date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    )
    if args.metadata:
        with open(args.metadata, "r", encoding="utf-8") as fh:
            overrides = json.load(fh)
        for key, value in overrides.items():
            if hasattr(meta, key) and value is not None:
                setattr(meta, key, str(value))
    return meta


def discover_chapter_paths(input_path: Path, chapter_glob: str, sort: str) -> List[Path]:
    if input_path.is_file():
        return [input_path]
    if not input_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")
    paths = sorted(input_path.glob(chapter_glob))
    if sort == "mtime":
        paths.sort(key=lambda p: (p.stat().st_mtime, p.name))
    else:
        paths.sort(key=lambda p: p.name)
    return [p for p in paths if p.is_file()]


def chapter_title_from_markdown(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip()
            if title:
                return title
    return fallback


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return slug or "chapter"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def inline_markdown_to_html(text: str) -> str:
    escaped = html.escape(text)
    for pattern, replacement in INLINE_TAG_REPLACEMENTS:
        escaped = pattern.sub(replacement, escaped)
    return escaped


def render_markdown(markdown_text: str) -> str:
    lines = markdown_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks: List[str] = []
    paragraph: List[str] = []
    list_stack: List[str] = []
    in_code = False
    code_lines: List[str] = []
    code_lang = ""

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            joined = " ".join(s.strip() for s in paragraph).strip()
            if joined:
                blocks.append(f"<p>{inline_markdown_to_html(joined)}</p>")
        paragraph = []

    def close_lists() -> None:
        while list_stack:
            blocks.append(f"</{list_stack.pop()}>" )

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code:
                blocks.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
                code_lines = []
                in_code = False
                code_lang = ""
            else:
                flush_paragraph()
                close_lists()
                in_code = True
                code_lang = stripped[3:].strip()
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not stripped:
            flush_paragraph()
            close_lists()
            continue

        if stripped == "---" or stripped == "***":
            flush_paragraph()
            close_lists()
            blocks.append("<hr/>")
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading_match:
            flush_paragraph()
            close_lists()
            level = len(heading_match.group(1))
            content = inline_markdown_to_html(heading_match.group(2).strip())
            blocks.append(f"<h{level}>{content}</h{level}>")
            continue

        bullet_match = re.match(r"^([*-]|\d+[.)])\s+(.+)$", stripped)
        if bullet_match:
            flush_paragraph()
            marker = bullet_match.group(1)
            item = inline_markdown_to_html(bullet_match.group(2).strip())
            list_type = "ol" if marker[0].isdigit() else "ul"
            if not list_stack or list_stack[-1] != list_type:
                close_lists()
                list_stack.append(list_type)
                blocks.append(f"<{list_type}>")
            blocks.append(f"<li>{item}</li>")
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            close_lists()
            quote = inline_markdown_to_html(stripped.lstrip("> ").strip())
            blocks.append(f"<blockquote><p>{quote}</p></blockquote>")
            continue

        paragraph.append(stripped)

    if in_code:
        blocks.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
    flush_paragraph()
    close_lists()
    return "\n".join(blocks)


def make_nav_document(chapters: Sequence[Chapter], metadata: BookMetadata) -> str:
    items = "\n".join(
        f'<li><a href="{chapter.filename}">{html.escape(chapter.title)}</a></li>' for chapter in chapters
    )
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
  <title>{html.escape(metadata.title)}</title>
  <meta charset="utf-8" />
</head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>{html.escape(metadata.title)}</h1>
    <ol>
      {items}
    </ol>
  </nav>
</body>
</html>
"""


def make_style_css() -> str:
    return textwrap.dedent(
        """
        body {
          font-family: serif;
          line-height: 1.6;
          margin: 0;
          padding: 0 1.1em;
        }
        h1, h2, h3, h4, h5, h6 {
          line-height: 1.25;
          margin: 1.2em 0 0.6em;
        }
        p {
          margin: 0 0 1em;
          text-align: justify;
          widows: 2;
          orphans: 2;
        }
        ul, ol {
          margin: 0 0 1em 1.4em;
          padding: 0;
        }
        blockquote {
          margin: 1em 1.5em;
          padding-left: 1em;
          border-left: 0.2em solid #999;
          color: #444;
        }
        pre {
          white-space: pre-wrap;
          font-family: monospace;
          font-size: 0.9em;
          background: #f5f5f5;
          padding: 0.9em;
          border-radius: 0.4em;
          overflow-x: auto;
        }
        code {
          font-family: monospace;
        }
        hr {
          border: 0;
          border-top: 1px solid #bbb;
          margin: 1.5em 0;
        }
        a {
          color: #1a4b8c;
        }
        """
    ).strip() + "\n"


def make_content_document(chapter: Chapter, metadata: BookMetadata) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>{html.escape(chapter.title)}</title>
  <meta charset="utf-8" />
  <link rel="stylesheet" type="text/css" href="styles/style.css" />
</head>
<body>
  <section epub:type="chapter" id="{slugify(chapter.title)}">
    <h1>{html.escape(chapter.title)}</h1>
    {chapter.html_body}
  </section>
</body>
</html>
"""


def make_container_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""


def make_opf(chapters: Sequence[Chapter], metadata: BookMetadata) -> str:
    manifest_items = [
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav" />',
        '<item id="css" href="styles/style.css" media-type="text/css" />',
    ]
    spine_items = []
    for idx, chapter in enumerate(chapters, 1):
        item_id = f"chap{idx}"
        manifest_items.append(
            f'<item id="{item_id}" href="text/{chapter.filename}" media-type="application/xhtml+xml" />'
        )
        spine_items.append(f'<itemref idref="{item_id}" />')
    return f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="{OPF_NAMESPACE}" unique-identifier="bookid" version="3.0" xml:lang="{html.escape(metadata.language)}">
  <metadata xmlns:dc="{DC_NAMESPACE}">
    <dc:identifier id="bookid">{html.escape(metadata.identifier)}</dc:identifier>
    <dc:title>{html.escape(metadata.title)}</dc:title>
    <dc:language>{html.escape(metadata.language)}</dc:language>
    <dc:creator>{html.escape(metadata.author)}</dc:creator>
    <dc:publisher>{html.escape(metadata.publisher)}</dc:publisher>
    <dc:subject>{html.escape(metadata.subject)}</dc:subject>
    <dc:date>{html.escape(metadata.date or datetime.now(timezone.utc).strftime("%Y-%m-%d"))}</dc:date>
    <dc:description>{html.escape(metadata.description)}</dc:description>
  </metadata>
  <manifest>
    {' '.join(manifest_items)}
  </manifest>
  <spine>
    <itemref idref="nav"/>
    {' '.join(spine_items)}
  </spine>
</package>
"""


def build_chapters(paths: Sequence[Path]) -> List[Chapter]:
    chapters: List[Chapter] = []
    for index, path in enumerate(paths, 1):
        markdown_text = read_text(path)
        title = chapter_title_from_markdown(markdown_text, f"Chapter {index}")
        html_body = render_markdown(markdown_text)
        chapters.append(
            Chapter(
                source_path=path,
                title=title,
                html_body=html_body,
                filename=f"chapter-{index:03d}.xhtml",
            )
        )
    return chapters


def write_epub(output_path: Path, chapters: Sequence[Chapter], metadata: BookMetadata) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", make_container_xml())
        zf.writestr("OEBPS/content.opf", make_opf(chapters, metadata))
        zf.writestr("OEBPS/nav.xhtml", make_nav_document(chapters, metadata))
        zf.writestr("OEBPS/styles/style.css", make_style_css())
        for chapter in chapters:
            zf.writestr(f"OEBPS/text/{chapter.filename}", make_content_document(chapter, metadata))


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    metadata = load_metadata(args)
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    chapter_paths = discover_chapter_paths(input_path, args.chapter_glob, args.sort)
    if not chapter_paths:
        print(f"No chapter files found in {input_path}", file=sys.stderr)
        return 2

    chapters = build_chapters(chapter_paths)
    write_epub(output_path, chapters, metadata)

    print(f"Wrote EPUB: {output_path}")
    print(f"Chapters: {len(chapters)}")
    for chapter in chapters:
        print(f" - {chapter.source_path} -> {chapter.filename} ({chapter.title})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
