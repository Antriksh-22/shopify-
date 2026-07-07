import base64
import hashlib
import hmac
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from shopify_ai_automation.shopify import verify_shopify_hmac


class ShopifyWebhookTests(unittest.TestCase):
    def test_verifies_hmac(self) -> None:
        body = b'{"id": 123}'
        secret = "test-secret"
        digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
        signature = base64.b64encode(digest).decode("utf-8")

        self.assertTrue(verify_shopify_hmac(body, signature, secret))
        self.assertFalse(verify_shopify_hmac(body, "bad-signature", secret))


if __name__ == "__main__":
    unittest.main()
