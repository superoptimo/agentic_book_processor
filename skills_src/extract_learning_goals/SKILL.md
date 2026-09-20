---
name: extract_learning_goals
description: Stand-alone backfill for vaults/[book]/.learning-goals.md — drafts a Focus-Area-tagged learning-goals file for any already-processed book (has vaults/[book]/book-guidelines.md) that doesn't have one yet, by reading that book's existing Topic List rather than re-processing the source PDF. This is the same drafting ability book-guidelines now performs automatically as its own Step 5 for freshly-generated guidelines — this skill exists to run that ability on demand, especially across every book folder in vaults/ at once, so vaults created under a legacy version of book-guidelines (before it drafted .learning-goals.md itself) can be brought up to date without re-running /book-guidelines on every book. Never overwrites an existing .learning-goals.md. Manual invocation only — invoke explicitly with /extract_learning_goals, never automatically.
disable-model-invocation: true
argument-hint: "[book-folder-name] (optional — omit to scan every processed book in vaults/)"
---

# Extract Learning Goals (Backfill)

Drafts `vaults/[book]/.learning-goals.md` — the Focus-Area-tagged, per-book learning-goals file that `book-topic-article` and `learning-roadmap` both read — for books that were already run through `/book-guidelines` but never got one. This is the exact drafting logic described in `book-guidelines.SKILL.md`'s Step 5, factored out into its own on-demand skill so it can be run:

- **in bulk**, across an entire vault of already-processed books in one call, which is the main reason this skill exists — a workbench that's been running since before `book-guidelines` drafted `.learning-goals.md` automatically can have dozens of books missing it, and re-running `/book-guidelines` on each just to pick up Step 5 would mean paying the full PDF re-extraction cost for no reason;
- **on a single book**, e.g. if a user deliberately deleted a book's `.learning-goals.md` and wants a fresh auto-draft instead of hand-writing one.

**Ownership note:** this skill and `book-guidelines`' own Step 5 both write the same target file (`vaults/[book]/.learning-goals.md`), which would normally violate this pipeline's one-writer-per-file convention (see `conventions-and-principles`). The split is intentional and non-overlapping in practice: `book-guidelines`' Step 5 only ever fires *inline*, immediately after that same run freshly built the Topic List in its own Step 4 — it never re-runs against a book it didn't just process. This skill only ever fires *standalone*, against a book's `book-guidelines.md` that already exists on disk from some earlier run. The two never touch the same file in the same run, and both obey the same non-destructive rule (Step 2 below): neither one ever overwrites an existing `.learning-goals.md`.

**Invocation:** this skill only runs when explicitly called with `/extract_learning_goals`. It must never be triggered automatically by Claude inferring intent from conversation — always wait for the explicit command.

This skill assumes the same project layout as the rest of the pipeline:

```
vaults/.learning-goals.md          <- required input: workbench-wide Focus Areas + learning goals
vaults/[book]/book-guidelines.md   <- required input per book: must already exist (prerequisite)
vaults/[book]/.learning-goals.md   <- output (only if absent): book-specific Focus-Area-tagged draft
```

## Workflow

### Step 1 — Resolve scope

