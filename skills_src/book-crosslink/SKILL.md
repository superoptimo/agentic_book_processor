---
name: book-crosslink
description: Post-processing pass that wires up an already-generated collection of book-topic-article notes, with three responsibilities: (1) cross-referencing between article bodies via Obsidian [[wikilinks]] wherever one article's prose mentions another's topic or a subsection concept, including similarity-based near-miss matches, not just exact ones; (2) linking each entry in vaults/[book]/book-guidelines.md's Topic List to its corresponding generated article, once that article exists; (3) fully assembling/maintaining the vault's "index.md" Map-of-Content note from that same linked Topic List. This is the sole owner of book-guidelines.md's link updates and of the Index note — book-topic-article and book-topic-batch only ever generate the topic articles themselves, never touch book-guidelines.md, and never produce an index. Runs a bundled deterministic script (scripts/crosslink.py) rather than hand-editing prose, so it's safe to re-run repeatedly as new articles get added. Manual invocation only — invoke explicitly with /book-crosslink, never automatically.
disable-model-invocation: true
argument-hint: "[book-folder-name] [--dry-run] [--verbose] [--fuzzy-threshold 0.62] [--no-fuzzy] [--no-guidelines-links] [--no-index]"
---

# Book Article Cross-Linker

**Invocation:** this skill only runs when explicitly called with `/book-crosslink`. It must never be triggered automatically by Claude inferring intent from conversation — always wait for the explicit command, even after a `book-topic-batch` run that clearly left the vault ready for it.

Wires up an existing, partially-or-fully-generated `book-topic-article` vault, end to end:

1. cross-references article prose against each other (exact + similarity search),
2. links every entry in `book-guidelines.md`'s Topic List to its matching generated article, once one exists, and
3. fully regenerates `index.md` from that same linked Topic List.

**This skill is the sole owner of book-guidelines.md's link state and of the Index note.** Neither `book-topic-article` nor `book-topic-batch` touches `book-guidelines.md` or produces an index — they only generate the topic articles themselves. This keeps a clean separation: the batch/single-article skills are pure *generators*, and this skill is the pure *wiring* stage that runs after them (and can run again after every subsequent batch, since it's idempotent).

**Why this is a script, not freehand editing:** reliably finding "the first plain-text occurrence of this exact term, but not inside a code block/math block/existing link/frontmatter, and not a duplicate of a link already present" across a whole folder — plus parsing and precisely rewriting a structured two-level list inside `book-guidelines.md` without disturbing its other sections — is exactly the kind of repetitive, rule-governed text transformation that should be deterministic rather than left to per-file judgement calls. The bundled `scripts/crosslink.py` handles all of that consistently.

```
vaults/[book]/*.md                    <- input AND output: existing generated articles, edited in place
vaults/[book]/book-guidelines.md          <- input AND output: only the Topic List section is ever touched
vaults/[book]/index.md       <- output: fully (re)derived from book-guidelines.md's Topic List each run
vaults/[book]/.crosslink-glossary.md  <- optional input: manual term -> target overrides
vaults/[book]/.crosslink-ignore.md    <- optional input: terms to never auto-link
```

## What the script does (so you can explain it, not just invoke it)

The script runs three passes with different guarantees. Keep this distinction straight when explaining results to the user: **pass 1 and pass 3 are safe to fully automate; pass 2 is a recall tool that needs a judgment call before anything gets written.**

**Pass 1 — exact matching between article bodies (auto-applied):**

1. **Builds a glossary of linkable terms** from the folder itself — no external topic list needed:
   - every article's own title (its filename) → a whole-file link target
   - every `##`/`###` heading inside every article → a heading-anchor link target (`[[Slug#Heading]]`)
   - merged with any manual entries from `.crosslink-glossary.md`, if present (format: `Term | Target-Slug` or `Term | Target-Slug#Heading`, one per line)
2. **Filters out generic noise** via a small built-in stoplist (words like "Example", "Summary", "Rules" that show up as headings constantly but make useless, over-eager links) plus anything the user adds to `.crosslink-ignore.md`.
3. **Scans each article's prose**, explicitly protecting: YAML frontmatter, fenced code blocks, inline code spans, `$...$`/`$$...$$` math, and text already inside `[[...]]` or `[...](...)`. Only real prose is eligible for linking.
4. **Links the first occurrence only** of each term per article, matched case-insensitively but preserving the original casing as the link's display text (`[[Target|original text]]`) so the sentence reads exactly as before, just with a link wrapped around it.
5. **Never self-links** — a term is skipped if its target is the article it already appears in.
6. **Is idempotent** — before adding a link, it checks whether the file already links to that exact target anywhere (not just at that specific spot), so re-running after new articles are added won't create duplicate or conflicting links to concepts already covered.
7. **Only writes files that actually changed**, and reports exactly what was linked, per file.

**Pass 2 — similarity search between article bodies (advisory only, never auto-applied):**

