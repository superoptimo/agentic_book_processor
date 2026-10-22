# Article Style — Workbench Defaults

> Place this file at `vaults/.article-style.md` to apply it to every book.
> Copy it into `vaults/[book]/.article-style.md` (trimmed to just what differs)
> to refine it for one specific book — book-level settings win only where they
> genuinely conflict with this file; everything else here still applies.
>
> This file *augments* `book-topic-article`'s fixed core contract (first-principles
> sequencing, LaTeX-only math, Obsidian conventions, output path). It cannot
> remove or override that contract — only add detail on top of it.

## Audience calibration

Strong software engineer. Comfortable with: type systems, compilers, operational
semantics, category-adjacent thinking from programming (functors-as-traits,
monads-as-patterns). Not comfortable with: dense math notation on its own,
proof-theoretic shorthand, unexplained Greek-letter soup. Every piece of
notation gets named in words the first time it appears, even if the book
doesn't bother to.

## Grounding languages (priority order)

1. **Rust** — primary. Whenever a construct can be shown as a `trait`, an
   `enum`, a typestate pattern, or a small compiler-pass snippet, do that first
   and in the most detail.
2. **Lean** — secondary, but promote to primary whenever the source material
   is itself type-theoretic, set-theoretic, or proof-theoretic (definitional
   equality, judgments, elaboration, unification). Lean's kernel is often the
   most literal translation of the book's formalism, so prefer showing that
   correspondence explicitly (e.g. "this is exactly `rfl`", "this is what
   `isDefEq` is doing").
3. **Python** — tertiary, used for quick illustrative sketches where Rust's
   ceremony would obscure the point (e.g. a five-line recursive-descent
   sketch), not for anything load-bearing.

If a topic doesn't naturally fit one of the three, say so rather than forcing
a strained analogy — a missing example is better than a misleading one.

## Depth & structure defaults

- Prefer worked examples over abstract description wherever the source
  material gives you the material for one.
- Include at least one "what breaks without this" paragraph per major
  subsection — the motivating failure mode, not just the motivating goal.
- End every article with a short **"Where this leads"** section: one or two
  sentences on what later material in the book depends on this topic.
- Diagrams: use Mermaid (fenced ` ```mermaid ` blocks) for flowcharts, state
  machines, sequence diagrams, and mind-map-shaped relationships — renders
  natively in Obsidian and GitHub. Use inline embedded SVG (raw
  `<svg>...</svg>` in the markdown body) for anything more structural or
  spatial than Mermaid's grammar handles well — derivation trees with custom
  layout, annotated diagrams, side-by-side comparisons. SVGs must be
  self-contained: explicit `fill`/`stroke` hex or named colors (no CSS
  variables — those only mean something in Claude.ai's chat Visualizer, not
  in Obsidian), and colors picked to stay legible on both light and dark
  vault themes (favor mid-gray strokes/lines over pure black or white).
  ASCII/text diagrams are a fallback for quick, genuinely simple call-outs
  only — not the default for real structural diagrams anymore.

## Voice

Direct, precise, a little conversational. Prefer short declarative sentences
over long qualifier-stacked ones. It's fine to editorialize briefly on why a
formalism is elegant or annoying — this is a study guide, not a textbook
excerpt.

## GENERAL RESPONSE GUIDELINES & FORMATTING RULES

### Mathematical Notation & LaTeX
- ALWAYS use standard LaTeX for mathematical notation — symbols, formulas, and named theorems alike.
- Use single dollar signs (`$...$`) for inline math and double dollar signs (`$$ ... $$`) on their own line for standalone/display equations.
- NEVER place LaTeX formulas or mathematical symbols inside code blocks or inline code spans (`` `...` ``). Backticks are reserved exclusively for executable or pseudo-code constructs (e.g. function names, code snippets) — not for math, even short symbols like a single variable.
  - Wrong: `` `A ⇒ B` `` or a fenced block containing `∀x. P(x)`
  - Right: `$A \Rightarrow B$` inline, or a `$$...$$` block for a standalone rule/derivation

### MathJax Compatibility (Obsidian)
All math must render in Obsidian's MathJax (TeX input with the standard base, AMS, and `\newcommand`-free subset). Write only commands that MathJax supports out of the box.

**Never use:**
- LaTeX packages or package-specific commands: `bussproofs` (`\AxiomC`, `\UnaryInfC`, `\BinaryInfC`, ...), `mathpartir` (`\inferrule`, `\mathpar`), `prooftrees`, `tikz`, `tikz-cd`, `braket`, `physics`, `cancel`-style extras unless confirmed supported.
- Text-mode and document commands: `\textsc`, `\textsf`, `\emph`, `\textbf` inside math, `\usepackage`, `\begin{document}`, `\begin{tabular}`, `\begin{theorem}`, `\label`, `\ref`, `\cite`.
- Custom macros: no `\newcommand`, `\renewcommand`, `\def`, or `\DeclareMathOperator`. Always write every symbol out in full, even if it is repeated many times.
- `\bm` and `\mathscr`. Use `\boldsymbol{}` or `\mathbf{}`, and `\mathcal{}`.

**Use these replacements:**
- Small caps or rule names: `\mathsf{Var}`, `\mathrm{Var}`, or `\text{Var}` (plain text only, no nested macros).
- Operator names: `\operatorname{name}`.
- Multi-line or aligned equations: `\begin{aligned} ... \end{aligned}` inside `$$ ... $$`. Do not use the bare `align`, `equation`, or `eqnarray` environments.
- Tables of math: Markdown tables, or `\begin{array}{cc} ... \end{array}` inside math. Never `tabular`.
- Piecewise definitions: `\begin{cases} ... \end{cases}`.

**Inference rules and derivation trees** (no proof-tree packages): build them with nested `\dfrac`, separating premises with `\quad`, and put the rule name in parentheses on the right.

$$\dfrac{\Gamma \vdash M : A \to B \quad \Gamma \vdash N : A}{\Gamma \vdash M\,N : B}\ (\mathsf{App})$$

For a multi-step tree, nest one `\dfrac` inside the numerator of the next. For a very wide tree, split it into several named sub-derivations instead of forcing one line.

**Markdown/Obsidian pitfalls to avoid:**
- Do not put a bare `|` inside a Markdown table cell that contains math. Use `\mid` or `\vert` (`\Vert` for a double bar) so the table does not break.
- Do not leave a space just inside the `$` delimiters: write `$x$`, not `$ x $`. Do not put `$` next to a digit or word character in a way that could be read as currency.
- Put `$$ ... $$` blocks on their own lines, with a blank line before and after.
- Do not use Unicode math symbols (⇒, ∀, ⊢, λ) in running text; write them in LaTeX (`$\Rightarrow$`, `$\forall$`, `$\vdash$`, `$\lambda$`).
- Write type annotations with braces around the colon: `$\lambda x{:}A.\,M$`.

**If a construct seems to need an unsupported package:** restructure it with `array`, `aligned`, or nested `\dfrac`. Do not fall back to a code block, an image, or raw ASCII art for math.