1. Take `[book]` from `$ARGUMENTS`, if given.
   - **A book folder name given:** scope is that one book. Match against folder names under `vaults/` the same way other skills do (best match on exact name, informal title, or nickname; if genuinely ambiguous, list candidates and ask rather than guessing).
   - **No argument given:** scope is *every* subfolder of `vaults/` that has a `book-guidelines.md` (skip dotfiles/dotfolders and any folder without one — those haven't been processed yet and aren't this skill's job to touch).
2. Read `vaults/.learning-goals.md` once, up front, specifically its **Focus Areas** section (name, slug, description, conceptual-connections list per area) — this is shared across every book in scope, so read it once rather than per-book.
   - **If `vaults/.learning-goals.md` is missing, or has no Focus Areas section:** stop here for the whole run and tell the user there's no fixed category set to tag against yet. Point them at `vaults/.learning-goals.md`'s Focus Areas convention (see `book-guidelines.SKILL.md`) rather than inventing categories ad hoc — a category set invented here would fork the taxonomy `learning-roadmap` and `book-topic-article` both depend on.

### Step 2 — Filter to books that actually need this

For each book folder in scope:

1. Confirm `vaults/[book]/book-guidelines.md` exists. (It always will for folders discovered by the no-argument scan in Step 1; for an explicitly named book, double-check and tell the user to run `/book-guidelines [book]` first if it's missing — same prerequisite rule as `book-topic-article`.)
2. Check whether `vaults/[book]/.learning-goals.md` already exists.
   - **If it exists:** skip this book entirely — do not read it, do not touch it, do not regenerate it. Never overwrite or append to a learning-goals file, whether it was user-authored or drafted by an earlier run of this skill or of `book-guidelines`' own Step 5; a file that already exists may encode deliberate hand-edited narrowing. Record the skip for Step 6's summary.
   - **If it's absent:** this book proceeds to Step 3.

This filtering step is what keeps a bulk, no-argument run cheap: books that already have a `.learning-goals.md` are pruned before Step 3 ever opens their `book-guidelines.md` Topic List.

### Step 3 — Read each in-scope book's existing Topic List

For each book that survived Step 2:

1. Read `vaults/[book]/book-guidelines.md` — specifically its **Topic List** section. Do *not* re-open `sources/[book]/book.pdf`; unlike `book-topic-article` (which always goes back to the source PDF for article fidelity), this skill only needs the already-compressed Topic List — that's the right level of abstraction for a routing/emphasis file, and re-reading the whole book here would defeat the point of a cheap backfill.
2. Note the book's title (from the Header) for the output file's title line.

### Step 4 — Tag topics against Focus Areas

For each in-scope book, tag each **top-level** Topic List entry against every Focus Area it genuinely belongs to, matching semantically against each area's description and conceptual-connections list from the workbench file — not by keyword string-matching alone. A topic may carry more than one Focus Area tag. A topic that fits none of the areas well is simply left untagged, not force-fit into the closest one.

### Step 5 — Write each book's `.learning-goals.md`

Write `vaults/[book]/.learning-goals.md` using exactly this structure (identical to `book-guidelines.SKILL.md`'s Step 5 template, so a book's file reads the same regardless of which skill produced it):

```markdown
# Learning Goals — <Book Title>

> Drafted automatically by `/extract_learning_goals` from this book's existing
> Topic List, tagged against the Focus Areas defined in `vaults/.learning-goals.md`.
> This is a starting point, not a final answer — edit freely to narrow
> emphasis, add a book-specific angle, or override a tag.

## Focus Areas covered by this book

### <Focus Area Name> (`<slug>`)
- <Top-level topic from the Topic List, verbatim>
- <Another matching top-level topic>

### <Next Focus Area Name> (`<slug>`)
- ...

## Untagged topics

<Only include this section if at least one top-level topic didn't fit any
Focus Area well. List them plainly — this is a signal for the user, not a
failure.>
- <Topic>
```

- List **every** Focus Area that has at least one matching topic in this book — omit an area entirely if nothing in the book maps to it, rather than padding it with a weak match.
- Under each area, list top-level topic names only, exactly as phrased in the book's existing Topic List — not subtopics. This file sets emphasis at the topic level; `book-topic-article` resolves the finer-grained connection when it writes the actual deep-dive.
- Keep this file short — it's a routing/emphasis aid, not a second Topic List. Don't restate subtopics, definitions, or page ranges here; those already live in `book-guidelines.md`.
- The only difference from a file `book-guidelines` would have drafted inline is the attribution line in the blockquote (`/extract_learning_goals` vs. `/book-guidelines`) — purely so a user can later tell which tool produced a given file; the rest of the template, and the tagging judgment behind it, is identical.

### Step 6 — Confirm

After the run, tell the user, for the whole batch (or the single book, if one was named):
- how many book folders were in scope,
- how many `.learning-goals.md` files were drafted, and which books,
- how many were skipped because a `.learning-goals.md` already existed (these were left untouched),
- how many named books (if any, in single-book mode) were skipped because they have no `book-guidelines.md` yet — point the user at `/book-guidelines [book]` for those,
- if the run stopped at Step 1 for lack of Focus Areas in `vaults/.learning-goals.md`, say that instead of the above.

## Example

Input: `/extract_learning_goals` (no argument — bulk backfill)
- `vaults/.learning-goals.md` found, with a Focus Areas section defining `type-theory`, `automated-reasoning`, `sat-smt-csp`, `static-analysis`.
- Vault scan: 14 book folders have `book-guidelines.md`. Of those, 5 already have `.learning-goals.md` (some hand-written, some drafted by earlier `/book-guidelines` runs since it started doing Step 5 automatically) — skipped untouched. The remaining 9 are legacy books from before that convention existed.
- For each of the 9: read the existing Topic List, tag top-level topics against the 4 Focus Areas, write `vaults/[book]/.learning-goals.md`.
- Summary: "14 books in scope. 9 `.learning-goals.md` files drafted (listed by book). 5 already had one and were left untouched."

Input: `/extract_learning_goals thompson-type-theory`
- Single-book mode. `vaults/thompson-type-theory/book-guidelines.md` exists; `vaults/thompson-type-theory/.learning-goals.md` does not.
- Topic List read from the existing `book-guidelines.md`; "The Curry–Howard Isomorphism" tagged `type-theory` (and `automated-reasoning`, if the chapter also covers proof-term assignment as proof search); "Sense and Denotation" left untagged as purely historical/philosophical framing.
- Output: `vaults/thompson-type-theory/.learning-goals.md` drafted.
- Summary: "1 book in scope. `.learning-goals.md` drafted for `thompson-type-theory`, tagged against `type-theory` and `automated-reasoning`."
