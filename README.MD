# Airline Baggage Claim Validation Agent

An agentic AI system for validating airline baggage claims using a hybrid decision pipeline that combines deterministic business rules, MCP-based tool access, RAG over policy documents, LLM-based policy interpretation, and post-decision guardrails.

The system supports delayed, lost, and damaged baggage claims and returns one of:

- `APPROVE`
- `REJECT`
- `MANUAL_REVIEW`

---

## Overview

Airline baggage claims often require multiple manual steps:

- verifying the passenger booking
- checking baggage tracking events
- determining whether the claim is operationally valid
- retrieving the applicable baggage policy
- evaluating claimed expenses against that policy
- escalating high-risk or ambiguous cases for human review

This project automates that workflow while deliberately separating deterministic logic from LLM-based reasoning.

Objective facts and hard business rules are handled in Python, while the LLM is used only where semantic interpretation is useful, such as evaluating claim expenses against policy text.

---

## Architecture

```text
                        Streamlit UI
                             |
                             v
                         FastAPI API
                             |
                             v
                    LangGraph Workflow
                             |
          +------------------+------------------+
          |                  |                  |
          v                  v                  v
   Deterministic        MCP Integration      Policy RAG
     Validation              |                  |
          |                  v                  v
          |             MCP Client          Chroma
          |                  |                  |
          |                  v                  v
          |             MCP Server        Policy Documents
          |                  |
          |                  v
          |          Simulated Airline Data
          |
          +------------------+
                             |
                             v
                     OpenAI LLM Decision
                             |
                             v
                    Deterministic Guardrails
                             |
                             v
          APPROVE / REJECT / MANUAL_REVIEW
```

---

## Tech Stack

### Backend

- Python 3.12
- FastAPI
- Pydantic
- LangGraph

### Agent Integration

- Model Context Protocol (MCP)
- MCP Python SDK

### Retrieval

- Chroma
- Local policy document indexing
- Retrieval-Augmented Generation

### LLM

- OpenAI API
- Structured Outputs using Pydantic schemas

### Frontend

- Streamlit

### Testing and Evaluation

- pytest
- pytest-asyncio
- mocked LangGraph regression tests
- labeled evaluation dataset

### Observability

- Python structured logging
- LangSmith tracing
- latency monitoring
- token usage tracking

### DevOps

- Git
- GitHub Actions
- Docker configuration

---

## How It Works

A user submits a baggage claim containing:

```json
{
  "pnr": "ABC123",
  "bag_tag": "BG001",
  "claim_type": "DELAYED_BAGGAGE",
  "expenses": [
    {
      "category": "clothing",
      "amount": 150
    },
    {
      "category": "toiletries",
      "amount": 40
    }
  ]
}
```

The system processes the claim through multiple stages.

### 1. Booking Verification

The workflow verifies:

- the PNR exists
- the baggage tag belongs to the booking

Invalid bookings are rejected before any LLM call is made.

---

### 2. Baggage Verification

The system retrieves baggage tracking events through MCP.

Example:

```json
{
  "bag_tag": "BG001",
  "events": [
    {
      "airport": "DFW",
      "event": "CHECKED_IN"
    },
    {
      "airport": "DFW",
      "event": "LOADED"
    },
    {
      "airport": "JFK",
      "event": "MISSING"
    }
  ]
}
```

---

### 3. Claim-Type Routing

LangGraph routes the claim into a dedicated workflow based on claim type:

```text
DELAYED_BAGGAGE
LOST_BAGGAGE
DAMAGED_BAGGAGE
```

Each branch performs deterministic evidence validation.

Examples:

- delayed baggage must contain evidence of a missing bag
- lost baggage must be formally confirmed as lost
- damaged baggage must contain a damage event

---

### 4. Deterministic Validation

Objective business rules are intentionally kept outside the LLM.

Examples include:

