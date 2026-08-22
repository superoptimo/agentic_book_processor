---
name: book-topic-article
description: Generates a deep-dive Obsidian/Markdown article on one topic drawn from a book already processed. Uses a document in the project workspace book-guidelines.md purely as an index to locate the right chapter(s)/pages, then re-reads the specified PDF book attached in the project workspace (book.pdf) by user directly for full technical fidelity, and generates a markdown document with a first-principles, style-and-goals-aware explainer. If book-guidelines.md doesn't exist yet, tell the user to run /book-guidelines first instead of fabricating one. Manual invocation only — invoke explicitly with /book-topic-article, never automatically.
disable-model-invocation: true
argument-hint: \"[topic]\""
---

# Book Topic Article Generator

Turns a single topic from a book into a polished, teachable Obsidian note: a first-principles explainer, shaped by a configurable style and a configurable set of learning goals. This skill produces one focused deep-dive per topic, and there can be many of these per book.

**Relationship to `book-guidelines`:** that skill's output, `book-guidelines.md`, is this skill's *map*, not its *material*. The guidelines "Topic List" and "Chapter Summaries" tell this skill *where* to look in the source PDF; the actual article content always comes from re-reading the relevant pages of `book.pdf` directly. Never write an article from the guidelines summary alone — it's deliberately compressed and will produce a shallow, generic result.

This skill assumes the same fixed project layout as `book-guidelines`, plus two optional config layers:

```
book.pdf           <- input: the original book
book-guidelines.md  <- input: the book's topic index (prerequisite)
article-style.md   <- optional: book-specific style augmentation
learning-goals.md         <- optional: workbench-wide learning goals
```

## Workflow

### Step 1 — Resolve the book and confirm the prerequisite exists

1. Confirm `book.pdf` exists.
2. Confirm `book-guidelines.md` exists.
   - **If it's missing:** stop here. Tell the user this book hasn't been processed yet and that they should run `/book-guidelines [book]` first. Do not attempt to reconstruct a topic index yourself by skimming the PDF — that's a different skill's job and skipping it will produce inconsistent vaults.   
2. Read `book-guidelines.md` in full.

### Step 2 — Resolve the requested topic against the guidelines

1. Take `[topic]` from the user's request (explicit argument, or described in natural language — e.g. "the part about universes" should resolve against a Topic List / Chapter Summaries entry like "The Set of Small Sets (The First Universe)").
2. Search both the **Topic List** (the nested ontology) and the **Chapter Summaries** headers for the best-matching entry or entries. Matching should be semantic, not just literal string matching — the user's phrasing won't always match the book's chapter title verbatim.
3. From the matched Chapter Summaries entry/entries, note the **page range** (e.g. "pp. 13–22") — this is what makes Step 3 targeted instead of a re-read of the whole book.
4. If the topic spans multiple chapters or parts (common for topics that recur across the book, e.g. "propositions as sets"), note all relevant ranges — the article should synthesize across them, not just cover the first hit.
5. If nothing in the guidelines plausibly matches the requested topic, say so explicitly and ask whether the user wants to (a) pick a different/adjacent topic that *is* covered, or (b) have you do a fresh full-book search anyway (expensive, and a sign the guidelines may need regenerating).

### Step 3 — Go back to the source for real material

1. From the file "book.pdf" pull out the actual raw material the article will be built from:
   - the book's own precise definitions and terminology (preserve notation exactly — don't paraphrase symbols away),
   - any named theorems, lemmas, or worked examples the book itself uses,
   - the section's own motivating narrative (why the book introduces this concept where it does),
   - anything the guidelines' Chapter Summary flagged under "Key Definitions & Concepts" or "Key Questions" for that chapter — treat those as a checklist of things the article should actually address, not just gesture at.

### Step 4 — Resolve style and learning goals

This skill has a small **fixed core contract** (below) that always applies, plus **configurable layers** that augment it. Configuration never removes or contradicts the core contract — it only adds emphasis, defaults, and extra structure on top.

**4a. Core contract (fixed, always applies, not overridable):**

