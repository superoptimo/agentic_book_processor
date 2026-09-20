#!/usr/bin/env python3
"""
crosslink2.py — insert Obsidian [[wikilinks]] between a folder of generated
topic articles, cross-referencing shared terms/concepts, AND wire up
book-guidelines.md itself with suffix-style links.

Usage:
    python crosslink2.py /path/to/workspace/[book] [--dry-run] [--verbose]
                          [--fuzzy-threshold 0.62] [--max-fuzzy 15] [--no-fuzzy]
                          [--no-index]

This is a fork of crosslink.py (see scripts/crosslink.py) with two changes:

  1. The book folder lives under workspace/[book] instead of vaults/[book].
     (This only affects what path callers pass in; the script itself just
     operates on whatever folder it's given.)

  2. book-guidelines.md is no longer purely read-only. Its prose is still
     NEVER rewritten — no term inside a sentence is ever wrapped in a link —
     but pass 3 now appends link(s) as a trailing SUFFIX after each Topic
     List entry's title text and after each Chapter Summaries entry (the
     chapter's "**Summary:**" line and each "**N.M Section Name**" bullet
     under "Key Definitions & Concepts by Section"), in the form:

         <original text, untouched> : [[Target|Link]]
         <original text, untouched> : [[Target1|Link1]], [[Target2|Link2]]

     i.e. "Link" is always the literal display text for a single match;
     multiple matches for the same entry are numbered Link1, Link2, ...
     Because this suffix is appended (not interleaved into the prose) and is
     always recomputed fresh from scratch on every run and stripped/replaced
     rather than accumulated, re-running the script is still idempotent and
     book-guidelines.md's own Topic List/Chapter Summaries wording is never
     otherwise altered.

PASS 1 — exact matching between article bodies (auto-applied): identical to
crosslink.py — see that script's docstring for the full description.

PASS 2 — similarity search between article bodies (advisory only, never
auto-applied): identical to crosslink.py.

PASS 3 — book-guidelines.md suffix-linking + Index assembly (auto-applied,
narrowly scoped, WRITES to book-guidelines.md unlike crosslink.py):
  Walks book-guidelines.md line by line. Inside "## Topic List", every
  top-level entry and subtopic bullet gets matched against the set of
  generated articles (exact slug match, then a collision-suffixed match,
  then a similarity fallback — same tiers as crosslink.py, but returning
  every article that clears the bar, not just the best one) and a suffix
  naming the match(es) is appended/replaced at the end of the line. Inside
  "## Chapter Summaries", the same matching is applied to each chapter's
  "**Summary:**" line (matched against the chapter's own title) and to each
  "**N.M Section Name**" bullet under "Key Definitions & Concepts by
  Section" (matched against the section name). Every other line (Header,
  Key Questions, page ranges, etc.) is left completely untouched.

  index.md is then fully regenerated from the (now suffix-linked) Topic List
  section of book-guidelines.md, plus a trailing "## Extra Topics" section
  for any generated article that no Topic List entry matched this run — same
  semantics as crosslink.py's Extra Topics section.

Excluded from scanning/linking as *source* files for passes 1 and 2 (a
heading inside them is not built into the glossary either, since they're
meta/index files rather than generated topic articles — pass 3 only ever
reads+writes book-guidelines.md, and only writes index.md):
  - book-guidelines.md
  - index.md
  - dotfiles (.crosslink-glossary.md, .crosslink-ignore.md, .article-style.md, etc.)
"""

import argparse
import difflib
import os
import re
import sys
from dataclasses import dataclass

STOPWORDS = {
    "the", "a", "an", "of", "and", "or", "in", "on", "for", "to", "is",
    "are", "with", "as", "by", "at", "from", "this", "that", "its",
}

DEFAULT_STOPLIST = {
    "example", "examples", "summary", "introduction", "overview",
    "definition", "definitions", "rules", "rule", "notes", "note",
    "background", "motivation", "conclusion", "references", "appendix",
    "key questions", "key definitions", "key definitions & concepts",
    "formation", "introduction rule", "elimination rule", "equality rule",
}

HEADING_RE = re.compile(r"^(#{2,3})\s+(.*)$", re.MULTILINE)
FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
DISPLAY_MATH_RE = re.compile(r"\$\$.*?\$\$", re.DOTALL)
INLINE_MATH_RE = re.compile(r"(?<!\$)\$(?!\$)[^$\n]+?\$(?!\$)")
WIKILINK_RE = re.compile(r"\[\[.*?\]\]")
MDLINK_RE = re.compile(r"\[[^\]]*\]\([^)]*\)")

# --- pass 3: book-guidelines.md structural regexes -------------------------