- booking validity
- baggage ownership
- baggage status
- whether loss has been formally confirmed
- automatic approval thresholds
- confidence thresholds

This reduces unnecessary LLM calls and prevents the model from making decisions about facts that can be verified deterministically.

---

## MCP Integration

The project uses Model Context Protocol as the integration boundary between the agent workflow and simulated airline systems.

Current MCP tools include:

```text
lookup_booking
lookup_baggage
```

The application flow is:

```text
LangGraph
    |
    v
MCP Client
    |
    v
MCP Server
    |
    v
Data Service
    |
    v
Synthetic Airline Data
```

The current implementation uses MCP over `stdio`.

`stdio` stands for standard input/output. The MCP client launches the MCP server as a subprocess and communicates with it through process input/output streams.

In a production deployment, the same MCP server could instead run independently and communicate with the application over a network transport.

Conceptually:

```text
FastAPI / LangGraph Service
          |
          v
      MCP Client
          |
          v
   Remote MCP Server
          |
          v
Reservation / Baggage / Claims Systems
```

MCP is used here to decouple agent orchestration from backend implementation details.

---

## Policy Retrieval with Chroma

Policies are stored as Markdown documents under:

```text
policies/
```

The current policy set includes:

```text
delayed_baggage.md
lost_baggage.md
damaged_baggage.md
```

These documents are indexed into Chroma.

The workflow builds a semantic retrieval query using:

- claim type
- claimed expenses
- eligibility requirements
- reimbursement rules
- exclusions
- manual-review conditions

The relevant policy is then added to the LangGraph state before the LLM decision.

This design allows policy changes without rewriting decision logic.

A policy can be updated and re-indexed independently of the application workflow.

---

## LLM-Based Policy Interpretation

The OpenAI model is used only after:

- booking validation
- baggage validation
- claim-type validation
- policy retrieval

The LLM receives:

```text
claim type
expenses
baggage tracking data
retrieved policy
```

It returns a structured response containing:

```text
decision
approved_amount
reason
confidence
```

Example:

```json
{
  "decision": "APPROVE",
  "approved_amount": 190.0,
  "reason": "The claimed clothing and toiletries are eligible under the delayed baggage policy.",
  "confidence": 0.88
}
```

Structured Outputs are used so the model response conforms to a defined Pydantic schema instead of returning arbitrary text.

---

## Guardrails

The LLM does not have final authority.

A deterministic post-processing layer applies business controls after the model returns its recommendation.

Examples:

```text
approved amount > $500
        |
        v
MANUAL_REVIEW
```

and:

```text
confidence < 0.75
        |
        v
MANUAL_REVIEW
```

This ensures high-value or low-confidence decisions are escalated rather than automatically approved.

---

## Lost Baggage Handling

The workflow distinguishes between:

```text
LOST
```

and:

```text
CONFIRMED_LOST
```

A `LOST` event means that the bag is currently missing but has not yet been formally declared unrecoverable.

This results in:

```text
MANUAL_REVIEW
```

A `CONFIRMED_LOST` event allows the workflow to continue to policy retrieval and LLM evaluation.

This distinction prevents premature lost-baggage settlements.

---

## Evaluation

The system includes a curated evaluation suite covering 15 claim scenarios.

Test scenarios include:

- valid delayed baggage claims
- delivered baggage submitted as delayed
- high-value delayed baggage claims
- excluded expense categories
- valid confirmed lost baggage
- unconfirmed lost baggage
- invalid lost claims
- high-value lost claims
- valid damaged baggage claims
- invalid damaged baggage claims
- high-value damaged baggage claims
- invalid PNR
- mismatched baggage tags
- missing baggage tracking data
- policy retrieval validation

### Evaluation Results

```text
Decision Accuracy:              15/15 (100%)
Policy Retrieval Accuracy:       8/8  (100%)
Manual Review Routing Accuracy:  5/5  (100%)
```

These results are based on a curated regression suite rather than a large-scale production dataset.

