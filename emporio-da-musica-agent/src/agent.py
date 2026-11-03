import re
import ollama

from src.tools import (
    search_products,
    get_product_details,
    get_active_promotions,
    get_order_status,
)
from src.policies import search_policies


MODEL_NAME = "qwen2.5:3b"


SYSTEM_PROMPT = """
You are the virtual customer service assistant of Empório da Música,
a musical instrument store located in Campo Grande, Brazil.

Always respond in English.
Be friendly, professional, clear and helpful.

IMPORTANT RULES:
- Never invent prices, stock, promotions or order information.
- Use verified store data for products, prices, stock and orders.
- If verified information is unavailable, say so.
- Order verification requires only the order ID and registered email.
- Never request the customer's full name or order date.
- Do not expose unnecessary customer information.
- The store sells musical instruments, not accessories.
- Never invent store policies.
- Use only the information provided by the application.
- If policies are ambiguous or conflicting, explain this and
  recommend contacting store management.
"""


# Terms that identify accessories or supplies, not instruments.
# Check these before product search so "guitar strings" is not
# mistakenly interpreted as a request for guitars.
ACCESSORY_TERMS = [
    "guitar string", "guitar strings", "strings for guitar",
    "bass strings", "piano strings",
    "pick", "picks", "guitar pick", "guitar picks",
    "plectrum", "plectrums",
    "cable", "cables", "instrument cable",
    "strap", "straps", "guitar strap",
    "tuner", "tuners", "metronome",
    "capo", "capos",
    "stand", "stands", "instrument stand",
    "case", "cases", "gig bag", "gig bags",
    "bag", "bags",
    "amplifier cable", "patch cable", "patch cables",
    "pedal", "pedals", "effects pedal",
    "drum sticks", "sticks", "drumstick", "drumsticks",
    "music stand", "music stands",
    "cleaning kit", "cleaner", "polish",
    "mouthpiece", "mouthpieces",
]


def is_accessory_request(message):
    """Return True when the customer is asking about an accessory."""
    text = message.lower()
    return any(term in text for term in ACCESSORY_TERMS)


def is_generic_price_question(message):
    """
    Detect a price question that names only a broad instrument type.
    In that case, ask what kind/model the customer wants instead of
    returning an arbitrary list of products.
    """
    text = message.lower()

    price_terms = [
        "price", "prices", "cost", "how much", "what does",
        "how expensive", "value",
    ]
    if not any(term in text for term in price_terms):
        return False

    # If the customer named a specific brand or model, search the catalog.
    brands = [
        "fender", "gibson", "ibanez", "taylor",
        "yamaha", "tagima", "prs", "gretsch",
    ]
    if any(brand in text for brand in brands):
        return False

    # Generic instrument terms. A broad request such as "price of a guitar"
    # needs clarification before selecting a product.
    instrument_terms = [
        "guitar", "guitars", "bass", "basses",
        "piano", "pianos", "keyboard", "keyboards",
        "violin", "violins", "ukulele", "ukuleles",
        "drum", "drums", "instrument", "instruments",
    ]
    return any(term in text for term in instrument_terms)


def is_policy_question(message):
    """Identify questions about store policies."""
    text = message.lower()

    policy_words = [
        "hour", "hours", "opening", "closing", "open", "closed",
        "payment", "payments", "pix", "installment", "installments",
        "credit card", "debit card", "boleto",
        "return", "returns", "refund", "exchange", "exchanges",
        "defect", "defective", "delivery", "shipping", "freight",
        "tracking", "warranty", "guarantee",
        "privacy", "personal data", "lgpd",
        "store policy", "store policies",
        "business days", "calendar days",
    ]
    return any(word in text for word in policy_words)


