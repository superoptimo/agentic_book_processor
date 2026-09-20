---
name: book-topic-article
description: Generates a deep-dive Obsidian/Markdown article on one topic drawn from a book already processed by the book-guidelines skill. Uses vaults/[book]/book-guidelines.md purely as an index to locate the right chapter(s)/pages, then re-reads sources/[book]/book.pdf directly for full technical fidelity, and writes a first-principles, style-and-goals-aware explainer to vaults/[book]/[Topic-Slug].md. Do NOT use this to regenerate or replace book-guidelines.md itself (that's book-guidelines's job) — if vaults/[book]/book-guidelines.md doesn't exist yet, tell the user to run /book-guidelines first instead of fabricating one.
Manual invocation only — invoke explicitly with /book-topic-article, never automatically.
disable-model-invocation: true
argument-hint: "[book-folder-name] \"[topic]\""
---

# Book Topic Article Generator

Turns a single topic from a book into a polished, teachable Obsidian note: a first-principles explainer, shaped by a configurable style and a configurable set of learning goals. Unlike `book-guidelines` (which produces one compressed index per book), this skill produces one focused deep-dive per topic, and there can be many of these per book.

**Relationship to `book-guidelines`:** that skill's output, `book-guidelines.md`, is this skill's *map*, not its *material*. The guidelines "Topic List" and "Chapter Summaries" tell this skill *where* to look in the source PDF; the actual article content always comes from re-reading the relevant pages of `sources/[book]/book.pdf` directly. Never write an article from the guidelines summary alone — it's deliberately compressed and will produce a shallow, generic result.

This skill assumes the same fixed project layout as `book-guidelines`, plus two optional config layers:

```
sources/[book]/book.pdf           <- input: the original book
vaults/[book]/book-guidelines.md  <- input: the book's topic index (prerequisite)
vaults/[book]/[Topic-Slug].md     <- output: this skill's article

vaults/.article-style.md          <- optional: workbench-wide style augmentation
vaults/[book]/.article-style.md   <- optional: book-specific style augmentation
vaults/.learning-goals.md         <- optional: workbench-wide learning goals
vaults/[book]/.learning-goals.md  <- optional: book-specific learning goals
```

## Workflow

### Step 1 — Resolve the book and confirm the prerequisite exists

1. Identify `[book]` from the user's message. They may give the exact `sources/` folder name, or refer to the book informally (title, author, nickname) — match against the folder names under `sources/` and pick the best match. If genuinely ambiguous between two or more books, list the candidates and ask; don't guess silently between unrelated books.
2. Confirm `vaults/[book]/book-guidelines.md` exists.
   - **If it's missing:** stop here. Tell the user this book hasn't been processed yet and that they should run `/book-guidelines [book]` first. Do not attempt to reconstruct a topic index yourself by skimming the PDF — that's a different skill's job and skipping it will produce inconsistent vaults.   
3. Read `book-guidelines.md` in full.

### Step 2 — Resolve the requested topic against the guidelines

1. Take `[topic]` from the user's request (explicit argument, or described in natural language — e.g. "the part about universes" should resolve against a Topic List / Chapter Summaries entry like "The Set of Small Sets (The First Universe)").
2. Search both the **Topic List** (the nested ontology) and the **Chapter Summaries** headers for the best-matching entry or entries. Matching should be semantic, not just literal string matching — the user's phrasing won't always match the book's chapter title verbatim.
3. From the matched Chapter Summaries entry/entries, note the **page range** (e.g. "pp. 13–22") — this is what makes Step 3 targeted instead of a re-read of the whole book.
4. If the topic spans multiple chapters or parts (common for topics that recur across the book, e.g. "propositions as sets"), note all relevant ranges — the article should synthesize across them, not just cover the first hit.
5. If nothing in the guidelines plausibly matches the requested topic, say so explicitly and ask whether the user wants to (a) pick a different/adjacent topic that *is* covered, or (b) have you do a fresh full-book search anyway (expensive, and a sign the guidelines may need regenerating).

