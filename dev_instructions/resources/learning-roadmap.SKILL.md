---
name: learning-roadmap
description: Generates (and regenerates) vaults/learning-roadmap.md, a single Obsidian note that synthesizes the user's standing learning goals from vaults/.learning-goals.md with the topic coverage already extracted into every vaults/[book]/book-guidelines.md, producing an ordered, prerequisite-aware curriculum: core topics, sequenced basic-to-advanced, each annotated with why it matters for the user's goals, which books/notes to study for it, key concepts, key questions, and optional external sources beyond what's on hand. Reads book-guidelines.md files and vaults/.article-style.md/.learning-goals.md as input only — never writes to them, never generates topic articles itself (that's book-topic-article/book-topic-batch's job). Manual invocation only — invoke explicitly with /learning-roadmap, never automatically.
disable-model-invocation: true
argument-hint: "[--focus \"[optional theme or project to emphasize]\"]"
---

# Learning Roadmap Generator

Turns the user's learning goals and the whole collection of already-processed books in `vaults/` into one synthesized, sequenced curriculum: `vaults/learning-roadmap.md`. Where `book-guidelines` indexes a single book and `book-topic-article`/`book-topic-batch` write per-topic deep-dives, this skill is the one note that looks *across every book at once* and answers "given what I'm trying to learn, and what's on hand, what should I study, in what order, and why."

**Invocation:** this skill only runs when explicitly called with `/learning-roadmap`. It must never be triggered automatically by Claude inferring intent from conversation — always wait for the explicit command, even after a `book-guidelines` or `book-topic-batch` run that clearly changed what's available to draw from.

This skill assumes the same project layout as the rest of the pipeline, plus the workbench-wide config layer:

```
vaults/.learning-goals.md         <- input: the user's standing learning objectives (required — see Step 1)
vaults/.article-style.md          <- optional input: workbench-wide style/audience/language notes, read for framing/language only
vaults/[book]/book-guidelines.md  <- input: one per already-processed book (Header + Topic List + Chapter Summaries)
vaults/[book]/*.md                <- input (metadata only): used to note which topics already have a generated article
vaults/learning-roadmap.md        <- output: the single synthesized roadmap, written at the vaults root
```

`book-guidelines.md` and every other input here are read-only — this skill never edits a book's guidelines, never touches an Index note, and never generates topic articles. It only reads across the vault and writes the one roadmap file.

## Workflow

### Step 1 — Read the user's learning goals

1. Read `vaults/.learning-goals.md` in full. This is the anchor for everything else: the user's stated goal projects (e.g. "build a compiler," "build a proof assistant," "understand category-theoretic semantics well enough to read papers cold").
   - **If it's missing:** stop and tell the user this file is required for a meaningful roadmap — ask them to write their learning goals into `vaults/.learning-goals.md` (a few sentences on what they're trying to build or understand is enough) before running this skill. Do not fabricate goals to fill the gap.
