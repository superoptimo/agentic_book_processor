# Agentic Book Processor

A toolset for turning academic PDF books into didactic **Obsidian wikis**, driven by a
pipeline of AI skills for Claude Code, Open Code, and other agentic code assistants.

Point it at a source book and it produces a structured, cross-linked vault: a study-guide
index, first-principles deep-dive articles per topic (grounded in code examples, shaped by
your own learning goals), and an Obsidian index note wiring it all together — the kind of
material you'd want if you were teaching yourself the book, not just summarizing it.

This repository is the **toolset itself** (the skills, scripts, and templates, plus the
script that scaffolds a new working project from them) — not a book workspace. Use
`build_workspace.py` to generate an actual project you point at your own books.

## What it does

1. **`/book-guidelines`** reads a source PDF and produces a compact study-guide index:
   a header (title/author/summary/intent), a two-level topic ontology for the whole book,
   and chapter-by-chapter summaries with key definitions and study questions.
2. **`/book-topic-article`** / **`/book-topic-batch`** turn topics from that index into
   full Obsidian articles — one focused deep-dive per topic, re-reading the source PDF
   directly for fidelity (never generated from the compressed guidelines alone), written
   first-principles-before-symbols, and grounded in code examples per a configurable style.
   `book-topic-batch` orchestrates this across an entire book's topic list (or just its
   subtopics, with `--deep`) in one pass.
3. **`/book-crosslink`** wires the resulting vault together: cross-references shared
   concepts between articles as Obsidian `[[wikilinks]]`, links the guidelines' topic list
   to the articles that now exist, and (re)builds the vault's `index.md` — safe to re-run
   after every batch that adds new articles.

All four skills are **manual-invocation only** — none of them fire automatically; you
always call them explicitly, in that order, one book at a time.

## Repository layout

```
build_workspace.py          <- scaffolds a new book-processing workspace (see below)
skills_src/                 <- the skill pipeline itself
  book-guidelines/SKILL.md
  book-topic-article/SKILL.md
  book-topic-batch/SKILL.md
  book-crosslink/SKILL.md
scripts/
  crosslink.py               <- deterministic helper script that book-crosslink runs
templates/
  article-style.template.md  <- starting point for tone/audience/grounding-language config
  learning-goals.template.md <- starting point for the reader's standing learning objectives
build/                       <- generated workspaces land here (see Quick start)
```

## Quick start: build a workspace

`build_workspace.py` scaffolds a self-contained project workspace under `./build/`,
with the skills installed for the AI assistant of your choice:

```bash
python3 build_workspace.py <project_name> [--platform agents|claude|opencode]
```

- `project_name` — the workspace folder name, created at `./build/<project_name>`.
- `--platform` (optional, default `agents`) — which assistant the skills are laid out
  for: `agents` → generic `.agents/`, `claude` → Claude Code's `.claude/`, `opencode` →
  Open Code's `.opencode/`.

This creates:

```
build/<project_name>/
  sources/                        <- put source books here: sources/[book]/book.pdf
  script/                         <- copy of scripts/ (e.g. crosslink.py)
  vaults/                         <- generated Obsidian output, one folder per book
  vaults/.article-style.md        <- workbench-wide style defaults, copied from templates/
  vaults/.learning-goals.md       <- workbench-wide learning goals, copied from templates/
  [.agents|.claude|.opencode]/skills/   <- the skill pipeline, ready for that assistant
  README.md                       <- usage instructions specific to that workspace
```

It's safe to re-run: it recreates the folder structure and re-copies scripts/skills/
templates, but never touches `sources/` or already-generated `vaults/[book]/*.md` content.

## Using the skills in a generated workspace

Once a workspace is built, open it with the matching AI assistant (e.g. `claude` in
`build/<project_name>/` for the `claude` platform) and:

1. Drop a PDF at `sources/[book]/book.pdf`.
2. `/book-guidelines [book]` — generates `vaults/[book]/book-guidelines.md`.
3. `/book-topic-batch [book]` (or `/book-topic-article [book] "[topic]"` for a single
   topic) — generates the deep-dive articles. Add `--deep` to also generate one article
   per subtopic, not just per top-level topic.
4. `/book-crosslink [book]` — links articles to each other and to the guidelines' topic
   list, and (re)builds `vaults/[book]/index.md`. Re-run this after every batch that adds
   new articles.

### Configuring style and learning goals

Two optional config layers shape every generated article, without ever inventing content
the source pages don't support:

- **`.article-style.md`** — audience calibration, grounding-language priority (e.g.
  Rust/Lean/Python), tone, structural conventions (see `templates/article-style.template.md`
  for a full example).
- **`.learning-goals.md`** — your own standing learning objectives, used to decide which
  facets of a topic get the deepest treatment and what the closing synthesis connects to
  (see `templates/learning-goals.template.md`).

Each can be set workbench-wide (`vaults/.article-style.md`, `vaults/.learning-goals.md`)
and/or refined per book (`vaults/[book]/.article-style.md`, `vaults/[book]/.learning-goals.md`);
book-level settings only override the workbench default where they genuinely conflict —
everything else still applies.

## Adding a new book

Repeat per book, independently:

```
sources/[new-book]/book.pdf
```

then run the same four-skill pipeline against `[new-book]`. `book-topic-batch` skips
articles that already exist (safe to re-run to fill out a partial vault), and
`book-crosslink` is idempotent, so growing a vault incrementally is the normal workflow,
not a one-time run.
