
from pathlib import Path
import re
import unicodedata
import pymupdf


# Path to the store policy PDF
BASE_DIR = Path(__file__).resolve().parent.parent
PDF_PATH = BASE_DIR / "data" / "store_policies.pdf"


def normalize_text(text):
    """Remove accents and normalize text for searching."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        char for char in text
        if not unicodedata.combining(char)
    )
    return text.lower()


def load_policy_pages():
    """Extract text from every page of the policy PDF."""
    if not PDF_PATH.exists():
        raise FileNotFoundError(
            f"Policy PDF not found: {PDF_PATH}"
        )

    pages = []

    with pymupdf.open(PDF_PATH) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            content = page.get_text("text").strip()

            if content:
                pages.append({
                    "page": page_number,
                    "content": content
                })

    if not pages:
        raise ValueError(
            "No text could be extracted from the policy PDF."
        )

    return pages


def find_phone_numbers(pages):
    """
    Extract Brazilian phone numbers containing an area code.
    Returns unique numbers with their original formatting.
    """
    phone_pattern = re.compile(
        r"(?<!\d)"
        r"(?:\+?55[\s.-]*)?"
        r"\(?\d{2}\)?[\s.-]*"
        r"(?:9\d{4}|\d{4})[\s.-]?\d{4}"
        r"(?!\d)"
    )

    phones = {}

    for page in pages:
        content = page["content"]

        for match in phone_pattern.finditer(content):
            original_number = match.group(0).strip()
            digits = re.sub(r"\D", "", original_number)

            # Remove Brazil country code for comparison.
            if digits.startswith("55") and len(digits) in (12, 13):
                digits = digits[2:]

            if len(digits) not in (10, 11):
                continue

            phones[digits] = original_number

    return list(phones.values())


def detect_phone_conflicts(pages):
    """
    Detect whether the policy document contains multiple
    distinct phone numbers.
    """
    phone_numbers = find_phone_numbers(pages)

    return {
        "has_conflict": len(phone_numbers) > 1,
        "numbers": phone_numbers
    }


# Keyword expansion for policy retrieval.
KEYWORD_GROUPS = {
    "hours": [
        "hours", "opening", "closing", "open", "closed",
        "business hours", "horario", "funcionamento",
        "aberto", "fechado"
    ],
    "payment": [
        "payment", "payments", "pix", "credit", "debit",
        "installment", "installments", "parcelamento",
        "pagamento", "cartao", "desconto"
    ],
    "returns": [
        "return", "refund", "exchange", "defect",
        "cancellation", "troca", "devolucao",
        "reembolso", "defeito", "cancelamento"
    ],
    "delivery": [
        "delivery", "shipping", "shipment", "tracking",
        "freight", "entrega", "frete", "envio",
        "rastreamento", "transportadora"
    ],
    "warranty": [
        "warranty", "guarantee", "manufacturing defect",
        "garantia", "fabricacao"
    ],
    "promotions": [
        "promotion", "promotions", "discount", "black friday",
        "promocao", "promocoes", "desconto", "oferta"
    ],
    "privacy": [
        "privacy", "personal data", "lgpd", "data protection",
        "privacidade", "dados pessoais"
    ],
    "products": [
        "accessories", "instruments", "products",
        "acessorios", "instrumentos", "produtos"
    ]
}


def expand_keywords(question):
    """Identify related terms based on the question."""
    normalized_question = normalize_text(question)
    keywords = set(normalized_question.split())

    for group in KEYWORD_GROUPS.values():
        if any(
            normalize_text(term) in normalized_question
            for term in group
        ):
            for term in group:
                keywords.update(normalize_text(term).split())

    return keywords


def search_policies(question, top_k=3):
    """
    Retrieve the most relevant policy pages.
    Also reports phone number conflicts found in the document.
    """
    pages = load_policy_pages()
    keywords = expand_keywords(question)

    # Check the entire document for conflicting phone numbers.
    phone_conflicts = detect_phone_conflicts(pages)

    scored_pages = []

    for page in pages:
        normalized_content = normalize_text(page["content"])
        score = 0

        for keyword in keywords:
            if len(keyword) > 2:
                score += len(
                    re.findall(
                        rf"\b{re.escape(keyword)}\b",
                        normalized_content
                    )
                )

        if score > 0:
            scored_pages.append({
                "page": page["page"],
                "score": score,
                "content": page["content"]
            })

    scored_pages.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    results = scored_pages[:top_k]

    if not results:
        return {
            "found": False,
            "message": (
                "No relevant information was found in the "
                "store policy document. Ask store management "
                "before providing a definitive answer."
            ),
            "results": [],
            "phone_conflicts": phone_conflicts
        }

    return {
        "found": True,
        "results": results,
        "phone_conflicts": phone_conflicts
    }


if __name__ == "__main__":
    print("=" * 50)
    print("EMPORIO DA MUSICA - POLICY SEARCH TEST")
    print("=" * 50)

    question = input("\nEnter a policy question: ")

    result = search_policies(question)

    if result["found"]:
        for item in result["results"]:
            print(f"\n--- PDF PAGE {item['page']} ---")
            print(item["content"])
    else:
        print("\nNo relevant policy found.")
        print(result["message"])

    conflicts = result["phone_conflicts"]

    print("\n--- PHONE NUMBER AUDIT ---")

    if conflicts["has_conflict"]:
        print("Conflicting phone numbers detected:")

        for number in conflicts["numbers"]:
            print(f"- {number}")
    else:
        print("No conflicting phone numbers detected.")
