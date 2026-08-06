from __future__ import annotations

import json
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = PLUGIN_ROOT / "skills"
CONTRACT = (
    SKILLS_ROOT
    / "ask-matt"
    / "references"
    / "decision-question-contract.md"
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class DecisionQuestionContractTests(unittest.TestCase):
    def test_automatic_engineering_entry_loads_the_shared_contract(self) -> None:
        ask_matt = read(SKILLS_ROOT / "ask-matt" / "SKILL.md")
        contract = read(CONTRACT)

        self.assertIn("references/decision-question-contract.md", ask_matt)
        self.assertIn("every governed engineering workflow", contract)
        for phrase in (
            "two or three",
            "structured choice tool",
            "numbered text",
            "one decision question at a time",
            "free-form",
            "observable result",
            "benefits",
            "disadvantages",
            "risks",
            "costs",
            "constraints",
            "downstream consequences",
            "suitable",
            "unsuitable",
        ):
            self.assertIn(phrase, contract)

    def test_interview_entrypoints_reinforce_the_shared_contract(self) -> None:
        for skill in ("grilling", "grill-me", "grill-with-docs"):
            text = read(SKILLS_ROOT / skill / "SKILL.md")
            self.assertIn(
                "decision-question-contract.md",
                text,
                msg=skill,
            )

    def test_default_mode_uses_numbered_fallback_instead_of_stopping(self) -> None:
        for skill in (
            "clarify-improvement-proposals",
            "govern-modular-event-architecture",
        ):
            text = read(SKILLS_ROOT / skill / "SKILL.md")
            folded = text.casefold()
            self.assertIn("numbered text", folded, msg=skill)
            self.assertNotIn(
                "do not replace it with markdown questions",
                folded,
                msg=skill,
            )
            self.assertNotIn(
                "tell the user to switch with `/plan` or `shift+tab`, then stop",
                folded,
                msg=skill,
            )

    def test_repository_decisions_require_turn_boundary_grilling_handoff(self) -> None:
        for skill in (
            "ask-matt",
            "explain-code-flow",
            "clarify-improvement-proposals",
        ):
            text = read(SKILLS_ROOT / skill / "SKILL.md")
            normalized = " ".join(text.split())
            self.assertIn("has_unresolved_decision=true", text, msg=skill)
            self.assertIn("selected_skill=grilling", text, msg=skill)
            self.assertIn("spec-governance.reconcile", text, msg=skill)
            self.assertIn("if and only if", normalized, msg=skill)
            self.assertIn("short or numeric answers", normalized, msg=skill)
            self.assertIn("no open decisions", normalized, msg=skill)
            self.assertIn("resume target", normalized, msg=skill)

        explain = read(SKILLS_ROOT / "explain-code-flow" / "SKILL.md")
        clarify = read(
            SKILLS_ROOT / "clarify-improvement-proposals" / "SKILL.md"
        )
        self.assertIn("stop before presenting the options", explain)
        self.assertIn("hand off before showing the options", clarify)

    def test_contract_preserves_free_form_and_authorization_boundaries(self) -> None:
        contract = read(CONTRACT)
        ask_matt = read(SKILLS_ROOT / "ask-matt" / "SKILL.md")

        self.assertIn("combined", contract)
        self.assertIn("premise-correcting", contract)
        self.assertIn("開始執行", contract)
        self.assertIn("native system permission", contract)
        self.assertIn("`開始執行`", ask_matt)

    def test_plugin_entry_metadata_advertises_cross_mode_choices(self) -> None:
        manifest = json.loads(
            read(PLUGIN_ROOT / ".codex-plugin" / "plugin.json")
        )
        default_prompt = "\n".join(manifest["interface"]["defaultPrompt"])

        self.assertIn("two or three", default_prompt)
        self.assertIn("numbered text", default_prompt)
        self.assertIn("Reassess every user turn", default_prompt)
        self.assertIn("unresolved-decision", default_prompt)


if __name__ == "__main__":
    unittest.main()
