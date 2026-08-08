#!/usr/bin/env python3
"""
crosslink.py — insert Obsidian [[wikilinks]] between a folder of generated
topic articles, cross-referencing shared terms/concepts.

Usage:
    python crosslink.py /path/to/vaults/[book] [--dry-run] [--verbose]
                         [--fuzzy-threshold 0.62] [--max-fuzzy 15] [--no-fuzzy]

This runs in two passes:

PASS 1 — exact matching (auto-applied):
  1. Builds a glossary of linkable terms from every article in the folder:
       - the article's own title (its filename, minus .md)      -> whole-file link
       - every H2 (##) / H3 (###) heading inside each article   -> heading-anchor link
       - any entries from an optional .crosslink-glossary.md    -> manual overrides/additions
  2. Filters out overly generic terms (a small built-in stoplist, plus
     anything listed in an optional .crosslink-ignore.md).
  3. For every article, scans its prose (skipping YAML frontmatter, fenced
     code blocks, inline code spans, $...$ / $$...$$ math, and any text
     already inside [[...]]) and wraps the FIRST occurrence of each other
     article's term with a wikilink, preserving the original casing as the
     link's display text: [[Target-Slug|original text]] or
     [[Target-Slug#Heading|original text]].
  4. Never links a term back to the article it already lives in (no self-links).
  5. Is idempotent: already-linked text is detected and left alone, so
     re-running the script on an already-processed folder is a safe no-op
     (unless new articles/headings were added since the last run).
  6. Only writes files that actually changed, and prints a per-file report
     of what was linked.

PASS 2 — similarity search (advisory only, NEVER auto-applied):
  Exact matching alone misses articles that refer to the same concept in
  different words (e.g. "the universe of small sets" vs. an article titled
  "Universes", or "defeq" vs. a heading "Definitional Equality"). Pass 2
  scans the same protected-span-safe prose for word-windows whose normalized
  text (lowercased, light stopword/plural stripping) is *similar* to a
  glossary term — using a blend of sequence-similarity and word-overlap — and
  reports candidates above a threshold as SUGGESTIONS, never edits.
  Semantic judgment of whether a fuzzy suggestion is actually the same
  concept is left to whoever reviews the report (a human, or the assistant
  running this skill) — string similarity is a recall tool for surfacing
  candidates, not a substitute for understanding what they mean. Confirmed
  suggestions should be promoted into .crosslink-glossary.md (as an exact
  entry) and then picked up automatically by pass 1 on the next run — that
  keeps every link that actually lands in a file coming from the same
  reviewed, deterministic mechanism.

PASS 3 — guidelines Topic List linking + Index assembly (auto-applied, but narrowly scoped):
  Unlike passes 1/2, book-guidelines.md and the "index.md" note are not
  scanned as prose. Instead:
    - Only the "## Topic List" section of book-guidelines.md is touched. Every
      top-level entry and every subtopic bullet is checked against the set
      of generated articles in the folder; if a matching article exists, the
      entry's text is wrapped in a wikilink to it (exact slug match first,
      then a same-parent-suffix match for collision-disambiguated filenames,
      then a similarity-based fallback reusing pass 2's scoring). Entries
      with no matching article yet are left as plain text — so the Topic
      List doubles as a live "what's been written" indicator. Idempotent:
      already-linked entries are skipped.
    - "index.md" is then fully regenerated from that same
      (now-linked) Topic List content, with a back-link to book-guidelines.md.
      Being fully derived, it's simply rewritten each run rather than
      diffed/merged — cheap, and always exactly in sync.

Excluded from scanning/linking as *source* files for passes 1 and 2 (a
heading inside them is not built into the glossary either, since they're
meta/index files rather than generated topic articles — pass 3 is the only
pass that touches them, and only in the narrow way described above):
  - book-guidelines.md
  - index.md
  - dotfiles (.crosslink-glossary.md, .crosslink-ignore.md, .article-style.md, etc.)
"""

import argparse
import difflib
import os
import re
import sys
from dataclasses import dataclass, field

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

