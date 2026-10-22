# Codex capabilities

Use the filesystem, patch tools and connected sources actually exposed by the session. Create a Markdown file when no document editor is available; provide a clickable file link. Do not call Claude-specific `create_file` or `str_replace` tools unless they are really exposed.

For Reader Testing, use a fresh sub-agent without inherited conversation (for example `fork_turns="none"` when that option is available). Pass only the document, audience and reader questions. Ask it to answer questions, identify assumed knowledge, ambiguities and contradictions. Record the results and fix the document. This workflow authorizes reader delegation only; respect host restrictions.

Without an isolated reader capability, provide 5–10 questions and ask the user to open a new Codex or ChatGPT conversation containing only the document and those questions. Record user-returned results. Until then Reader Testing is NOT RUN; do not invent successful outcomes. Missing file access or unavailable connectors should produce a concrete fallback, not a nonexistent tool call.
