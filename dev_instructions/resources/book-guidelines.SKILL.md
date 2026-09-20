---
name: book-guidelines
description: Generates a structured "guidelines" markdown study-guide for a book, from a fixed sources/[book]/book.pdf input to a fixed vaults/[book]/book-guidelines.md output. Manual invocation only — invoke explicitly with /book-guidelines, never automatically.
disable-model-invocation: true
argument-hint: "[book-folder-name]"
---

# Book Guidelines Generator

Turns a source book file into a single, richly structured Markdown "book-guidelines" document: a header, a nested ontological topic index, and a chapter-by-chapter breakdown with key definitions and study questions.

**Invocation:** this skill only runs when explicitly called with `/book-guidelines`. It must never be triggered automatically by Claude inferring intent from conversation — always wait for the explicit command.

This skill assumes (and enforces) a fixed project layout:

```
sources/[book]/book.pdf   <- input: the book always lives here, always named book.pdf
vaults/[book]/            <- output: the generated guideline markdown goes here
```

`[book]` is a folder name, one per book (e.g. `sources/thompson-type-theory/book.pdf`).

## Workflow

### Step 1 — Resolve the book folder

1. Take `[book]` from `$ARGUMENTS`. If no argument was given, ask the user which folder under `sources/` to process (list the available ones as candidates) — do not guess.
2. The input file is always `sources/[book]/book.pdf`. Confirm it exists at that exact path.
3. If `sources/[book]/book.pdf` doesn't exist, check for a close match (typos, different casing on `[book]`) before telling the user it's missing. Never invent or fetch a book from the web to fill the gap, and never process a differently-named file in that folder without confirming with the user first — the convention is strictly `book.pdf`.

### Step 2 — Extract the content

The source is always a PDF. Extract its text. If the PDF is scanned/image-based, OCR may be required; flag this to the user if extraction yields little to no text rather than silently producing a thin guide.

For long books, don't try to hold the entire raw text in context at once if it's very large — read it chapter-by-chapter (using table-of-contents / heading markers to find chapter boundaries) rather than truncating silently. If the book has no clear chapter/section markup, infer reasonable divisions from the text (major headings, part breaks, numbered sections) and note that the chapter boundaries are inferred.

### Step 3 — Analyze

While reading, track for each chapter (or, for unstructured books, each major part):
- A one-paragraph summary of what the chapter covers and why it's there.
- Section-by-section (or subsection-by-subsection) important **definitions and concepts** — named terms, formal definitions, key distinctions the author draws. Prefer the author's own terminology; keep definitions concise (one line to a few lines each).
- 1–3 **key questions** per chapter that a critical reader should be able to answer after reading it — these should probe the chapter's central claims or trickiest distinctions, not trivia.

Also track, across the whole book:
- The book's title, author(s), and — if stated or inferable from the preface/intro — the author's own stated purpose/intent for writing it.
- Every named topic/subtopic in the book, so it can be organized into a nested outline (see template below). Group related subtopics under their parent topic; mirror the book's own part/chapter/section structure where it's sensible, but reorganize into a cleaner ontology where the book's structure is more historical/narrative than topical.

### Step 4 — Write the output file

Create the file at exactly:

```
vaults/[book]/book-guidelines.md
```

- The filename is always `book-guidelines.md` — no book title, no other variation. The book folder name (`[book]`) is what disambiguates one book's guide from another's, not the filename.
- Create the `vaults/[book]/` folder if it doesn't exist yet.

Use exactly this document structure:

```markdown
# <Book Title> — Guidelines

## Header

**Title:** ...
**Author(s):** ...
**Publication:** ...

**Brief Summary:**
[2-5 sentences: what the book covers and its central thesis/organizing idea]

**Intent of the Author:**
[1-3 sentences: why the author wrote it / what they want the reader to come away with]

---

## Topic List

1. **<Broad topic, phrased as a generalized category>**
   - <Subtopic, phrased as a plain, title-cased sentence/fragment — no punctuation>
   - <Subtopic>
2. **<Broad topic>**
   - <Subtopic>
   - ...

---

## Chapter Summaries

### Chapter N: <Chapter Title> (pp. X–Y)

**Summary:** [1-2 sentences]

**Key Definitions & Concepts by Section:**
- **N.1 <Section Name>** — term (definition), term (definition), ...
- **N.2 <Section Name>** — ...

**Key Questions:**
1. ...
2. ...

---
[repeat per chapter]
```

