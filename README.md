# ParkIQ: Enterprise Smart Parking Intelligence Platform

ParkIQ is a state-of-the-art, AI-powered ticketless smart parking platform featuring real-time visual telemetry, LangChain-based RAG documentation assistance, automated Firebase push alerts, and predictive analytics.

---

## 1. Architectural Overview

```
                        +----------------------------+
                        |  Nginx Container (Port 80) |
                        |     React Frontend (Vite)  |
                        +--------------+-------------+
                                       | (HTTP / WebSocket)
                                       v
                        +----------------------------+
                        | FastAPI Container (8000)  |
                        |      Platform Backend      |
                        +----+-------------+----+----+
                             |             |    |
            (Local Fallback) |   (HTTP)    |    | (SQLAlchemy)
                             |             |    |
                             v             |    v
                   +--------------+        |  +--------------+
                   | Chroma DB    |        |  | PostgreSQL   |
                   | Vector Store |        |  | (Port 5432)  |
                   +--------------+        |  +--------------+
                                           v
                        +----------------------------+
                        | FastAPI Container (8001)  |
                        |    AI Prediction Engine    |
                        +----------------------------+
```

ParkIQ is composed of four main microservice blocks:
1. **React Frontend (Nginx)**: Visual dashboard styled with Tailwind CSS, drawing telemetry and charts via Recharts.
2. **FastAPI Backend (Uvicorn)**: Relational model coordinator handling gate scanning, active session tracking, and WebSockets. Includes a LangChain RAG vector index using Chroma.
3. **AI Microservice**: Gradient Boosting and Isolation Forest inference engine for occupancy forecasting and QR fraud checks.
4. **PostgreSQL & Redis**: Database records and telemetry cache.

---

## 2. Local Desktop Run Instructions

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL server

### Step 1: Start Backend API
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
$env:DATABASE_URL="postgresql+psycopg2://parkiq:parkiq_pass@localhost:5432/parkiq_db"
uvicorn app.main:app --reload
```

### Step 2: Start AI Service
```bash
cd ai_service
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --port 8001 --reload
```

### Step 3: Start Frontend SPA
```bash
cd frontend
npm install
npm run dev
```
Navigate to `http://localhost:5173`. Use preset login credentials (e.g. `driver@parkiq.com` / `driver123`) to authenticate.

---

## 3. Docker Compose Local Execution

To run the entire ParkIQ ecosystem in a single container network locally:

```bash
# Build and boot all containers (Postgres, Redis, Backend, AI Service, and Frontend)
docker compose up --build -d

# Verify all services are online
docker compose ps
```

The services will be exposed at:
- **Frontend SPA Portal**: `http://localhost:80`
- **Backend API Gateway**: `http://localhost:8000/docs`
- **AI Inference microservice**: `http://localhost:8001`

---

## 4. Production AWS Deployment Guide

We prepare AWS production deployment using **Terraform** for resource provisioning, **AWS ECR** for image management, and **EC2/RDS/S3** for runtime hosting.

### Step 1: Provision Cloud Resources
Initialize and run Terraform from the `/aws_deployment` folder:

```bash
cd aws_deployment

# Initialize AWS provider plugin
terraform init

# Generate deployment execution blueprint
terraform plan -out=tfplan.binary

# Provision EC2, RDS PostgreSQL, and S3 Bucket
terraform apply tfplan.binary
```

*Note: Save the outputs displaying the EC2 host IP, RDS Postgres database endpoint hostname, and S3 bucket details.*

### Step 2: Build & Push Images to ECR
Authenticate with AWS ECR and push your Docker containers:

```bash
# Login to AWS ECR registry
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# Build and tag containers
docker build -t parkiq-backend ./backend
docker tag parkiq-backend:latest <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/parkiq-backend:latest

docker build -t parkiq-ai-service ./ai_service
docker tag parkiq-ai-service:latest <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/parkiq-ai-service:latest

docker build -t parkiq-frontend ./frontend
docker tag parkiq-frontend:latest <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/parkiq-frontend:latest

# Push to Amazon registry
docker push <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/parkiq-backend:latest
docker push <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/parkiq-ai-service:latest
docker push <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/parkiq-frontend:latest
```

### Step 3: Run Application on EC2
SSH into the EC2 host, download the `docker-compose.yml` file, configure the production parameters (pointing to RDS Postgres instead of local Postgres), and launch the app:

```bash
# SSH into EC2 Server
ssh -i "your-key.pem" ubuntu@<EC2_PUBLIC_IP>

# Create deployment folder and pull compose config
mkdir deployment && cd deployment
curl -o docker-compose.yml https://raw.githubusercontent.com/your-repo/parkiq/main/docker-compose.yml

# Edit the compose file environment variables:
# - DATABASE_URL = postgresql+psycopg2://parkiq_admin:<RDS_PASSWORD>@<RDS_ENDPOINT>:5432/parkiq_prod
# - Replace image builds with ECR images.

# Boot application
docker compose up -d
```
Your enterprise platform is now fully deployed and secure!
