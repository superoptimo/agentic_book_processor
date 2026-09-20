---
name: learning-roadmap
description: Generates (and regenerates) a synthesized, sequenced curriculum note from vaults/.learning-goals.md and the topic coverage already extracted into every vaults/[book]/book-guidelines.md. Run with no arguments, it produces the full cross-Focus-Area roadmap at vaults/learning-roadmap.md. Run with --focus [slug], where [slug] is one of the Focus Areas defined in vaults/.learning-goals.md (e.g. type-theory, automated-reasoning, sat-smt-csp, static-analysis), it narrows both the inventory pass and the output to that area alone, writing vaults/learning-roadmap-[slug].md — this is the cheap, quota-friendly mode for a large vault (dozens of books, 50+ topics each), since books with nothing tagged to that Focus Area are skipped rather than fully re-read. Reads book-guidelines.md files and vaults/.article-style.md/.learning-goals.md (workbench and per-book) as input only — never writes to them, never generates topic articles itself (that's book-topic-article/book-topic-batch's job). Manual invocation only — invoke explicitly with /learning-roadmap, never automatically.
disable-model-invocation: true
argument-hint: "[--focus [type-theory|automated-reasoning|sat-smt-csp|static-analysis]]"
---

# Learning Roadmap Generator

Turns the user's learning goals and the whole collection of already-processed books in `vaults/` into one synthesized, sequenced curriculum. Where `book-guidelines` indexes a single book and `book-topic-article`/`book-topic-batch` write per-topic deep-dives, this skill is the one note that looks *across every book at once* and answers "given what I'm trying to learn, and what's on hand, what should I study, in what order, and why."

Two modes:
- **Full roadmap** (no `--focus`): covers every Focus Area, sectioned by area, written to `vaults/learning-roadmap.md`.
- **Focused roadmap** (`--focus [slug]`): covers exactly one Focus Area, written to `vaults/learning-roadmap-[slug].md`. This mode exists specifically to keep the skill usable against a large vault (dozens of books, 50+ topics each) without depleting the token quota on every run — see Step 2's filtering rule.

**Invocation:** this skill only runs when explicitly called with `/learning-roadmap`. It must never be triggered automatically by Claude inferring intent from conversation — always wait for the explicit command, even after a `book-guidelines` or `book-topic-batch` run that clearly changed what's available to draw from.

This skill assumes the same project layout as the rest of the pipeline, plus the workbench-wide config layer:

```
vaults/.learning-goals.md          <- input: the user's standing learning objectives + Focus Areas (required — see Step 1)
vaults/.article-style.md           <- optional input: workbench-wide style/audience/language notes, read for framing/language only
vaults/[book]/book-guidelines.md   <- input: one per already-processed book (Header + Topic List + Chapter Summaries)
vaults/[book]/.learning-goals.md   <- optional input: per-book Focus-Area tags, used to pre-filter which books need a full read (see Step 2)
vaults/[book]/*.md                 <- input (metadata only): used to note which topics already have a generated article
vaults/learning-roadmap.md         <- output (no --focus): the full cross-area synthesized roadmap, written at the vaults root
vaults/learning-roadmap-[slug].md  <- output (--focus [slug]): the single-area roadmap, written at the vaults root
```

`book-guidelines.md` and every other input here are read-only — this skill never edits a book's guidelines, never touches a per-book `.learning-goals.md`, never touches an Index note, and never generates topic articles. It only reads across the vault and writes the one roadmap file for the mode it's running in.

## Workflow

### Step 1 — Read the user's learning goals and resolve the mode

1. Read `vaults/.learning-goals.md` in full. This is the anchor for everything else: the user's stated goal projects (e.g. "build a compiler," "build a proof assistant," "understand category-theoretic semantics well enough to read papers cold"), and — if present — its **Focus Areas** section (name, slug, description, conceptual-connections list per area).
   - **If it's missing:** stop and tell the user this file is required for a meaningful roadmap — ask them to write their learning goals into `vaults/.learning-goals.md` (a few sentences on what they're trying to build or understand is enough) before running this skill. Do not fabricate goals to fill the gap.
