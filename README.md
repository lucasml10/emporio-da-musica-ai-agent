# Emporio da Musica AI Agent

An AI-powered customer service agent for a fictional musical instruments store in Campo Grande, Brazil. Built with Python and Ollama, the application answers customer questions in natural language using product data, order information, promotions, and store policies.

## Features

- **Product Search:** Search available musical instruments by name, category, and price.
- **Product Details:** Retrieve product descriptions, specifications, prices, and stock availability.
- **Promotions:** Display currently active promotions.
- **Order Tracking:** Check order status using the order ID and registered customer email.
- **Policy Retrieval:** Answer questions about store hours, payments, exchanges, returns, shipping, and warranties.
- **Scope Control:** Politely redirect requests for products and services outside the store's scope.
- **Natural Language Responses:** Use Qwen 2.5 3B through Ollama for general customer interactions.

## Technology Stack

- Python
- Ollama
- Qwen 2.5 3B
- Pandas
- PyMuPDF
- Unittest

## Architecture

The application uses a hybrid approach combining deterministic Python logic and a local language model.

1. **Request Routing:** Classifies customer requests and directs them to the appropriate functionality.
2. **Structured Data Retrieval:** Uses CSV datasets to retrieve product information, stock, promotions, and order details.
3. **Policy Retrieval:** Searches the store's PDF policy document using keyword-based retrieval.
4. **Language Model:** Uses Qwen 2.5 3B through Ollama for general conversational responses.

This design prioritizes reliable data retrieval for business-critical information while using the language model for natural language interaction.

## Project Structure

```text
emporio-da-musica-ai-agent/
├── emporio-da-musica-agent/
│   ├── data/
│   │   ├── categories.csv
│   │   ├── customers_public.csv
│   │   ├── order_items.csv
│   │   ├── orders.csv
│   │   ├── products.csv
│   │   ├── promotions.csv
│   │   └── store_policies.pdf
│   ├── examples/
│   │   └── conversations.md
│   ├── src/
│   │   ├── agent.py
│   │   ├── data_loader.py
│   │   ├── llm.py
│   │   ├── policies.py
│   │   └── tools.py
│   ├── tests/
│   │   └── test_agent.py
│   ├── main.py
│   └── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

## Requirements

- Python 3.10 or newer
- Ollama installed
- Qwen 2.5 3B model

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/lucasml10/emporio-da-musica-ai-agent.git
cd emporio-da-musica-ai-agent/emporio-da-musica-agent
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Download the language model

```bash
ollama pull qwen2.5:3b
```

## Running the Application

Start the customer service agent:

```bash
python main.py
```

Alternatively:

```bash
python -m src.agent
```

The application will start an interactive terminal session.

Type `exit` to close the application.

## Running Tests

Execute the automated tests:

```bash
python -m unittest discover -s tests -v
```

The project includes tests for request classification, accessory restrictions, policy questions, order validation, and language model integration.

## Data Privacy

The repository uses `customers_public.csv`, containing anonymized customer records for demonstration purposes.

The original `customers.csv` file is excluded through `.gitignore` and should not be published.

The datasets are static challenge fixtures and do not represent a live store database.

## Limitations

- Data is retrieved from static CSV files.
- Policy retrieval uses keyword-based matching.
- The interface is currently terminal-based.
- The language model runs locally through Ollama.
- The application does not integrate with a real payment, inventory, or shipping provider.
- Policy ambiguities require human review.

## Future Improvements

- Implement semantic retrieval using embeddings and a vector database.
- Add a web-based chat interface.
- Integrate a persistent database.
- Improve automated intent classification.
- Add conversation history and session management.
- Implement human handoff for complex customer requests.

## Development Approach

AI-assisted development tools were used during implementation, debugging, and documentation. Architecture decisions, code integration, and testing were reviewed throughout development.

---

**Project:** Emporio da Musica AI Agent  
**Author:** Lucas Pereira de Melo Barbosa  
**GitHub:** https://github.com/lucasml10