Notes on filling the template:
- The **Topic List** is a single unified ontology for the *whole book*, not one list per chapter — group by subject matter, not by chapter number. See **Topic List Style** below for exact formatting rules.
- The **Chapter Summaries** section is the one place that stays chapter-ordered, matching the book's own table of contents.
- Preserve important formal notation (symbols, formulas) exactly as the book uses it — don't paraphrase notation away. See **Mathematical Notation** below for how to format it. (This applies to Chapter Summaries; the Topic List itself stays in plain sentences per the style rules below — LaTeX there only if a symbol *is* the concept and can't be named in words, e.g. `$\lambda$-calculus`.)
- If a chapter has no natural subsections, just give a flat bullet list of definitions/concepts instead of the "by section" breakdown.
- Skip empty subsections rather than padding with "N/A".

**Topic List Style:**
- **Exactly two levels, no deeper.** Numbered top-level topics (`1.`, `2.`, ...), each a broad category in **bold**. Each gets a flat list of bulleted subtopics indented one level underneath — never a third level, never sub-bullets under a subtopic.
- **Top-level topics are generalized categories**, not chapter titles or section titles — the name a reader would search for if they wanted "everything about X" (e.g. "The Curry–Howard Isomorphism", "Sense and Denotation (Frege's Dichotomy)").
- **Subtopics are plain sentences or sentence fragments that name what the concept *is*, not what the book *says about* it.** Convert the source material's own longer, punctuation-heavy headings/claims into short, plain, title-cased phrases:
  - Strip trailing parentheticals, dates, colons, and semicolons that just add commentary or attribution: `Deductions as trees; hypotheses "alive" vs "dead" (discharged)` → `Deductions as trees`
  - Strip named attributions/dates that aren't essential to recognizing the concept: `Gentzen's theorem (1934): the cut rule is eliminable` → `Gentzen's theorem` (keep the named result if that's how the book/field refers to it, drop the year and the restated claim)
  - Collapse compound, multi-clause headings into one short descriptive sentence rather than preserving every clause: `Resolution: restricting cut to substitution instances of axioms; Horn clauses and PROLOG as disciplined cut` → `Resolution by restricting cuts to substitution instances of Horn clauses`
  - No colons, semicolons, or parenthetical asides inside a subtopic line. If the source heading has multiple ideas glued together with `;` or `:`, either merge them into one plain sentence (preferred) or split into two separate subtopic bullets if they're genuinely distinct concepts.
  - Keep proper nouns, named theorems, and essential mathematical notation (per the Mathematical Notation rules) — simplification means cutting *punctuation and restated claims*, not cutting the actual concept name.
- **Consistency matters more than exhaustiveness.** Every subtopic line should read the same way — a short, plain, declarative phrase — not a mix of full sentences, fragments, and notation-heavy strings. When in doubt, favor the shorter, more general phrasing.

**Mathematical Notation & LaTeX:**
- ALWAYS use standard LaTeX for mathematical notation — symbols, formulas, and named theorems alike.
- Use single dollar signs (`$...$`) for inline math and double dollar signs (`$$ ... $$`) on their own line for standalone/display equations.
- NEVER place LaTeX formulas or mathematical symbols inside code blocks or inline code spans (`` `...` ``). Backticks are reserved exclusively for executable or pseudo-code constructs (e.g. function names, code snippets) — not for math, even short symbols like a single variable.
  - Wrong: `` `A ⇒ B` `` or a fenced block containing `∀x. P(x)`
  - Right: `$A \Rightarrow B$` inline, or a `$$...$$` block for a standalone rule/derivation

### Step 5 — Confirm

After writing the file, briefly tell the user where it was saved (`vaults/[book]/book-guidelines.md`) and flag anything notable from extraction (e.g. "chapter boundaries were inferred — the source PDF had no heading markup" or "pages 40-52 were image scans and may be under-represented").

## Example

Input: `sources/thompson-type-theory/book.pdf`
Output: `vaults/thompson-type-theory/book-guidelines.md`

The output follows the template above: a Header naming Simon Thompson and summarizing the Curry-Howard framing, a two-level Topic List with broad numbered categories like "The Curry–Howard Isomorphism" or "Sense and Denotation (Frege's Dichotomy)" (rather than just "Chapter 4", "Chapter 5", "Chapter 7") and short plain-sentence subtopics underneath each, and nine Chapter Summaries each with per-section definitions and 2-3 key questions.

```markdown
## Topic List

1. **Sense and Denotation (Frege's Dichotomy)**
   - Sense vs. denotation
   - The Tarskian tradition
   - The Heyting tradition
2. **The Curry–Howard Isomorphism**
   - Simply typed $\lambda$-calculus
   - Denotational vs. operational significance of a type
```
