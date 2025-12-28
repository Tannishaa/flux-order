# Flux-Order: High-Concurrency Ticketing System

A resilient, event-driven microservices architecture designed to handle high-traffic flash sales without race conditions or inventory overselling.

##  Architecture
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

##  Key Features
- **Zero Race Conditions:** Uses Redis `SET NX` (Mutex) to ensure atomic inventory checks.
- **Scalable:** Workers can be scaled horizontally (`docker-compose up --scale worker=3`).
- **Fault Tolerant:** Failed orders are returned to the queue for retry.

##  How to Run
1. **Infrastructure:**
   ```bash
   cd terraform
   terraform init && terraform apply
```
