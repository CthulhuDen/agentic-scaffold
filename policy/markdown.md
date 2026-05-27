# Markdown conventions

These rules apply to all `.md` files in this repository. Documentation content rules live in
[`doc-quality.md`](doc-quality.md).

## Line wrapping

All `.md` files in this repository use a soft cap of 120 characters per line. Regular prose paragraphs must
be wrapped to respect this limit. Exceptions:

- **Code blocks** may exceed 120 characters when the code itself requires it.
- **Tables** may exceed the limit when a cell's content requires it. Table source is column-aligned by display
  width so pipe delimiters line up vertically: header and body cells use one leading and trailing space plus
  padding; separator cells use one leading and trailing space around a run of hyphens stretched to fill the column.
- **URLs** are kept on a single line, even if that exceeds the limit.

An inline code span (single backticks) may be wrapped across a line break: CommonMark converts any line ending
inside the span to a single space, so the rendered output matches the unwrapped form. Inside a list item, indent
the continuation line to the list-item content column so the wrap is parsed as part of the same span.

Wrap each line to 110–120 characters. A few characters early at a natural clause boundary is fine;
wrapping below 100 is not. When editing prose, re-flow the affected paragraph so the result respects this band —
do not leave short lines behind from prior wraps.

## Structure

Code blocks are for literal code, command syntax, or verbatim file content. Other content uses lists, tables,
or prose: a list of files with descriptions belongs in a list; a fixed set of values with labels belongs in
a table or a definition-style list.

## Cross-references

Whenever a Markdown document mentions another `.md` file, or a section within any `.md` file (including the
same document), the reference must be a real Markdown link — to the file path for a whole-document reference,
or to the section anchor for a section reference.

**Exception: `ROADMAP.md`.** The roadmap is an optional file that may not be present in the repository, and
mentions of it are always conceptual rather than navigation pointers. Plain backticks are used; a Markdown link
would dangle when the file is absent.

**Exception: skill names.** Skill mentions are never written as Markdown links to the skill's `SKILL.md`: a link
invites a Read of the file, and a mid-flow Read is the wrong mechanism for accessing a skill on any supported
harness, each of which exposes a native skill-invocation primitive instead. When agent instructions name a skill,
write the bare name in backticks (`` `skill-name` ``). When the mention carries invocation intent — i.e. the reader
is expected to invoke the skill at that point rather than merely recognize it — the surrounding prose must make that
intent explicit (for example, "invoke the `skill-name` skill before continuing").

## Headings

Section headings use AP-style Title Case: capitalize the first and last word and all nouns, verbs, adjectives,
adverbs, and pronouns; lowercase articles, coordinating conjunctions, and prepositions of three letters or fewer
(`and`, `or`, `the`, `of`, `in`, `to`, `by`, `on`, `for`). Hyphenated compounds capitalize both parts
(`Post-Allowlist Body`, `System-Prompt Addendum`). Code identifiers inside headings stay verbatim — backticks
preserve source casing.
