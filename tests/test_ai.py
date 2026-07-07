from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from shopify_ai_automation.ai import parse_json_object


class AIParsingTests(unittest.TestCase):
    def test_parses_fenced_json(self) -> None:
        parsed = parse_json_object('```json\n{"confidence": 0.9, "risk": "normal"}\n```')

        self.assertEqual(parsed["confidence"], 0.9)
        self.assertEqual(parsed["risk"], "normal")

    def test_parses_json_with_surrounding_text(self) -> None:
        parsed = parse_json_object('Here is the result: {"summary_style": "empathetic"} Thanks.')

        self.assertEqual(parsed["summary_style"], "empathetic")


if __name__ == "__main__":
    unittest.main()