def answer_policy_question(user_message):
    """
    Retrieve policy information and answer using verified information
    from the store policy PDF.
    """
    policy_data = search_policies(user_message)

    if not policy_data["found"]:
        return (
            "I couldn't find reliable information about this subject "
            "in our store policy document. Please contact our store "
            "management for confirmation."
        )

    text = user_message.lower()

    # Opening hours
    if any(word in text for word in [
        "hour", "hours", "opening", "closing", "open", "closed"
    ]):
        return (
            "Our store opening hours are:\n\n"
            "- Monday to Friday: 09:00 AM to 06:00 PM\n"
            "- Saturday: 09:00 AM to 01:00 PM\n"
            "- Sundays and holidays: Closed\n\n"
            "Opening hours may be extended on special dates. "
            "Any changes will be announced in advance."
        )

    # Defective products
    if any(word in text for word in [
        "defect", "defective", "broken", "manufacturing"
    ]):
        return (
            "According to our store policy:\n\n"
            "- Products with manufacturing defects can be exchanged "
            "within 30 calendar days after purchase.\n"
            "- After 30 days, customers should contact the manufacturer "
            "directly for warranty assistance.\n"
            "- Empório da Música may help mediate the process upon request.\n"
            "- Damage caused by misuse, falls, excessive moisture or "
            "unauthorized modifications is not covered.\n\n"
            "Please contact our customer service team for assistance."
        )

    # Installment payments
    if "installment" in text or "installments" in text:
        return (
            "According to our payment policy, credit card installments "
            "are available under these conditions:\n\n"
            "- 1 to 3 installments: no interest. Installments below "
            "R$ 50.00 are not allowed.\n"
            "- 4 to 6 installments: minimum installment of R$ 80.00.\n"
            "- 7 to 12 installments: minimum installment of R$ 100.00.\n\n"
            "All installment options are interest-free according "
            "to the policy document."
        )

    # Other policy questions: pass retrieved PDF content to the model.
    context = ""
    for item in policy_data["results"]:
        context += (
            f"\nPDF PAGE {item['page']}:\n"
            f"{item['content']}\n"
        )

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT + """
You are answering a question about store policies.

STRICT RULES:
- Use only facts explicitly stated in the supplied document.
- Never add deadlines, requirements, fees or conditions
  that are not explicitly stated.
- Do not infer missing information.
- If information is missing or ambiguous, say so.
- Recommend contacting store management when necessary.
- Always answer in English.
""",
        },
        {
            "role": "user",
            "content": (
                f"Customer question: {user_message}\n\n"
                f"Policy document:\n{context}"
            ),
        },
    ]
    return generate_final_answer(messages)


def deterministic_fallback(message):
    """
    Identify product and promotion requests that can be answered
    directly using verified CSV data.
    """
    text = message.lower()

    # Promotions
    promotion_words = [
        "promotion", "promotions", "discount", "discounts",
        "offer", "offers", "sale",
    ]
    if any(word in text for word in promotion_words):
        return get_active_promotions()

    # Product search
    product_words = [
        "guitar", "guitars", "bass", "basses",
        "piano", "pianos", "keyboard", "keyboards",
        "violin", "violins", "ukulele", "ukuleles",
        "drum", "drums", "fender", "gibson", "ibanez",
        "taylor", "yamaha", "tagima", "prs", "gretsch",
        "instrument", "instruments",
    ]
    if not any(word in text for word in product_words):
        return None

    category = None
    if "guitar" in text:
        category = "Guitarras"
    elif "bass" in text:
        category = "Baixos"
    elif "piano" in text or "keyboard" in text:
        category = "Teclados e Pianos"
    elif "violin" in text:
        category = "Cordas Orquestrais"
    elif "ukulele" in text:
        category = "Ukuleles"
    elif "drum" in text:
        category = "Baterias e Percussão"

    brands = [
        "fender", "gibson", "ibanez", "taylor",
        "yamaha", "tagima", "prs", "gretsch",
    ]
    query = next((brand for brand in brands if brand in text), "")

    # For a clear category request such as "Do you have guitars?",
    # searching by category is sufficient. For a named brand, search
    # by brand as well.
    return search_products(query=query, category=category)


