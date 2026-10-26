---
name: book-topic-article
description: Generates a deep-dive Obsidian/Markdown article on one topic drawn from a book already processed by the book-guidelines skill. Uses vaults/[book]/book-guidelines.md purely as an index to locate the right chapter(s)/pages, then re-reads sources/[book]/book.pdf directly for full technical fidelity, and writes a first-principles, style-and-goals-aware explainer to vaults/[book]/[Topic-Slug].md, using any Focus-Area tags in vaults/[book]/.learning-goals.md to prioritize which goal-connections to surface. Every numbered definition, lemma, theorem, notation and example in the source pages is presented, complete and clearly restated, as its own self-contained block, so the reader can study each one in isolation without going back to the book. Accepts a topic title, a free-form --prompt (which can also set style, emphasis, angle, or output language for that one article), or both. Do NOT use this to regenerate or replace book-guidelines.md itself (that's book-guidelines's job) — if vaults/[book]/book-guidelines.md doesn't exist yet, tell the user to run /book-guidelines first instead of fabricating one.
Manual invocation only — invoke explicitly with /book-topic-article, never automatically.
disable-model-invocation: true
argument-hint: "[book-folder-name] [\"topic\"] [--prompt \"free-form request: angle, questions, style, emphasis\"]"
---

# Book Topic Article Generator

Turns a single topic from a book into a polished, teachable Obsidian note: a first-principles explainer, shaped by a configurable style and a configurable set of learning goals. Unlike `book-guidelines` (which produces one compressed index per book), this skill produces one focused deep-dive per topic, and there can be many of these per book.

**The article is learning material, not a transcription.** Its job is to make the topic understood better than the book's own presentation does, so the reader can study from the note without having to go back to the PDF to find what a definition really says. Two failures are equally bad:
- *Losing content:* summarising a definition into a sentence, dropping a clause or a side condition, or naming a lemma in passing without stating it. The reader then has to open the book to learn what the concept actually is.
- *Copying the book:* pasting the book's text without making it clearer. The note must add value: plain-language restatement, structure, motivation, examples, diagrams, grounding code.

The rule is: **complete in substance, free in presentation.** Every definition, notation, lemma, theorem and example in scope is present, with all of its clauses and conditions, as its own readable unit. How it is presented (wording, layout, tables, diagrams, order within a unit, worked examples) is chosen for clarity.

**Relationship to `book-guidelines`:** that skill's output, `book-guidelines.md`, is this skill's *map*, not its *material*. The guidelines "Topic List" and "Chapter Summaries" tell this skill *where* to look in the source PDF; the actual article content always comes from re-reading the relevant pages of `sources/[book]/book.pdf` directly. Never write an article from the guidelines summary alone — it's deliberately compressed and will produce a shallow, generic result.

## Invocation forms

```
/book-topic-article <book> "<topic>"                       # topic only (original behaviour)
/book-topic-article <book> "<topic>" --prompt "<prompt>"   # topic + steering prompt
/book-topic-article <book> --prompt "<prompt>"             # prompt only: the topic is derived from it
```

- `<book>` is the first token (folder name or informal reference, see Step 1).
- `"<topic>"` is an optional quoted title or description, as before.
- `--prompt "<prompt>"` is optional. Everything inside the quotes following the flag is the **prompt**: a free-form request that may (a) name or imply the topic, (b) pose specific questions the article must answer, (c) pick an angle or scope ("only the algorithmic side", "compare with Lean's kernel"), and/or (d) specify style and emphasis (audience, grounding language, depth, structure, tone, diagrams, output language). If the prompt contains a literal `"`, expect it escaped or in single quotes; if the argument string is otherwise ambiguous, treat everything after `--prompt` as the prompt.
- If neither a topic nor a prompt is given, ask for one.
- Treat the prompt's text as the user's own instructions for this article, but never as a way to skip the prerequisite checks, the source re-read, or the fidelity rules (Steps 1, 3 and 4a).

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

