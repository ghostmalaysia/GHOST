import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.ai import providers
from core.ai.collaboration import collaborate
from core.ghost import ask_ghost, build_memory_context
from core.autonomy import permission_guard, tool_registry


class GhostFlowTests(unittest.TestCase):

    def test_chat_uses_configured_provider(self):
        with patch("core.ghost.ask", return_value="balasan") as mock_ask:
            answer = ask_ghost([{"role": "user", "content": "halo"}])

        self.assertEqual(answer, "balasan")
        self.assertEqual(mock_ask.call_args.args[0], "qwen")

    def test_chat_attaches_memory_as_untrusted_reference(self):
        context = '[{"source":"LOCAL","category":"general","content":"fakta"}]'
        with patch("core.ghost.ask", return_value="ok") as mock_ask:
            ask_ghost(
                [{"role": "user", "content": "soalan"}],
                memory_context=context,
            )

        sent = mock_ask.call_args.args[1]
        self.assertIn("[MEMORY REFERENCES", sent[0]["content"])
        self.assertIn("fakta", sent[0]["content"])
        self.assertEqual(sent[0]["content"].count("soalan"), 1)

    def test_chat_reports_provider_error(self):
        with patch("core.ghost.ask", side_effect=providers.ProviderError("rosak")):
            answer = ask_ghost([{"role": "user", "content": "halo"}])

        self.assertTrue(answer.startswith("AI error:"))

    def test_memory_context_drops_credentials(self):
        context = build_memory_context([
            {"source": "LOCAL", "category": "note", "content": "kopi hijau"},
            {"source": "LOCAL", "category": "secret", "content": "api_key=abcdef1234567890"},
        ])

        self.assertIn("kopi hijau", context)
        self.assertNotIn("abcdef1234567890", context)

    def test_memory_context_respects_budget(self):
        self.assertEqual(build_memory_context([{"content": "x" * 100}], 10), "")

    def test_collaboration_needs_two_providers(self):
        with self.assertRaises(ValueError):
            collaborate("tugas", ["qwen"])

    def test_collaboration_runs_draft_review_and_final(self):
        stages = []

        with patch(
            "core.ai.collaboration.ask",
            side_effect=lambda name, messages: "hasil-" + name,
        ) as mock_ask:
            result = collaborate(
                "tugas",
                ["qwen", "claude"],
                progress=stages.append,
            )

        self.assertEqual(result["draft"], "hasil-qwen")
        self.assertEqual(result["reviews"][0]["text"], "hasil-claude")
        self.assertEqual(result["final"], "hasil-qwen")
        self.assertEqual(mock_ask.call_count, 3)
        self.assertEqual(len(stages), 3)

    def test_provider_config_is_validated(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.json"
            path.write_text('{"providers": {}}', encoding="utf-8")
            with patch.object(providers, "_config_path", return_value=path):
                with self.assertRaises(providers.ProviderError):
                    providers.load_config()

    def test_policy_registry_works_without_generated_file(self):
        missing = Path(tempfile.gettempdir()) / "ghost-no-tool-knowledge.json"
        with patch.object(tool_registry, "KNOWLEDGE_FILE", missing):
            registry = tool_registry.load_knowledge()
            self.assertIn("uname", registry["tools"])

        with patch.object(permission_guard, "check_permission", return_value=True):
            result = permission_guard.evaluate_tool_request(
                "Inspect system information", "uname", "termux"
            )

        self.assertEqual(result["status"], "policy_passed_not_executed")
        self.assertFalse(result["execution_performed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
