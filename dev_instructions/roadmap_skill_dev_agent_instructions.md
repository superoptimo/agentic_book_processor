Create an skill for generating a **Learning Roadmap** as an Obsidian note. 

This skill is triggered by command exclusively, by invoking `\learning-roadmap`

This skill operates within the project `vaults` folder, where there are these elements:
1. Markdown files for the learning goals and article style: `vaults/.article-style.md`, `vaults/.learning-goals.md`
2. A list of subfolders, each one relates to an obsidian book that is based on an original academic book that is located in the folder `./sources`as a pdf file. Each obsidian books is composed by the following notes:
    - The corresponding `book-guidelines.md`note that contains the meta information of the original book, its ontological list of topics and an structured summary of each chapter and section with key definitions and relevant questions.
    - A group of obsidian notes generated as learning material that summarizes and exposes ground concepts based on each topic related to the book.
    - Optionally, there is an Index.md file that only contains links to the notes in the book. (this file is ignored).
    
The idea is generating the roadmap document at the root of the `vaults` folder. Which is called `learning-roadmpap.md`. For elaborating the purpoted  learning roadmap, the skill tells the agent to follow these instructions: 
- Read and analize carefully the learning goals of the user, whose are expressed in the `vaults/.learning-goals.md`. Then suggest (from your background academic knowledge) a preliminar roadmap of learning topics that allow the user to understand the fundamentals for developing skills needed for developing his goal projects (F.E. a compiler, perhaps a proof assistant etc.). 
- Analize the books in the `vaults` folder (each subfolder) that correspond to the related obsidian notes and the book-guidelines. Extract from teach `book-guidelines.md` the book meta-information and the list of topics and important concepts from each chapter/section summary. Organize such list of extracted concepts into the roadmap structure categorically. 
- Then re-arrange the roadmap structure with the core topics and the associated book references (extracted from vaults folders), and for each topic in the roadmap anotate the suggested sources to review (books and notes), key concets. 
- Present the roadmap in a comprehensible list structure, in order of relevance and preparation: list first the basic knowledge of topics, and then the advanced and complex concepts that are based on the basic fundamentals. Each roadmap core topic details the pre-requisites and signales the expected learning goals and elements, suggesting how they would be useful  for the learning goal of the user. Then the suggested sources to read and the key definitions to analize. Generate a couple of key questions (they may be taken from book-guideliness summaries). And if possible, suggest additional book and research sources that are not included (if your knowledge base suggest such thing).

This is an example of Roadmap topic with its meta information:
```
## 1. Proposition as Types (Core Topic)
#### Pre-requisites:
Set theory, boolean logic, natural deduction, derivations.

#### Why this topic is important.

... explain how this topic is useful for the user developing goals and learning process. 
... Also list the upcoming concepts and topics that require this knowledge.

#### Sources to Study
1. Book 1.
    - Note A.
    - Note B, section 1
2. Book 2.
....
....

#### Additional external sources (if apply)
... Suggest other academic references to estudy and complement the knwoledge

#### Key Concepts and defintions 
1. Key concept 1,
 - Definition.
2. Key concept 2

#### Relevant Questions
1. question1 ?
2. question2 ?
3. question1 ?

```

Present the roadmap with a brief introduction and motivation.
