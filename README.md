# Flux-Order: High-Concurrency Ticketing System
![CI Status](https://github.com/Tannishaa/flux-order/actions/workflows/ci.yml/badge.svg)

*A resilient, event-driven microservices architecture designed to handle high-traffic flash sales without race conditions or inventory overselling.*

## Architecture
```mermaid
    User((User)) -->|Select Seat| FE[Next.js Frontend]
    FE -->|POST /buy| API[Flask API]
    API -->|1. Push Order| SQS[(AWS SQS Queue)]
    SQS -->|2. Poll Message| Worker[Python Worker]
    Worker -->|3. Acquire Lock| Redis[(Redis Distributed Lock)]
    Worker -->|4. Confirm Sale| DB[(AWS DynamoDB)]
    FE -.->|5. Real-time Polling| API
    API -.->|6. Fetch Sold Seats| DB
```
- **API (Flask):** Accepts orders and pushes them to an SQS Queue (Asynchronous processing).
- **Worker (Python):** Polls SQS, acquires a Distributed Lock (Redis), and updates DynamoDB.
- **Infrastructure:** Fully managed via Terraform (IaC).
- **Orchestration:** Docker Compose.

##  Tech Stack
- **Language:** Python 3.11
- **Cloud:** AWS (SQS, DynamoDB)
- **Containerization:** Docker & Docker Compose
- **IaC:** Terraform
- **Database:** Redis (Locking), DynamoDB (Storage)
- **Testing:** Locust (Load Testing), Pytest (Unit Testing)
##  Key Features
- **Zero Race Conditions:** Uses Redis `SET NX` (Mutex) to ensure atomic inventory checks.
- **Scalable:** Workers can be scaled horizontally (`docker-compose up --scale worker=3`).
- **Fault Tolerant:** Failed orders are returned to the queue for retry.
- **High Concurrency:** Tested to handle 160+ RPS with 1000+ concurrent users.

##  System Performance & Observability
- **Monitoring:** Implemented a custom TUI (Terminal User Interface) dashboard using the `Rich` library to monitor real-time queue depth, revenue, and worker health.
- **Race Condition Testing:** Verified using two simultaneous frontend sessions; Redis Distributed Locking successfully rejected overlapping requests for the same `item_id`.
- **Latency:** Sub-second processing time from SQS message pickup to DynamoDB confirmation.

##  Logic & Architecture
This project is an exploration of high-concurrency distributed systems.

* **Message Broker:** Utilizes AWS SQS for decoupling.
* **Concurrency Control:** Implements a Redis-based Distributed Lock (Mutex) to prevent race conditions during seat selection.
* **Database:** DynamoDB for persistent, low-latency storage of confirmed orders.

 **Note:** `To protect the integrity of the project and prevent unauthorized duplication, setup and deployment instructions are not provided publicly. If you are a recruiter or an engineer interested in the infrastructure setup, please reach out to me directly!`

## Security & Resilience
**Secret Management:** Utilizes environment variables via `.env` files (excluded from version control) and Docker `env_file` injection.

**Infrastructure Security:** Uses IAM roles with least-privilege access for AWS SQS and DynamoDB interactions.

**History Hygiene:** Repository history is periodically audited and scrubbed of any legacy configuration strings using `git-filter-repo`.