Exact matching misses the case the user specifically asked this skill to handle: two articles referring to the same concept in noticeably different words (a plural/reworded variant, a reordered phrase, a different but overlapping set of words — e.g. "the universe of small sets" phrased loosely elsewhere as "small-sets universe," or a heading "Definitional Equality" mentioned elsewhere as "definitional equalities"). For every glossary term, pass 2 slides a word-window of comparable length across each *other* article's unprotected prose and scores it against the term using a blend of sequence similarity and word-overlap on a lightly normalized form (lowercased, minor stopword/plural stripping — order-insensitive, so reordered phrases still score well). Anything above `--fuzzy-threshold` (default `0.62`) is reported, not written.

This is intentionally **not** treated as a real semantic/meaning-based match — it's a lexical recall net that surfaces plausible candidates (including some false positives) for a second opinion. String similarity doesn't know that two phrases mean the same thing, only that they're spelled similarly; genuinely different concepts that happen to share several words (or, conversely, true synonyms spelled completely differently, like an acronym) will not be handled correctly by this pass. That judgment call belongs to whoever reviews the report — which, in this pipeline, is you (the assistant), reading the printed suggestions and deciding which ones are real.

**Pass 3 — guidelines Topic List linking + Index assembly (auto-applied, narrowly scoped):**

Unlike passes 1/2, `book-guidelines.md` and `index.md` are never scanned as free prose. Instead:

1. Only the **`## Topic List` section** of `book-guidelines.md` is parsed — the Header and Chapter Summaries sections are never touched, no matter what they contain.
2. Every top-level entry and every subtopic bullet is matched against the set of generated articles, in order of confidence: an **exact** filename-slug match first, then a **collision-suffixed** match (for a subtopic disambiguated as `Beta-Reduction-(Theory-of-Expressions).md`), then a **fuzzy** similarity fallback (reusing pass 2's scoring) for minor wording drift between the guidelines phrasing and the article that actually got generated for it.
3. A matched entry gets its text wrapped in a wikilink (`[[Target|original text]]`), preserving the numbering/bolding/bullet formatting exactly. An entry with no match yet is left as plain text — so **the Topic List itself doubles as a live "what's been generated so far" indicator.**
4. **Every entry is re-evaluated on every run**, not just unlinked ones — but a stable exact/collision match never changes, and a fuzzy match is only ever *replaced* by a later exact/collision match (e.g. once a subtopic that had fallen back to linking its parent category gets its own dedicated article), never by a different fuzzy match. This keeps steady-state runs a true no-op while still letting imprecise early links self-correct as the vault fills in — this was verified directly: a subtopic that initially fuzzy-matched its parent article correctly re-pointed to its own article the moment that article was generated, and stayed a no-op on every run before and after.
5. `index.md` is then **fully regenerated** from that same (now-linked) Topic List content, with a back-link to `book-guidelines.md` and a title pulled from the guidelines Header's `**Title:**` field (falling back to a humanized folder name if that's missing). Being entirely derived, it's simply rewritten each run rather than incrementally merged — cheap, and guaranteed to always be exactly in sync with the Topic List.

## The review-and-promote loop for pass-2 suggestions

Because pass 2 never writes anything, a confirmed suggestion needs one more step to actually become a link:

1. Run the script; read its "possible related mention(s)" section per file.
2. For each suggestion, use your own judgment (not just the printed score) on whether it's really the same concept — the score is a filter, not a verdict.
3. For every suggestion you confirm, add it as a new line to `vaults/[book]/.crosslink-glossary.md` in the format `Matched Phrase | Target-Slug` (or `Target-Slug#Heading` for a specific section) — this is the same override file pass 1 already reads, so promoting a fuzzy match makes it permanent and exact-match-safe from then on.
4. Re-run the script (without `--dry-run`) — the newly glossary'd phrase is now linked deterministically by pass 1, and will no longer show up as a pass-2 suggestion on future runs.
5. Discard suggestions you don't confirm — they'll simply be reported again next run if the wording is still there, which is fine; nothing needs to be done to "dismiss" them permanently unless the user wants to suppress that specific heading/term entirely, in which case `.crosslink-ignore.md` is the right place for it instead.

## Workflow

### Step 1 — Resolve the book and confirm there's something to work with

1. Resolve `[book]` the same way the other skills in this pipeline do (match against `sources/` folder names).
2. List `vaults/[book]/`. Passes 1/2 (article-to-article cross-referencing) need at least two eligible articles — if fewer, the script itself will say so and simply skip them, not error out. Pass 3 (guidelines linking + Index) is meaningful with even a single generated article and `book-guidelines.md` present, so this skill is still worth running even right after the very first `book-topic-article` call, not just after a full `book-topic-batch` run.

### Step 2 — Run the script

Run the bundled script against the vault folder:

```bash
python3 scripts/crosslink.py "vaults/[book]" --verbose
```

