Make a new skill named `/book-crosslink2` based on the original `/book-crosslink`, but with these modifications:

1. Instead of looking for books at `vaults` folder, it will search books at `workspace` folder, such as `workspace/[book]` as it artifacts will be found like 
```
workspace/[book]/*.md                    <- input AND output: existing generated articles, edited in place
workspace/[book]/book-guidelines.md          <- input only: read-only, NEVER written by this skill
```
Additionally, the target artifacts will be located at the same target book folder (`workspace/[book]`) such as 
```
workspace/[book]/index.md       <- output: fully (re)derived from book-guidelines.md's Topic List
                                  each run, plus a trailing "Extra Topics" section for any
                                  article no Topic List entry matched
workspace/[book]/.crosslink-glossary.md  <- optional input: manual term -> target overrides
workspace/[book]/.crosslink-ignore.md    <- optional input: terms to never auto-link
```

2. This skill will use a new modified script called `crosslink2.py` located at `scripts/`, which will be inspired on the original `crosslink.py`

3. This new skill (book-crosslink2) is already allowed to modify `book-guidelines.md` inside book folder (`workspace/[book]/book-guidelines.md`), but link refereces should
follow these style format:

#### Links at main topic list

Links at topic list should be aggregated as sufixes after the topic text tile, without modifying the original text as the artifact `[[Target|Link]]` (considering `Target` as the referenced target obsidian note, and "Link" is always the same label for all cases) such as:

---

## Topic List

1. **<Broad topic, phrased as a generalized category>** : `[[TargetTopic1|Link]]`
   - <Subtopic, phrased as a plain, title-cased sentence/fragment — no punctuation> : `[[TargetSubTopic1|Link]]`
   - <Subtopic> : `[[TargetSubTopic1|Link1]]`, `[[TargetSubTopic2|Link2]]`
2. **<Broad topic>** `[[TargetTopic2|Link]]`
   - <Subtopic> `[[TargetSubTopic3|Link1]]`, `[[TargetSubTopic4|Link2]]`..., `[[TargetSubTopicN|LinkN]]`
   - ... 

---

In case that there are more than 1 note related with a subtopic, create additional links enumerated as a list (Link1, Link2 etc).

#### Links at Chapter summary

Links at chaper summaries should be aggregated as sufixes after the Section/Title text tile, without modifying the original text as the artifact `[[Target|Link]]`, in a similar fashion as in the Topic list, after the summmary sentences and at the end of each section listing such as:

---

## Chapter Summaries

### Chapter N: <Chapter Title> (pp. X–Y)

**Summary:** [1-2 sentences] . `[[TargetNote|Link]]`

**Key Definitions & Concepts by Section:**
- **N.1 <Section Name>** — term (definition), term (definition), .... `[[TargetNote1|Link]]`
- **N.2 <Section Name>** — ... `[[TargetNote2|Link1]]`, `[[TargetNote2|Link2]]`

**Key Questions:**
1. ...
2. ...

---

As same in topic list, in case that there are more than 1 note related with section topics, create additional links enumerated as a list (Link1, Link2 etc).
