# Flux-Order: High-Concurrency Ticketing System
![CI Status](https://github.com/Tannishaa/flux-order/actions/workflows/ci.yml/badge.svg)

*A resilient, event-driven microservices architecture designed to handle high-traffic flash sales without race conditions or inventory overselling.*

## Architecture
```mermaid
graph TD
    User((User)) -->|POST /buy| API[Flask API]
    API -->|1. Push Order| SQS[(AWS SQS Queue)]
    SQS -->|2. Poll Message| Worker[Python Worker]
    Worker -->|3. Acquire Lock| Redis[(Redis Cache)]
    Redis -->|If Locked| SQS
    Redis -->|If Free| DB[(AWS DynamoDB)]
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

##  How to Run
1. **Infrastructure:**
   ```bash
   cd terraform
   terraform init && terraform apply
   ```
2. **Configuration:**
   Create a `.env` file in the root directory with your AWS credentials and Terraform outputs:
   ```ini
   # AWS Credentials
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_REGION=ap-south-1

   # Infrastructure Config (From Terraform Outputs)
   SQS_QUEUE_URL=https://sqs.ap-south-1.amazonaws.com/123456789/flux-queue-iac
   DYNAMODB_TABLE=FluxOrdersIAC

   # Redis Config
   REDIS_HOST=redis
   REDIS_PORT=6379
   ```
3. **Deploy: Run the containers in the background:**

```Bash

docker-compose up --build -d
```
4. **Observability (Live Monitor)**
Launch the TUI (Terminal User Interface) to see real-time queue depth and worker status:

```Bash

python monitor.py
```
5. **Stress Testing (Locust)**
Simulate thousands of concurrent users to test system resilience:

* Start the swarm:

```Bash

locust
```
* Open http://localhost:8089 in your browser.

* Set Users to 1000, Spawn Rate to 50, and Host to http://localhost:5000.

* Click Start Swarming and watch the dashboard!
6. **Unit Testing**
Run the test suite locally:
```Bash

python -m pytest
```
`Note: This project uses GitHub Actions for automated CI/CD. Every push to main triggers a remote test run.`

## Security & Resilience
**Secret Management:** Utilizes environment variables via `.env` files (excluded from version control) and Docker `env_file` injection.

**Infrastructure Security:** Uses IAM roles with least-privilege access for AWS SQS and DynamoDB interactions.

**History Hygiene:** Repository history is periodically audited and scrubbed of any legacy configuration strings using `git-filter-repo`.