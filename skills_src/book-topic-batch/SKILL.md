---
name: book-topic-batch
description: Orchestrates book-topic-article across a book's Topic List, turning vaults/[book]/book-guidelines.md into a full collection of Obsidian articles in one pass. Defaults to the top-level topics only; pass --deep to also generate an article per subtopic bullet. Requires vaults/[book]/book-guidelines.md to already exist; if it doesn't, tell the user to run /book-guidelines first rather than fabricating a topic list. This skill only generates article files — it never modifies book-guidelines.md and never produces an index; after it runs (or after any run that adds new articles), suggest /book-crosslink to link book-guidelines.md's Topic List entries to the new articles and (re)build the vault's index. Manual invocation only — invoke explicitly with /book-topic-batch, never automatically.
disable-model-invocation: true
argument-hint: "[book-folder-name] [--deep] [--topics \"a, b, c\"] [--overwrite]"
---

# Book Topic Batch Generator

**Invocation:** this skill only runs when explicitly called with `/book-topic-batch`. It must never be triggered automatically by Claude inferring intent from conversation — always wait for the explicit command, even if the request clearly describes generating a whole vault's worth of articles.

Drives `book-topic-article` (see its `SKILL.md`) once per topic across an entire book, so a whole vault of teaching articles can be produced from a single request instead of one topic at a time. This skill does no article-writing itself — its job is entirely: **parse the topic queue → plan what needs doing → invoke `book-topic-article`'s workflow per topic → track progress.**

**This skill's responsibility ends at generating article files.** It never modifies `book-guidelines.md` and never creates or updates an index note — that's `book-crosslink`'s job exclusively (both linking `book-guidelines.md`'s Topic List entries to the articles this skill produces, and fully assembling `[book] - Index.md` from that linked list). Keeping these separate means this skill stays a pure generator, safe to re-run repeatedly to fill out a vault, without also having to reason about link state or index bookkeeping.

There are exactly two modes for building the queue:

- **Default mode** — only the top-level Topic List entries (the bolded, numbered items, e.g. `**1. Introduction**`, `**2. Natural Deduction**`). One article per broad category.
- **Deep mode** (`--deep`) — every item at both levels: every top-level entry *and* every subtopic bullet beneath it, each as its own article.

No other granularity exists. `book-guidelines` guarantees the Topic List is exactly two levels deep, so these two modes are the complete set of reasonable traversal depths — there's no partial/custom depth to configure.

Treat every individual article generation exactly as `book-topic-article/SKILL.md` specifies (resolve topic against guidelines → re-read the source PDF pages → apply the Rust/Python/Lean first-principles style → write to `vaults/[book]/[Topic-Slug].md` → confirm). This skill exists purely to enumerate the topics and coordinate the repeated invocation cleanly — it does not duplicate or shortcut those steps.

```
sources/[book]/book.pdf              <- input (read indirectly, via book-topic-article)
vaults/[book]/book-guidelines.md         <- input only: topic queue source, never written to by this skill
vaults/[book]/[Topic-Slug].md        <- output: one per topic, via book-topic-article
```

## Workflow

### Step 1 — Resolve the book and confirm the prerequisite

Same resolution as `book-topic-article`: match `[book]` against `sources/` folder names (ask only if genuinely ambiguous). Confirm `vaults/[book]/book-guidelines.md` exists — if not, stop and tell the user to run `/book-guidelines [book]` first.

### Step 2 — Parse the topic queue from the Topic List

1. Read the **Topic List** section of `book-guidelines.md` — the nested ontology, not the Chapter Summaries. The current `book-guidelines` skill guarantees this list is **exactly two levels deep**: numbered, bolded top-level topics (`**1. Introduction**`), each with a flat, unindented-further list of bulleted subtopics underneath. There is no third level to worry about.
2. Determine the mode from the request:
   - **No `--deep` flag (default): queue top-level entries only.** Each numbered, bolded item becomes one article — a broad-category overview, potentially spanning several chapters. This is the common case and keeps the batch size modest (typically 6–12 articles for most books).
   - **`--deep` flag present: queue every item at both levels.** Every top-level entry *and* every subtopic bullet beneath it each becomes its own article — the top-level one a broad overview, each subtopic one a focused deep-dive. Phrase subtopics with their parent for disambiguation when resolving against the guidelines and when there's a name collision (e.g. "Beta Reduction (within Theory of Expressions)") — `book-topic-article` resolves this the same way it resolves any other topic name.
   - Recognize deep-mode intent from natural phrasing too, not just the literal flag — "include subtopics," "go deeper," "every topic and subtopic" should all trigger the same behavior as `--deep`.
