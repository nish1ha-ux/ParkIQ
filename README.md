# 🚗 ParkIQ — AI-Powered Smart Parking Intelligence Platform

ParkIQ is an AI-powered smart parking management platform designed to make parking more intelligent, secure, and convenient for both vehicle owners and parking administrators.

The platform combines real-time parking management, secure vehicle QR identification, AI-based predictions, RAG-powered assistance, analytics, and automated notifications into one system.

---

## ✨ Key Features

### 👤 Driver Features
- Secure user authentication with JWT
- Vehicle registration and management
- Physical vehicle QR code
- Real-time parking session tracking
- Parking countdown timer
- Checkout and payment workflow
- AI-powered estimated departure prediction
- Parking notifications
- AI/RAG parking assistant
- Privacy-safe public QR status

### 🏢 Admin Features
- Parking occupancy dashboard
- Live parking telemetry
- Occupancy forecasting
- Peak congestion prediction
- Revenue analytics
- Parking session monitoring
- Fraud detection
- AI-powered parking insights

### 🤖 AI Features
- Departure time prediction
- Parking occupancy prediction
- Intelligent slot recommendation
- Congestion prediction
- Fraud detection
- RAG-powered parking assistant
- Grounded responses using parking knowledge documents

### 🔐 Security
- JWT authentication
- Role-based access control
- AES-256-GCM protected QR references
- Tamper protection
- QR replay protection
- Privacy-safe public QR information
- Rate limiting and protected AI endpoints
- Environment-based secrets
- Production configuration validation

---

## 🏗️ System Architecture

```text
                    ┌─────────────────────┐
                    │   React Frontend    │
                    │ TypeScript +        │
                    │ Tailwind CSS        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   FastAPI Backend   │
                    │ Authentication      │
                    │ Parking Management  │
                    │ QR & Sessions       │
                    └──────┬───────┬──────┘
                           │       │
                 ┌─────────┘       └─────────┐
                 ▼                           ▼
        ┌─────────────────┐        ┌─────────────────┐
        │   PostgreSQL    │        │      Redis      │
        │   / SQLite      │        │ Cache & State   │
        └─────────────────┘        └─────────────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │   AI Service     │
                  │ Python + FastAPI │
                  └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │ AI / RAG Layer   │
                  │ Gemini +          │
                  │ LangChain +       │
                  │ ChromaDB          │
                  └──────────────────┘

## 🛠️ Tech Stack

### Frontend
- React
- TypeScript
- Tailwind CSS
- Vite

### Backend
- Python
- FastAPI
- SQLAlchemy
- JWT Authentication
- WebSockets

### AI / ML
- Python
- Scikit-learn
- Google Gemini
- LangChain
- ChromaDB

### Database & Infrastructure
- SQLite
- Redis
- Docker
- Docker Compose

### Planned Production Infrastructure
- PostgreSQL / Amazon RDS
- AWS EC2
- Amazon S3
- Amazon ElastiCache
- CloudFront
- CloudWatch

### Planned Integrations
- Razorpay
- Google Maps API