0. **Prompt-only or prompt-augmented requests.** If `--prompt` was given, first split it mentally into (i) *subject matter* (what to cover), (ii) *questions/angle* (what the article must answer or the slice it should take) and (iii) *style/emphasis directives* (handled in Step 4e). Use (i) as the topic when no explicit `[topic]` was passed; when both are passed, the explicit `[topic]` anchors the guidelines lookup and the prompt narrows or redirects it. If the prompt implies several distinct topics, either treat them as one themed article when they hang together or say so and ask whether to split; don't silently produce a sprawling article.
1. Take `[topic]` from the user's request (explicit argument, the subject matter extracted from the prompt, or described in natural language — e.g. "the part about universes" should resolve against a Topic List / Chapter Summaries entry like "The Set of Small Sets (The First Universe)").
2. Search both the **Topic List** (the nested ontology) and the **Chapter Summaries** headers for the best-matching entry or entries. Matching should be semantic, not just literal string matching — the user's phrasing won't always match the book's chapter title verbatim.
3. From the matched Chapter Summaries entry/entries, note the **page range** (e.g. "pp. 13–22") — this is what makes Step 3 targeted instead of a re-read of the whole book.
4. If the topic spans multiple chapters or parts (common for topics that recur across the book, e.g. "propositions as sets"), note all relevant ranges — the article should synthesize across them, not just cover the first hit.
5. **Check for existing articles.** List `vaults/[book]/` and look for existing notes that cover the same topic (match on slug words and on frontmatter `title`/`chapters`). If one substantially overlaps the request, do not overwrite it silently: tell the user what exists and ask whether to (a) leave it, (b) regenerate it, or (c) write a complementary article under a different slug with a clearly distinct angle (and cross-link the two with a wikilink). If the prompt itself already says "replace/regenerate/update X" or "complement X", follow that without asking. Never overwrite an existing file you have not looked at.
6. If nothing in the guidelines plausibly matches the requested topic, say so explicitly and ask whether the user wants to (a) pick a different/adjacent topic that *is* covered, or (b) have you do a fresh full-book search anyway (expensive, and a sign the guidelines may need regenerating).

### Step 3 — Go back to the source for real material

1. Open `sources/[book]/book.pdf` and extract the pages identified in Step 2. Use the `pdf-reading` skill's approach (`pdftotext -layout` for prose/definitions/notation; rasterize + view specific pages if the section relies on figures, diagrams, tables, or typeset symbols that text extraction would mangle). When in doubt about a symbol or a clause, look at the rasterized page rather than trusting the text layer.
   If the prompt poses specific questions or an angle, widen or shift the extraction to whatever pages actually answer them (guidelines page ranges are a starting point, not a fence), and keep a checklist of the prompt's questions.
   Extend the range by a page on each side of the guidelines range: definitions and examples often straddle page breaks.
2. **Build the Source Inventory (mandatory, before writing anything).** Go through the extracted pages line by line and list, in order of appearance, every numbered or named formal item, with its number, its kind and its page:
   - Definitions, Notations, Conventions
   - Lemmas, Theorems, Propositions, Corollaries, Facts
   - Examples, Remarks, Exercises (the ones the text relies on)
   - Proofs (each one, including "proof left as exercise" and "see reference X")
   - Named rules, axioms, figures and tables

   For each **Definition** also list every numbered sub-clause (1), (2), (3)... and every symbol or term it introduces. A definition with four clauses is four inventory entries, not one. For each **Lemma/Theorem** list every sub-claim and every term or symbol it *uses*. Keep the inventory in your working notes; it is the checklist for Step 5.4 and the table in Step 6.
3. From the extraction, also pull out:
   - the book's own motivating narrative (why the book introduces this concept where it does, and the book's informal reading of each statement: "intuitively...", "in words...", "this says that...") — these informal readings are part of the material, keep them,
   - anything the guidelines' Chapter Summary flagged under "Key Definitions & Concepts" or "Key Questions" for that chapter — treat those as a checklist of things the article should actually address, not just gesture at.
4. **Dependency closure.** For every term or symbol used in a statement on the inventory (for example `dom`, a projection, a subcontext), check whether the book defines it. If the definition lies in the extracted pages, it is on the inventory already. If it lies elsewhere (an earlier chapter), find it, add it to the inventory with its original number, and reproduce it in the article (or, if it is long and only peripheral, state it briefly and cite its number). Never use a defined symbol in a statement without its definition being reachable from the article.
5. If the extracted pages turn out to be thin (e.g. a one-paragraph topic), that's fine — say so in the final confirmation rather than padding the article artificially.