3. Independently of the mode, an **explicit subset** always narrows the queue: if the user names specific topics (`--topics "..."`, or just lists them in the request), queue exactly that subset instead of walking the full list — this works the same whether or not `--deep` is also given (a named subtopic still requires `--deep`-style resolution against the guidelines even if the overall run isn't in deep mode).
4. Preserve the Topic List's own ordering in the queue (top-to-bottom, and in deep mode, each top-level entry immediately followed by its own subtopics) — it's a reasonable reading order and makes the eventual index note coherent.
5. **Filename collisions (deep mode only):** because both levels get queued together, it's possible (if uncommon) for a subtopic phrase to collide with another item's slug. If two different queued items would produce the same `[Topic-Slug].md`, disambiguate the later one by appending its parent category, e.g. `Beta-Reduction-(Theory-of-Expressions).md`.

### Step 3 — Plan: skip what already exists

1. For each queued topic, compute its expected filename (`[Topic-Slug].md`, same Title-Case-With-Hyphens convention as `book-topic-article`) and check whether it already exists in `vaults/[book]/`.
2. **Default: skip topics that already have an article.** This makes the skill safe to re-run to "fill out" a partially-built vault without wasting work or clobbering hand-edited notes.
3. Only regenerate existing articles if the user explicitly asks (`--overwrite`, "regenerate everything", "redo them all").
4. Before running, tell the user the plan in one short line: how many topics total, how many will be generated vs. skipped (already present). Default-mode batches are typically small (6–12 articles) and rarely need a check-in. **Deep-mode batches are much larger** (often 20–50+ items, since every subtopic is now included) — if a deep-mode run is about to generate more than ~20 articles, state the count explicitly and give the user a chance to narrow it down (e.g. via `--topics`) before committing to the full run. This is a genuinely large, multi-step, token- and time-expensive batch, and a quick sanity check here is worth the friction. For smaller batches (default mode, or a narrowed `--topics` deep-mode run), just proceed.

### Step 4 — Generate, tracking progress

1. Maintain a simple status list across the run (pending → in progress → done / skipped / failed) and surface it periodically rather than going silent through a long batch — the user should be able to tell it's working and roughly how far along it is.
2. **If subagent/parallel task tooling is available in this environment:** dispatch a small number of topics concurrently (a concurrency cap of ~3–4 is reasonable — these are PDF-reading, long-generation tasks, so going wider risks rate limits and makes progress harder to track) rather than fully serial. Each dispatched unit runs the complete `book-topic-article` workflow for exactly one topic.
3. **If no parallel tooling is available:** process the queue strictly one topic at a time, completing each article fully (including its own confirmation step) before starting the next.
4. On a per-topic failure (e.g. the topic doesn't resolve cleanly against the guidelines, or the source pages turn out to have essentially nothing to say) — don't abort the whole batch. Log it as failed/skipped with a one-line reason and continue to the next topic; report all failures together at the end.

### Step 5 — Final summary, and hand off to book-crosslink

Report, in one short block: how many articles were generated this run, how many were skipped because they already existed, how many failed (with their one-line reasons). Don't re-print the per-article confirmations from Step 4 in full — those were already surfaced during the run; this is just the batch-level roundup.

Since this skill never touches `book-guidelines.md` or an index, close by telling the user to run `/book-crosslink [book]` next if they want the vault's Topic List linked to the new articles and the index brought up to date — both this skill and `book-crosslink` are manual-invocation only, so don't run it automatically on their behalf; just name the command.

## Example

**Default mode** — Input: `/book-topic-batch Martin-Löf_Type_Theory`
- Resolves `book = Martin-Löf_Type_Theory`; `vaults/Martin-Löf_Type_Theory/book-guidelines.md` exists → proceed.
- No `--deep` → queue is the 8 top-level Topic List entries only (Foundations, Theory of Expressions, Semantics of Judgement Forms, Set-Forming Operations, Subsets, Monomorphic Type Theory, Programming and Program Derivation, Reference Material).
- Of these, `Theory-of-Expressions.md` already exists (from the earlier single-topic run) → skipped by default.
- Plan reported: "8 topics total, 7 to generate, 1 already present — proceeding" (well under the ~20 threshold, so no confirmation needed).
- Generates the remaining 7 via `book-topic-article`, tracking progress as it goes.
- Final summary: "7 generated, 1 skipped (already existed), 0 failed. Run `/book-crosslink Martin-Löf_Type_Theory` next to link these into `book-guidelines.md`'s Topic List and update the vault index."

**Deep mode** — Input: `/book-topic-batch Martin-Löf_Type_Theory --deep`
- Same book, same prerequisite check.
- `--deep` → queue is all 8 top-level entries plus their subtopic bullets — 8 + 27 = 35 items total.
- Plan reported: "35 items total (deep mode), 34 to generate, 1 already present — that's over the ~20 threshold, want me to proceed with the full run, or narrow it with `--topics`?" User confirms "go ahead."
- Generates the remaining 34 via `book-topic-article`, tracking progress as it goes.
- Final summary: "34 generated, 1 skipped (already existed), 0 failed. Run `/book-crosslink Martin-Löf_Type_Theory` next to link these into `book-guidelines.md`'s Topic List and update the vault index."