Use `--dry-run` first if the user wants to preview changes before committing (recommended the first time this is run on a given vault, or any time `.crosslink-ignore.md`/`.crosslink-glossary.md` was just edited and the effect is untested) — this suppresses every write across all three passes, including book-guidelines.md and the Index note. Once satisfied, run it again without `--dry-run` to actually write the changes. Pass 2 never writes regardless of `--dry-run`.

Use `--no-guidelines-links` to skip pass 3's guidelines/Index work entirely (this also implicitly skips the Index, since it's derived from the linked Topic List), or `--no-index` to keep the guidelines links but skip regenerating the Index note specifically.

Do not attempt to replicate any of this logic by manually editing files with `str_replace` — the whole point of scripting these steps is the consistency guarantee across every file (including the structured parsing of `book-guidelines.md`) simultaneously.

### Step 3 — Review the exact-match report (pass 1)

The script prints, per file, exactly which text spans got linked and to what. After it runs:

1. Summarize the totals (files changed, links added) rather than repeating the full verbose output.
2. If the report shows suspicious-looking links (e.g. a very short or very generic term that slipped past the stoplist and got linked somewhere it doesn't belong), flag the specific line to the user and suggest adding that term to `.crosslink-ignore.md` for next time — don't silently "fix" it by hand-editing around the script's output, since that would just be undone the next run.
3. If the user wants finer control going forward (specific terms always pointing to a specific article/section, regardless of what the automatic heading-scan would pick), point them at `.crosslink-glossary.md` as the durable way to encode that, rather than one-off manual edits.

### Step 4 — Review the similarity suggestions (pass 2) and promote the real ones

The script also prints a "possible related mention(s)" section per file — phrasings that are *similar to but not identical with* a glossary term, above `--fuzzy-threshold`. These were **not** written to any file.

1. Go through each suggestion and judge it on meaning, not just the printed score — a high lexical-similarity score does not guarantee the same concept, and a real synonym can score low if it's spelled very differently (e.g. an acronym). This is where your understanding of the book's content, not string-matching, does the actual work.
2. For every suggestion you confirm is a genuine same-concept mention, add a line to `vaults/[book]/.crosslink-glossary.md`: `Matched Phrase | Target-Slug` (or `Target-Slug#Heading`).
3. Re-run the script (`python3 scripts/crosslink.py "vaults/[book]" --verbose`, without `--dry-run`) so pass 1 picks up the newly glossary'd phrases and writes the links deterministically.
4. Tell the user how many suggestions you reviewed, how many you promoted, and briefly why you set aside the rest (if any looked like false positives, say so — it helps them calibrate `--fuzzy-threshold` for next time if they want fewer or more candidates surfaced).

### Step 5 — Report the guidelines/Index result (pass 3)

The script reports how many Topic List entries were newly linked or upgraded in `book-guidelines.md`, and whether the Index note was updated or already current. Summarize this plainly — how many topics in the guidelines are now linked to an actual article vs. still awaiting one is genuinely useful information for the user tracking progress on a large vault (especially a deep-mode `book-topic-batch` run with dozens of subtopics).

### Step 6 — Mention re-run safety

Note for the user that this is meant to be **re-run after every future `book-topic-article`/`book-topic-batch` run** that adds new articles to the same vault — because all three passes are either idempotent or purely advisory, re-running the whole thing is the normal way to keep a growing vault fully wired (both article-to-article and guidelines-to-article), not a one-time operation.

## Example

Input: `/book-crosslink Martin-Löf_Type_Theory`
- Resolves `book = Martin-Löf_Type_Theory`; finds 8+ generated articles (not all topics generated yet) plus `book-guidelines.md`.
- Runs `python3 scripts/crosslink.py "vaults/Martin-Löf_Type_Theory" --verbose`.
- Pass-1 report: e.g. `Theory-of-Expressions.md: 3 links added` (mentions of "Definitional Equality," "Universes," and "Program Derivation" each wrapped on first occurrence), `Universes.md: 2 links added`, etc.
- Pass-2 report: e.g. `Universes.md: 2 possible related mention(s)` — `"the set of small sets" ~ "Universes" (score 0.71)` and `"defeq" ~ "Definitional Equality" (score 0.31, below threshold, not shown)`. The first is judged a real match (same concept, reworded) and promoted to `.crosslink-glossary.md` as `the set of small sets | Universes`; the acronym wasn't caught by similarity at all, since it shares no words with the target — worth telling the user that abbreviations need a manual glossary entry, not the similarity pass, if they want those covered.
- Re-runs the script; the promoted phrase is now linked by pass 1.
- Pass-3 report: `12 Topic List entries linked in book-guidelines.md` (out of 35 total, since it's a deep-mode vault that isn't fully generated yet — 23 subtopics are still plain text, correctly left unlinked). `Index note updated at vaults/index.md`.
- Summary to the user: "11 links added across 7 articles via exact matching; 3 similarity suggestions reviewed, 1 promoted and applied, 2 set aside as unrelated. In book-guidelines.md, 12 of 35 Topic List entries now link to a generated article (the rest are still awaiting one) — Index note updated to match."