### Step 4 — Resolve style and learning goals

This skill has a small **fixed core contract** (below) that always applies, plus **configurable layers** that augment it. Configuration never removes or contradicts the core contract — it only adds emphasis, defaults, and extra structure on top.

**4a. Core contract (fixed, always applies, not overridable):**

- **Objective:** build a precise, durable mental model of the source concept — not a superficial gloss.
- **Sequencing — first principles before symbols:** always explain the intuitive "why" a construct exists (what problem it solves, what breaks without it) *before* introducing its formal notation. Symbols should land as "oh, that's the formal version of what I just understood," not as the starting point. This is compatible with the fidelity rules below: the motivation comes first, then the formal block, then the unpacking.
- **Formal-statement fidelity (the rule that makes the article self-sufficient):**
  1. **Every item on the Source Inventory that falls within the topic appears in the article.** Definitions, notations, lemmas, theorems, propositions, corollaries, numbered examples that illustrate them, and the book's proofs. Omit an item only if it is genuinely outside the topic, and then list it in the Step 6 coverage report. Never drop a definition because it looks auxiliary (domain of a context, projection, subcontext...): if a later statement uses it, it must be there.
  2. **One block per item.** Each Definition, Lemma, Theorem, Proposition, Corollary and Example gets its own visually separate block, never merged into a running paragraph and never reduced to a mention ("the Thinning Lemma says one can add junk"). The block must be readable in isolation, without the surrounding prose.
  3. **Block format.** Use an Obsidian callout so the block is also a plain blockquote outside Obsidian:

     ```
     > [!definition] Definition 2.10.1 (Domain, dom, subcontext, ...)
     > 1. First clause, in the book's wording and notation.
     > 2. Second clause...
     ```

     Callout types: `definition`, `theorem` (for lemmas, theorems, propositions, corollaries), `example`, `note` (remarks), `proof`. The title line carries the book's number, kind and name exactly as printed (`Lemma 2.10.5 (Thinning, Condensing, Permutation)`).
  4. **Complete in substance, clear in presentation.** The *Statement* part of a block must contain every clause of the book's statement and every condition attached to it ("in the same order", "and vice versa", side conditions such as $x\notin\mathrm{dom}(\Gamma)$), so nothing the reader needs is missing. Use the book's symbols and technical terms (so the note can be cross-referenced), but the wording is free: restate in plainer language, split a dense clause into steps, add a table or a small diagram, order the clauses so they build on each other, give the number of each sub-clause. Never weaken, strengthen, merge away or silently drop a condition, and never change what is defined or claimed.
  5. **Self-contained.** A block must not rely on a symbol the reader has not seen defined. If it uses `dom`, the definition of `dom` is in an earlier block (or is cited by number and restated in one line).
  6. **Block anatomy.** Each block is a small lesson, in this order (omit a part only when it would be empty):
     - **Statement:** the formal content, complete, in the callout.
     - **In plain words:** what it says, and the intuition behind it, including what each clause is for.
     - **Why it is there / what breaks without it:** the problem it solves, or the failure if a clause or condition were removed.
     - **Example:** the book's numbered example(s) for it, worked clearly, and/or an original one (a table, a trace, a tiny diagram).
     - **Grounding:** code or analogy, per the resolved style.
     Where the book offers its own informal reading or motivating remark, use it (attributed). Quality of explanation matters more than brevity: a reader who finishes a block should be able to apply the concept.
  7. **Examples stay attached.** The book's numbered examples for a definition (e.g. Examples 2.10.2 for Definition 2.10.1) are kept with it, with their concrete values, and explained: say what each example illustrates, and call out the subtle case (e.g. a variable in the projection set that is not in the domain).
  8. **Proofs.** Present the book's proof as a clear argument: state the induction hypothesis, one case per list item, and say why each case works, in plain words. It need not be word for word. If the book proves only some cases, say exactly what it leaves out and where it delegates ("the book treats only the (abst) case; the rest is in Barendregt 1992, Prop. 3.2.7"). If the book gives no proof ("see Exercise 2.16", "see reference X"), say so rather than inventing one. A proof or argument the article writes itself is labelled as commentary.
  9. **Attribution.** The Statement part reflects the book's claim. Anything that goes beyond the book (extra intuition that stretches it, code, analogies, extensions, connections to other systems) is marked *(commentary)* wherever it could be mistaken for the book's own content.