- **Objective:** build a precise, durable mental model of the source concept — not a superficial gloss.
- **Sequencing — first principles before symbols:** always explain the intuitive "why" a construct exists (what problem it solves, what breaks without it) *before* introducing its formal notation. Symbols should land as "oh, that's the formal version of what I just understood," not as the starting point.
- **Tone:** rigorous, clear, intellectually engaging — never condescending, never hand-wavy. Precision is not sacrificed for accessibility.
- **Math notation:** LaTeX only (`$...$` inline, `$$...$$` for display), never inside backticks or code fences. Code fences are reserved exclusively for real, syntactically valid code.
- **Default audience** (used only if no style file overrides it): a technical reader with strong programming fundamentals but limited formal/abstract-math background.
- **Default grounding** (used only if no style file overrides it): pair every abstract construct with a concrete code example or analogy in Rust, Python, and Lean.
- **Obsidian conventions:** short YAML frontmatter (`title`, source book, chapter(s)/page range, `tags`); a wikilink back to the index (`[[book-guidelines|↩ Back to guidelines]]`) near the top or bottom; otherwise portable Markdown so the note still renders outside Obsidian.
- **Output language:** resolved *only* from `article-style.md` layers (workbench and/or book-level) — never inferred from anything else. Default: **English**, unless a style file explicitly sets a different output language (see 4b). If both a workbench-level and a book-level style file set a language, book-level wins for that book. Regardless of prose language, the following always stay as-is, untranslated:
  - code inside fences (syntax is the target language's syntax, e.g. Rust/Python/Lean keywords stay Rust/Python/Lean keywords),
  - LaTeX math,
  - proper nouns, named theorems, and the book's own technical terminology on first use (give the prose-language explanation, then the source term in parentheses if the book's own language differs, e.g. "type inhabitation (*habitación de tipos*)" — never silently drop the term the reader would need to cross-reference back to the book or to other literature),
  - YAML frontmatter *keys* (`title`, `tags`, etc. stay as written in this skill) — frontmatter *values* follow the prose language.

**4b. Load and merge configurable layers, in this order (later layers augment, never override, earlier ones):**

1. Core contract (4a).
2. `article-style.md`, if present — workbench-wide defaults (audience calibration, preferred grounding languages, output prose language, depth targets, recurring structural asks, house voice).
3. `learning-goals.md`, if present — the user's standing learning objectives, independent of any one book. Also resolve how this particular book serves those objectives, or book-specific goals.

If a style file is absent at some level, just skip it — absence means "no augmentation at that level," not an error. If style layers conflict with each other (workbench vs. book-specific), the more specific (book-level) wins for that particular point, but only for genuinely conflicting instructions — non-conflicting guidance from both still applies.

**4c. Apply learning goals as emphasis, not as new topics, and never as a language signal.** Learning-goals files describe the reader's broader project and should shape:
   - which of the topic's facets get the deepest treatment (the ones most load-bearing for the stated goals),
   - what the closing synthesis connects the topic to (Step 5.3),
   - which code-grounding languages or paradigms get priority when the goals name a specific target system (e.g. a reader building a Rust verifier should see Rust-side grounding treated as primary, not just one of three equally-weighted options).
   Learning goals should never cause the article to wander off-topic into content the source pages don't support — they steer emphasis and connections, not invention. **Learning-goals files may be written in any language, independent of the article's output language** (e.g. a Spanish-language `learning-goals.md` paired with English-language articles is expected and fine) — only `article-style.md`'s output-language setting decides what language the article is written in; the goals file's own language is never treated as a signal for that.

### Step 5 — Write the article

1. Follow the output path and Obsidian conventions from the core contract (4a).
2. **Content shape** (a guide, not a rigid template — let the topic and the resolved style dictate the exact structure):
   - Open with the first-principles motivation: what problem does this concept solve, why does the book introduce it here.
   - Break the topic into its constituent ideas, each one immediately paired with its grounding (per the resolved style) — don't front-load all the analogies at the end.
   - Preserve the book's own notation faithfully throughout.
   - Close with a short synthesis: how this topic connects back into the book's larger structure (what depends on it, what it depends on), and — if learning-goals files are in effect — a brief note on how it bears on those goals (e.g. "this is the mechanism your elaborator's unifier will need for implicit-argument resolution"). A text-diagram is often effective for the structural half of this.
3. **Depth:** this is a genuine deep-dive, not a re-statement of the guidelines summary. Let the richness of the source material (Step 3), tempered by any depth guidance from the resolved style, determine the length naturally rather than targeting a fixed word count.

## Example

Input: `/book-topic-article Theory of Expressions`
- Prerequisite check: `book-guidelines.md` exists and `book.pdf`exists too → proceed.
- Guidelines match: Chapter 3, "Expressions and Definitional Equality" (pp. 13–22), Topic List section "2. Theory of Expressions."
- Source re-read: `book.pdf`, pages 13–22.
- Style resolution: `article-style.md` found (sets Rust as primary grounding language); no book-specific style file; `learning-goals.md` found (compiler/elaborator project).
- Output: Opening with why a logic book needs a syntax layer before its logic, application/abstraction/combination/selection each grounded primarily in Rust (with Python/Lean as secondary), arities explained as a proto-type-system, and a closing synthesis noting this layer is the ancestor of the AST the reader's verifier will type-check.