def generate_final_answer(messages):
    """Generate a natural language response using Ollama."""
    response = ollama.chat(
        model=MODEL_NAME,
        messages=messages,
        options={"temperature": 0},
    )
    return response["message"]["content"]


def chat_with_agent(user_message):
    text = user_message.lower()

    # 1. Accessories: answer directly before policy/product routing.
    if is_accessory_request(text):
        return (
            "We currently sell musical instruments only and do not "
            "carry accessories or supplies such as guitar strings, "
            "picks, cables or straps. We'd be happy to help you find "
            "a musical instrument!"
        )

    # 2. Generic price questions: clarify instead of listing arbitrary items.
    if is_generic_price_question(text):
        return (
            "Of course! Are you looking for an electric, acoustic or "
            "classical guitar? If you have a specific model or brand "
            "in mind, let me know and I can check its current price "
            "and availability."
        )

    # 3. Policy questions: consult the PDF.
    if is_policy_question(text):
        return answer_policy_question(user_message)

    # 4. Order verification: handled directly by Python.
    if "order" in text:
        order_id = re.search(
            r"\border(?:\s*(?:id|number))?\s*(?:is|:|#)?\s*(\d+)\b",
            user_message,
            re.IGNORECASE,
        )
        email = re.search(
            r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",
            user_message,
            re.IGNORECASE,
        )

        if not order_id or not email:
            return (
                "To check your order, please provide your order ID "
                "and registered email address. No order date or full "
                "name is required."
            )

        result = get_order_status(order_id.group(1), email.group(0))
        if "error" in result:
            return result["error"]

        return (
            "I successfully verified your order!\n\n"
            f"Order ID: {result['order_id']}\n"
            f"Status: {result['status']}\n"
            f"Order date: {result['order_date']}\n"
            f"Total: R$ {result['total_brl']:,.2f}\n"
            f"Payment method: {result['payment_method']}\n"
            f"Tracking code: {result['tracking_code']}\n"
            f"Estimated delivery: {result['estimated_delivery']}"
        )

    # 5. Product and promotion queries.
    verified_data = deterministic_fallback(user_message)

    if verified_data is not None:
        if "products" in verified_data:
            products = verified_data["products"]
            if not products:
                return (
                    "I couldn't find any matching products currently "
                    "available in our inventory."
                )

            answer = "Here are the available products:\n\n"
            for product in products:
                answer += (
                    f"Product: {product['name']}\n"
                    f"Price: R$ {product['price_brl']:,.2f}\n"
                    f"Stock: {product['stock_quantity']} units\n\n"
                )
            return answer

        if "promotions" in verified_data:
            promotions = verified_data["promotions"]
            if not promotions:
                return "There are currently no active promotions."

            answer = "Here are our current promotions:\n\n"
            for promotion in promotions:
                answer += (
                    f"Product: {promotion['product_name']}\n"
                    f"Original price: R$ "
                    f"{promotion['original_price_brl']:,.2f}\n"
                    f"Discount: {promotion['discount_percent']}%\n"
                    f"Description: {promotion['description']}\n\n"
                )
            return answer

    # 6. General questions handled by Qwen.
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    return generate_final_answer(messages)


if __name__ == "__main__":
    print("=" * 55)
    print("EMPORIO DA MUSICA - AI CUSTOMER SERVICE")
    print("=" * 55)
    print("\nAssistant is ready!")
    print("Type 'exit' to close the application.\n")

    while True:
        user_message = input("Customer: ").strip()

        if user_message.lower() in ["exit", "quit", "bye"]:
            print("\nAssistant: Thank you for contacting us!")
            break

        if not user_message:
            continue

        try:
            answer = chat_with_agent(user_message)
            print("\nAssistant:")
            print(answer)
            print()
        except Exception as error:
            print("\nAssistant: Sorry, an error occurred.")
            print(f"Technical details: {error}\n")