### Runtime Metrics

```text
Average End-to-End Latency: 4.75 seconds

Total Input Tokens:  2,911
Total Output Tokens: 1,468

LLM Calls: 8
Total Claims: 15
```

Only 8 of the 15 evaluation scenarios required an LLM call.

The remaining 7 cases were resolved through deterministic validation before reaching the model.

This reduces:

- API cost
- latency
- unnecessary model usage
- risk of model-driven decisions for objective facts

---

## Testing

The project uses `pytest` for automated regression testing.

Run:

```bash
python -m pytest -v
```

The test suite includes deterministic unit tests for:

- delayed baggage validation
- lost baggage validation
- damaged baggage validation
- high-value guardrails
- low-confidence guardrails

It also includes a mocked end-to-end LangGraph regression test.

The end-to-end test mocks:

- MCP booking lookup
- MCP baggage lookup
- Chroma policy retrieval
- LLM response

This allows the full orchestration flow to be tested without:

- calling OpenAI
- incurring API cost
- depending on external services
- introducing nondeterministic model behavior into CI

---

## Evaluation Runner

The real evaluation pipeline can be run using:

```bash
python -m evaluation.run_evaluation
```

Unlike the mocked pytest suite, this evaluation executes the real application components, including the LLM.

It reports:

```text
Decision Accuracy
Policy Retrieval Accuracy
Manual Review Routing Accuracy
Average Latency
Input Tokens
Output Tokens
Number of LLM Calls
```

---

## Observability

The application uses both traditional logging and AI-specific tracing.

### Application Logging

Python logging records high-level claim execution information such as:

```text
PNR
claim type
final decision
end-to-end latency
```

Example:

```text
claim_result |
pnr=ABC123 |
claim_type=DELAYED_BAGGAGE |
decision=APPROVE |
latency=4.31s
```

### LangSmith

LangSmith is used to inspect LangGraph execution traces.

It provides visibility into:

- graph execution
- node transitions
- inputs and outputs
- LLM calls
- latency
- failures
- token usage

This makes it possible to investigate unexpected decisions and understand how a claim moved through the workflow.

---

## GitHub Actions CI

GitHub Actions runs the automated test suite on:

```text
push to main
pull request to main
```

The CI pipeline:

```text
Checkout repository
        |
        v
Setup Python 3.12
        |
        v
Install dependencies
        |
        v
Run pytest
```

The CI tests do not require an OpenAI API key because external dependencies are mocked.

This keeps the pipeline:

- deterministic
- free to run
- isolated from external APIs

---

## Docker

The repository includes:

```text
Dockerfile
.dockerignore
```

The application container is based on:

```text
python:3.12-slim
```

The FastAPI application is exposed on:

```text
8000
```

Example build:

```bash
docker build -t airline-baggage-agent .
```

Example run:

```bash
docker run --env-file .env -p 8000:8000 airline-baggage-agent
```

---

## Streamlit Interface

The project includes a lightweight Streamlit frontend.

Users can enter:

- PNR
- baggage tag
- claim type
- expense categories
- expense amounts

The frontend submits the claim to FastAPI and displays:

- final decision
- reason
- approved amount
- model confidence
- policy used

Run:

```bash
streamlit run ui/app.py
```

The Streamlit app typically runs at:

```text
http://localhost:8501
```

---

## Running Locally

### 1. Clone the repository

```bash
git clone <repository-url>
cd airline-baggage-agent
```

### 2. Create a virtual environment

```bash
python3.12 -m venv .venv
```

Activate it:

macOS/Linux:

```bash
source .venv/bin/activate
```

Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create:

```text
.env
```

Add:

```text
OPENAI_API_KEY=your_openai_api_key

LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=airline-baggage-agent
```

LangSmith tracing is optional.

To disable it:

```text
LANGSMITH_TRACING=false
```

### 5. Index policies

Run:

```bash
python -m scripts.index_policies
```