2. Resolve the mode from `$ARGUMENTS`:
   - **No `--focus`:** full-roadmap mode. Output is `vaults/learning-roadmap.md`, covering every Focus Area defined in the workbench file (or, if the file has no Focus Areas section at all, covering the goals as a single undivided curriculum the way this skill worked before Focus Areas existed).
   - **`--focus [slug]`:** focused mode. Validate `[slug]` against the workbench file's Focus Areas — it must match one of the defined slugs exactly. If it doesn't match (typo, or the workbench file has no Focus Areas section to validate against), tell the user the valid slugs and stop rather than guessing which area they meant. On a valid match, output is `vaults/learning-roadmap-[slug].md`, and every later step in this skill operates on that one area only — this is what keeps the run cheap against a large vault.
3. Optionally skim `vaults/.article-style.md` if present, only to pick up framing/output-language cues (see Step 5) — it has no bearing on curriculum content.
4. From your own academic/technical background knowledge (independent of what's in `vaults/` so far), sketch a **preliminary roadmap**: the fundamentals a learner genuinely needs, in a sensible order, to reach the stated goals — restricted to the resolved Focus Area's scope in focused mode, across all areas in full mode. This preliminary pass matters even for topics no book in `vaults/` covers yet — it's what lets Step 4 flag real gaps instead of only ever describing what's already on hand.

### Step 2 — Inventory the vault (filtered by mode)

This is the step where focused mode earns its token savings — do the filtering in 2.2 *before* reading anything expensive, not after.

1. List every subfolder of `vaults/` (each one a book, per the pipeline's convention), skipping dotfiles/dotfolders and the `learning-roadmap*.md` output files.
2. **Pre-filter each book folder before doing a full read, when in focused mode:**
   - If `vaults/[book]/.learning-goals.md` exists and has a "Focus Areas covered by this book" section (per `book-guidelines`' Step 5 convention), check whether the resolved `[slug]` appears there. If it doesn't, **skip this book entirely** for both this step and every later step — don't open its `book-guidelines.md` at all. Note the skip so Step 6 can report how many books were pruned this way.
   - If `vaults/[book]/.learning-goals.md` doesn't exist, or exists but predates the Focus Areas convention (no such section), this book can't be cheaply pre-filtered — fall back to reading its `book-guidelines.md` Header and Topic List (not the full Chapter Summaries yet) and judge relevance semantically against the resolved area's description before deciding whether to fully extract it. This costs more than a tagged skip but far less than extracting every book unconditionally.
   - In full-roadmap mode, skip this filtering — every processed book is in scope, same as before Focus Areas existed.
3. For each book folder that survives filtering, read `vaults/[book]/book-guidelines.md`:
   - **If a subfolder has no `book-guidelines.md` yet**, skip it for extraction purposes but you may still note it exists (it hasn't been processed — nothing to draw from yet).
   - From the Header, note the book's title, author(s), and stated intent — useful context for *why* this source suits a given roadmap topic.
   - From the **Topic List**, extract every top-level topic and subtopic exactly as phrased. In focused mode, when the book *did* have Focus-Area tags (2.2's first case), extract from the topics under the matched area only — the tagging in `.learning-goals.md` already tells you which top-level topics apply; you don't need to re-judge every subtopic in the book against the area.
   - From **Chapter Summaries**, extract key definitions/concepts and key questions per chapter/section for the topics in scope — these are your source material for each roadmap topic's "Key Concepts" and "Relevant Questions," not material to invent fresh.
4. Also list the `.md` files already present directly in each in-scope `vaults/[book]/` folder (excluding `book-guidelines.md`, `.learning-goals.md`, and `index.md`) — these are the topic articles already generated. Knowing which roadmap topics already have a written note (versus only a guidelines entry) is useful to flag in Step 4's "Sources to Study," since a generated note is a more concrete study source than a bare guidelines mention.

### Step 3 — Merge into a categorized structure

1. Take the preliminary roadmap from Step 1 and the concept inventory from Step 2 (already filtered to the resolved area, in focused mode), and merge them: every extracted book topic/subtopic should land under the roadmap category it actually belongs to, even where the phrasing across books differs (e.g. two books' "Confluence" and "The Church–Rosser Property" are the same concept — merge them, don't duplicate the roadmap entry).
2. **Full-roadmap mode:** organize into top-level sections by Focus Area (in the order the workbench file defines them), and within each area's section, organize categorically by topic — not by book and not by chapter. A topic tagged against more than one area (per the workbench file's conceptual-connections tags) appears under its primary area, with a cross-reference note under the other(s) rather than being duplicated in full. If the workbench file has no Focus Areas section, fall back to one flat categorical structure, same as before Focus Areas existed.
   **Focused mode:** organize categorically by topic within the single resolved area — no area-sectioning needed since there's only one area in scope.
3. Where the preliminary roadmap (Step 1) named a fundamental with no matching book coverage in `vaults/`, keep that topic in the roadmap anyway (per Step 4's "Additional external sources") rather than silently dropping it just because nothing on hand covers it yet.

### Step 4 — Sequence and annotate each topic

Re-arrange the merged structure into final sequence: **basic/foundational topics first, advanced topics that build on them later** (within each Focus Area section, in full-roadmap mode). For every roadmap topic, work out and record:

1. **Pre-requisites** — the other roadmap topics (or general background) this one assumes. A prerequisite may sit in a different Focus Area section (e.g. a `sat-smt-csp` topic assuming a `type-theory` fundamental) — cross-reference it by name rather than restating it.
2. **Why this topic is important** — how it serves the user's stated goals from `vaults/.learning-goals.md` specifically (not a generic "this is foundational" — name the concrete downstream payoff, e.g. "this is the mechanism your elaborator's unifier will need"), and which later roadmap topics depend on it.
3. **Sources to Study** — every in-scope book (and, if one already exists, generated note) from `vaults/` that covers this topic, grouped by book. Prefer citing a specific generated article/section over a bare book title when one exists (per Step 2.4).
4. **Additional external sources** (only if genuinely warranted) — other academic references, from your own background knowledge, that would strengthen this topic beyond what's currently in `vaults/` — papers, textbooks, or canonical references not already covered. Omit this subsection entirely for a topic where the on-hand sources are already sufficient; don't pad every topic with filler suggestions.
5. **Key Concepts and Definitions** — drawn from the matching book-guidelines' Chapter Summaries where available (Step 2.3), not invented fresh; supplement briefly from background knowledge only where the on-hand material is thin.
6. **Relevant Questions** — 2-4 questions, preferring ones lifted or adapted from the source book-guidelines' "Key Questions," supplemented from background knowledge if a topic has no book coverage yet.

### Step 5 — Write the roadmap

Write to exactly `vaults/learning-roadmap.md` in full mode, or `vaults/learning-roadmap-[slug].md` in focused mode (create/overwrite; this file is fully regenerated each run, the same way `book-crosslink`'s Index note is — cheap, and always in sync with the current vault and goals file, rather than incrementally patched). Never write both files in one run — only the mode actually requested.

- **Output language:** follow `vaults/.article-style.md`'s output-language setting if present (same rule as `book-topic-article`'s core contract — see that skill for the exact precedence, though only the workbench-level file applies here since this note isn't book-specific); default to English otherwise. Keep proper nouns, named theorems, LaTeX math, and code untranslated regardless.
- **Math notation:** LaTeX only (`$...$` inline, `$$...$$` display), never inside backticks or code fences — same convention as every other skill in this pipeline.
- **Obsidian conventions:** wikilink to each cited book's guidelines (`[[book-guidelines|...]]`, disambiguated per book folder since several books each have their own) and, where one exists, directly to the generated topic article (`[[Topic-Slug]]`) rather than only the book title in prose. In full mode, also wikilink each Focus Area section header to the single-area roadmap it corresponds to where one already exists on disk (`[[learning-roadmap-[slug]|↪ focused roadmap]]`), so the two output modes stay cross-navigable.

**Focused mode structure** (`vaults/learning-roadmap-[slug].md`):

```markdown
# Learning Roadmap — <Focus Area Name>

[Brief introduction: 2-4 sentences restating this Focus Area's role in the user's
stated goals, and the shape/motivation of the sequence that follows.]

## 1. <Core Topic Name> (Core Topic)

#### Pre-requisites
<Other roadmap topics or general background this one assumes>

#### Why this topic is important
<How this serves the user's stated goals specifically, and what later topics depend on it>

#### Sources to Study
1. [[book-guidelines|Book 1 Title]]
   - [[Topic-Slug|Note A]]
   - Note B, section N (no article yet)
2. [[book-guidelines|Book 2 Title]]
   - ...

#### Additional external sources
<Only if warranted — other academic references to complement what's on hand>

#### Key Concepts and Definitions
1. Key concept 1 — definition
2. Key concept 2 — definition

#### Relevant Questions
1. ...?
2. ...?

---

## 2. <Next Core Topic> (Core Topic)
...
```

**Full-roadmap mode structure** (`vaults/learning-roadmap.md`): the same per-topic block, but topics are grouped under a `##` heading per Focus Area (in the workbench file's defined order), each topic then numbered within its area's section as `### <Area Number>.<Topic Number>`:

```markdown
# Learning Roadmap

[Brief introduction: 2-4 sentences restating the user's learning goals in your own
words across all Focus Areas, and the overall shape/motivation of the sequence
that follows.]

## Area 1. <Focus Area Name> (`<slug>`)

### 1.1 <Core Topic Name> (Core Topic)

#### Pre-requisites
...
[same per-topic block fields as focused mode]
...

---

### 1.2 <Next Core Topic>
...

## Area 2. <Next Focus Area Name> (`<slug>`)

### 2.1 ...
```

If the workbench file has no Focus Areas section, fall back to the flat, unsectioned `## N. <Topic>` numbering from before Focus Areas existed.

Number topics in final learning-path order (basic-to-advanced, respecting the pre-requisite chains from Step 4), not in the order books happen to sit in `vaults/`.

### Step 6 — Confirm

After writing the file, tell the user:
- where it was saved (`vaults/learning-roadmap.md` or `vaults/learning-roadmap-[slug].md`, whichever mode ran),
- how many roadmap topics were produced and how many books in `vaults/` were drawn from,
- **in focused mode**, how many books were pruned by the Step 2.2 pre-filter (tag-skipped vs. semantically judged out-of-scope) — this is the number that demonstrates the token savings,
- which topics (if any) are flagged as needing external sources because no book in `vaults/` covers them yet — this is a natural prompt toward what to add to `sources/` and process next,
- if `vaults/.learning-goals.md` was missing and the run was stopped at Step 1, say so instead of the above,
- if an invalid `--focus` slug was given and the run was stopped at Step 1, list the valid slugs instead of the above.

## Example

**Full mode.** Input: `/learning-roadmap`
- `vaults/.learning-goals.md` found: user wants to build a dependently-typed proof assistant, with a Focus Areas section defining `type-theory`, `automated-reasoning`, `sat-smt-csp`, `static-analysis`.
- Preliminary background roadmap sketched per area.
- Vault inventory (no pre-filtering — full mode covers everything): `thompson-type-theory/` (book-guidelines.md + 6 articles + `.learning-goals.md` tagging most topics `type-theory`), `boolos-computability-logic/` (book-guidelines.md, no articles yet), `martin-lof-type-theory/` (no book-guidelines.md — skipped for extraction, noted as unprocessed).
- Merge: "Natural Deduction" appears in both `thompson-type-theory` and `boolos-computability-logic`'s Topic Lists, both tagged `automated-reasoning` — merged into one roadmap entry citing both, filed under the `automated-reasoning` section.
- Output: `vaults/learning-roadmap.md`, sectioned into 4 Focus Area headings, 7 topics total distributed across them.
- Summary: "7 roadmap topics across 4 Focus Area sections, drawn from 2 processed books (`martin-lof-type-theory/` has no guidelines yet, so it wasn't drawn from)."

**Focused mode.** Input: `/learning-roadmap --focus sat-smt-csp`
- `[slug]` validated against the workbench file's 4 defined areas — matches.
- Vault has 12 book folders; 8 have `.learning-goals.md` files with Focus-Area tags, and only 3 of those tag `sat-smt-csp` — the other 5 tagged books are skipped without opening their `book-guidelines.md` at all. The remaining 4 untagged books get a cheap Header+Topic-List relevance check; 1 turns out relevant and gets fully extracted, 3 are judged out of scope and skipped.
- Output: `vaults/learning-roadmap-sat-smt-csp.md`, 5 topics sequenced (CSP fundamentals → domain propagation → CEGAR → CHC solving → SMT-backed invariant synthesis), sourced from the 4 in-scope books.
- Summary: "5 roadmap topics for `sat-smt-csp`, drawn from 4 of 12 books in `vaults/` (5 books pruned by Focus-Area tag, 3 more pruned after a quick relevance check — 8 books never had their full guidelines read this run)."
