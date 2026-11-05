---
name: hackmd-note-writer
description: Convert the current technical conversation, supplied notes, or source material into a complete HackMD-compatible Markdown note. Use when the user asks to整理討論、建立 HackMD 筆記、輸出可直接貼入 HackMD 的 Markdown、使用 HackMD 原生 [TOC] 目錄，或加入 HackMD tags。 Do not use for ordinary short answers, isolated wording edits, or summaries that are not intended as a reusable HackMD note.
---

# HackMD note generation workflow

Create one complete HackMD note that can be pasted directly into HackMD without removing wrapper text.

## 1. Resolve the source scope

1. Determine what content belongs in the note:
   - If the user says「以上討論」, use the relevant discussion in the current conversation.
   - If the user names a starting point, begin from that point.
   - If the user specifies a range of discussion topics, include only that range.
   - If the user supplies text or files, use those materials.
2. Treat a HackMD URL as the intended destination or context unless the user explicitly asks to read or update the page and the required tool is available.
3. Do not invent missing technical facts.
4. Preserve important corrections, distinctions, examples, limitations, and conclusions.
5. Account for every substantive source unit. A unit may appear in the synthesized main text or in a preservation appendix, but it must not disappear merely because it does not fit a topic cluster.
6. Omit only exact semantic duplicates and pure conversational scaffolding such as greetings, acknowledgements, or coordination messages. Preserve false starts, side observations, and meta-discussion when they contain technical meaning, an unresolved concern, or useful context.

## 2. Synthesize the source by topic

Before drafting the note, reorganize the source material semantically. Do not use the conversation order as the default chapter order.

1. Break the source into atomic content units:
   - questions
   - definitions
   - claims
   - corrections
   - examples
   - problems
   - solutions
   - decisions
   - limitations

2. Group related units into topic clusters according to:
   - the same subject
   - the same technical concept
   - the same problem or failure mode
   - the same mechanism
   - the same solution
   - the same implementation concern

3. Merge related points even when they appeared far apart in the conversation.

4. Separate unrelated topics even when they appeared next to each other in the conversation.

5. Remove repeated questions and explanations. Keep the most complete and accurate version.

6. When a later discussion corrects an earlier explanation:
   - use the corrected explanation as the main conclusion;
   - preserve any substantive earlier explanation in the preservation appendix when it is not useful in the main text, and label it as superseded or corrected;
   - do not present both explanations as equally correct.

7. Give every atomic content unit one disposition:
   - `main`: integrated into a topic cluster;
   - `appendix-unclassified`: substantive but not naturally classifiable;
   - `appendix-unresolved`: an open question, tentative idea, or incomplete line of reasoning;
   - `appendix-superseded`: corrected or rejected material retained for completeness;
   - `omit`: only an exact semantic duplicate or pure conversational scaffolding.

8. Give every core concept one canonical location in the note. Refer back to that chapter instead of explaining the same concept repeatedly.

9. Arrange the topic clusters according to conceptual dependency and learning order:

   Purpose or problem
   → prerequisites
   → core concepts
   → architecture or workflow
   → detailed mechanisms
   → failure modes and misconceptions
   → solutions
   → examples
   → advantages and limitations
   → implementation
   → summary

10. Preserve chronological order only when chronology is technically meaningful, such as:
   - debugging history
   - event sequences
   - protocol exchanges
   - state transitions
   - step-by-step procedures

11. Do not use conversation-oriented chapter names such as:
    - Question 1
    - Follow-up question
    - Next discussion
    - Additional question
    - Later correction

    Name chapters after the technical subject they explain.

Before writing, internally create a topic map with these fields:

| Source unit | Topic cluster | Disposition | Duplicates | Corrections | Dependencies |
|---|---|---|---|---|---|

Use this topic map as a coverage ledger and to construct the document outline. Before drafting, verify that every substantive source unit has a `main` or `appendix-*` disposition. Do not include the topic map in the final note unless the user requests it.

## 3. Preserve material outside the synthesis

