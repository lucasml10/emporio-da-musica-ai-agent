import unittest
from unittest.mock import patch

from src.agent import (
    chat_with_agent,
    is_accessory_request,
    is_generic_price_question,
    is_policy_question,
)


class TestEmporioAgent(unittest.TestCase):

    def test_accessory_request(self):
        self.assertTrue(
            is_accessory_request("Do you sell guitar strings?")
        )

    def test_not_accessory_request(self):
        self.assertFalse(
            is_accessory_request("Do you sell guitars?")
        )

    def test_generic_price_question(self):
        self.assertTrue(
            is_generic_price_question("How much does a guitar cost?")
        )

    def test_specific_brand_price_question(self):
        self.assertFalse(
            is_generic_price_question("How much is a Fender guitar?")
        )

    def test_policy_question(self):
        self.assertTrue(
            is_policy_question("What are your opening hours?")
        )

    def test_accessory_response(self):
        response = chat_with_agent("Do you sell guitar strings?")

        self.assertIn("do not", response.lower())
        self.assertIn("accessories", response.lower())

    def test_generic_price_response(self):
        response = chat_with_agent("How much does a guitar cost?")

        self.assertIn("electric", response.lower())
        self.assertIn("acoustic", response.lower())

    def test_order_requires_email(self):
        response = chat_with_agent("I want to check order #1")

        self.assertIn("email address", response.lower())

    @patch("src.agent.generate_final_answer")
    def test_general_question_uses_llm(self, mock_llm):
        mock_llm.return_value = "Hello! How can I help you?"

        response = chat_with_agent("Hello!")

        self.assertEqual(response, "Hello! How can I help you?")
        mock_llm.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)