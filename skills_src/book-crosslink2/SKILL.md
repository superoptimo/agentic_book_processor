---
name: book-crosslink2
description: Post-processing pass that wires up an already-generated collection of book-topic-article notes living under workspace/[book] (not vaults/[book]), with three responsibilities — (1) cross-referencing between article bodies via Obsidian [[wikilinks]] wherever one article's prose mentions another's topic or a subsection concept, including similarity-based near-miss matches, not just exact ones; (2) appending suffix-style `[[Target|Link]]` reference(s) directly onto book-guidelines.md's own Topic List entries and Chapter Summaries entries (after the entry's title text, never rewriting the text itself), so book-guidelines.md is deliberately no longer read-only in this variant of the skill; (3) fully assembling/maintaining workspace/[book]/index.md, mirroring the now-linked Topic List, plus a trailing "Extra Topics" section for any generated article no Topic List entry matched. Runs a deterministic script (scripts/crosslink2.py, at the project's working-directory root — not inside this skill's folder) rather than hand-editing prose, so it's safe to re-run repeatedly as new articles get added. This is the workspace/-folder, guidelines-writing sibling of /book-crosslink (which targets vaults/[book] and never touches book-guidelines.md) — don't confuse the two; use whichever matches the folder layout in play. A fourth, independent mode — `--curate-learning-roadmaps` — instead curates workspace/learning-roadmap*.md (the workspace/-root notes the learning-roadmap skill writes, e.g. workspace/learning-roadmap-type-theory.md), verifying and where possible repairing the `[[wikilinks]]` inside each topic's "Sources to Study" list that point into workspace/[book] article folders, plus cross-references between the roadmap notes themselves; see the "Curating learning-roadmap-*.md" section below. Can be invoked explicitly with /book-crosslink2, or automatically by Claude when a task calls for it (e.g. as a step in another skill's workflow, such as /crosslink-bulk).
argument-hint: "[book-folder-name] [--dry-run] [--verbose] [--fuzzy-threshold 0.62] [--no-fuzzy] [--no-index] [--curate-learning-roadmaps]"
---

# Book Article Cross-Linker 2 (workspace/ variant)

**Invocation:** this skill runs when explicitly called with `/book-crosslink2`, or when Claude invokes it directly as part of another task or skill's workflow (e.g. `/crosslink-bulk` running it once per newly onboarded book).

**This is a fork of `/book-crosslink`**, adapted for a different folder layout and a different policy on `book-guidelines.md`:

| | `/book-crosslink` | `/book-crosslink2` (this skill) |
|---|---|---|
| Book folder root | `vaults/[book]` | `workspace/[book]` |
| Script | `scripts/crosslink.py` | `scripts/crosslink2.py` |
| `book-guidelines.md` | read-only, never written | **written**: suffix links appended after Topic List and Chapter Summaries entries |
| Article-body cross-linking (passes 1/2) | same | same |
| `index.md` | derived from an in-memory-only linked copy of the Topic List | derived directly from the now on-disk-linked Topic List |

```
workspace/[book]/*.md                    <- input AND output: existing generated articles, edited in place
workspace/[book]/book-guidelines.md      <- input AND output: Topic List / Chapter Summaries entries get
                                             suffix links appended in place; nothing else in this file is
                                             ever touched (Header, Key Questions, page ranges, etc. pass
                                             through byte-for-byte unchanged)
workspace/[book]/index.md                <- output: fully (re)derived from book-guidelines.md's (now
                                             linked) Topic List each run, plus a trailing "Extra Topics"
                                             section for any article no Topic List entry matched
workspace/[book]/.crosslink-glossary.md  <- optional input: manual term -> target overrides
workspace/[book]/.crosslink-ignore.md    <- optional input: terms to never auto-link
```

## The suffix-link style

Unlike `/book-crosslink`, which (for Topic List entries only, and only in-memory) wrapped an entry's own text in a wikilink, this skill **never rewrites the entry's original text**. Instead it appends a colon-separated suffix after it, on the same line, using the literal display text `Link` (or `Link1`, `Link2`, ... when more than one article matches):

```
## Topic List

1. **Sense and Denotation** : [[Sense-and-Denotation|Link]]
   - Frege's dichotomy between sense and denotation : [[Sense-and-Denotation|Link]]
   - The subformula property of normal deductions : [[Parcels-and-Subformulas|Link1]], [[Natural-Deduction|Link2]]
   - Proofs as the constructive content behind a true sentence
```

(The last bullet has no suffix at all — no generated article matched it yet. That's expected and informative, same as an unlinked Topic List entry in `/book-crosslink`'s index.)

The same style applies inside `## Chapter Summaries`, both on the chapter's own `**Summary:**` line (matched against the chapter title) and on each `**N.M Section Name**` bullet under "Key Definitions & Concepts by Section" (matched against the section name):

