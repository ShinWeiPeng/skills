# Claude capabilities

In Claude Code, use its exposed file read/write/edit and connector tools. In Claude web or desktop, use artifacts and connectors only when available; otherwise draft Markdown and provide the content or an accessible file. Tool availability varies by session.

For Reader Testing, use a fresh isolated Claude sub-agent if supported and authorized. Give it only the document, audience and reader questions, without inherited authoring context. Check answers, assumed knowledge, ambiguities and contradictions; record results and iterate.

If no isolated reader is available, give the user 5–10 questions and instructions to start a fresh Claude conversation at https://claude.ai with only the document and questions. Ask for its answers and blind spots. Mark Reader Testing NOT RUN until results return. Never substitute same-context self-review for an independent reader, and never report unavailable tools or connector access as successful.
