# HackMD note style guide

## 1. Output format

Treat the output as two layers:

1. The raw HackMD note used for validation.
2. The final response wrapper used to expose a copy button in the UI.

The raw note must begin with:

```markdown
# Document title
```

and end with:

```markdown
###### tags: `Tag1` `Tag2`
```

Do not include an outer code fence in the raw note passed to the validator.

After validation succeeds, wrap the complete raw note in one outer Markdown code fence:

~~~text
````markdown
# Document title

[TOC]

...

###### tags: `Tag1` `Tag2`
````
~~~

Use at least four backticks so triple-backtick code blocks can remain inside the note. If the note contains a longer backtick sequence, make the outer fence longer than every sequence inside it. Do not add explanatory prose outside the outer fence. The UI copy button should copy the raw note without the wrapper.

---

## 2. Native HackMD directives

Use HackMD's built-in syntax:

```markdown
[TOC]
```

and:

```markdown
###### tags: `Tag1` `Tag2`
```

Do not manually generate TOC links, anchors, or a separate TAG chapter.

---

## 3. Heading hierarchy

Use this hierarchy:

```text
# Document title

[TOC]

## 1. Major chapter
### 1.1 Subsection
#### 1.1.1 Detail
## 2. Major chapter

###### tags: `Tag1` `Tag2`
```

Rules:

- Exactly one level-1 heading is allowed.
- The title is the only level-1 heading.
- Major chapters use `##`.
- Subsections use `###`.
- Use `####` only beneath a `###` subsection.
- Do not skip heading levels.
- Do not create `## TOC` or `## TAG`.
- The `###### tags:` line is HackMD metadata and is excluded from normal heading hierarchy checks.

---

## 4. Native TOC rules

The exact standalone line:

```markdown
[TOC]
```

must be the first non-empty content line after the document title.

Rules:

- Use only one `[TOC]` directive.
- Do not add a `## TOC` heading.
- Do not write manual entries such as `[Chapter](#chapter)`.
- Do not calculate anchors.
- HackMD automatically builds the TOC from headings.

---

## 5. Native tags rules

The final non-empty line must follow this form:

```markdown
###### tags: `Codex` `Skill` `HackMD`
```

Rules:

- Use exactly six `#` characters.
- Use the lowercase keyword `tags:`.
- Keep tags on the same line.
- Wrap every tag in inline-code backticks.
- Write `Codex`, not `#Codex`.
- Use at least one tag.
- Do not create a `## TAG` heading.
- Do not place content after the tags line.

---

## 6. Code fences

Code examples inside the raw note may use triple-backtick fences.

Rules:

- add a language label when known;
- use `text` for conceptual diagrams or directory trees;
- close every fence;
- keep the raw note free of a document-wide outer fence during validation;
- add the longer delivery fence only after validation succeeds.

Do not add generated attributes such as:

```text
id="abc123"
```

---

## 7. Technical accuracy

Preserve exact technical identifiers:

```text
WritePrivateProtocolTask
heap_caps_free
0x6040
memory_order_seq_cst
```

Distinguish:

- **Fact**: directly supported by source material;
- **Inference**: reasoned interpretation;
- **Unverified**: plausible but not confirmed.

---

## 8. Manual validation checklist

Validate the raw note before adding the delivery wrapper:

- [ ] Raw Markdown only
- [ ] No opening outer code fence in the raw note
- [ ] No closing outer code fence in the raw note
- [ ] Exactly one `#` document title
- [ ] `[TOC]` is the first non-empty line after the title
- [ ] Only one `[TOC]` directive exists
- [ ] No `## TOC` heading exists
- [ ] No manual TOC link list exists
- [ ] Major chapters use `##`
- [ ] Subsections use `###`
- [ ] No heading-level jumps
- [ ] Internal code fences are balanced
- [ ] Internal code fences have language labels
- [ ] Final non-empty line uses `###### tags:`
- [ ] Every tag uses inline-code backticks
- [ ] Tags do not start with `#`
- [ ] No `## TAG` heading exists
- [ ] No content appears after the tags line

Then validate the final response:

- [ ] The complete raw note is wrapped in exactly one outer code fence
- [ ] The outer fence specifies `markdown` as its language
- [ ] The outer fence is longer than every backtick sequence inside the note
- [ ] No explanatory prose appears before or after the outer fence
- [ ] The title is the first non-empty line inside the outer fence
- [ ] The tags line is the final non-empty line inside the outer fence