```
### Chapter 1: Sense, Denotation and Semantics (pp. 1–7)

**Summary:** Introduces Frege's sense/denotation dichotomy... : [[Sense-and-Denotation|Link]]

**Key Definitions & Concepts by Section:**
- **1.1 Sense and denotation in logic** — sense (the syntactic instructions...)... : [[Sense-and-Denotation|Link]]
  - **1.1.2 The syntactic tradition** — ...(1930). : [[Natural-Deduction|Link1]], [[Sense-and-Denotation|Link2]]
```

Everything else in `book-guidelines.md` — the `## Header` section, page ranges, `**Key Questions:**` — is left completely untouched.

**Idempotent by construction:** every run strips any suffix a previous run appended and recomputes it fresh from the current set of generated articles, so re-running never accumulates duplicate or stale links, and a subtopic that only fuzzy-matched loosely early on will pick up its own dedicated article's exact match the moment that article exists.

## What the script does (so you can explain it, not just invoke it)

`scripts/crosslink2.py` runs three passes with different guarantees, same as `crosslink.py`: **pass 1 and pass 3 are safe to fully automate; pass 2 is a recall tool that needs a judgment call before anything gets written.**

**Pass 1 — exact matching between article bodies (auto-applied):** identical mechanics to `/book-crosslink`'s pass 1 — builds a glossary from every article's title + `##`/`###` headings (merged with `.crosslink-glossary.md`), filters generic terms via a stoplist plus `.crosslink-ignore.md`, scans each article's prose (protecting frontmatter/code/math/existing links/headings), and wraps the first occurrence of each other article's term in a wikilink, never self-linking, idempotently.

**Pass 2 — similarity search between article bodies (advisory only, never auto-applied):** identical mechanics to `/book-crosslink`'s pass 2 — surfaces reworded/near-miss phrasings above `--fuzzy-threshold` (default `0.62`) as printed suggestions, never written to any file. Promote a confirmed one into `.crosslink-glossary.md` so pass 1 picks it up deterministically next run — same review-and-promote loop as `/book-crosslink` (see that skill's Step 4 if you need the detailed walkthrough; it's unchanged here).

**Pass 3 — book-guidelines.md suffix-linking + Index assembly (auto-applied, narrowly scoped, WRITES to book-guidelines.md):**