### Step 3 — Go back to the source for real material

1. Open `sources/[book]/book.pdf` and extract the pages identified in Step 2. Use the `pdf-reading` skill's approach (`pdftotext -layout` for prose/definitions/notation; rasterize + view specific pages if the section relies on figures, diagrams, or tables that text extraction would mangle).
2. From that extraction, pull out the actual raw material the article will be built from:
   - the book's own precise definitions and terminology (preserve notation exactly — don't paraphrase symbols away),
   - any named theorems, lemmas, or worked examples the book itself uses,
   - the section's own motivating narrative (why the book introduces this concept where it does),
   - anything the guidelines' Chapter Summary flagged under "Key Definitions & Concepts" or "Key Questions" for that chapter — treat those as a checklist of things the article should actually address, not just gesture at.
3. If the extracted pages turn out to be thin (e.g. a one-paragraph topic), that's fine — say so in the final confirmation rather than padding the article artificially.

### Step 4 — Resolve style and learning goals

This skill has a small **fixed core contract** (below) that always applies, plus **configurable layers** that augment it. Configuration never removes or contradicts the core contract — it only adds emphasis, defaults, and extra structure on top.

**4a. Core contract (fixed, always applies, not overridable):**

- **Objective:** build a precise, durable mental model of the source concept — not a superficial gloss.
- **Sequencing — first principles before symbols:** always explain the intuitive "why" a construct exists (what problem it solves, what breaks without it) *before* introducing its formal notation. Symbols should land as "oh, that's the formal version of what I just understood," not as the starting point.
- **Tone:** rigorous, clear, intellectually engaging — never condescending, never hand-wavy. Precision is not sacrificed for accessibility.
- **Math notation:** LaTeX only (`$...$` inline, `$$...$$` for display), never inside backticks or code fences. Code fences are reserved exclusively for real, syntactically valid code.
- **Obsidian conventions:** short YAML frontmatter (`title`, source book, chapter(s)/page range, `tags`); a wikilink back to the index (`[[book-guidelines|↩ Back to guidelines]]`) near the top or bottom; otherwise portable Markdown so the note still renders outside Obsidian.
- **Output path:** exactly `vaults/[book]/[Topic-Slug].md`, `[Topic-Slug]` in Title-Case-With-Hyphens, mirroring the guidelines' chapter title capitalization where applicable.
- **Default audience** (used only if no style file overrides it): a technical reader with strong programming fundamentals but limited formal/abstract-math background.
- **Default grounding** (used only if no style file overrides it): pair every abstract construct with a concrete code example or analogy in Rust, Python, and Lean.
- **Output language:** resolved *only* from `.article-style.md` layers (workbench and/or book-level) — never inferred from anything else. Default: **English**, unless a style file explicitly sets a different output language (see 4b). If both a workbench-level and a book-level style file set a language, book-level wins for that book. Regardless of prose language, the following always stay as-is, untranslated:
  - code inside fences (syntax is the target language's syntax, e.g. Rust/Python/Lean keywords stay Rust/Python/Lean keywords),
  - LaTeX math,
  - proper nouns, named theorems, and the book's own technical terminology on first use (give the prose-language explanation, then the source term in parentheses if the book's own language differs, e.g. "type inhabitation (*habitación de tipos*)" — never silently drop the term the reader would need to cross-reference back to the book or to other literature),
  - YAML frontmatter *keys* (`title`, `tags`, etc. stay as written in this skill) — frontmatter *values* follow the prose language.

**4b. Load and merge configurable layers, in this order (later layers augment, never override, earlier ones):**

