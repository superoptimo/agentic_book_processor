# Learning Goals — Workbench Defaults

> `book-topic-article` uses this file to decide emphasis and
> closing synthesis — never to invent content the source pages don't support.

## Standing project

I'm building an accelerated, self-directed learning system for advanced
Type Theory, Abstract Interpretation, and Formal Proofs, aimed at two
concrete engineering targets:

1. **A Rust compiler/verifier** that can check program correctness against
   logic-clause specifications (Hoare triples, or dependent-subtyping style
   contracts), with a custom automated theorem prover embedded in the
   toolchain.
2. **A meta-programming elaborator** that resolves implicit arguments via
   metavariable unification — in the spirit of Miller's pattern unification —
   using bidirectional typing, modeled on how Lean's elaborator and kernel
   unifier actually work.

## How articles should use this

- **Weight toward mechanism, not just theory.** When a topic has both a
  "what it means" reading and a "how you'd implement/check it" reading,
  give real space to the second — that's the part that transfers to the
  compiler and elaborator projects.
- **Flag load-bearing topics explicitly.** If a topic is a direct
  prerequisite for one of the two targets above (e.g. definitional equality
  → the elaborator's `isDefEq`; substitution and context validity → Hoare-triple
  soundness), say so in the closing synthesis, not just implicitly through
  the Rust/Lean grounding.
- **Prioritize Rust grounding for anything checker/verifier-shaped**
  (typing rules, judgment forms, proof search, substitution) — this is the
  material that will eventually become actual Rust code.
- **Prioritize Lean grounding for anything elaboration/unification-shaped**
  (metavariables, implicit arguments, definitional vs. propositional
  equality, bidirectional inference vs. checking) — treat Lean's own
  elaborator/kernel behavior as source material worth citing by name when
  the book's formalism maps onto it.
- **Don't force the connection.** Plenty of topics (e.g. pure syntax,
  historical framing, notation conventions) don't bear directly on either
  target — for those, just skip the "how this feeds the project" note rather
  than manufacturing a strained one.

## Specific threads to keep surfacing across books

- Judgment forms and typing rules, as the shared ancestor of both "a type
  checker" and "a proof checker" — I want the connection between these two
  framings made explicit whenever a book supports it.
- Substitution, context management, and variable capture — the recurring
  plumbing under both Hoare-logic soundness proofs and elaboration.
- Unification: first-order vs. higher-order, pattern unification (Miller
  patterns) as the tractable fragment, and where a book's own equality/
  definitional-equality machinery is doing unification's job without naming
  it as such.
- Bidirectional typing (inference vs. checking modes) wherever a book's
  presentation of typing rules can be read that way, even if the book itself
  doesn't use that framing.

## Non-goals (to keep articles from over-reaching)

- Not currently building a homotopy type theory library — HoTT-adjacent
  material can be treated as background/context, not a primary target.
- Not trying to reproduce Lean's full elaborator — the goal is understanding
  the core unification/elaboration mechanism well enough to build a much
  smaller, purpose-built one, so articles should favor the minimal-mechanism
  explanation over exhaustive coverage of Lean's actual implementation
  complexity.
