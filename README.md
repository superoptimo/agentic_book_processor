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

These four are the core pipeline, run in order, one book at a time. A second layer of
skills builds on top of them once you have several processed books in `vaults/` — see
[Additional skills](#additional-skills) below.

Every skill here is **manual-invocation only** — you always call it explicitly — with
one exception: `book-crosslink2` (used internally by `crosslink-bulk`) may also be
invoked automatically by Claude as a step in another skill's workflow.

## Repository layout

```
build_workspace.py          <- scaffolds a new book-processing workspace (see below)
skills_src/                 <- the skill pipeline itself
  book-guidelines/SKILL.md
  book-topic-article/SKILL.md
  book-topic-batch/SKILL.md
  book-crosslink/SKILL.md
  extract_learning_goals/SKILL.md   <- backfills vaults/[book]/.learning-goals.md
  learning-roadmap/SKILL.md         <- synthesizes a cross-book study roadmap
  crosslink-bulk/SKILL.md           <- onboards new vaults/ books into workspace/
  book-crosslink2/SKILL.md          <- workspace/ variant of book-crosslink, driven by crosslink-bulk
scripts/
  crosslink.py               <- deterministic helper script that book-crosslink runs
  crosslink2.py              <- deterministic helper script that book-crosslink2 runs
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

## Additional skills

Once you have several books run through the core pipeline, these skills work *across*
`vaults/`, rather than on a single book at a time. They read the same `vaults/`
layout the core pipeline produces and are all still manual-invocation only.

### `/extract_learning_goals` — backfill per-book learning goals

`book-guidelines` normally drafts `vaults/[book]/.learning-goals.md` itself (tagging that
book's Topic List against the Focus Areas defined in `vaults/.learning-goals.md`) as the
last step of processing a book. If some of your books predate that behavior, or you
deleted a book's `.learning-goals.md` and want it redrafted, run this skill to backfill it
without re-reading the source PDF:

```bash
/extract_learning_goals              # scan every book in vaults/ missing a .learning-goals.md
/extract_learning_goals "[book]"     # backfill just one book
```

It reads each book's already-generated `book-guidelines.md` Topic List (not the PDF), and
never overwrites a `.learning-goals.md` that already exists — hand edits are always safe.
Requires `vaults/.learning-goals.md` to already have a **Focus Areas** section, since
that's the fixed category set every book gets tagged against.

### `/learning-roadmap` — synthesize a cross-book study curriculum

Turns `vaults/.learning-goals.md` plus the topic coverage across every processed book's
`book-guidelines.md` into one sequenced curriculum note — prerequisites, why each topic
matters for your stated goals, which books/articles cover it, and open gaps nothing in
`vaults/` covers yet.

```bash
/learning-roadmap                      # full roadmap, all Focus Areas -> vaults/learning-roadmap.md
/learning-roadmap --focus type-theory  # one Focus Area only -> vaults/learning-roadmap-type-theory.md
```

`--focus [slug]` is the quota-friendly mode for a large vault: books not tagged to that
Focus Area (per their `.learning-goals.md`) are skipped instead of fully re-read. Both
modes only read `vaults/` (guidelines, per-book/workbench config, generated article
filenames) and fully regenerate their one output file each run — nothing else is ever
modified.

### `/crosslink-bulk` — onboard new books into a curated `workspace/`

For setups that maintain a separate, hand-curated `workspace/` copy of the vault (distinct
from the raw `vaults/` pipeline output), this skill finds every book or root-level
`learning-roadmap*.md` note that exists in `vaults/` but hasn't been copied into
`workspace/` yet, copies it over, and cross-links it there via `/book-crosslink2`:

```bash
/crosslink-bulk             # copy and crosslink everything new
/crosslink-bulk --dry-run   # preview what would be copied, without writing anything
```

It never modifies `vaults/` (strictly read-only source) and never re-copies a book already
present in `workspace/` — re-running `/book-crosslink2 [book]` directly is how an existing
`workspace/` book picks up newly generated articles. After copying, it runs
`/book-crosslink2 --curate-learning-roadmaps` once to cross-reference all roadmap notes
together.

`/book-crosslink2` itself is the `workspace/`-folder counterpart to `/book-crosslink`: same
article cross-linking, but it additionally appends `[[wikilinks]]` directly onto
`book-guidelines.md`'s Topic List/Chapter Summaries entries and can curate
`learning-roadmap*.md` notes via `--curate-learning-roadmaps`. You normally reach it
through `/crosslink-bulk` rather than calling it directly, unless you're re-syncing a
single already-onboarded book.

## Adding a new book

Repeat per book, independently:

```
sources/[new-book]/book.pdf
```

then run the same four-skill pipeline against `[new-book]`. `book-topic-batch` skips
articles that already exist (safe to re-run to fill out a partial vault), and
`book-crosslink` is idempotent, so growing a vault incrementally is the normal workflow,
not a one-time run.
