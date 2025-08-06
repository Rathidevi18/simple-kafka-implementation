Bidding System
This project is a real-time bidding system built with a FastAPI backend, Kafka for message queuing, PostgreSQL for persistent storage, and a simple HTML frontend. It allows users to submit bids, view the highest bid, and retrieve all bids. Bids are processed asynchronously via Kafka and stored in both a PostgreSQL database and a log file.
Project Structure
bidding-system/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Backend dependencies
│   ├── Dockerfile           # Dockerfile for FastAPI
│   └── static/
│       └── index.html       # HTML frontend
├── consumers/
│   ├── db_consumer.py       # Kafka consumer for PostgreSQL
│   ├── file_consumer.py     # Kafka consumer for file logging
│   ├── Dockerfile.consumer1 # Dockerfile for db_consumer
│   ├── Dockerfile.consumer2 # Dockerfile for file_consumer
│   └── requirements.txt     # Consumer dependencies
├── init.sql                 # PostgreSQL schema initialization
├── docker-compose.yml       # Docker Compose configuration
├── .gitignore               # Git ignore file
└── README.md                # This file

Features

Frontend: A simple HTML form (index.html) for submitting bids and displaying the highest bid.
Backend: FastAPI application with endpoints:
POST /submit_bid: Submits a bid to Kafka.
GET /highest_bid: Retrieves the highest bid from PostgreSQL.
GET /bids: Retrieves all bids from PostgreSQL.
GET /: Serves the HTML frontend.


Message Queue: Kafka handles asynchronous bid processing with a bids topic (3 partitions).
Consumers:
Two PostgreSQL consumers (postgres-group) insert bids into the bids table.
One file consumer (file-group) logs bids to /app/bids_log/bids.log.


Database: PostgreSQL stores bids with columns id, name, price, and bid_ts.
Deployment: Docker Compose orchestrates Zookeeper, Kafka, PostgreSQL, FastAPI, and consumers.

Prerequisites

Docker and Docker Compose
Git

Setup Instructions

Clone the Repository:
git clone <repository-url>
cd bidding-system


Create .gitignore:Create a .gitignore file to exclude unnecessary files:
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
*.egg-info/
*.egg

# Docker
pgdata/
bids_log/
*.log

# IDE and misc
.idea/
*.swp
*.swo
.DS_Store


Create init.sql:In the project root, create init.sql to initialize the PostgreSQL database:
CREATE TABLE bids (
    id SERIAL PRIMARY KEY,
    name VARCHAR,
    price INTEGER,
    bid_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


Create requirements.txt:

For backend/requirements.txt:fastapi
uvicorn
kafka-python
psycopg2-binary


For consumers/requirements.txt:kafka-python
psycopg2-binary




Build and Run with Docker Compose:
docker-compose up --build


Builds and starts all services (Zookeeper, Kafka, PostgreSQL, FastAPI, and consumers).
Wait for services to be healthy (Kafka and PostgreSQL healthchecks ensure readiness).


Access the Application:

Open http://localhost:8000 in a browser to access the HTML frontend.
Submit bids via the form, which will be processed by Kafka and stored in PostgreSQL and bids.log.



Usage

Submit a Bid:
Enter a name and bid price in the form at http://localhost:8000.
The bid is sent to the FastAPI backend, published to the Kafka bids topic, and processed by consumers.


View Highest Bid:
The frontend displays the highest bid, fetched from /highest_bid.


View All Bids:
Access http://localhost:8000/bids to retrieve all bids from PostgreSQL.


Check Logs:
View bids.log in the bids_log/ directory for logged bids.
Check container logs for debugging:docker-compose logs <service-name>





Services

zookeeper: Coordinates Kafka, running on port 2181.
kafka: Message broker for the bids topic, accessible at kafka:9092.
postgres: PostgreSQL database (bidsdb), accessible at postgres:5432.
fastapi: FastAPI backend, accessible at http://localhost:8000.
consumer1, consumer1b: Kafka consumers (postgres-group) that insert bids into PostgreSQL.
consumer2: Kafka consumer (file-group) that logs bids to bids_log/bids.log.

Notes

Environment Variables: The PostgreSQL password (rathi) is hardcoded for simplicity. In production, use a .env file:touch .env
echo "POSTGRES_PASSWORD=rathi" >> .env

Update docker-compose.yml and consumer scripts to use ${POSTGRES_PASSWORD}.
Scaling Consumers: Add more postgres-group consumers by updating docker-compose.yml or scaling:docker-compose up --scale consumer1=3


Persistence: PostgreSQL data is stored in the pgdata volume, and bids.log is persisted in bids_log/.
Log Rotation: The bids.log file grows indefinitely; implement log rotation in production.

Troubleshooting

Kafka Connection Errors:
Ensure Kafka is healthy:docker-compose logs kafka


Verify kafka:9092 is reachable within the kafka-net network.


PostgreSQL Errors:
Check if init.sql ran correctly:docker-compose exec postgres psql -U postgres -d bidsdb -c "\dt"


Ensure the bids table exists.


Frontend Not Loading:
Verify index.html is in backend/static/.
Check FastAPI logs:docker-compose logs fastapi





Contributing

Fork the repository.
Create a branch: git checkout -b feature-name.
Commit changes: git commit -m "Add feature".
Push to the branch: git push origin feature-name.
Open a pull request.

License
This project is licensed under the MIT License.