Keep the main chapters concise and topic-oriented, then add preservation appendices near the end of the note when needed.

1. Use `## Preserved discussion` as the major appendix heading. Create only the applicable subsections:
   - `### Unclassified but substantive points`
   - `### Open questions and incomplete threads`
   - `### Superseded or corrected points`
2. Preserve the source order within each subsection unless another order is necessary for comprehension.
3. Use faithful paraphrases by default. Retain the original wording as a short quotation when paraphrasing could change its nuance.
4. Add enough context for each item to remain understandable on its own.
5. Clearly mark uncertainty and the reason an item was not integrated into the main synthesis.
6. Do not create this appendix when every substantive unit is already represented in the main chapters.
7. Treat the appendix as a lossless semantic fallback, not as a transcript dump: exact duplicates and content-free conversational scaffolding still need not be copied.

## 4. Plan the heading hierarchy

Build the heading hierarchy from the synthesized topic map, not from the order in which messages appeared.

- Use exactly one level-1 heading (`#`) for the document title.
- Use level-2 headings (`##`) for major topic clusters.
- Use level-3 headings (`###`) for concepts within a cluster.
- Use level-4 headings (`####`) only when a level-3 subsection genuinely needs another layer.
- Combine small, closely related topic clusters into one major chapter.
- Split a topic cluster only when it contains multiple independently useful concepts.
- Arrange prerequisite concepts before mechanisms that depend on them.
- Place examples after the concepts they demonstrate.
- Place misconceptions and corrections next to the corresponding concept.
- Never preserve the source conversation's chapter order merely because it appeared first.
- Never skip a heading level.

## 5. Use HackMD native TOC syntax

Immediately after the level-1 title, add the exact standalone line:

```markdown
[TOC]
```

Recommended opening structure:

```markdown
# Document title

[TOC]

---
```

Rules:

- Use HackMD's native `[TOC]` directive.
- Do not create a `## TOC` heading.
- Do not manually write a list of TOC links.
- Do not manually calculate heading anchors.
- Let HackMD generate and update the table of contents from the heading hierarchy.

## 6. Write the note

1. Explain ideas progressively from foundational concepts to implementation details.
2. Preserve technical names, function names, commands, register addresses, and code identifiers exactly.
3. Use tables for comparisons.
4. Use numbered steps for procedures.
5. Use Mermaid diagrams only when they clarify architecture, workflow, state transitions, or data flow.
6. Preserve useful examples, but label hypothetical examples clearly.
7. Distinguish confirmed facts, reasoned inferences, and unverified assumptions.
8. Do not present inferred documentation as authoritative.
9. Include source links in a `## References` chapter only when they materially support the note.
10. Do not include ChatGPT writing-block wrappers, citation control tokens, generated element IDs, or UI-specific syntax.

### Format mathematical expressions with MathJax

1. Detect explicit mathematical relationships such as equations, inequalities, functions, sets, probabilities, indexed variables, sums, and integrals, and express them with HackMD-compatible MathJax using LaTeX syntax.
2. Use `$...$` for a short expression embedded in prose, such as `$E=mc^2$`.
3. Use `$$...$$` for an expression that needs its own line or is part of a derivation. Put the opening and closing `$$` delimiters on separate lines.
4. Do not put spaces immediately inside inline math delimiters. Write `$x+y$`, not `$ x+y $`.
5. Preserve the source meaning. When a mathematical relationship is ambiguous or incomplete, keep the original wording and do not invent a formula.
6. Do not convert source code, technical identifiers, shell variables, currency amounts, or isolated units into MathJax merely because they contain symbols or numbers.

## 7. Format internal code blocks

1. Use triple-backtick fences for code blocks inside the note.
2. Add a language identifier whenever known:
   - `cpp`
   - `c`
   - `python`
   - `bash`
   - `powershell`
   - `json`
   - `yaml`
   - `toml`
   - `markdown`
   - `mermaid`
   - `text`
