# Learning Goals — Workbench Defaults

> Place this file at `vaults/.learning-goals.md` to apply it to every book.
> Add `vaults/[book]/.learning-goals.md` for a book-specific angle on top of
> this (e.g. "this particular book is mainly here for Part 3, the rest is
> background"). `book-topic-article` uses this file to decide emphasis and
> closing synthesis — never to invent content the source pages don't support.
> `book-guidelines` uses the **Focus Areas** below as the fixed category set
> when it drafts a book-specific `.learning-goals.md`. `learning-roadmap`
> uses them as the roadmap's top-level organizing structure, and as the
> valid values for `--focus`.

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
- This compiler will implement **A meta-programming elaborator** that resolves implicit arguments via metavariable unification — in the spirit of Miller's pattern unification — using bidirectional typing, modeled on how Lean's elaborator and kernel unifier actually work.
- This compiler will include a Constraint Satisfaction Programming (CSP) kernel for searching counterfacts that could break the type invariants of the analized programs. This CSP will support the Abstract Interpretation process for proving absence of bugs by over-approximating program semantics, while CSP efficiently proves the presence of bugs by searching for concrete, satisfying assignments (counterexamples/counterfacts). This should be implement domain/lattice propagation and handling integrer and non-linear equations, but also abstract data structures as complex domains (represented like automata grammars DFA).

---

## Focus Areas

This is the **fixed category set** for the whole pipeline. Every topic
extracted from a book — in a Topic List, a roadmap entry, or a per-book
`.learning-goals.md` — should be tagged against one or more of these four
areas. The partition is **not strict**: a topic that genuinely sits at an
intersection (e.g. unification, which is both a Type Theory mechanism and
an Automated Reasoning procedure) should carry every area it belongs to,
not be forced into a single bucket.

Each area has a **slug** — this is the exact string used for
`learning-roadmap`'s `--focus` argument and for the resulting
`vaults/learning-roadmap-[slug].md` filename.

### 1. Type Theory — `type-theory`

Lambda Calculus, Computability, Dependent Types, Indexed Families,
inductive structures, abstract data types, recursion and fixed points,
symbolic automata.

**Conceptual connections:** judgments, contexts, dependent types,
definitional equality, $\Pi$-types, $\Sigma$-types, inductive types,
refinement types, metavariables, bidirectional typing, elaboration,
operational semantics.

**Downstream payoff:** the elaborator's term/type representation, the
kernel's `isDefEq`, and the refinement-type surface language itself.

### 2. Automated Reasoning — `automated-reasoning`

Proof Theory, derivations, quantifiers, constructive Higher-Order Logic,
unification procedures, abductive reasoning, rewriting rules, Craig
interpolation, focused sequent calculus, linear logic. Intersects heavily
with Type Theory (unification, definitional equality) and with SAT/SMT/CSP
(clause generation, resolution).

**Conceptual connections:** unification, constraint generation, Hoare
logic, weakest preconditions, proof certificates, proof reconstruction,
trusted kernels, Monadic Second-Order Logic.

**Downstream payoff:** the metavariable unifier (Miller's pattern
unification fragment), proof-term reconstruction feeding the trusted
kernel, and the theorem prover's clause/resolution engine.

### 3. SAT/SMT/CSP — `sat-smt-csp`

Satisfiability (SAT), Satisfiability Modulo Theories (SMT), Constraint
Satisfaction Problems (CSP), constraint/domain propagation, CEGAR
(counterexample-guided abstraction refinement), integer and non-linear
constraint solving, automata/DFA-based domains for abstract data
structures.

**Conceptual connections:** SAT, SMT, CHCs (Constrained Horn Clauses),
CEGAR, symbolic execution, Structural Tractability, Algebraic Graph
Theory.

**Downstream payoff:** the CSP kernel that searches for concrete
counterexamples (proving bug *presence*) alongside the abstract
interpreter's over-approximation (proving bug *absence*), and the
solver backend feeding verification-condition discharge.

### 4. Static Analysis & Abstract Interpretation — `static-analysis`

Abstract Interpretation, Dataflow Analysis, Reachability Analysis, Model
Checking modulo theories, Galois connections, abstract lattices, domain
propagation methods.

**Conceptual connections:** abstract interpretation, reachability
analysis, invariant generation, symbolic execution, Galois Connection,
abstract lattices, domain propagation.

**Downstream payoff:** automated Hoare-contract / Horn-clause invariant
generation, and the soundness argument for the compiler's
over-approximating analysis passes.

---

# Required Conceptual Connections

Whenever relevant, explicitly connect the topic to the list below. Each
entry is tagged with the Focus Area(s) it primarily belongs to, so
`book-topic-article` and `learning-roadmap` can use the tag as a routing
hint — but a topic should still be connected to any entry that's
genuinely relevant regardless of tag.

* judgments — `type-theory`
* contexts — `type-theory`
* dependent types — `type-theory`
* definitional equality — `type-theory`
* Π-types — `type-theory`
* Σ-types — `type-theory`
* inductive types — `type-theory`
* refinement types — `type-theory`
* metavariables — `type-theory`, `automated-reasoning`
* unification — `type-theory`, `automated-reasoning`
* constraint generation — `automated-reasoning`, `sat-smt-csp`
* constraint solving — `sat-smt-csp`
* bidirectional typing — `type-theory`
* elaboration — `type-theory`
* operational semantics — `type-theory`
* Hoare logic — `automated-reasoning`, `static-analysis`
* weakest preconditions — `automated-reasoning`, `static-analysis`
* symbolic execution — `sat-smt-csp`, `static-analysis`
* abstract interpretation — `static-analysis`
* reachability analysis — `static-analysis`, `sat-smt-csp`
* invariant generation — `static-analysis`
* SAT — `sat-smt-csp`
* SMT — `sat-smt-csp`
* CHCs — `sat-smt-csp`, `static-analysis`
* CEGAR — `sat-smt-csp`, `static-analysis`
* proof certificates — `automated-reasoning`
* proof reconstruction — `automated-reasoning`
* trusted kernels — `automated-reasoning`, `type-theory`
* Constraint Satisfaction Problems — `sat-smt-csp`
* Structural tractability — `sat-smt-csp`
* Monadic Second-Order Logic — `automated-reasoning`
* Algebraic graph theory — `sat-smt-csp`

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
- **Tag by Focus Area, don't silo by it.** A topic tagged `type-theory` and
  `automated-reasoning` (e.g. unification) should draw on both areas'
  conceptual-connection lists, not just the first one listed.

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

Each thread below is tagged with its primary Focus Area(s).

- Judgment forms and typing rules, as the shared ancestor of both "a type
  checker" and "a proof checker" — I want the connection between these two
  framings made explicit whenever a book supports it. — `type-theory`,
  `automated-reasoning`
- Substitution, context management, and variable capture — the recurring
  plumbing under both Hoare-logic soundness proofs and elaboration. —
  `type-theory`, `automated-reasoning`
- Unification: first-order vs. higher-order, pattern unification (Miller
  patterns) as the tractable fragment, and where a book's own equality/
  definitional-equality machinery is doing unification's job without naming
  it as such. — `type-theory`, `automated-reasoning`
- Bidirectional typing (inference vs. checking modes) wherever a book's
  presentation of typing rules can be read that way, even if the book itself
  doesn't use that framing. — `type-theory`
- Proof search. Clause simplification and unification of terms. —
  `automated-reasoning`
- Abstract Interpretation, Symbolic Execution and Constraint Programming applied
  on satisfability of verification conditions for evaluating program guards, reachability analysis and path coverage. —
  `static-analysis`, `sat-smt-csp`
- Satisfability Modulo Theories, Reachability, Linear and Non-Linear constraint programming. —
  `sat-smt-csp`
- Galois Connection, abstract lattices and domain propagation methods. —
  `static-analysis`
- Abductive Reasoning, Craig Interpolation and Clause Generation for refinement of types and verification conditions. —
  `automated-reasoning`, `sat-smt-csp`
