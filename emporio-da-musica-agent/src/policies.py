
from pathlib import Path
import re
import unicodedata
import fitz


# Caminho do PDF com as políticas da loja
BASE_DIR = Path(__file__).resolve().parent.parent
PDF_PATH = BASE_DIR / "data" / "store_policies.pdf"


def normalize_text(text):
    """Remove acentos e padroniza o texto para facilitar a busca."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        char for char in text
        if not unicodedata.combining(char)
    )
    return text.lower()


def load_policy_pages():
    """Extrai o texto de cada página do PDF."""
    if not PDF_PATH.exists():
        raise FileNotFoundError(
            f"Policy PDF not found: {PDF_PATH}"
        )

    pages = []

    with fitz.open(PDF_PATH) as pdf:
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


# Expansão de termos para ajudar a encontrar políticas relevantes.
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
    """Identifica assuntos relacionados à pergunta."""
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
    Busca as páginas mais relevantes do documento de políticas.
    Retorna o conteúdo encontrado para o agente utilizar.
    """
    pages = load_policy_pages()
    keywords = expand_keywords(question)

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
            "results": []
        }

    return {
        "found": True,
        "results": results
    }


if __name__ == "__main__":
    print("=" * 50)
    print("EMPORIO DA MUSICA - POLICY SEARCH TEST")
    print("=" * 50)

    question = input(
        "\nEnter a policy question: "
    )

    result = search_policies(question)

    if result["found"]:
        for item in result["results"]:
            print(f"\n--- PDF PAGE {item['page']} ---")
            print(item["content"])
    else:
        print("\nNo relevant policy found.")
        print(result["message"])
