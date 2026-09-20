# Learning Goals — Workbench Defaults

> Place this file at `vaults/.learning-goals.md` to apply it to every book.
> Add `vaults/[book]/.learning-goals.md` for a book-specific angle on top of
> this (e.g. "this particular book is mainly here for Part 3, the rest is
> background"). `book-topic-article` uses this file to decide emphasis and
> closing synthesis — never to invent content the source pages don't support.

## Standing project

I'm building an accelerated, self-directed learning system for advanced
Type Theory, Abstract Interpretation, and Formal Proofs.

Help me to acquire the theoretical and engineering knowledge required to
design and implement a **Rust-based compiler for a dependent/refinement type language with automated formal verification capabilities**, 
that can check program correctness against logic-clause specifications (Hoare triples, or dependent-subtyping style contracts), with a custom automated theorem prover embedded in the toolchain.

The compiler's functionality goals are:
- Constraint-based inference for refinement types.
- Reasoning about First and Second-order logic grounded in dependent type theory.
- Abstract interpretation for automated invariant generation (Hoare contracts, Horn clauses, requires/ensures conditions).
- This compiler will implement **A meta-programming elaborator** that resolves implicit arguments via metavariable unification — in the spirit of   Miller's pattern unification — using bidirectional typing, modeled on how Lean's elaborator and kernel unifier actually work.
- This compiler will include a Constraint Satisfaction Programming (CSP) kernel for searching counterfacts that could break the type invariants of the analized programs. This CSP will support the Abstract Interpretation process for proving absence of bugs by over-approximating program semantics, while CSP efficiently proves the presence of bugs by searching for concrete, satisfying assignments (counterexamples/counterfacts). This should be implement domain/lattice propagation and handling integrer and non-linear equations, but also abstract data structures as complex domains (represented like automata grammars DFA). 

# Required Conceptual Connections

Whenever relevant, explicitly connect the topic to:

* judgments
* contexts
* dependent types
* definitional equality
* Π-types
* Σ-types
* inductive types
* refinement types
* metavariables
* unification
* constraint generation
* constraint solving
* bidirectional typing
* elaboration
* operational semantics
* Hoare logic
* weakest preconditions
* symbolic execution
* abstract interpretation
* reachability analysis
* invariant generation
* SAT
* SMT
* CHCs
* CEGAR
* proof certificates
* proof reconstruction
* trusted kernels
* Constraint Satisfaction Problems
* Structural tractability
* Monadic Second-Order Logic
* Algebraic graph theory
   
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

# Depth Requirements

Assume the learner has:

* strong programming experience
* strong Rust knowledge
* significant familiarity with compilers
* growing knowledge of dependent type theory
* familiarity with Lean-like theorem proving
* interest in proof theory and logic programming

Do NOT spend excessive space explaining elementary programming concepts.

Instead, spend depth on:

* formal definitions
* inference rules
* semantic distinctions
* algorithmic mechanisms
* invariants
* representations
* complexity
* implementation tradeoffs
* soundness
* completeness
* trusted computing base
* proof-producing architecture

When introducing mathematical machinery, explain it from first principles before using advanced terminology.

  
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
- Proof search. Clause simplification and unification of terms.
- Abstract Interpretation, Symbolic Execution and Constraint Programming applied
  on satisfability of verification conditions for evaluating program guards, reachability analysis and path coverage.
- Satisfability Modulo Theories, Reachability, Linear and Non-Linear constraint programming.
- Galois Connection, abstract lattices and domain propagation methods.
- Abductive Reasoning, Craig Interpolation and Clause Generation for refinement of types and verification conditions.
  