1. Core contract (4a).
2. `vaults/.article-style.md`, if present — workbench-wide defaults (audience calibration, preferred grounding languages, output prose language, depth targets, recurring structural asks, house voice).
3. `vaults/[book]/.article-style.md`, if present — book-specific refinements on top of the workbench default (e.g. a denser book might call for more worked examples, or this one book's articles should be in a different prose language than the workbench norm — say, working through a Spanish-language source and wanting the article in Spanish too).
4. `vaults/.learning-goals.md`, if present — the user's standing learning objectives, independent of any one book.
5. `vaults/[book]/.learning-goals.md`, if present — how this particular book serves those objectives, or book-specific goals.

If a style file is absent at some level, just skip it — absence means "no augmentation at that level," not an error. If style layers conflict with each other (workbench vs. book-specific), the more specific (book-level) wins for that particular point, but only for genuinely conflicting instructions — non-conflicting guidance from both still applies.

**4c. Apply learning goals as emphasis, not as new topics, and never as a language signal.** Learning-goals files describe the reader's broader project and should shape:
   - which of the topic's facets get the deepest treatment (the ones most load-bearing for the stated goals),
   - what the closing synthesis connects the topic to (Step 5.3),
   - which code-grounding languages or paradigms get priority when the goals name a specific target system (e.g. a reader building a Rust verifier should see Rust-side grounding treated as primary, not just one of three equally-weighted options).
   Learning goals should never cause the article to wander off-topic into content the source pages don't support — they steer emphasis and connections, not invention. **Learning-goals files may be written in any language, independent of the article's output language** (e.g. a Spanish-language `.learning-goals.md` paired with English-language articles is expected and fine) — only `.article-style.md`'s output-language setting decides what language the article is written in; the goals file's own language is never treated as a signal for that.

### Step 5 — Write the article

1. Follow the output path and Obsidian conventions from the core contract (4a).
2. **Content shape** (a guide, not a rigid template — let the topic and the resolved style dictate the exact structure):
   - Open with the first-principles motivation: what problem does this concept solve, why does the book introduce it here.
   - Break the topic into its constituent ideas, each one immediately paired with its grounding (per the resolved style) — don't front-load all the analogies at the end.
   - Preserve the book's own notation faithfully throughout.
   - Close with a short synthesis: how this topic connects back into the book's larger structure (what depends on it, what it depends on), and — if learning-goals files are in effect — a brief note on how it bears on those goals (e.g. "this is the mechanism your elaborator's unifier will need for implicit-argument resolution"). A text-diagram is often effective for the structural half of this.
3. **Depth:** this is a genuine deep-dive, not a re-statement of the guidelines summary. Let the richness of the source material (Step 3), tempered by any depth guidance from the resolved style, determine the length naturally rather than targeting a fixed word count.

### Step 6 — Confirm

After writing the file, briefly tell the user:
- where it was saved, and which chapter(s)/pages it drew from,
- which style/goals config files were found and applied (e.g. "used vaults/.article-style.md and vaults/[book]/.learning-goals.md; no book-specific style file found"),
- anything notable about the source material (e.g. "this topic spans chapters 7 and 13", "the section had no worked examples in the book, so the code examples here are original illustrations of the same idea"),
- if applicable, the legacy-filename note from Step 1.

## Example

Input: `/book-topic-article thompson-type-theory "Theory of Expressions"`
- Prerequisite check: `vaults/thompson-type-theory/book-guidelines.md` exists → proceed.
- Guidelines match: Chapter 3, "Expressions and Definitional Equality" (pp. 13–22), Topic List section "2. Theory of Expressions."
- Source re-read: `sources/thompson-type-theory/book.pdf`, pages 13–22.
- Style resolution: `vaults/.article-style.md` found (sets Rust as primary grounding language); no book-specific style file; `vaults/.learning-goals.md` found (compiler/elaborator project).
- Output: `vaults/thompson-type-theory/Theory-of-Expressions.md` — opening with why a logic book needs a syntax layer before its logic, application/abstraction/combination/selection each grounded primarily in Rust (with Python/Lean as secondary), arities explained as a proto-type-system, and a closing synthesis noting this layer is the ancestor of the AST the reader's verifier will type-check.