1. Walks `book-guidelines.md` line by line, tracking whether it's inside `## Topic List`, inside `## Chapter Summaries` (and which chapter), or neither.
2. Inside `## Topic List`: every top-level numbered entry and every subtopic bullet gets matched against the set of generated articles, in order of confidence — **exact** filename-slug match, then **collision-suffixed** match (for a subtopic disambiguated as `Beta-Reduction-(Theory-of-Expressions).md`), then a **fuzzy** similarity fallback (checked against both an article's title and its own section headings). Unlike `/book-crosslink`, this tier returns **every** article that clears the fuzzy bar and sits within a small score window of the best match (capped at 4), not just the single best one — that's what produces multi-link suffixes (`Link1`, `Link2`, ...).
3. Inside `## Chapter Summaries`: the chapter's `**Summary:**` line is matched against that chapter's own title (from its `### Chapter N: Title (pp. X–Y)` heading); each `**N.M Section Name**` bullet is matched against the section name text. Same three-tier matching and multi-link suffix rules as the Topic List.
4. A matched entry gets ` : [[Target|Link]]` (or ` : [[T1|Link1]], [[T2|Link2]]`, ...) appended right after its original text; an unmatched entry is left exactly as it was, with no suffix at all.
5. **Every entry is re-evaluated on every run** against the live set of generated articles — nothing persists between runs except the articles and `book-guidelines.md` itself, and any previous suffix is stripped before recomputing, so there's no stale state to clean up.
6. `index.md` is then fully regenerated by copying the (now suffix-linked) `## Topic List` section straight out of `book-guidelines.md`, with a back-link to `book-guidelines.md` and a title from the guidelines Header's `**Title:**` field. Being entirely derived, it's rewritten each run rather than incrementally merged.
7. **Every generated article stem gets tracked as either "claimed" or "unclaimed"** by Topic List matching specifically (Chapter Summaries matches don't count toward this, mirroring `/book-crosslink`'s index semantics). Any stem never claimed by a Topic List entry this run is listed under a trailing `## Extra Topics` heading in `index.md`, each as a plain wikilink — so every article physically present in the folder stays reachable from the Index even if it never had a dedicated Topic List bullet. If every article matched, the section is omitted entirely.

## Workflow

### Step 1 — Resolve the book and confirm there's something to work with

1. Resolve `[book]` the same way the other skills in this pipeline do (match against `sources/` folder names).
2. List `workspace/[book]/`. Passes 1/2 need at least two eligible articles — the script itself will say so and skip them if not, rather than erroring. Pass 3 is meaningful with even a single generated article and `book-guidelines.md` present.

### Step 2 — Run the script

```bash
python3 scripts/crosslink2.py "workspace/[book]" --verbose
```

Use `--dry-run` first if the user wants to preview changes before committing (recommended the first time this is run on a given book folder, since — unlike `/book-crosslink` — this now includes a write to `book-guidelines.md` itself, not just to the articles and the Index) — this suppresses every write, including `book-guidelines.md` and `index.md`. Once satisfied, run it again without `--dry-run`.

Use `--no-index` to skip pass 3 entirely (no `book-guidelines.md` suffix-linking, no Index regeneration).

Do not attempt to replicate any of this logic by manually editing files with `str_replace` — the whole point of scripting these steps is the consistency guarantee across every file, including the structured, idempotent suffix rewriting inside `book-guidelines.md`.

### Step 3 — Review the exact-match report (pass 1)

Same as `/book-crosslink`: summarize totals rather than the full verbose dump; flag any suspicious over-eager link and suggest `.crosslink-ignore.md`; point at `.crosslink-glossary.md` for durable manual overrides.

### Step 4 — Review the similarity suggestions (pass 2) and promote the real ones

Same review-and-promote loop as `/book-crosslink`: judge each suggestion on meaning (not just the score), promote confirmed ones into `.crosslink-glossary.md` as `Matched Phrase | Target-Slug`, and re-run without `--dry-run` so pass 1 picks them up deterministically.

### Step 5 — Report the guidelines-linking and Index result (pass 3)

The script reports how many Topic List / Chapter Summaries entries now carry a suffix link, and whether `book-guidelines.md` and `index.md` were updated or already current. Since `book-guidelines.md` is genuinely modified by this skill (unlike `/book-crosslink`), be explicit with the user about that — name it as a real edit, not just a report. Also mention how many articles ended up unmatched and listed under `## Extra Topics`, same as `/book-crosslink`'s Step 5 — don't guess whether that's expected extra coverage or a wording mismatch with the guidelines; report the names and let the user decide.

### Step 6 — Mention re-run safety

Re-run this after every future `book-topic-article`/`book-topic-batch` run that adds new articles to the same `workspace/[book]` folder — all three passes are idempotent, advisory, or fully re-derived, so re-running is the normal way to keep a growing book folder fully wired.

## Curating learning-roadmap-*.md (`--curate-learning-roadmaps`)

The `learning-roadmap` skill writes one or more synthesized curriculum notes directly at the `workspace/` root — `workspace/learning-roadmap.md` (full mode) and/or `workspace/learning-roadmap-[slug].md` (focused mode, e.g. `workspace/learning-roadmap-type-theory.md`). Each topic in those notes cites its `workspace/[book]/` sources two ways: a numbered `[[[book]/book-guidelines|Title]]` entry, followed by nested `[[Topic-Slug]]` bullets pointing at that book's generated articles — plus, separately, `[[learning-roadmap-[slug]|...]]` cross-references between the roadmap notes themselves where one Focus Area's topic intersects another's. None of that is under `book-crosslink2`'s normal per-book scope, and nothing regenerates it when a book folder gets renamed or an article gets re-slugged — a roadmap note can quietly go stale in a way nothing else in the pipeline notices.

`--curate-learning-roadmaps` is a **fourth, independent mode**, orthogonal to passes 1–3: it does not take a `[book-folder-name]` argument (the positional argument becomes the `workspace/` root instead, when given; it defaults to `workspace`) and it never touches article bodies, `book-guidelines.md`, or `index.md`. It only reads/writes `workspace/learning-roadmap*.md`.

```bash
python3 scripts/crosslink2.py --curate-learning-roadmaps workspace --dry-run --verbose
```

Use `--dry-run` first, same rationale as Step 2 — this mode writes directly to the roadmap notes when it can confidently repair a link. Drop `--dry-run` once the report looks right.

**What it does, per roadmap file:**

1. Walks every `#### Sources to Study` block. Each numbered entry (`1. [[[book]/book-guidelines|Title]]`) sets the "current book" for the bullets under it, until the next numbered entry or the end of the block.
2. Every bare wikilink target inside that block (i.e. not already folder-qualified, not a `learning-roadmap-*` cross-reference) is checked against the current book's actual generated articles in `workspace/[book]/`:
   - **Exact stem match** — left untouched, it's already correct.
   - **No exact match, but a single confident fuzzy match** (same three-tier matching `crosslink2.py` uses for `book-guidelines.md`'s own Topic List) — the link is **rewritten in place** to the correct target, display text preserved.
   - **No confident match** — left untouched and reported as unresolved (this is often just "no article generated for this topic yet," same as an un-suffixed Topic List entry — not necessarily a bug).
3. Every `[[[book]/book-guidelines|...]]` link (anywhere in the file) is checked for a matching `workspace/[book]/book-guidelines.md` — flagged as a **dangling book reference** if not, never rewritten (there's no way to guess which book was meant).
4. Every `[[learning-roadmap-[slug]|...]]` cross-reference (anywhere in the file) is checked against the other `workspace/learning-roadmap*.md` files present — flagged as a **dangling roadmap reference** if the target doesn't exist yet (e.g. a Focus Area not generated yet — again often expected, not a bug).
5. Idempotent: re-running never re-flags an already-fixed link, and never touches a line it already resolved correctly.

Report the totals plainly to the user: links auto-repaired (name the old → new target for each — this is a real edit, same transparency bar as pass 3's `book-guidelines.md` writes), how many article links are left unresolved, and how many dangling book/roadmap references were found. A dangling book reference is expected and common — most `sat-smt-csp`/`static-analysis`/`automated-reasoning` roadmap topics cite books that live in *other* projects' `workspace/` trees or simply haven't been processed into this one yet; don't imply it's a defect, just surface the list so the user can judge which ones warrant adding to `sources/` next. Unresolved article links and dangling roadmap references get the same treatment — list them, let the user decide, don't guess.

## Example

Input: `/book-crosslink2 Martin-Löf_Type_Theory`
- Resolves `book = Martin-Löf_Type_Theory`; finds 8+ generated articles under `workspace/Martin-Löf_Type_Theory/` plus `book-guidelines.md`.
- Runs `python3 scripts/crosslink2.py "workspace/Martin-Löf_Type_Theory" --verbose`.
- Pass-1 report: e.g. `Theory-of-Expressions.md: 3 link(s) added`.
- Pass-2 report: a fuzzy suggestion `"the set of small sets" ~ "Universes" (score 0.71)` is judged a real match and promoted to `.crosslink-glossary.md` as `the set of small sets | Universes`; script re-run, now linked by pass 1.
- Pass-3 report: `24 Topic List / Chapter Summaries entries linked in book-guidelines.md (updated)`. `1 article(s) unmatched by any Topic List entry — listed under Extra Topics: Beta-Reduction-Worked-Examples`. `Index note updated at workspace/Martin-Löf_Type_Theory/index.md`.
- Summary to the user: "11 links added across 7 articles via exact matching; 1 similarity suggestion promoted. book-guidelines.md itself was edited this time — 24 Topic List/Chapter-Summary entries now carry `[[...|Link]]` suffixes pointing at generated articles. One extra article, Beta-Reduction-Worked-Examples, didn't match any Topic List entry and is listed under a new Extra Topics section in the Index instead."

**`--curate-learning-roadmaps` example.** Input: `/book-crosslink2 --curate-learning-roadmaps`
- Runs `python3 scripts/crosslink2.py --curate-learning-roadmaps workspace --dry-run --verbose` first.
- Finds 4 roadmap files at the `workspace/` root: `learning-roadmap-automated-reasoning.md`, `learning-roadmap-sat-smt-csp.md`, `learning-roadmap-static-analysis.md`, `learning-roadmap-type-theory.md`.
- `learning-roadmap-automated-reasoning.md`: one bullet reads `[[Curry-Howard-Isomorphism]]` under the `03_proofs_and_types_girard_1989/` entry, but the actual generated article is `The-Curry-Howard-Isomorphism.md` — a single confident fuzzy match, so it's rewritten to `[[The-Curry-Howard-Isomorphism]]`. Several other numbered entries in the same file cite books (e.g. `29_Elaboration_in_Dependent_Type_Theory_De_Moura_2015`) that don't have a `workspace/` folder in this project yet — flagged as dangling book references, not touched.
- `learning-roadmap-type-theory.md`: `[[Untyped-Lambda-Calculus]]` under `04_TAPL_Pierce_2002/` has no exact or confident fuzzy match (the book's actual articles use a different family of names) — left as-is, reported unresolved.
- Re-run without `--dry-run` to apply the one confident fix.
- Summary to the user: "4 roadmap files scanned, 1 updated. 1 link auto-repaired ([[Curry-Howard-Isomorphism]] → [[The-Curry-Howard-Isomorphism]] in learning-roadmap-automated-reasoning.md). 1 article link left unresolved (Untyped-Lambda-Calculus, no confident match in 04_TAPL_Pierce_2002/). ~90 dangling book references across the 4 files — expected, since most cited books haven't been processed into this project's workspace/ yet; full list available with --verbose."
