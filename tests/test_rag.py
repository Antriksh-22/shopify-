from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from shopify_ai_automation.rag import LocalKnowledgeBase


class LocalKnowledgeBaseTests(unittest.TestCase):
    def test_retrieves_relevant_policy(self) -> None:
        kb = LocalKnowledgeBase.from_markdown(Path("samples/policies.md"))
        results = kb.search("damaged item refund replacement")

        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0].title, "Returns And Refunds")


if __name__ == "__main__":
    unittest.main()