This creates the local Chroma vector database.

### 6. Start FastAPI

```bash
uvicorn app.main:app --reload
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

### 7. Start Streamlit

In another terminal:

```bash
streamlit run ui/app.py
```

---

## Example Claim

Request:

```json
{
  "pnr": "ABC123",
  "bag_tag": "BG001",
  "claim_type": "DELAYED_BAGGAGE",
  "expenses": [
    {
      "category": "clothing",
      "amount": 150
    },
    {
      "category": "toiletries",
      "amount": 40
    }
  ]
}
```

Example response:

```json
{
  "decision": "APPROVE",
  "approved_amount": 190.0,
  "reason": "The claimed clothing and toiletries are eligible under the delayed baggage policy.",
  "confidence": 0.88,
  "policy_source": "delayed_baggage.md"
}
```

---

## Project Structure

```text
airline-baggage-agent/
│
├── app/
│   ├── graph/
│   │   └── claim_graph.py
│   │
│   ├── mcp/
│   │   ├── client.py
│   │   └── server.py
│   │
│   ├── models/
│   │   ├── claim.py
│   │   └── enums.py
│   │
│   ├── services/
│   │   ├── data_service.py
│   │   ├── llm_service.py
│   │   ├── observability.py
│   │   └── policy_service.py
│   │
│   └── main.py
│
├── data/
│   ├── bookings.json
│   ├── baggage_events.json
│   └── claims.json
│
├── policies/
│   ├── delayed_baggage.md
│   ├── lost_baggage.md
│   └── damaged_baggage.md
│
├── evaluation/
│   ├── test_cases.json
│   └── run_evaluation.py
│
├── scripts/
│   ├── index_policies.py
│   ├── test_mcp.py
│   ├── test_openai.py
│   ├── test_llm_service.py
│   └── test_policy_search.py
│
├── tests/
│   ├── test_claim_graph.py
│   ├── test_claim_validation.py
│   └── test_guardrails.py
│
├── ui/
│   └── app.py
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── Dockerfile
├── .dockerignore
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
```

---

## Design Decisions

### Why not use the LLM for everything?

Operational facts such as whether a booking exists or whether a bag was actually delayed can be determined reliably in code.

Using an LLM for those decisions would increase:

- cost
- latency
- nondeterminism
- hallucination risk

The model is therefore limited to policy interpretation, where semantic reasoning adds value.

### Why LangGraph?

For a single linear workflow, plain Python would be sufficient.

LangGraph becomes useful here because the system contains:

- multiple claim types
- conditional routing
- shared state
- manual-review paths
- deterministic and AI-driven stages
- future extensibility for additional claim workflows

### Why MCP?

For the current project scale, direct HTTP or Python calls would be simpler.

MCP is used to model how an enterprise agent can interact with multiple operational systems through standardized tool contracts.

In a larger deployment, MCP tools could abstract:

- reservation APIs
- baggage systems
- claims systems
- customer systems
- payment systems
- legacy services

without coupling LangGraph directly to each backend implementation.

### Why Chroma?

Policy documents are external knowledge that may change independently of application code.

Using retrieval allows policies to be updated and re-indexed without embedding all business rules directly into prompts or Python logic.

---

## Future Improvements

Potential improvements include:

- duplicate claim detection
- receipt upload and OCR
- receipt fraud detection
- customer claim history
- multiple bags per booking
- policy versioning and effective dates
- metadata-filtered retrieval
- hybrid search
- reranking
- real airline API integration
- remote HTTP-based MCP server
- authentication and authorization
- database-backed persistence
- human-review dashboard
- claim audit history
- model fallback strategy
- prompt/version regression tracking
- larger evaluation datasets
- LLM-as-a-judge evaluation
- deployment to a cloud platform

---

## Disclaimer

The airline data and policies used in this project are synthetic and created for demonstration purposes.

The project does not represent or implement the internal baggage claim systems or policies of any real airline.
