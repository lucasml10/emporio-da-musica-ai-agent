# Empório da Música — AI Customer Service Agent

An AI-powered customer service assistant developed in Python for Empório da Música, a fictional musical instrument store located in Campo Grande, Brazil.

The application handles customer messages in natural language and provides answers using verified store information, including product inventory, active promotions, order records, and store policies.

## Features

- **Product search:** Find musical instruments using product names, brands, categories, and price filters.
- **Product details:** Retrieve information from the store's product catalog.
- **Active promotions:** Display currently active offers based on store data.
- **Order tracking:** Verify order status using the order ID and registered customer email.
- **Policy retrieval:** Search the store's policy PDF to answer questions about payments, returns, exchanges, warranties, delivery, and opening hours.
- **Out-of-scope handling:** Politely redirect requests for accessories and products not sold by the store.
- **Natural language responses:** Use a local language model to handle general customer interactions.

## Technology Stack

- **Python** — application logic and data processing.
- **Ollama** — local model execution.
- **Qwen 2.5 3B** — language model.
- **Pandas** — CSV data processing.
- **PyMuPDF** — PDF policy extraction and retrieval.
- **Unittest** — automated tests.

## Architecture

The application uses a hybrid approach combining deterministic Python routing, structured data retrieval, document-based policy retrieval, and language model generation.

1. Customer messages are received through the command-line interface.
2. The agent identifies the type of request.
3. Product, promotion, and order requests are handled through Python functions connected to CSV datasets.
4. Policy questions retrieve relevant information from the store policy PDF.
5. General questions are forwarded to the local Qwen model through Ollama.
6. The agent returns a response in English.

This design prioritizes verified information for business-critical data instead of relying exclusively on language model generation.

## Project Structure

```text
emporio-da-musica-agent/
├── data/
│   ├── categories.csv
│   ├── customers_public.csv
│   ├── order_items.csv
│   ├── orders.csv
│   ├── products.csv
│   ├── promotions.csv
│   └── store_policies.pdf
├── src/
│   ├── agent.py
│   ├── data_loader.py
│   ├── llm.py
│   ├── policies.py
│   └── tools.py
├── tests/
│   └── test_agent.py
├── examples/
│   └── conversations.md
├── main.py
└── requirements.txt
```

## Requirements

- Python 3.10 or newer.
- Ollama installed and running.
- Qwen 2.5 3B model downloaded.

## Installation

Clone the repository:

```bash
git clone YOUR_PUBLIC_REPOSITORY_URL
cd emporio-da-musica-agent
```

Create and activate a virtual environment:

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Download the language model:

```bash
ollama pull qwen2.5:3b
```

Make sure Ollama is running before starting the application.

## Running the Application

From the project root, execute:

```bash
python main.py
```

If using the module entry point instead:

```bash
python -m src.agent
```

The assistant accepts customer messages in the terminal. Type `exit` to close the application.

## Running Tests

Execute:

```bash
python -m unittest discover -s tests -v
```

The current automated test suite contains 9 tests covering accessory requests, product price clarification, policy detection, order verification requirements, and language model routing.

## Data Privacy

The public project uses `customers_public.csv`, which contains anonymized customer records.

The original `customers.csv` file is excluded from version control through `.gitignore`.

Order verification requires both an order ID and the registered email address. The application does not request a customer's full name or order date for this process.

## Limitations

- Product, order, and promotion information depends on the supplied CSV datasets.
- The policy retrieval mechanism uses keyword-based matching rather than a full semantic vector search.
- General language model responses depend on the locally running Qwen model.
- The application currently runs through a command-line interface.
- The supplied datasets are static and are not connected to a live store management system.
- Ambiguous policy cases may require human support.

## Future Improvements

- Implement a web-based customer service interface.
- Add semantic vector search for policy retrieval.
- Introduce conversation history and persistent sessions.
- Expand automated testing and integration testing.
- Add structured logging and monitoring.
- Improve intent classification and human handoff workflows.
- Integrate with a live inventory and order management system.

## Development Approach

This project was developed as part of a technical challenge for an AI Engineer role.

AI-assisted development tools were used during implementation and debugging. Architecture decisions, integration, testing, and validation were reviewed throughout development.



