
import unittest
from unittest.mock import patch

from src.agent import (
    chat_with_agent,
    generate_final_answer,
    is_accessory_request,
    is_contact_question,
    is_generic_price_question,
    is_policy_question,
    answer_contact_question,
)

from src.policies import (
    find_phone_numbers,
    detect_phone_conflicts,
)


class TestEmporioAgent(unittest.TestCase):

    # Accessory detection

    def test_accessory_request(self):
        self.assertTrue(
            is_accessory_request("Do you sell guitar strings?")
        )

    def test_not_accessory_request(self):
        self.assertFalse(
            is_accessory_request("Do you sell guitars?")
        )

    def test_accessory_detection_word_boundary(self):
        self.assertFalse(
            is_accessory_request("I need a standard guitar.")
        )

    # Price detection

    def test_generic_price_question(self):
        self.assertTrue(
            is_generic_price_question("How much does a guitar cost?")
        )

    def test_specific_brand_price_question(self):
        self.assertFalse(
            is_generic_price_question("How much is a Fender guitar?")
        )

    # Policy detection

    def test_policy_question(self):
        self.assertTrue(
            is_policy_question("What are your opening hours?")
        )

    # Customer responses

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

    # Input validation

    def test_empty_message(self):
        response = chat_with_agent("")

        self.assertIn("enter a message", response.lower())

    def test_whitespace_message(self):
        response = chat_with_agent("   ")

        self.assertIn("enter a message", response.lower())

    def test_invalid_message_type(self):
        response = chat_with_agent(None)

        self.assertIn("valid text message", response.lower())

    # Ollama error handling

    @patch(
        "src.agent.ollama.chat",
        side_effect=Exception("Ollama unavailable")
    )
    def test_ollama_connection_error(self, mock_ollama):
        response = generate_final_answer([
            {"role": "user", "content": "Hello!"}
        ])

        self.assertIn("unable to generate", response.lower())
        mock_ollama.assert_called_once()

    # Order privacy

    @patch("src.agent.get_order_status")
    def test_order_response_does_not_expose_payment_or_total(
        self,
        mock_order,
    ):
        mock_order.return_value = {
            "order_id": "123",
            "status": "Shipped",
            "order_date": "2026-11-20",
            "total_brl": 500.00,
            "payment_method": "Credit Card",
            "tracking_code": "BR123456",
            "estimated_delivery": "2026-11-25",
        }

        response = chat_with_agent(
            "Please check order #123 for lucas@example.com"
        )

        self.assertIn("123", response)
        self.assertIn("shipped", response.lower())
        self.assertIn("br123456", response.lower())
        self.assertNotIn("500.00", response)
        self.assertNotIn("credit card", response.lower())

        mock_order.assert_called_once_with(
            "123",
            "lucas@example.com",
        )

    # Contact information detection

    def test_contact_question_detection(self):
        self.assertTrue(
            is_contact_question(
                "What is your store WhatsApp number?"
            )
        )

    @patch("src.agent.search_policies")
    def test_contact_question_does_not_reveal_conflicting_numbers(
        self,
        mock_search,
    ):
        mock_search.return_value = {
            "found": True,
            "results": [],
            "phone_conflicts": {
                "has_conflict": True,
                "numbers": [
                    "(67) 3341-4444",
                    "(67) 3321-4500",
                ],
            },
        }

        response = answer_contact_question()

        self.assertIn("conflicting", response.lower())
        self.assertNotIn("3341-4444", response)
        self.assertNotIn("3321-4500", response)

    @patch("src.agent.search_policies")
    def test_contact_question_with_one_verified_number(
        self,
        mock_search,
    ):
        mock_search.return_value = {
            "found": True,
            "results": [],
            "phone_conflicts": {
                "has_conflict": False,
                "numbers": ["(67) 3341-4444"],
            },
        }

        response = answer_contact_question()

        self.assertIn("(67) 3341-4444", response)
        self.assertNotIn("conflicting", response.lower())

    @patch(
        "src.agent.search_policies",
        side_effect=Exception("PDF unavailable"),
    )
    def test_contact_question_handles_pdf_error(
        self,
        mock_search,
    ):
        response = answer_contact_question()

        self.assertIn("unable to verify", response.lower())
        self.assertNotIn("3341-4444", response)
        self.assertNotIn("3321-4500", response)

    # Phone number audit

    def test_phone_conflict_detection(self):
        pages = [
            {
                "page": 1,
                "content": "Phone: (67) 3341-4444",
            },
            {
                "page": 6,
                "content": "WhatsApp: (67) 3321-4500",
            },
        ]

        result = detect_phone_conflicts(pages)

        self.assertTrue(result["has_conflict"])
        self.assertEqual(len(result["numbers"]), 2)

    def test_single_phone_number_no_conflict(self):
        pages = [
            {
                "page": 1,
                "content": "Phone: (67) 3341-4444",
            },
        ]

        result = detect_phone_conflicts(pages)

        self.assertFalse(result["has_conflict"])
        self.assertEqual(len(result["numbers"]), 1)

    # LLM integration

    @patch("src.agent.generate_final_answer")
    def test_general_question_uses_llm(self, mock_llm):
        mock_llm.return_value = "Hello! How can I help you?"

        response = chat_with_agent("Hello!")

        self.assertEqual(response, "Hello! How can I help you?")
        mock_llm.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