TOPIC_LIST_SECTION_RE = re.compile(r"##\s*Topic List\s*\n(.*?)(?=\n##\s|\Z)", re.DOTALL)
TOP_LEVEL_LINE_RE = re.compile(r"^(\d+\.\s+\*\*)(.+?)(\*\*\s*)$")
SUBTOPIC_LINE_RE = re.compile(r"^(\s*-\s+)(.+?)(\s*)$")
TITLE_FIELD_RE = re.compile(r"^\*\*Title:\*\*\s*(.+)$", re.MULTILINE)


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
            # strip trailing markdown emphasis markers etc. for the matchable term
            clean = re.sub(r"[*_`]", "", heading).strip()
            if not clean or clean.lower() in ignore:
                continue
            if len(clean) < 4:  # skip very short/noisy headings
                continue
            entries.append(GlossaryEntry(term=clean, target=stem, anchor=heading))
    return entries


def build_stem_headings(articles, ignore: set):
    """Map each article stem to its cleaned ##/### heading texts (same
    cleaning/filtering as build_glossary), for pass 3's fuzzy fallback to
    match a Topic List subtopic against section headings, not just each
    article's whole title."""
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
    """Return a sorted list of (start, end) character ranges that must not be touched:
    frontmatter, fenced code, inline code, math, existing wikilinks, existing md links,
    and heading lines themselves (## / ###) — a term must never be inserted into a
    heading's own text, since that corrupts the heading rather than cross-referencing
    prose, and a mangled heading would also poison future glossary-building off it."""
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
    # Longest term first, so multi-word phrases win over their substrings.
    terms = sorted(
        (g for g in glossary if g.target != source_stem),
        key=lambda g: len(g.term),
        reverse=True,
    )
    # De-duplicate by (term.lower(), target) so the same heading isn't tried twice.
    seen_pairs = set()
    deduped = []
    for g in terms:
        key = (g.term.lower(), g.wikitarget())
        if key not in seen_pairs:
            seen_pairs.add(key)
            deduped.append(g)
    terms = deduped

    protected = protected_spans(text)
    linked_terms_this_file = set()  # only first occurrence per term text, across all target candidates

    def already_links_to(wikitarget: str) -> bool:
        # If the file already contains a [[wikitarget...]] link anywhere (from this run
        # or a previous one), don't add another link to the same target/anchor. This is
        # what makes re-running the script idempotent even when a term appears with
        # different casing/wording at different points in the file.
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
        # extend protected spans to cover the newly inserted link (shift later spans)
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
    Used only to compute similarity scores — never used for the actual
    auto-applied linking in pass 1, which matches on exact original text."""
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
    # Containment: what fraction of a's own words appear in b. Symmetric
    # measures (ratio, jaccard) unfairly punish a short, precise phrase (e.g.
    # a Topic List subtopic) being checked against a much longer, descriptive
    # heading it's fully covered by (e.g. "Stable functions" against "Stable
    # functions: continuity alone isn't enough") — the extra length in b dilutes
    # both ratio and jaccard even though every word of a is right there in b.
    # Guarded by a minimum normalized length so a lone short/numeric token
    # (e.g. a stray "1" or "4" picked up from a "§7.1.4"-style section number)
    # can't trivially claim containment=1.0 against any heading that happens
    # to contain that same digit.
    containment = len(aset & bset) / len(aset) if aset and len(na) >= 6 else 0.0
    return max(ratio, jaccard, containment)


def tokenize_with_offsets(text: str):
    return [(m.group(0), m.start(), m.end()) for m in re.finditer(r"\w+", text)]


def fuzzy_suggestions(source_stem: str, text: str, glossary, threshold: float, max_suggestions: int):
    """Advisory-only pass: find word-windows in `text` whose normalized form is
    similar-but-not-identical to a glossary term belonging to a different
    article. Returns a list of (score, matched_phrase, GlossaryEntry), sorted
    by descending score, with overlapping candidate windows deduplicated by
    keeping the highest-scoring one. Never modifies `text`."""
    protected = protected_spans(text)  # includes pass-1's newly inserted links
    tokens = tokenize_with_offsets(text)
    terms = [g for g in glossary if g.target != source_stem]

    raw = []
    for g in terms:
        k = len(g.term.split())
        for window_size in sorted({max(1, k - 1), k, k + 1}):
            for i in range(len(tokens) - window_size + 1):
                start, end = tokens[i][1], tokens[i + window_size - 1][2]
                if overlaps(start, end, protected):
                    continue
                phrase = text[start:end]
                # Skip near-identical text — that's pass 1's job, not a "suggestion".
                if phrase.strip().lower() == g.term.strip().lower():
                    continue
                score = similarity(phrase, g.term)
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


def find_matching_article(topic_text: str, stems: list, stem_headings: dict = None):
    """Given a Topic List entry's text, find the generated article (by filename
    stem) it corresponds to. Tries, in order: exact slug match; a
    collision-disambiguated variant (e.g. 'Beta-Reduction-(Theory-of-Expressions)'
    for a plain 'Beta Reduction' entry); then a similarity-based fallback
    (reusing pass 2's scoring) for wording drift between the guidelines and
    the article actually generated for it. The fallback checks each candidate
    article's own title AND its section headings (via stem_headings) — a
    subtopic phrase usually echoes a heading inside its true parent article
    more closely than that article's overall title, and without checking
    headings too, a short subtopic can spuriously out-score its own parent
    against an unrelated sibling article whose *title* happens to share more
    surface words. Returns (target, match_tier) where match_tier is 'exact',
    'collision', or 'fuzzy', or (None, None) if nothing matches at all."""
    slug = slugify(topic_text)
    if slug in stems:
        return slug, "exact"
    prefix = slug + "-("
    for s in stems:
        if s.startswith(prefix):
            return s, "collision"
    stem_headings = stem_headings or {}
    best, best_score = None, 0.0
    for s in stems:
        score = similarity(topic_text, slug_title(s))
        for heading in stem_headings.get(s, []):
            heading_score = similarity(topic_text, heading)
            if heading_score > score:
                score = heading_score
        if score > best_score:
            best_score, best = score, s
    if best_score >= 0.55:
        return best, "fuzzy"
    return None, None


WIKI_ENTRY_RE = re.compile(r"^\[\[([^|\]]+)\|([^\]]+)\]\]$")


def update_guidelines_links(vault_folder: str, stems: list, dry_run: bool, stem_headings: dict = None):
    """Wrap each Topic List entry (both levels) in book-guidelines.md with a
    wikilink to its matching generated article, if one exists. Only the
    Topic List section is touched — Header and Chapter Summaries are left
    completely alone.

    Every entry is re-evaluated on every run, linked or not — this is still
    effectively idempotent for the steady-state case (a stable exact/collision
    match re-resolves to itself and the line doesn't change), but it also lets
    an entry that was only fuzzy-matched to a *different* article (e.g. a
    subtopic that fell back to linking its parent category because its own
    dedicated article didn't exist yet) get upgraded to a precise exact/
    collision match once that dedicated article shows up in a later run.
    A fuzzy match is only ever replaced by an exact/collision-tier match, never
    by a different fuzzy match — that would risk unstable flip-flopping
    between two similarly-scored candidates on successive runs. Returns
    (path_or_None, entries_changed, topic_list_text_after)."""
    path = os.path.join(vault_folder, "book-guidelines.md")
    if not os.path.exists(path):
        return None, 0, ""

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    section_match = TOPIC_LIST_SECTION_RE.search(text)
    if not section_match:
        return path, 0, ""

    section_start, section_end = section_match.span(1)
    section_text = text[section_start:section_end]

    entries_changed = 0

    def resolve_entry(prefix: str, entry_text: str, suffix: str) -> str:
        nonlocal entries_changed
        wiki = WIKI_ENTRY_RE.match(entry_text.strip())
        if wiki:
            existing_target, display_text = wiki.group(1), wiki.group(2)
            new_target, tier = find_matching_article(display_text, stems, stem_headings)
            if new_target and tier in ("exact", "collision") and new_target != existing_target:
                entries_changed += 1
                return f"{prefix}[[{new_target}|{display_text}]]{suffix}"
            return prefix + entry_text + suffix  # leave as-is: stable, or only a fuzzy alternative exists
        new_target, _tier = find_matching_article(entry_text, stems, stem_headings)
        if new_target:
            entries_changed += 1
            return f"{prefix}[[{new_target}|{entry_text}]]{suffix}"
        return prefix + entry_text + suffix

    def process_line(line: str) -> str:
        m = TOP_LEVEL_LINE_RE.match(line)
        if m:
            return resolve_entry(m.group(1), m.group(2), m.group(3))
        m2 = SUBTOPIC_LINE_RE.match(line)
        if m2:
            return resolve_entry(m2.group(1), m2.group(2), m2.group(3))
        return line

    new_section_text = "\n".join(process_line(l) for l in section_text.split("\n"))

    if new_section_text != section_text and not dry_run:
        new_text = text[:section_start] + new_section_text + text[section_end:]
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_text)

    return path, entries_changed, new_section_text


def extract_book_title(guidelines_text: str, fallback_folder_name: str) -> str:
    m = TITLE_FIELD_RE.search(guidelines_text)
    if m:
        return m.group(1).strip()
    return fallback_folder_name.replace("-", " ").replace("_", " ")


def build_index(vault_folder: str, folder_name: str, book_title: str, topic_list_text: str, dry_run: bool):
    """Fully (re)generate 'index.md' from the (already-linked)
    Topic List content. Being entirely derived from book-guidelines.md, this is
    just rewritten each run rather than incrementally merged — cheap, and
    guaranteed to stay in sync. Returns (path, changed: bool)."""
    index_path = os.path.join(vault_folder, "index.md")
    content = (
        f"# {book_title} — Index\n\n"
        f"[[book-guidelines|↩ Back to guidelines]]\n\n"
        f"{topic_list_text.strip(chr(10))}\n"
    )
    old_content = None
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            old_content = f.read()
    changed = content != old_content
    if changed and not dry_run:
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(content)
    return index_path, changed


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", help="vaults/[book] folder containing the generated articles")
    ap.add_argument("--dry-run", action="store_true", help="report changes without writing files")
    ap.add_argument("--verbose", action="store_true", help="print every link added, not just the totals")
    ap.add_argument("--no-fuzzy", action="store_true", help="skip pass 2 (similarity suggestions) entirely")
    ap.add_argument("--fuzzy-threshold", type=float, default=0.62,
                     help="minimum similarity score (0-1) for a pass-2 suggestion (default: 0.62)")
    ap.add_argument("--max-fuzzy", type=int, default=15,
                     help="max pass-2 suggestions to report per file (default: 15)")
    ap.add_argument("--no-guidelines-links", action="store_true",
                     help="skip pass 3's book-guidelines.md Topic List linking")
    ap.add_argument("--no-index", action="store_true",
                     help="skip pass 3's index.md (re)generation")
    args = ap.parse_args()

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
                suggestions = fuzzy_suggestions(stem, new_text, glossary, args.fuzzy_threshold, args.max_fuzzy)
                if suggestions:
                    total_suggestions += len(suggestions)
                    print(f"\n{os.path.basename(path)}: {len(suggestions)} possible related mention(s) — NOT auto-linked, review and add confirmed ones to .crosslink-glossary.md:")
                    for score, phrase, g in suggestions:
                        print(f"    \"{phrase}\" ~ \"{g.term}\"  (score {score:.2f})  -> would be [[{g.wikitarget()}]]")

    print(f"\n{'(dry run) ' if args.dry_run else ''}Pass 1/2: {total_links_added} link(s) added across {total_files_changed} file(s), "
          f"{total_suggestions} similarity suggestion(s) surfaced for review, out of {len(articles)} article(s) scanned.")

    # Pass 3: guidelines Topic List linking + Index assembly
    if not args.no_guidelines_links:
        gl_path, gl_links_added, topic_list_text = update_guidelines_links(folder, stems, args.dry_run, stem_headings)
        if gl_path is None:
            print("\nPass 3: no book-guidelines.md found in this folder — skipping Topic List linking and Index.")
        else:
            print(f"\nPass 3: {gl_links_added} Topic List entr{'y' if gl_links_added == 1 else 'ies'} linked in book-guidelines.md.")
            if not args.no_index:
                with open(gl_path, "r", encoding="utf-8") as f:
                    guidelines_text = f.read()
                folder_name = os.path.basename(os.path.normpath(folder))
                book_title = extract_book_title(guidelines_text, folder_name)
                # Re-derive topic_list_text from the file on disk when not a dry run,
                # so the Index reflects what was actually written.
                if not args.dry_run:
                    section_match = TOPIC_LIST_SECTION_RE.search(guidelines_text)
                    topic_list_text = section_match.group(1) if section_match else topic_list_text
                index_path, index_changed = build_index(folder, folder_name, book_title, topic_list_text, args.dry_run)
                status = "updated" if index_changed else "already up to date"
                print(f"Pass 3: Index note {status} at {index_path}.")
    elif not args.no_index:
        print("\nPass 3: --no-guidelines-links also skips Index generation (Index is derived from the linked Topic List).")


if __name__ == "__main__":
    main()