- **Tone:** rigorous, clear, intellectually engaging — never condescending, never hand-wavy. Precision is not sacrificed for accessibility.
- **Math notation:** LaTeX only (`$...$` inline, `$$...$$` for display), never inside backticks or code fences. Code fences are reserved exclusively for real, syntactically valid code. Inside callouts keep math inline where possible; display math inside a callout needs every line prefixed with `>`. Remember the MathJax constraint: one `\tag` per math block.
- **Diagrams:** never draw ASCII / box-drawing / text-art diagrams (no `┌─│└→` or `+---+` layouts, in code fences or elsewhere), whatever the word used for them ("diagram", "tiny diagram", "trace picture"). Use a ` ```mermaid ` block for flowcharts, state machines, sequences, dependency graphs and relationship maps, and inline `<svg>` for derivation trees, annotated or spatial layouts and side-by-side comparisons, following the Diagrams rules in `.article-style.md` (self-contained SVG, explicit hex colors, legible on light and dark themes). Where a table or a derivation rendered with LaTeX (`\cfrac`, `\dfrac`, array) says it better, use that. This rule is binding: style layers may refine it but cannot reinstate ASCII diagrams.
- **Obsidian conventions:** short YAML frontmatter (`title`, source book, chapter(s)/page range, `tags`); a wikilink back to the index (`[[book-guidelines|↩ Back to guidelines]]`) near the top or bottom; otherwise portable Markdown so the note still renders outside Obsidian.
- **Output path:** exactly `vaults/[book]/[Topic-Slug].md`, `[Topic-Slug]` in Title-Case-With-Hyphens, mirroring the guidelines' chapter title capitalization where applicable. For prompt-driven articles with no explicit topic title, derive the slug from the article's actual subject (2–8 words, ASCII, no punctuation), and avoid colliding with an existing file (Step 2.5). Never put the whole prompt in the filename.
- **Source fidelity:** every substantive claim attributed to the book must come from the pages re-read in Step 3. A prompt can steer, narrow, or ask for original illustrations (code, analogies), but cannot make the article assert that the book says something it doesn't. Material beyond the book (e.g. how Lean's kernel does it) is allowed when the prompt, style or goals ask for it, and must be marked as the author's commentary, not the book's.
- **Default audience** (used only if no style file overrides it): a technical reader with strong programming fundamentals but limited formal/abstract-math background.
- **Default grounding** (used only if no style file overrides it): pair every abstract construct with a concrete code example or analogy in Rust, Python, and Lean.
- **Output language:** resolved *only* from explicit style settings: `.article-style.md` layers (workbench and/or book-level) and, for a single article, an explicit language directive in `--prompt` (see 4e) — never inferred from anything else (not from the language of the prompt's own wording, the goals files, or the book). Default: **English**, unless one of those explicitly sets a different output language. Precedence: prompt > book-level style > workbench-level style. Regardless of prose language, the following always stay as-is, untranslated:
  - code inside fences (syntax is the target language's syntax, e.g. Rust/Python/Lean keywords stay Rust/Python/Lean keywords),
  - LaTeX math,
  - proper nouns, named theorems, and the book's own technical terminology on first use (give the prose-language explanation, then the source term in parentheses if the book's own language differs, e.g. "type inhabitation (*habitación de tipos*)" — never silently drop the term the reader would need to cross-reference back to the book or to other literature),
  - the text of formal blocks keeps the book's notation; if the output language differs from the book's, translate the wording faithfully, clause by clause, and keep the book's number and original term in the block title,
  - YAML frontmatter *keys* (`title`, `tags`, etc. stay as written in this skill) — frontmatter *values* follow the prose language.

**4b. Load and merge configurable layers, in this order (later layers augment, never override, earlier ones):**

1. Core contract (4a).
2. `vaults/.article-style.md`, if present — workbench-wide defaults (audience calibration, preferred grounding languages, output prose language, depth targets, recurring structural asks, house voice).
3. `vaults/[book]/.article-style.md`, if present — book-specific refinements on top of the workbench default (e.g. a denser book might call for more worked examples, or this one book's articles should be in a different prose language than the workbench norm — say, working through a Spanish-language source and wanting the article in Spanish too).
4. `vaults/.learning-goals.md`, if present — the user's standing learning objectives, independent of any one book.
5. `vaults/[book]/.learning-goals.md`, if present — how this particular book serves those objectives, or book-specific goals.

6. The `--prompt`, if given, applies last and most specifically — see 4e.

If a style file is absent at some level, just skip it — absence means "no augmentation at that level," not an error. If style layers conflict with each other (workbench vs. book-specific), the more specific (book-level) wins for that particular point, but only for genuinely conflicting instructions — non-conflicting guidance from both still applies. No style layer can lower the formal-statement fidelity rules in 4a: a depth or brevity setting shortens the article's *commentary*, never the formal blocks.

**4c. Apply learning goals as emphasis, not as new topics, and never as a language signal.** Learning-goals files describe the reader's broader project and should shape:
   - which of the topic's facets get the deepest treatment (the ones most load-bearing for the stated goals),
   - what the closing synthesis connects the topic to (Step 5.3),
   - which code-grounding languages or paradigms get priority when the goals name a specific target system (e.g. a reader building a Rust verifier should see Rust-side grounding treated as primary, not just one of three equally-weighted options).
   Learning goals should never cause the article to wander off-topic into content the source pages don't support — they steer emphasis and connections, not invention. **Learning-goals files may be written in any language, independent of the article's output language** (e.g. a Spanish-language `.learning-goals.md` paired with English-language articles is expected and fine) — only `.article-style.md`'s output-language setting decides what language the article is written in; the goals file's own language is never treated as a signal for that.

**4d. Resolve Focus Area tags, when present, as the finest-grained emphasis signal.** If `vaults/.learning-goals.md` defines a **Focus Areas** section (name, slug, description, conceptual-connections list per area) and `vaults/[book]/.learning-goals.md` tags this article's topic — or the top-level Topic-List entry it belongs to — against one or more of those areas:
   - Treat the tagged area(s)' "Required Conceptual Connections" and "Specific threads to keep surfacing" entries (from the workbench file) as the *first* things to check for relevance to this topic, ahead of scanning the full untagged list — they're the highest-probability payoff for this particular article.
   - When a topic carries two or more area tags (e.g. `type-theory` + `automated-reasoning` for a topic on unification), draw from every tagged area's connections rather than picking one — the tags are cumulative, not a forced single classification.
   - If the topic is untagged (either it wasn't tagged in `vaults/[book]/.learning-goals.md`, or that file predates the Focus Areas convention and has no tags at all), fall back to 4c's ungated behavior — scan the full workbench connections list as before. An untagged topic is not a signal to skip goal-connection work, only a signal there's no narrower shortlist to prioritize.
   - This never overrides 4c's "don't force the connection" rule — a tag says *where to look first*, not that every connection in that area's list must appear in the article.

**4e. Apply the prompt as the most specific layer, below only the core contract.** When `--prompt` is present it is the final, per-article layer on top of 4b's stack:
   - **Style/emphasis directives** in the prompt (audience, grounding languages and their priority, depth, number of worked examples, structure, diagram preferences, tone, output language, "skip the history", "code-first", etc.) win over `.article-style.md` and `.learning-goals.md` on genuinely conflicting points, and add to them otherwise. Non-conflicting file guidance still applies.
   - **Content directives** (questions to answer, angle, scope, comparisons) define what the article is *about*; the learning-goals emphasis of 4c/4d still decides which connections go in the closing synthesis, unless the prompt says to omit or change it.
   - **Core-contract limits.** The prompt cannot switch off LaTeX-only math, first-principles-before-symbols sequencing, source fidelity, the formal-statement fidelity rules, the Obsidian frontmatter/back-link, or the output path rules. If it asks for something that conflicts (e.g. "start with the formulas", "put math in code blocks", "keep it short, just summarise the definitions"), keep the contract, still honor the intent where possible (e.g. a very short formal statement up front *after* a one-paragraph motivation, or shorter commentary), and mention the deviation in Step 6.
   - **Unsupported asks.** If the prompt asks for something the source pages don't support (a result the book never proves, a comparison the book doesn't make), either provide it as clearly-labelled commentary or leave it out and say so in Step 6. Don't fabricate book content.
   - **Record it.** Add a short `prompt:` frontmatter key (one line, the prompt trimmed to ~200 characters) so the article's provenance and angle are recoverable. (Value follows the prose language; the key stays `prompt`.)

### Step 5 — Write the article

1. Follow the output path and Obsidian conventions from the core contract (4a).
2. **Content shape** (a guide, not a rigid template — let the topic and the resolved style dictate the exact structure):
   - Open with the first-principles motivation: what problem does this concept solve, why does the book introduce it here.
   - Break the topic into its constituent ideas. For each idea use this rhythm: *motivation in plain words* → *formal block(s) with the full statement* (definitions first, then examples, then lemmas/theorems, then proofs), each following the block anatomy of 4a.6 → *grounding* (per the resolved style). Don't front-load all the analogies at the end. Prefer a table, a diagram or a worked trace over a paragraph whenever it makes a definition easier to see.
   - Keep related items adjacent and in the book's order, so that cross-references such as "by Definition 2.4.5" can be followed in the note.
   - Preserve the book's notation faithfully throughout.
   - Close with a short synthesis: how this topic connects back into the book's larger structure (what depends on it, what it depends on), and — if learning-goals files are in effect — a brief note on how it bears on those goals (e.g. "this is the mechanism your elaborator's unifier will need for implicit-argument resolution"), naming the relevant Focus Area(s) by name where tags exist (per 4d) so the synthesis reads as goal-routed rather than generic. A Mermaid diagram (never ASCII art) is often effective for the structural half of this.
   - If a prompt was given, make sure every question it raised is answered somewhere recognisable (a section heading that echoes the question works well), and shape the structure around its angle in place of the generic "constituent ideas" breakdown when the two differ.
3. **Depth:** this is a genuine deep-dive, not a re-statement of the guidelines summary. Let the richness of the source material (Step 3), tempered by any depth guidance from the resolved style, determine the length naturally rather than targeting a fixed word count. Length pressure is relieved by shortening commentary and grounding, never by compressing or dropping formal blocks.
4. **Fidelity check (mandatory before saving).** Re-open the extraction and compare it with the draft:
   - For every Source Inventory entry in scope, confirm there is a block carrying the book's number and name, with every clause, symbol and side condition of the original present (wording may differ, content may not). Fix any entry that is missing, buried in a paragraph, or has lost a clause or condition.
   - For every block, confirm it is more than a copy: it has the plain-words explanation and an example, and a reader could understand it without the book.
   - For every symbol or defined term used inside a block, confirm its definition is present earlier in the article (dependency closure, Step 3.4).
   - For every numbered example the book attaches to a definition or lemma, confirm it is present with its concrete values.
   - For every proof, confirm it is present, or that its absence is stated with the book's reason or reference.
   - Confirm that content beyond the book's claim is marked as commentary.   

### Step 6 — Confirm

After writing the file, briefly tell the user:
- where it was saved, and which chapter(s)/pages it drew from,
- **a coverage report**: how many inventory items were in scope and how many appear as blocks, and a list of anything deliberately omitted with the reason (e.g. "Exercise 2.16 omitted: exercise, no solution in the book"). Silent omissions are not allowed,
- which style/goals config files were found and applied (e.g. "used vaults/.article-style.md and vaults/[book]/.learning-goals.md; no book-specific style file found"),
- anything notable about the source material (e.g. "this topic spans chapters 7 and 13", "the section had no worked examples in the book, so the code examples here are original illustrations of the same idea"),
- if `--prompt` was used: how you interpreted it (derived topic, angle, which directives were applied, which could not be honored and why, and whether it was checked against an existing article, with the cross-link if you wrote a complementary one),
- if applicable, the legacy-filename note from Step 1.

## Example

Input: `/book-topic-article thompson-type-theory "Theory of Expressions"`
- Prerequisite check: `vaults/thompson-type-theory/book-guidelines.md` exists → proceed.
- Guidelines match: Chapter 3, "Expressions and Definitional Equality" (pp. 13–22), Topic List section "2. Theory of Expressions."
- Source re-read: `sources/thompson-type-theory/book.pdf`, pages 13–22 (plus one page of margin on each side). Source Inventory built: every definition with its sub-clauses, every example, every lemma.
- Style resolution: `vaults/.article-style.md` found (sets Rust as primary grounding language); no book-specific style file; `vaults/.learning-goals.md` found (compiler/elaborator project, with a Focus Areas section); `vaults/thompson-type-theory/.learning-goals.md` found, tagging "Theory of Expressions" under `type-theory`.
- Output: `vaults/thompson-type-theory/Theory-of-Expressions.md` — opening with why a logic book needs a syntax layer before its logic, then each definition (application, abstraction, combination, selection, arities) as its own callout block with all clauses, followed by its unpacking and Rust-first grounding, and a closing synthesis that prioritizes `type-theory`'s conceptual connections (per 4d) — naming definitional equality and the elaborator's `isDefEq` explicitly — and noting this layer is the ancestor of the AST the reader's verifier will type-check. Step 6 reports "14 of 14 in-scope items covered, none omitted".

### Example of the required block style

Wrong, loses content (what this skill must not produce): "The domain of a context is its list of variables; a subcontext keeps some declarations and a projection restricts to a set of variables."

Also wrong, copies without teaching: the book's definition pasted verbatim with no explanation.

Right:

```
> [!definition] Definition 2.10.1 (Domain, subcontext, permutation, projection)
> Let $\Gamma\equiv x_1:\sigma_1,\dots,x_n:\sigma_n$ be a context (a list of declarations *subject : type*).
> 1. **Domain.** $\mathrm{dom}(\Gamma)=(x_1,\dots,x_n)$: the subjects only, types forgotten, order kept.
> 2. **Subcontext.** $\Gamma'\subseteq\Gamma$ if every declaration of $\Gamma'$ occurs in $\Gamma$, in the same order.
> 3. **Permutation.** $\Gamma'$ is a permutation of $\Gamma$ if both contain exactly the same declarations (order may differ).
> 4. **Projection.** $\Gamma\upharpoonright\Phi$ is the subcontext of $\Gamma$ with $\mathrm{dom}=\mathrm{dom}(\Gamma)\cap\Phi$: keep only declarations whose subject is in the variable set $\Phi$.
```

then: *In plain words* (a small table with a context, its dom, a subcontext, a permutation and a projection, so the four notions are seen side by side), *why it is there* (these are the vocabulary of the Free Variables and Thinning lemmas), the book's Examples 2.10.2 worked and explained (including the variable $u\in\Phi$ that is ignored because $u\notin\mathrm{dom}(\Gamma)$), and a few lines of Rust for `dom` and `project`.

### Example with a prompt

Input: `/book-topic-article nederpelt-geuvers-type-theory --prompt "How does type checking work once types are terms? Focus on the algorithm, Rust first, Lean second, skip the history. Complement the existing article on well-typedness."`
- No explicit topic: derive it from the prompt, "type checking in the dependent systems (λC/λD)", matched to Ch. 6 §6.3, Ch. 10 and Ch. 16 §16.2.
- Existing-article check finds an overlapping note on the simply typed case; the prompt says "complement", so write a new article with a distinct angle under a new slug and cross-link it.
- Style: prompt directives (Rust first, Lean second, no history) override the workbench grounding order where they conflict; the closing synthesis still uses the goals/Focus Area connections. The prompt's "focus on the algorithm" shapes the commentary and grounding; the book's definitions and rules for the algorithm are still reproduced in full blocks.
- Output: `vaults/nederpelt-geuvers-type-theory/Decidable-Type-Checking-in-LambdaC-and-LambdaD.md`, with a `prompt:` frontmatter line, and a Step 6 note listing how the prompt was interpreted and the coverage report.
