---
name: crosslink-bulk
description: Bulk onboarding pass that finds every book vault under vaults/ not yet present under workspace/, copies each one over wholesale, and runs /book-crosslink2 [book] on it; then does the same for root-level vaults/learning-roadmap*.md notes missing from workspace/, and finally runs /book-crosslink2 --curate-learning-roadmaps once to cross-reference all of them together. This is a batch driver over the existing per-book /book-crosslink2 skill — it never reimplements crosslinking logic itself, it only decides which books/roadmap notes are new and need to be brought into workspace/ and processed. Manual invocation only — invoke explicitly with /crosslink-bulk, never automatically.
disable-model-invocation: true
argument-hint: "[--dry-run]"
---

# Crosslink Bulk Onboarder

**Invocation:** this skill only runs when explicitly called with `/crosslink-bulk`. It must never be triggered automatically by Claude inferring intent from conversation.

Brings any book vault (or root-level learning-roadmap note) that exists in `vaults/` but not yet in `workspace/` into `workspace/`, then wires it up via the existing `/book-crosslink2` skill. It is purely a batch driver — all actual cross-linking logic lives in `scripts/crosslink2.py` via `/book-crosslink2`; this skill only decides *what's new* and *copies it over*.

```
vaults/[book]/                    <- input only, never modified
vaults/learning-roadmap*.md       <- input only, never modified
workspace/[book]/                 <- output: full copy of vaults/[book]/, then crosslinked in place
workspace/learning-roadmap*.md    <- output: copy of the vaults/ root note, then curated in place
```

## Step 1 — Diff book vaults and copy new ones

1. List folders directly under `vaults/` (each one a book) and folders directly under `workspace/` (ignore stray root-level files like `*.canvas`, `custom_notes`, `learning-roadmap*.md` when listing `workspace/` — those aren't books).
2. Any `vaults/[book]/` folder name with no matching `workspace/[book]/` folder is new. Report the full list of new books to the user before copying anything.
3. For each new book, in order:
   - a) Copy the whole folder: `cp -r "vaults/[book]" "workspace/[book]"`. Do not modify anything under `vaults/[book]` — it stays read-only source material.
   - b) Immediately run `/book-crosslink2 [book]` on the freshly-copied `workspace/[book]`, following that skill's own workflow (Steps 1–6 in its SKILL.md) end to end, including reviewing pass 1/pass 3 reports and handling any pass 2 similarity suggestions the same way `/book-crosslink2` normally would.
4. If a book folder already exists in both `vaults/` and `workspace/`, leave it alone — this skill only onboards *new* books, it does not re-sync or re-copy existing ones (re-running `/book-crosslink2 [book]` directly is how an existing book picks up newly generated articles, and is out of scope here).

## Step 2 — Diff and copy new learning-roadmap notes

1. List root-level files in `vaults/` matching the prefix `learning-roadmap` (e.g. `learning-roadmap-type-theory.md`, `learning-roadmap-sat-smt-csp.md`, `learning-roadmap.md`). List the same at the root of `workspace/`.
2. Any `vaults/learning-roadmap*.md` file with no same-named file under `workspace/` is new — copy it: `cp "vaults/[file]" "workspace/[file]"`.
3. Be conservative about oddly-named matches: a file that starts with `learning-roadmap` but doesn't fit the `learning-roadmap.md` / `learning-roadmap-[slug].md` shape (e.g. a `_old`/backup-looking variant) should be flagged to the user for a yes/no before copying, rather than copied silently — it may be legacy material that was deliberately never brought into `workspace/`.
4. Do not modify anything under `vaults/` — copies only, source stays untouched.

## Step 3 — Curate all learning-roadmap notes together

Once every new book and every new roadmap note has been copied into `workspace/`, run the cross-book curation pass once, covering all roadmap notes at once (not per-file):

```
/book-crosslink2 --curate-learning-roadmaps
```

Follow that skill's own workflow for this mode as documented in its SKILL.md (`--curate-learning-roadmaps` section) — `--dry-run` first, review the repair/unresolved/dangling-reference report, then re-run without `--dry-run` to apply confident fixes.

## Reporting

At the end, summarize plainly to the user:
- Which books were newly copied from `vaults/` to `workspace/` and crosslinked (name each one, plus a one-line digest of its `/book-crosslink2` result — links added, guidelines entries linked, unmatched/Extra Topics count).
- Which learning-roadmap notes were newly copied.
- Any oddly-named `learning-roadmap*` file flagged for confirmation and left uncopied pending the user's answer.
- The final `--curate-learning-roadmaps` result (links auto-repaired, unresolved links, dangling references).
- If nothing was new on either side (no new books, no new roadmap notes), say so plainly and skip straight to Step 3 — the curation pass is still worth running since it re-evaluates against whatever already exists in `workspace/`.

## Re-run safety

Safe to re-run at any time: Step 1/2 only ever act on vault/roadmap-note names not yet mirrored in `workspace/`, so a repeat run with nothing new in `vaults/` is a no-op except for the final idempotent curation pass.