2. Optionally skim `vaults/.article-style.md` if present, only to pick up framing/output-language cues (see Step 5) — it has no bearing on curriculum content.
3. From your own academic/technical background knowledge (independent of what's in `vaults/` so far), sketch a **preliminary roadmap**: the fundamentals a learner genuinely needs, in a sensible order, to reach the stated goals. This preliminary pass matters even for topics no book in `vaults/` covers yet — it's what lets Step 4 flag real gaps instead of only ever describing what's already on hand.

### Step 2 — Inventory the vault

1. List every subfolder of `vaults/` (each one a book, per the pipeline's convention), skipping dotfiles/dotfolders and the `learning-roadmap.md` output itself.
2. For each book folder found, read `vaults/[book]/book-guidelines.md`:
   - **If a subfolder has no `book-guidelines.md` yet**, skip it for extraction purposes but you may still note it exists (it hasn't been processed — nothing to draw from yet).
   - From the Header, note the book's title, author(s), and stated intent — useful context for *why* this source suits a given roadmap topic.
   - From the **Topic List**, extract every top-level topic and subtopic exactly as phrased.
   - From **Chapter Summaries**, extract key definitions/concepts and key questions per chapter/section — these are your source material for each roadmap topic's "Key Concepts" and "Relevant Questions," not material to invent fresh.
3. Also list the `.md` files already present directly in each `vaults/[book]/` folder (excluding `book-guidelines.md` and `index.md`) — these are the topic articles already generated. Knowing which roadmap topics already have a written note (versus only a guidelines entry) is useful to flag in Step 4's "Sources to Study," since a generated note is a more concrete study source than a bare guidelines mention.

### Step 3 — Merge into a categorized structure

1. Take the preliminary roadmap from Step 1 and the concept inventory from Step 2, and merge them: every extracted book topic/subtopic should land under the roadmap category it actually belongs to, even where the phrasing across books differs (e.g. two books' "Confluence" and "The Church–Rosser Property" are the same concept — merge them, don't duplicate the roadmap entry).
2. Organize categorically, not by book and not by chapter — the roadmap's structure is the *learning path*, and any given roadmap topic may draw on several books at once (and a given book may contribute to several roadmap topics).
3. Where the preliminary roadmap (Step 1) named a fundamental with no matching book coverage in `vaults/`, keep that topic in the roadmap anyway (per Step 4's "Additional external sources") rather than silently dropping it just because nothing on hand covers it yet.

### Step 4 — Sequence and annotate each topic

Re-arrange the merged structure into final sequence: **basic/foundational topics first, advanced topics that build on them later.** For every roadmap topic, work out and record:

1. **Pre-requisites** — the other roadmap topics (or general background) this one assumes.
2. **Why this topic is important** — how it serves the user's stated goals from `vaults/.learning-goals.md` specifically (not a generic "this is foundational" — name the concrete downstream payoff, e.g. "this is the mechanism your elaborator's unifier will need"), and which later roadmap topics depend on it.
3. **Sources to Study** — every book (and, if one already exists, generated note) from `vaults/` that covers this topic, grouped by book. Prefer citing a specific generated article/section over a bare book title when one exists (per Step 2.3).
4. **Additional external sources** (only if genuinely warranted) — other academic references, from your own background knowledge, that would strengthen this topic beyond what's currently in `vaults/` — papers, textbooks, or canonical references not already covered. Omit this subsection entirely for a topic where the on-hand sources are already sufficient; don't pad every topic with filler suggestions.
5. **Key Concepts and Definitions** — drawn from the matching book-guidelines' Chapter Summaries where available (Step 2.2), not invented fresh; supplement briefly from background knowledge only where the on-hand material is thin.
6. **Relevant Questions** — 2-4 questions, preferring ones lifted or adapted from the source book-guidelines' "Key Questions," supplemented from background knowledge if a topic has no book coverage yet.

If the user passed `--focus "[theme]"`, let it bias which topics get the deepest "why this matters" treatment and which get pulled earlier in the sequence — it should sharpen emphasis, not remove topics the goals file itself implies are needed.

### Step 5 — Write the roadmap

Write to exactly `vaults/learning-roadmap.md` (create/overwrite; this file is fully regenerated each run, the same way `book-crosslink`'s Index note is — cheap, and always in sync with the current vault and goals file, rather than incrementally patched).

- **Output language:** follow `vaults/.article-style.md`'s output-language setting if present (same rule as `book-topic-article`'s core contract — see that skill for the exact precedence, though only the workbench-level file applies here since this note isn't book-specific); default to English otherwise. Keep proper nouns, named theorems, LaTeX math, and code untranslated regardless.
- **Math notation:** LaTeX only (`$...$` inline, `$$...$$` display), never inside backticks or code fences — same convention as every other skill in this pipeline.
- **Obsidian conventions:** wikilink to each cited book's guidelines (`[[book-guidelines|...]]`, disambiguated per book folder since several books each have their own) and, where one exists, directly to the generated topic article (`[[Topic-Slug]]`) rather than only the book title in prose.

Structure the document as:

```markdown
# Learning Roadmap

[Brief introduction: 2-4 sentences restating the user's learning goals in your own words, and the overall shape/motivation of the sequence that follows.]

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

Number topics in final learning-path order (basic-to-advanced, respecting the pre-requisite chains from Step 4), not in the order books happen to sit in `vaults/`.

### Step 6 — Confirm

After writing the file, tell the user:
- where it was saved (`vaults/learning-roadmap.md`),
- how many roadmap topics were produced and how many books in `vaults/` were drawn from,
- which topics (if any) are flagged as needing external sources because no book in `vaults/` covers them yet — this is a natural prompt toward what to add to `sources/` and process next,
- if `vaults/.learning-goals.md` was missing and the run was stopped at Step 1, say so instead of the above.

## Example

Input: `/learning-roadmap`
- `vaults/.learning-goals.md` found: user wants to build a dependently-typed proof assistant.
- Preliminary background roadmap sketched: propositional/predicate logic → natural deduction → simply-typed lambda calculus → Curry–Howard → dependent types → tactic elaboration.
- Vault inventory: `thompson-type-theory/` (book-guidelines.md + 6 articles), `boolos-computability-logic/` (book-guidelines.md, no articles yet), `martin-lof-type-theory/` (no book-guidelines.md — skipped for extraction, noted as unprocessed).
- Merge: "Natural Deduction" appears in both `thompson-type-theory` and `boolos-computability-logic`'s Topic Lists — merged into one roadmap entry citing both.
- Sequenced: 7 core topics, basic (propositional logic) through advanced (dependent elimination/tactic design); the last topic has no coverage in any processed book, so it's flagged with 2 suggested external references instead of a "Sources to Study" list.
- Output: `vaults/learning-roadmap.md` written with all 7 topics, each with pre-requisites, goal-relevance, sources (linking directly to 4 existing articles where available), key concepts pulled from the guidelines, and 2-3 questions each.
- Summary to the user: "7 roadmap topics generated across 2 processed books (1 book folder — `martin-lof-type-theory/` — has no guidelines yet, so it wasn't drawn from); the final topic, tactic-based elaboration, isn't covered by any book on hand and is flagged with 2 external reference suggestions."
