I have a toolset for turning academic PDF books into didactic Obsidian wikis, driven by a
pipeline of AI skills for Claude Code. This toolset features an special functionality for 
generating a **Learning Roadmap** (with the skill `/learning-roadmap`) that interprets
a document with my **Learning Goals** (topics/concepts that I want to learn, and the projects that I want to develop by applying such learned concepts)
And searches into Obsidian vaults for collecting relevant learning material according with my learning goals and organizes the topics and metainformation
of books in order to elaborate an study plan document.

## Descrition of the Problem

THE PROBLEM THAT I HAVE is that my learning goals are too broad and the list of books sources is massive (About 80 academic books with more than 50 topics each one).
So the processing effort for Claude Code is overwhelming and it often depletes my token quota. 

So I want to refine the toolset skills in order to narrow the process by focusing the learning plan into a determined main categories. As you can see in the
project file `.learning-goals.md`, I want to acquire knowledge required to design and implement a **Rust-based compiler for a dependent/refinement type language with automated formal verification capabilities**, that can check program correctness against logic-clause specifications (Hoare triples, or dependent-subtyping style contracts), with a custom automated theorem prover embedded in the toolchain. This file is meant to be included in the root folder of generated vaults (`vaults/.learning-goals.md`) as the base guideline for generating articles for all books in the project.

So I want to structure my learning goals into at least 3 important categories: 
- **Type Theory** : Lambda Calculus, Computability, Dependent Types, Indexed Families, inductive structures, abstract data types, recursion fixed point, symbolic automata.
- **Automated Reasoning**: Proof Theory, derivations, quantifiers,  constructive High Order Logic concepts, unification procedures, abductive reasoning, rewritting rules, Craig interpolation and focused sequent and linear logic. This area could have interesections with SMT and Type Theory.
- **Static Analysis**: Abstract Interpretation, Constraint Satisfaction Problems, Dataflow Analysis, Reachability and Model Checking with modulo theories (SMT).

Those three would be the main focus areas where the broad list of topics. The partition of those topics shouldn't being strict. Some topics could belong to many principal categories. I want to structure `.learning-goals.md` better for including categorization into focus areas.


## Summary of project artifacts

In summary, here is a brief description of the functionality of the skills involved in this project:
1. **`/book-guidelines`** (defined at file `book-guidelines.SKILL.md`) reads a source PDF and produces a compact study-guide index:
   a header (title/author/summary/intent), a two-level topic ontology for the whole book,
   and chapter-by-chapter summaries with key definitions and study questions.
2. **`/book-topic-article`** (defined at file `book-topic-article.SKILL.md`) turn topics from that index into
   full Obsidian articles — one focused deep-dive per topic, re-reading the source PDF directly for fidelity 
   (never generated from the compressed guidelines alone), written first-principles-before-symbols, and grounded 
   in code examples per a configurable style. This skill takes into account the base learing golas `vaults/.learning-goals.md`, as same
   as a particular learning goals template inside the books folder `vaults/[book]/.learning-goals.md` for narrowing the focused topics.
3. **`/learning-roadmap`**  (defined at file `learning-roadmap.SKILL.md`) Generates a file `vaults/learning-roadmap.md`, a single Obsidian note that synthesizes the user's standing learning goals from `vaults/.learning-goals.md` with the topic coverage already extracted into every `vaults/[book]/book-guidelines.md`, producing an ordered, prerequisite-aware curriculum: core topics, sequenced basic-to-advanced, each annotated with why it matters for the user's goals, which books/notes to study for it, key concepts, key questions, and optional external sources beyond what's on hand. This skill has an optional parameter invoked with `--focus` which is meant to focus the roadmap generation into determined emphasis.
   
The usual procedure for preparing the obsidian workspace is the following:
1. Drop a PDF at `sources/[book]/book.pdf`.
2. `/book-guidelines [book]` — generates `vaults/[book]/book-guidelines.md`.
3. Invocation of `/book-topic-article [book] "[topic]"` generates the deep-dive articles into each book folder, using the input learning goals templates (`.learning-goals.md`). 
4. At late stage, `/learning-roadmap` is invoked for creating (or regenerate) the learning study plan from all book notes already generated in `vaults` folder.
   
## Tasks to develop

1. I want to structure `.learning-goals.md` better for including categorization into focus areas: **Type Theory**, **Automated Reasoning**, **SAT/SMT/CSP**, **Static Analysis and Abstract Interpreration**.
2. Upgrade `book-guidelines.SKILL.md` for generating a suggested *learning goals* configuration into book folder (`vaults/[book]/.learning-goals.md`) if not present. Such file should contain the relevant main categories that are referenced in the base file at vault root file (`vaults/.learning-goals.md` if present) and the particular topics relating to the source book.
3. Upgrade `book-topic-article.SKILL.md` skill for emphsizing the article generation on its corresponding learning goals while having fidelity to the original book source subjects and the relevance according to the aggregated `vaults/[book]/.learning-goals.md`.
4. At last, the most important thing is improving `learning-roadmap.SKILL.md` for generating a learning plan according to the focused area, and generates a file named with the focus postfix as `vaults/learning-roadmap-[focus area].md`.