3. Use `text` for directory trees, conceptual flows, and terminal-neutral examples.
4. Ensure every code fence is closed.
5. Keep the raw note free of a document-wide outer code fence. Add the delivery wrapper only after validation, as described in sections 8 and 9.

## 8. Use HackMD native tags syntax

The final non-empty line must use this format:

```markdown
###### tags: `Codex` `Skill` `HackMD`
```

Rules:

- Use exactly six `#` characters followed by `tags:`.
- Keep all tags on the same line.
- Put every tag inside inline-code backticks.
- Do not prefix individual tag names with `#`.
- Do not create a `## TAG` heading.
- Do not add headings, prose, separators, or blank content after the tags line.

## 9. Return Markdown in a copyable code block

Return the complete note inside one outer Markdown code fence so the user can copy the raw Markdown from the UI.

Use at least four backticks for the outer fence because the note may contain ordinary triple-backtick code fences:

~~~text
````markdown
# Document title

[TOC]

---

## 1. First chapter

```cpp
int value = 1;
```

---

###### tags: `Tag1` `Tag2`
````
~~~

Rules:

- Put the complete note inside one outer code fence.
- Add `markdown` as the outer fence language.
- Use four backticks for the outer fence when internal code blocks use three backticks.
- If the note contains four consecutive backticks, choose an even longer outer fence.
- Do not add explanatory prose before or after the outer code fence.
- The first line inside the outer fence must be the level-1 document title.
- The final non-empty line inside the outer fence must be the HackMD tags line.
- The code-block copy button should copy only the Markdown content, without the outer fence.

## 10. Validate the output

When filesystem and Python execution are available:

1. Save the drafted raw Markdown to a temporary `.md` file without the outer code fence.
2. Run:

```bash
python scripts/validate_hackmd_note.py <note-file>
```

3. Correct every reported error.
4. Run the validator again.
5. After validation succeeds, wrap the validated Markdown in one outer code fence for the final response.
6. Use at least four backticks for the outer fence and specify `markdown` as its language.

The temporary file passed to the validator must contain only the raw HackMD note. It must not contain the outer code fence or any explanatory prose.

If the note contains four or more consecutive backticks, use an outer fence longer than every backtick sequence appearing inside the note.

If scripts cannot be executed:

1. Manually verify the raw Markdown using the checklist in `references/hackmd-style-guide.md`.
2. Correct every detected issue.
3. Wrap the verified Markdown in the outer code fence only after manual verification is complete.

## 11. Final quality checklist

### Semantic organization

- The chapters are organized by topic rather than conversation order.
- Related points from different parts of the source were merged.
- Adjacent but unrelated discussions were separated.
- Repeated questions and explanations were deduplicated.
- Later corrections replaced earlier incorrect explanations.
- Every substantive source unit appears in the main synthesis or a preservation appendix.
- Unclassified, unresolved, and superseded substantive content was retained and clearly labeled.
- Only exact semantic duplicates and pure conversational scaffolding were omitted.
- Each core concept has one canonical chapter.
- Examples appear after the concepts they demonstrate.
- Chronological order is used only when event order is technically meaningful.
- Chapter titles describe technical subjects rather than conversation stages.

Before returning the note, confirm:

- The raw note passed automated validation, or was manually verified when the validator was unavailable.
- The complete note is wrapped in exactly one outer Markdown code fence.
- The outer code fence specifies `markdown` as its language.
- The outer fence is longer than every code fence used inside the note.
- No explanatory prose appears before or after the outer code fence.
- The first non-empty line inside the outer fence is the level-1 document title.
- There is exactly one `#` document title.
- Major chapters use `##`.
- Subsections use `###`.
- No heading-level jumps exist.
- `[TOC]` is the first non-empty content line after the title.
- There is no `## TOC` heading or manually written TOC list.
- Internal code blocks use triple backticks and language identifiers whenever the language is known.
- Every internal code fence is properly closed.
- The final non-empty line inside the outer fence matches `###### tags: \`Tag1\` \`Tag2\``.
- There is no `## TAG` heading.
- No prose, heading, separator, or blank content appears after the tags line inside the outer fence.
