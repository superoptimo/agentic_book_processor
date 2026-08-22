# Manual Prompts for generating Obsidian articles from books

These instruction scripts tells to a *free* web LLM how to analize a book ontologically, and 
generates learning-oriented articles from topics extracted from that book, in a similar fashion
as the agentic skills that are used in specialized code AI assistants (like Claude Code) for example 
the one specified in`book-topic-article/SKILL.md` from this repository.

## Usage Instructions

These non-agentic prompts are meant to be attached as files in web chatbot projects. The core idea
is to configure a project in ChatGPT or [Qwen chat](https://chat.qwen.ai/) for processing one book exclusively.

The process is divided in 2 stages: at first, a book guidelines needs to be generated from the book, and then
a project is configured with 4 scripts and the book file for geenerating individual articles based on topics.

### Stage 1: Generate Book Guideliness.

- In a new chat session, attach the book pdf and paste the instructions from [book-guidelines-prompt.md](book-guidelines-prompt.md). 
- Then copy the generated markdown text and save it as a file called `book-guidelines.md`. 

### Stage 2: Configure the project

1. Create a new project with the following instructions:
> Generate articles using book-topic-article.SKILL and book.pdf
2. Rename the book exactly as `book.pdf` and upload it to the project file resources.
3. Upload these script files for enabling the skill `book-topic-article` in the custom operation on the project:
    * [book-topic-article.SKILL.md](book-topic-article.SKILL.md).
    * [article-style.md](article-style.md).
    * [learning-goals.md](learning-goals.md).
    * The generated guideliness that you've saved in the previous stage, as `book-guidelines.md`.

### Generating articles

By using the skill `book-topic-article`, you could generate a learning article from the book in the configured project, by prompting this command
in a new chat session (F.E. *My Special Topic*, as the topic should be passed in quotes): 
>/book-topic-article "My Special Topic"

---

## Plus Tool: The Socratic Tutor

In this folder is included a socratic tutor skill ([socratic_tutor.SKILL](socratic_tutor.SKILL.md)) which can be used for configuring a NotebookLM or ChatGPT project for studying subjects from a group of books and learning resources. Just install it on the instructions at project settings.

This socratic tutor has 3 modes of operation:

### Mode 1: Freestyling Dialogue (Default Mode)

Whenever the user asks general questions, requests explanations, or seeks guidance across computer science, functional programming, logic, and mathematics.

### Mode 2: Socratic Exploration (Triggered by command)

Activated by the following command `"I want to study about [Topic]"`. In this mode the chatbot helps you to learn in a socratic style by guiding you in the mental structure about a fundamental topic. The chatbot address the user's core inquiry, then conclude your response with 1-2 targeted, penetrating follow-up questions to force them to refine their mental model.


### Mode 3: Mental Model Checkpoint (Triggered by command)

Activated by the following command `"Evaluate me on [Topic]"`. In this mode, the chatbot creates a questionary with 10 challenging questions on a topic. Generates exactly 10 high-friction diagnostic questions structured across three distinct tiers:

* Questions 1–4: Conceptual Soundness (Distinguishing adjacent concepts, identifying hidden assumptions, defining exact boundaries).
* Questions 5–8: Counter-Example Construction (Demanding a minimal scenario where a property fails if a specific condition is dropped).
* Questions 9–10: Structural Synthesis (Connecting this framework to code implementation, operational semantics, or a previous topic).
