from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from shopify_ai_automation.orchestrator import run_sample_order


class AutomationOrchestratorTests(unittest.TestCase):
    def test_sample_order_generates_multi_agent_actions(self) -> None:
        result = run_sample_order(Path("samples"))
        action_types = {action.action_type for action in result.actions}

        self.assertIn("draft_reply", action_types)
        self.assertIn("inventory_alert", action_types)
        self.assertIn("marketing_offer", action_types)
        self.assertGreaterEqual(result.estimated_savings_minutes, 15)


if __name__ == "__main__":
    unittest.main()