TOPIC_LIST_HEADING_RE = re.compile(r"^##\s*Topic List\s*$")
CHAPTER_SUMMARIES_HEADING_RE = re.compile(r"^##\s*Chapter Summaries\s*$")
OTHER_H2_RE = re.compile(r"^##\s+\S")

TOP_LEVEL_LINE_RE = re.compile(r"^(\d+\.\s+\*\*)(.+?)(\*\*\s*)$")
SUBTOPIC_LINE_RE = re.compile(r"^(\s*-\s+)(.+?)(\s*)$")

CHAPTER_HEADING_RE = re.compile(r"^###\s+Chapter\s+\d+:\s*(.+?)\s*(?:\(pp\.[^)]*\))?\s*$")
SUMMARY_LINE_RE = re.compile(r"^(\*\*Summary:\*\*\s*)(.+)$")
SECTION_LINE_RE = re.compile(r"^(\s*-\s+\*\*[\d.]+\s+)(.+?)(\*\*(?:\s*—.*)?)$")

# A previously-appended pass-3 suffix, so re-running strips it before
# recomputing fresh matches rather than accumulating duplicates.
OLD_SUFFIX_RE = re.compile(
    r"\s*:\s*\[\[[^\]|]+\|Link\d*\]\](?:\s*,\s*\[\[[^\]|]+\|Link\d*\]\])*\s*$"
)

TITLE_FIELD_RE = re.compile(r"^\*\*Title:\*\*\s*(.+)$", re.MULTILINE)
TOPIC_LIST_SECTION_RE = re.compile(r"##\s*Topic List\s*\n(.*?)(?=\n##\s|\Z)", re.DOTALL)


@dataclass
class GlossaryEntry:
    term: str          # canonical term text, as it should be matched (case-insensitive)
    target: str        # filename stem to link to, e.g. "Theory-of-Expressions"
    anchor: str = ""    # optional "#Heading" (without the #), empty for whole-file link

    def wikitarget(self) -> str:
        return f"{self.target}#{self.anchor}" if self.anchor else self.target


def slug_title(stem: str) -> str:
    """'Theory-of-Expressions' -> 'Theory of Expressions' for matching prose casing-insensitively."""
    return stem.replace("-", " ")


def is_meta_file(path: str) -> bool:
    name = os.path.basename(path)
    if name.startswith("."):
        return True
    if name == "book-guidelines.md":
        return True
    if name == "index.md":
        return True
    return False


