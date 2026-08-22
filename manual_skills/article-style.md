# Article Style — Workbench Defaults

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