def load_articles(folder: str):
    articles = []
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".md"):
            continue
        path = os.path.join(folder, name)
        if is_meta_file(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        articles.append((os.path.splitext(name)[0], path, text))
    return articles


def load_ignore_list(folder: str) -> set:
    ignore = set(DEFAULT_STOPLIST)
    path = os.path.join(folder, ".crosslink-ignore.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip().lstrip("-").strip()
                if line and not line.startswith("#"):
                    ignore.add(line.lower())
    return ignore


def load_manual_glossary(folder: str):
    """
    Optional override file, one entry per non-comment line, format:
        Term | Target-Slug
        Term | Target-Slug#Heading
    """
    entries = []
    path = os.path.join(folder, ".crosslink-glossary.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "|" not in line:
                    continue
                term, target = line.split("|", 1)
                term = term.strip()
                target = target.strip()
                anchor = ""
                if "#" in target:
                    target, anchor = target.split("#", 1)
                entries.append(GlossaryEntry(term=term, target=target.strip(), anchor=anchor.strip()))
    return entries


def build_glossary(articles, ignore: set):
    entries = []
    for stem, _path, text in articles:
        title_term = slug_title(stem)
        if title_term.lower() not in ignore:
            entries.append(GlossaryEntry(term=title_term, target=stem))

        body = FRONTMATTER_RE.sub("", text, count=1)
        for m in HEADING_RE.finditer(body):
            heading = m.group(2).strip()
            clean = re.sub(r"[*_`]", "", heading).strip()
            if not clean or clean.lower() in ignore:
                continue
            if len(clean) < 4:
                continue
            entries.append(GlossaryEntry(term=clean, target=stem, anchor=heading))
    return entries


def build_stem_headings(articles, ignore: set):
    """Map each article stem to its cleaned ##/### heading texts, for pass 3's
    fuzzy fallback to match a Topic List/Chapter Summaries entry against
    section headings, not just each article's whole title."""
    result = {}
    for stem, _path, text in articles:
        body = FRONTMATTER_RE.sub("", text, count=1)
        headings = []
        for m in HEADING_RE.finditer(body):
            heading = m.group(2).strip()
            clean = re.sub(r"[*_`]", "", heading).strip()
            if not clean or clean.lower() in ignore or len(clean) < 4:
                continue
            headings.append(clean)
        result[stem] = headings
    return result


def protected_spans(text: str):
    """Return a sorted list of (start, end) character ranges that must not be
    touched: frontmatter, fenced code, inline code, math, existing wikilinks,
    existing md links, and heading lines themselves."""
    spans = []
    fm = FRONTMATTER_RE.match(text)
    if fm:
        spans.append(fm.span())
    for pattern in (FENCE_RE, INLINE_CODE_RE, DISPLAY_MATH_RE, INLINE_MATH_RE, WIKILINK_RE, MDLINK_RE, HEADING_RE):
        for m in pattern.finditer(text):
            spans.append(m.span())
    spans.sort()
    return spans


def overlaps(a_start, a_end, spans):
    for s, e in spans:
        if a_start < e and s < a_end:
            return True
    return False


def link_article(source_stem: str, text: str, glossary, verbose_target=None):
    """Insert first-occurrence wikilinks for every glossary term not belonging
    to source_stem. Returns (new_text, list_of_(term, wikitarget))."""
    added = []
    terms = sorted(
        (g for g in glossary if g.target != source_stem),
        key=lambda g: len(g.term),
        reverse=True,
    )
    seen_pairs = set()
    deduped = []
    for g in terms:
        key = (g.term.lower(), g.wikitarget())
        if key not in seen_pairs:
            seen_pairs.add(key)
            deduped.append(g)
    terms = deduped

    protected = protected_spans(text)
    linked_terms_this_file = set()

    def already_links_to(wikitarget: str) -> bool:
        return re.search(r"\[\[" + re.escape(wikitarget) + r"(\||\])", text) is not None

    for g in terms:
        if g.term.lower() in linked_terms_this_file:
            continue
        if already_links_to(g.wikitarget()):
            continue
        pattern = re.compile(r"\b" + re.escape(g.term) + r"\b", re.IGNORECASE)
        m = None
        for cand in pattern.finditer(text):
            if not overlaps(cand.start(), cand.end(), protected):
                m = cand
                break
        if not m:
            continue
        original = text[m.start():m.end()]
        replacement = f"[[{g.wikitarget()}|{original}]]"
        text = text[:m.start()] + replacement + text[m.end():]
        shift = len(replacement) - len(original)
        new_spans = []
        for s, e in protected:
            if s >= m.end():
                s, e = s + shift, e + shift
            new_spans.append((s, e))
        new_spans.append((m.start(), m.start() + len(replacement)))
        protected = sorted(new_spans)
        linked_terms_this_file.add(g.term.lower())
        added.append((original, g.wikitarget()))

    return text, added


def normalize(phrase: str) -> str:
    """Lowercase, strip punctuation, drop light stopwords, naive de-pluralize.
    Used only to compute similarity scores."""
    s = re.sub(r"[^\w\s]", " ", phrase.lower())
    words = [w for w in s.split() if w not in STOPWORDS]
    words = [w[:-1] if w.endswith("s") and len(w) > 4 else w for w in words]
    return " ".join(words)


def similarity(a: str, b: str) -> float:
    na, nb = normalize(a), normalize(b)
    if not na or not nb:
        return 0.0
    ratio = difflib.SequenceMatcher(None, na, nb).ratio()
    aset, bset = set(na.split()), set(nb.split())
    jaccard = len(aset & bset) / len(aset | bset) if (aset | bset) else 0.0
    # Containment requires at least 2 words on the shorter side: a single
    # shared word (e.g. "chapter", "system") is trivially "fully contained"
    # in any heading that happens to include it, which would give a bare
    # one-word overlap the same 1.0 score as a genuine reworded phrase — so
    # a lone-word phrase can only ever be scored via ratio/jaccard, not
    # containment's free pass.
    containment = len(aset & bset) / len(aset) if len(aset) >= 2 and len(na) >= 6 else 0.0
    return max(ratio, jaccard, containment)


def tokenize_with_offsets(text: str):
    return [(m.group(0), m.start(), m.end()) for m in re.finditer(r"\w+", text)]


def build_term_index(glossary):
    """See crosslink.py — precomputes an inverted index so pass 2 doesn't
    compare every window against every glossary term."""
    MAX_WINDOW_SIZE = 8
    MIN_KEY_LEN = 3
    MAX_TERMS_PER_WORD = 10

    term_recs = []
    raw_inverted = {}
    window_sizes = set()
    for g in glossary:
        term_norm = normalize(g.term)
        term_set = set(term_norm.split()) if term_norm else set()
        idx = len(term_recs)
        term_recs.append((g, term_norm, term_set))
        for w in term_set:
            if len(w) >= MIN_KEY_LEN:
                raw_inverted.setdefault(w, []).append(idx)
        k = len(g.term.split())
        for size in (max(1, k - 1), k, k + 1):
            window_sizes.add(min(size, MAX_WINDOW_SIZE))

    inverted = {w: idxs for w, idxs in raw_inverted.items() if len(idxs) <= MAX_TERMS_PER_WORD}
    return term_recs, inverted, sorted(window_sizes)


def fuzzy_suggestions(source_stem: str, text: str, term_recs, inverted, window_sizes,
                       threshold: float, max_suggestions: int):
    """Advisory-only pass: find word-windows in `text` whose normalized form is
    similar-but-not-identical to a glossary term belonging to a different
    article. Never modifies `text`."""
    protected = protected_spans(text)
    tokens = tokenize_with_offsets(text)
    n = len(tokens)

    raw = []
    for window_size in window_sizes:
        if window_size > n:
            continue
        for i in range(n - window_size + 1):
            start, end = tokens[i][1], tokens[i + window_size - 1][2]
            if overlaps(start, end, protected):
                continue
            phrase = text[start:end]
            phrase_norm = normalize(phrase)
            if not phrase_norm:
                continue
            phrase_set = set(phrase_norm.split())

            candidate_idxs = set()
            for w in phrase_set:
                candidate_idxs.update(inverted.get(w, ()))
            if not candidate_idxs:
                continue

            phrase_lower = phrase.strip().lower()
            for idx in candidate_idxs:
                g, term_norm, term_set = term_recs[idx]
                if g.target == source_stem:
                    continue
                if phrase_lower == g.term.strip().lower():
                    continue
                shared = len(phrase_set & term_set)
                union_len = len(phrase_set | term_set)
                jaccard = shared / union_len if union_len else 0.0
                # See similarity()'s comment: a single-word window gets no
                # containment free pass just for appearing inside a heading.
                containment = (
                    shared / len(phrase_set)
                    if len(phrase_set) >= 2 and len(phrase_norm) >= 6 else 0.0
                )
                score = max(jaccard, containment)
                if score < threshold:
                    ratio = difflib.SequenceMatcher(None, phrase_norm, term_norm).ratio()
                    score = max(score, ratio)
                if score >= threshold:
                    raw.append((score, phrase, start, end, g))

    raw.sort(key=lambda x: -x[0])
    chosen = []
    used_spans = []
    for score, phrase, start, end, g in raw:
        if overlaps(start, end, used_spans):
            continue
        used_spans.append((start, end))
        chosen.append((score, phrase, g))
        if len(chosen) >= max_suggestions:
            break
    return chosen


def slugify(topic_text: str) -> str:
    """Mirror book-topic-article's Title-Case-With-Hyphens filename convention:
    internal whitespace -> single hyphen, everything else left as-is."""
    return re.sub(r"\s+", "-", topic_text.strip())


def find_matching_articles(topic_text: str, stems: list, stem_headings: dict = None,
                            fuzzy_threshold: float = 0.55, max_matches: int = 4,
                            score_window: float = 0.08):
    """Given a Topic List/Chapter Summaries entry's text, find every generated
    article (by filename stem) it plausibly corresponds to, in order of
    confidence: an exact slug match (returns just that one — it's
    definitive); else every collision-disambiguated variant sharing the same
    slug prefix (e.g. both 'Beta-Reduction-(Theory-of-Expressions).md' and
    'Beta-Reduction-(System-F).md' for a plain 'Beta Reduction' entry); else
    every article whose similarity score (checked against both its own title
    and its section headings, via stem_headings) clears fuzzy_threshold and
    sits within score_window of the best score found, capped at max_matches.
    Returns a list of target stems (possibly empty); order reflects
    confidence, highest first."""
    slug = slugify(topic_text)
    if slug in stems:
        return [slug]

    prefix = slug + "-("
    collisions = sorted(s for s in stems if s.startswith(prefix))
    if collisions:
        return collisions

    stem_headings = stem_headings or {}
    scored = []
    for s in stems:
        score = similarity(topic_text, slug_title(s))
        for heading in stem_headings.get(s, []):
            heading_score = similarity(topic_text, heading)
            if heading_score > score:
                score = heading_score
        if score >= fuzzy_threshold:
            scored.append((score, s))
    if not scored:
        return []
    scored.sort(key=lambda x: -x[0])
    best_score = scored[0][0]
    return [s for score, s in scored if score >= best_score - score_window][:max_matches]


def build_suffix(targets: list) -> str:
    """' : [[Target|Link]]' for a single match, or
    ' : [[T1|Link1]], [[T2|Link2]]' for several. Empty string if no match."""
    if not targets:
        return ""
    if len(targets) == 1:
        return f" : [[{targets[0]}|Link]]"
    parts = [f"[[{t}|Link{i + 1}]]" for i, t in enumerate(targets)]
    return " : " + ", ".join(parts)


def relink_guidelines(guidelines_text: str, stems: list, stem_headings: dict):
    """Walk book-guidelines.md line by line, rewriting only:
      - Topic List top-level entries and subtopic bullets, matched against
        their own text;
      - Chapter Summaries "**Summary:**" lines, matched against the
        enclosing chapter's title;
      - Chapter Summaries "**N.M Section Name**" bullets, matched against
        the section name.
    Every other line (Header, page ranges, Key Questions, etc.) passes
    through byte-for-byte unchanged. Any pass-3 suffix from a previous run
    is stripped before recomputing, so this is idempotent and always
    reflects the current set of generated articles.

    Returns (new_text, entries_linked, matched_stems) where matched_stems is
    the set of article stems claimed by at least one TOPIC LIST entry this
    run (Chapter Summaries matches don't count toward Extra Topics, mirroring
    the original skill's index semantics, which are Topic-List-derived)."""
    lines = guidelines_text.split("\n")
    out = []
    entries_linked = 0
    matched_stems = set()

    in_topic_list = False
    in_chapter_summaries = False
    current_chapter_title = None

    def resolve(entry_text: str, count_for_index: bool) -> str:
        nonlocal entries_linked
        targets = find_matching_articles(entry_text, stems, stem_headings)
        if targets:
            entries_linked += 1
            if count_for_index:
                matched_stems.update(t for t in targets if t in stems)
        return build_suffix(targets)

    for line in lines:
        if TOPIC_LIST_HEADING_RE.match(line):
            in_topic_list, in_chapter_summaries = True, False
            out.append(line)
            continue
        if CHAPTER_SUMMARIES_HEADING_RE.match(line):
            in_topic_list, in_chapter_summaries = False, True
            current_chapter_title = None
            out.append(line)
            continue
        if OTHER_H2_RE.match(line):
            in_topic_list, in_chapter_summaries = False, False
            out.append(line)
            continue

        stripped_line = OLD_SUFFIX_RE.sub("", line)

        if in_topic_list:
            m = TOP_LEVEL_LINE_RE.match(stripped_line)
            if m:
                suffix = resolve(m.group(2), count_for_index=True)
                out.append(f"{m.group(1)}{m.group(2)}**{suffix}")
                continue
            m = SUBTOPIC_LINE_RE.match(stripped_line)
            if m:
                suffix = resolve(m.group(2), count_for_index=True)
                out.append(f"{m.group(1)}{m.group(2)}{suffix}")
                continue
            out.append(line)
            continue

        if in_chapter_summaries:
            m = CHAPTER_HEADING_RE.match(line)
            if m:
                current_chapter_title = m.group(1)
                out.append(line)
                continue
            m = SUMMARY_LINE_RE.match(stripped_line)
            if m and current_chapter_title:
                suffix = resolve(current_chapter_title, count_for_index=False)
                out.append(f"{m.group(1)}{m.group(2)}{suffix}")
                continue
            m = SECTION_LINE_RE.match(stripped_line)
            if m:
                suffix = resolve(m.group(2), count_for_index=False)
                out.append(f"{m.group(1)}{m.group(2)}{m.group(3)}{suffix}")
                continue
            out.append(line)
            continue

        out.append(line)

    return "\n".join(out), entries_linked, matched_stems


def extract_book_title(guidelines_text: str, fallback_folder_name: str) -> str:
    m = TITLE_FIELD_RE.search(guidelines_text)
    if m:
        return m.group(1).strip()
    return fallback_folder_name.replace("-", " ").replace("_", " ")


def build_index(book_folder: str, book_title: str, topic_list_text: str,
                 extra_stems: list, dry_run: bool):
    """Fully (re)generate 'index.md' from book-guidelines.md's (already
    suffix-linked) Topic List section, plus a trailing "## Extra Topics"
    section for any generated article no Topic List entry claimed this run.
    Returns (path, changed: bool)."""
    index_path = os.path.join(book_folder, "index.md")
    content = (
        f"# {book_title} — Index\n\n"
        f"[[book-guidelines|↩ Back to guidelines]]\n\n"
        f"{topic_list_text.strip(chr(10))}\n"
    )
    if extra_stems:
        content += "\n---\n\n## Extra Topics\n\n"
        content += "Generated articles not (yet) matched to a Topic List entry in book-guidelines.md:\n\n"
        for stem in sorted(extra_stems, key=str.lower):
            content += f"- [[{stem}|{slug_title(stem)}]]\n"
    old_content = None
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            old_content = f.read()
    changed = content != old_content
    if changed and not dry_run:
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(content)
    return index_path, changed


# --- pass 4: learning-roadmap-*.md curation --------------------------------
#
# Distinct from passes 1-3: those operate on ONE workspace/[book] folder.
# This pass operates on the workspace/ ROOT, over every learning-roadmap-*.md
# file the learning-roadmap skill writes there (e.g.
# workspace/learning-roadmap-type-theory.md), plus workspace/learning-roadmap.md
# itself when present. Those roadmap notes cite generated articles living in
# *other* book folders (workspace/[book]/Topic-Slug.md) via wikilinks under
# each topic's "Sources to Study" list, and cite each other via
# "[[learning-roadmap-[slug]|...]]" cross-references. Nothing about resolving
# those links belongs in Obsidian's own resolver being trusted blindly — a
# renamed book folder or a re-slugged article leaves a dangling link behind
# with no signal — so this pass verifies and, where a confident fuzzy match
# exists, repairs them the same way pass 3 repairs book-guidelines.md.

LEARNING_ROADMAP_PREFIX = "learning-roadmap-"
LEARNING_ROADMAP_FULL = "learning-roadmap"

SOURCES_HEADING_RE = re.compile(r"^####\s*Sources to Study\s*$")
OTHER_H4_RE = re.compile(r"^####\s+\S")
OTHER_H3_RE = re.compile(r"^###\s+\S")
TOP_BOOK_ENTRY_RE = re.compile(r"^\d+\.\s+\[\[([^\]|#]+)(?:\|[^\]]*)?\]\]\s*$")

# Captures target, optional #anchor, optional |display for any wikilink.
ROADMAP_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)((?:#[^\]|]*)?)(?:\|([^\]]*))?\]\]")


def find_roadmap_files(workspace_root: str):
    if not os.path.isdir(workspace_root):
        return []
    names = []
    for name in sorted(os.listdir(workspace_root)):
        if not name.endswith(".md"):
            continue
        stem = name[:-3]
        if stem == LEARNING_ROADMAP_FULL or stem.startswith(LEARNING_ROADMAP_PREFIX):
            names.append(name)
    return names


def find_book_folders(workspace_root: str):
    """Only folders that actually hold a book-guidelines.md count as a
    resolvable book — everything else (custom_notes/, dotfolders, a book
    folder that hasn't been processed yet) is out of scope for link repair,
    though still reportable as a dangling book reference."""
    folders = []
    if not os.path.isdir(workspace_root):
        return folders
    for name in sorted(os.listdir(workspace_root)):
        path = os.path.join(workspace_root, name)
        if not os.path.isdir(path) or name.startswith("."):
            continue
        if os.path.exists(os.path.join(path, "book-guidelines.md")):
            folders.append(name)
    return folders


def build_book_cache(workspace_root: str, book_folders):
    cache = {}
    for folder in book_folders:
        folder_path = os.path.join(workspace_root, folder)
        articles = load_articles(folder_path)
        stems = [s for s, _p, _t in articles]
        ignore = load_ignore_list(folder_path)
        stem_headings = build_stem_headings(articles, ignore)
        cache[folder] = (stems, stem_headings)
    return cache


def curate_roadmap_text(text: str, book_cache: dict, roadmap_stems: set):
    """Walk one roadmap file's lines. Inside a '#### Sources to Study' block,
    track which book folder the current numbered entry names, and treat every
    bare (non-'/', non-'learning-roadmap') wikilink target found until the
    next numbered entry or the block's end as an article slug belonging to
    that folder. A '[[learning-roadmap-...]]' cross-reference and a
    folder-qualified '[[folder/book-guidelines|...]]' link are checked
    anywhere in the file, not just inside Sources to Study, since those don't
    need book-folder context to resolve.

    Returns (new_text, report) where report has:
      fixed:               [(old_target, new_target, book_folder)]
      unresolved_articles:  [(book_folder, target)]   — no confident match
      broken_book_refs:     [target]                  — book folder missing
      broken_roadmap_refs:  [target]                  — sibling roadmap missing
    """
    report = {
        "fixed": [],
        "unresolved_articles": [],
        "broken_book_refs": [],
        "broken_roadmap_refs": [],
    }
    lines = text.split("\n")
    out = []
    in_sources = False
    current_book_folder = None

    def repl(m):
        target, anchor, display = m.group(1), m.group(2) or "", m.group(3)

        if target == LEARNING_ROADMAP_FULL or target.startswith(LEARNING_ROADMAP_PREFIX):
            if target not in roadmap_stems:
                report["broken_roadmap_refs"].append(target)
            return m.group(0)

        if "/" in target:
            folder = target.split("/", 1)[0]
            if folder not in book_cache:
                report["broken_book_refs"].append(target)
            return m.group(0)

        if current_book_folder is None:
            return m.group(0)

        stems, stem_headings = book_cache[current_book_folder]
        if target in stems:
            return m.group(0)

        matches = find_matching_articles(slug_title(target), stems, stem_headings)
        if len(matches) == 1:
            new_target = matches[0]
            report["fixed"].append((target, new_target, current_book_folder))
            disp_part = f"|{display}" if display is not None else ""
            return f"[[{new_target}{anchor}{disp_part}]]"

        report["unresolved_articles"].append((current_book_folder, target))
        return m.group(0)

    for line in lines:
        if SOURCES_HEADING_RE.match(line):
            in_sources = True
            current_book_folder = None
            out.append(line)
            continue
        if in_sources and (OTHER_H4_RE.match(line) or OTHER_H3_RE.match(line) or OTHER_H2_RE.match(line)):
            in_sources = False
            current_book_folder = None
            out.append(line)
            continue

        if in_sources:
            m = TOP_BOOK_ENTRY_RE.match(line.strip())
            if m:
                folder = m.group(1).split("/", 1)[0]
                current_book_folder = folder if folder in book_cache else None
                if folder not in book_cache:
                    report["broken_book_refs"].append(m.group(1))

        out.append(ROADMAP_WIKILINK_RE.sub(repl, line))

    return "\n".join(out), report


def curate_learning_roadmaps(workspace_root: str, dry_run: bool, verbose: bool):
    roadmap_files = find_roadmap_files(workspace_root)
    if not roadmap_files:
        print(f"No learning-roadmap*.md files found at the root of {workspace_root} — nothing to curate.")
        return
    roadmap_stems = {name[:-3] for name in roadmap_files}

    book_folders = find_book_folders(workspace_root)
    book_cache = build_book_cache(workspace_root, book_folders)

    total_fixed = 0
    total_unresolved = 0
    total_broken_book = 0
    total_broken_roadmap = 0
    files_changed = 0

    for name in roadmap_files:
        path = os.path.join(workspace_root, name)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        new_text, report = curate_roadmap_text(text, book_cache, roadmap_stems)
        changed = new_text != text
        if changed:
            files_changed += 1
            if not dry_run:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_text)

        total_fixed += len(report["fixed"])
        total_unresolved += len(report["unresolved_articles"])
        total_broken_book += len(set(report["broken_book_refs"]))
        total_broken_roadmap += len(set(report["broken_roadmap_refs"]))

        if report["fixed"] or report["unresolved_articles"] or report["broken_book_refs"] or report["broken_roadmap_refs"]:
            print(f"\n{name}:")
            for old, new, folder in report["fixed"]:
                print(f"    fixed [[{old}]] -> [[{new}]]  (in {folder}/)")
            if verbose:
                for folder, target in report["unresolved_articles"]:
                    print(f"    unresolved [[{target}]] — no article in {folder}/ matched (not yet generated, or needs a manual fix)")
                for target in sorted(set(report["broken_book_refs"])):
                    print(f"    dangling book reference [[{target}]] — no such book folder with a book-guidelines.md under {workspace_root}/")
                for target in sorted(set(report["broken_roadmap_refs"])):
                    print(f"    dangling roadmap reference [[{target}]] — no such file at {workspace_root}/{target}.md")
            elif not report["fixed"]:
                print(f"    {len(report['unresolved_articles'])} unresolved article link(s), "
                      f"{len(set(report['broken_book_refs']))} dangling book reference(s), "
                      f"{len(set(report['broken_roadmap_refs']))} dangling roadmap reference(s) — rerun with --verbose to list them")

    print(f"\n{'(dry run) ' if dry_run else ''}Pass 4: {len(roadmap_files)} roadmap file(s) scanned "
          f"({', '.join(roadmap_files)}), {files_changed} updated. "
          f"{total_fixed} link(s) auto-repaired, {total_unresolved} article link(s) left unresolved, "
          f"{total_broken_book} dangling book reference(s), {total_broken_roadmap} dangling roadmap reference(s).")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", nargs="?",
                     help="workspace/[book] folder containing the generated articles "
                          "(with --curate-learning-roadmaps, this is the workspace/ root instead, "
                          "defaulting to 'workspace' if omitted)")
    ap.add_argument("--curate-learning-roadmaps", action="store_true",
                     help="curate workspace/learning-roadmap*.md link references instead of running "
                          "passes 1-3 on a single book folder")
    ap.add_argument("--dry-run", action="store_true", help="report changes without writing files")
    ap.add_argument("--verbose", action="store_true", help="print every link added, not just the totals")
    ap.add_argument("--no-fuzzy", action="store_true", help="skip pass 2 (similarity suggestions) entirely")
    ap.add_argument("--fuzzy-threshold", type=float, default=0.62,
                     help="minimum similarity score (0-1) for a pass-2 suggestion (default: 0.62)")
    ap.add_argument("--max-fuzzy", type=int, default=15,
                     help="max pass-2 suggestions to report per file (default: 15)")
    ap.add_argument("--no-index", action="store_true",
                     help="skip pass 3 entirely (book-guidelines.md suffix-linking and index.md regeneration)")
    args = ap.parse_args()

    if args.curate_learning_roadmaps:
        workspace_root = args.folder or "workspace"
        if not os.path.isdir(workspace_root):
            print(f"error: {workspace_root} is not a directory", file=sys.stderr)
            sys.exit(1)
        curate_learning_roadmaps(workspace_root, args.dry_run, args.verbose)
        return

    if not args.folder:
        ap.error("folder is required unless --curate-learning-roadmaps is given")

    folder = args.folder
    if not os.path.isdir(folder):
        print(f"error: {folder} is not a directory", file=sys.stderr)
        sys.exit(1)

    articles = load_articles(folder)
    stems = [stem for stem, _p, _t in articles]
    ignore = load_ignore_list(folder)
    stem_headings = build_stem_headings(articles, ignore)

    total_files_changed = 0
    total_links_added = 0
    total_suggestions = 0

    if len(articles) < 2:
        print("Fewer than two eligible articles found — skipping pass 1/2 cross-referencing.")
    else:
        glossary = build_glossary(articles, ignore)
        glossary.extend(load_manual_glossary(folder))

        if not args.no_fuzzy:
            term_recs, inverted, window_sizes = build_term_index(glossary)

        for stem, path, text in articles:
            new_text, added = link_article(stem, text, glossary)
            if added:
                total_files_changed += 1
                total_links_added += len(added)
                print(f"\n{os.path.basename(path)}: {len(added)} link(s) added")
                if args.verbose:
                    for original, target in added:
                        print(f"    \"{original}\" -> [[{target}]]")
                if not args.dry_run:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(new_text)

            if not args.no_fuzzy:
                suggestions = fuzzy_suggestions(stem, new_text, term_recs, inverted, window_sizes,
                                                 args.fuzzy_threshold, args.max_fuzzy)
                if suggestions:
                    total_suggestions += len(suggestions)
                    print(f"\n{os.path.basename(path)}: {len(suggestions)} possible related mention(s) — NOT auto-linked, review and add confirmed ones to .crosslink-glossary.md:")
                    for score, phrase, g in suggestions:
                        print(f"    \"{phrase}\" ~ \"{g.term}\"  (score {score:.2f})  -> would be [[{g.wikitarget()}]]")

    print(f"\n{'(dry run) ' if args.dry_run else ''}Pass 1/2: {total_links_added} link(s) added across {total_files_changed} file(s), "
          f"{total_suggestions} similarity suggestion(s) surfaced for review, out of {len(articles)} article(s) scanned.")

    # Pass 3: book-guidelines.md suffix-linking + Index assembly.
    if args.no_index:
        print("\nPass 3: --no-index skips guidelines-linking and Index generation entirely.")
        return

    guidelines_path = os.path.join(folder, "book-guidelines.md")
    if not os.path.exists(guidelines_path):
        print("\nPass 3: no book-guidelines.md found in this folder — skipping guidelines-linking and Index generation.")
        return

    with open(guidelines_path, "r", encoding="utf-8") as f:
        guidelines_text = f.read()

    new_guidelines_text, entries_linked, matched_stems = relink_guidelines(guidelines_text, stems, stem_headings)
    guidelines_changed = new_guidelines_text != guidelines_text
    if guidelines_changed and not args.dry_run:
        with open(guidelines_path, "w", encoding="utf-8") as f:
            f.write(new_guidelines_text)

    print(f"\nPass 3: {entries_linked} Topic List / Chapter Summaries entr{'y' if entries_linked == 1 else 'ies'} "
          f"linked in book-guidelines.md ({'updated' if guidelines_changed else 'already up to date'}).")

    extra_stems = [s for s in stems if s not in matched_stems]
    if extra_stems:
        print(f"Pass 3: {len(extra_stems)} article(s) unmatched by any Topic List entry — "
              f"listed under Extra Topics: {', '.join(sorted(extra_stems, key=str.lower))}")

    section_match = TOPIC_LIST_SECTION_RE.search(new_guidelines_text)
    topic_list_text = section_match.group(1) if section_match else ""
    folder_name = os.path.basename(os.path.normpath(folder))
    book_title = extract_book_title(new_guidelines_text, folder_name)
    index_path, index_changed = build_index(folder, book_title, topic_list_text, extra_stems, args.dry_run)
    status = "updated" if index_changed else "already up to date"
    print(f"Pass 3: Index note {status} at {index_path}.")


if __name__ == "__main__":
    main()
