<div align="center">

# 🚗 ParkIQ

### AI-Powered Smart Parking Intelligence Platform

<p>
  <strong>Smart Parking • Artificial Intelligence • Real-Time Systems • Security • RAG • Cloud</strong>
</p>

<br>

<img src="https://img.shields.io/badge/Status-Active%20Development-22c55e?style=for-the-badge" />
<img src="https://img.shields.io/badge/Tests-23%2F23%20Passing-22c55e?style=for-the-badge" />
<img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
<img src="https://img.shields.io/badge/AI%2FML-Enabled-8B5CF6?style=for-the-badge" />

<br><br>

<img src="https://img.shields.io/badge/React-TypeScript-61DAFB?style=flat-square&logo=react&logoColor=black" />
<img src="https://img.shields.io/badge/FastAPI-Python-009688?style=flat-square&logo=fastapi&logoColor=white" />
<img src="https://img.shields.io/badge/TailwindCSS-38BDF8?style=flat-square&logo=tailwindcss&logoColor=white" />
<img src="https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white" />
<img src="https://img.shields.io/badge/LangChain-1C3C3C?style=flat-square&logo=chainlink&logoColor=white" />
<img src="https://img.shields.io/badge/Gemini-AI-4285F4?style=flat-square&logo=google&logoColor=white" />
<img src="https://img.shields.io/badge/ChromaDB-RAG-FF6F61?style=flat-square" />

</div>

---

## 🌐 What is ParkIQ?

<table>
<tr>
<td width="65%">

**ParkIQ** is an AI-powered smart parking intelligence platform designed to make parking **smarter, safer, and more convenient**.

Unlike traditional parking systems that only focus on assigning spaces, ParkIQ combines:

- 🅿️ Real-time parking management
- 🚗 Vehicle-based QR identification
- 🤖 AI-powered predictions
- 📊 Parking analytics
- 🔐 Privacy-focused security
- 🧠 Retrieval-Augmented Generation (RAG)
- 🔔 Intelligent notifications
- 💳 Digital checkout workflow
- 🐳 Containerized infrastructure

The platform is designed around two major users:

**Drivers** manage their vehicles, QR identity, parking sessions, payments, and notifications.

**Administrators** monitor parking operations, occupancy, revenue, congestion, security, and AI-generated insights.

</td>

<td width="35%">

### 🎯 Core Idea

> **Turn a parking garage into an intelligent, data-driven system.**

<br>

🅿️  
**Smart Parking**

⬇️

🤖  
**AI Intelligence**

⬇️

📊  
**Real-Time Analytics**

⬇️

🔐  
**Secure & Private**

⬇️

☁️  
**Cloud Ready**

</td>
</tr>
</table>

---

# ✨ Key Features

<table>
<tr>
<td width="50%">

### 🚗 Smart Parking

- Vehicle registration
- Parking session management
- Real-time countdown
- Session checkout
- Occupancy monitoring
- Slot recommendation
- Parking activity tracking

</td>

<td width="50%">

### 🔐 Secure Vehicle QR

- Persistent physical vehicle QR
- AES-256-GCM protection
- Tamper protection
- Replay protection
- Privacy-safe public scanning
- Anti-enumeration protection

</td>
</tr>

<tr>
<td>

### 🤖 AI Intelligence

- Departure prediction
- Occupancy forecasting
- Slot recommendation
- Congestion prediction
- Fraud detection
- Intelligent notifications

</td>

<td>

### 🧠 RAG Assistant

- Parking rules
- Pricing information
- Facility information
- EV charging guidance
- Emergency procedures
- Visitor instructions
- Grounded responses
- Out-of-domain protection

</td>
</tr>

<tr>
<td>

### 🏢 Admin Intelligence

- Live parking dashboard
- Occupancy analytics
- Revenue analytics
- Peak congestion analysis
- Live telemetry
- Security monitoring
- AI insights

</td>

<td>

### 🛡️ Authentication & Security

- JWT authentication
- Role-Based Access Control
- Driver / Staff / Admin roles
- Protected APIs
- Protected AI endpoints
- Environment-based secrets
- Production configuration validation

</td>
</tr>
</table>

---

# 🚗 Vehicle QR System

ParkIQ is designed around a **physical QR code attached to each vehicle**.

The QR is persistent and does **not** need to be physically replaced or reprinted every few minutes.

When the vehicle owner parks, the backend associates the vehicle with the active parking session.

When another person scans the QR, ParkIQ can provide a privacy-safe status.

### 👀 Public Scan

<table>
<tr>
<td>

### ✅ Information that may be shown

🟢 Parking Active / Inactive  
⏱️ Approximate remaining time  
🚗 Estimated departure  
🔔 General status such as **Leaving Soon**

</td>

<td>

### ❌ Information that is protected

🔒 Owner name  
🔒 Phone number  
🔒 Email  
🔒 Payment information  
🔒 Exact parking slot  
🔒 Private account information

</td>
</tr>
</table>

> **Privacy principle:** A public QR scan should provide useful parking information without exposing the vehicle owner's personal information.

---

# 🤖 AI-Powered Parking Intelligence

ParkIQ separates its AI functionality into a dedicated Python/FastAPI service.

### AI Pipeline

```text
                PARKING DATA
                     │
                     ▼
          ┌─────────────────────┐
          │   AI Prediction     │
          │      Service        │
          └──────────┬──────────┘
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
 Departure       Occupancy      Fraud
 Prediction      Forecasting    Detection
       │             │             │
       └─────────────┼─────────────┘
                     ▼
             Parking Intelligence
                     │
                     ▼
            Driver / Admin UI
```

### 🧠 AI Capabilities

| Capability | Purpose |
|---|---|
| 🕐 Departure Prediction | Estimate when a parking session may end |
| 🅿️ Occupancy Prediction | Forecast future parking occupancy |
| 📍 Slot Recommendation | Recommend suitable available parking |
| 🚦 Congestion Prediction | Identify potential parking congestion |
| 🛡️ Fraud Detection | Detect suspicious parking activity |
| 🔔 Notification Intelligence | Support timely parking notifications |

---

# 🧠 RAG-Powered Parking Assistant

ParkIQ includes a **Retrieval-Augmented Generation assistant**.

Instead of relying only on a language model's general knowledge, the assistant can retrieve relevant information from a curated parking knowledge base.

```text
User Question
      │
      ▼
┌───────────────┐
│ Query Handler │
└───────┬───────┘
        │
        ▼
┌────────────────┐
│ Vector Search  │
│   ChromaDB     │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ Relevant Docs  │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ Gemini / LLM   │
└───────┬────────┘
        │
        ▼
 Grounded Response
```

### 📚 Knowledge Sources

The system can be grounded using information such as:

- Parking rules
- Pricing
- Visitor manuals
- Facility information
- EV charging guides
- Emergency procedures
- FAQs
- Parking layouts

The system also includes an **out-of-domain fallback** to reduce unsupported answers.

---

# 🏗️ System Architecture

```text
                         ┌────────────────────────┐
                         │      React Frontend     │
                         │   TypeScript + Vite     │
                         │      Tailwind CSS       │
                         └────────────┬───────────┘
                                      │
                                      │ REST / WebSocket
                                      ▼
                         ┌────────────────────────┐
                         │     FastAPI Backend     │
                         │                        │
                         │ Authentication         │
                         │ Vehicles               │
                         │ Parking Sessions       │
                         │ QR Management           │
                         │ Payments                │
                         │ Analytics               │
                         └───────┬────────┬───────┘
                                 │        │
                     ┌───────────┘        └────────────┐
                     ▼                                 ▼
           ┌─────────────────┐               ┌─────────────────┐
           │    Database     │               │      Redis      │
           │                 │               │                 │
           │ SQLite          │               │ Cache / State   │
           │ PostgreSQL*     │               │                 │
           └─────────────────┘               └─────────────────┘
                     │
                     │
                     ▼
           ┌────────────────────┐
           │     AI Service     │
           │    Python/FastAPI  │
           └──────────┬─────────┘
                      │
                      ▼
           ┌────────────────────┐
           │    AI / RAG Layer  │
           │                    │
           │ Scikit-learn       │
           │ Gemini             │
           │ LangChain          │
           │ ChromaDB           │
           └────────────────────┘

* PostgreSQL planned for production deployment
```

---

# 🔄 Complete User Workflow

```text
                    ┌─────────────────┐
                    │ Driver Registers│
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │ Add Vehicle     │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │ Physical QR     │
                    │ Assigned        │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │ Start Parking   │
                    │ Session         │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │ Track Duration  │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │ AI Departure    │
                    │ Prediction      │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │ Owner           │
                    │ Notification    │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │ Public QR       │
                    │ Status          │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │ Checkout &      │
                    │ Payment         │
                    └─────────────────┘
```

---

# 🖥️ Application Modules

<table>
<tr>
<td align="center" width="25%">

### 🚗

**Driver**

Vehicle  
Parking  
QR  
Payments

</td>

<td align="center" width="25%">

### 🏢

**Admin**

Dashboard  
Analytics  
Revenue  
Security

</td>

<td align="center" width="25%">

### 🤖

**AI**

Predictions  
Fraud  
Congestion  
Recommendations

</td>

<td align="center" width="25%">

### 🧠

**RAG**

Knowledge  
Retrieval  
Grounded AI  
Assistant

</td>
</tr>
</table>

---

# 🔐 Security Architecture

Security is treated as a core part of the platform.

### Authentication

```text
User
 │
 ▼
Login
 │
 ▼
JWT Authentication
 │
 ▼
Role Verification
 │
 ├───────────────┬───────────────┐
 ▼               ▼               ▼
Driver          Staff           Admin
```

### Security Controls

| Security Layer | Implementation |
|---|---|
| 🔑 Authentication | JWT |
| 👥 Authorization | RBAC |
| 🔐 QR Protection | AES-256-GCM |
| 🛡️ QR Security | Tamper + Replay Protection |
| 🚫 Public Privacy | Minimal information exposure |
| 🤖 AI Security | Protected AI endpoints |
| 🔒 Secrets | Environment variables |
| 🚦 Abuse Protection | Rate limiting / anti-enumeration |
| ⚙️ Production Safety | Configuration validation |

---

# 🛠️ Technology Stack

<table>
<tr>
<td width="50%">

### 🎨 Frontend

- React
- TypeScript
- Tailwind CSS
- Vite
- Responsive UI
- WebSockets

</td>

<td width="50%">

### ⚙️ Backend

- Python
- FastAPI
- SQLAlchemy
- JWT
- REST APIs
- WebSockets

</td>
</tr>

<tr>
<td>

### 🤖 AI / ML

- Python
- Scikit-learn
- Google Gemini
- LangChain
- ChromaDB
- RAG

</td>

<td>

### 🗄️ Data & Infrastructure

- SQLite
- PostgreSQL*
- Redis
- Docker
- Docker Compose

</td>
</tr>

<tr>
<td>

### 💳 Integrations

- Razorpay*
- Google Maps API*

</td>

<td>

### ☁️ Planned Cloud

- AWS EC2
- Amazon RDS
- Amazon S3
- ElastiCache
- CloudFront
- CloudWatch

</td>
</tr>
</table>

> `*` Planned or environment-dependent integration.

---

# 🐳 Docker Architecture

ParkIQ is containerized to provide a consistent development environment.

```text
                Docker Compose
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
    Frontend      Backend      AI Service
        │            │            │
        │            ├────────────┤
        │            │
        │        ┌───┴────┐
        │        ▼        ▼
        │     Redis    Database
        │
        └───────────────┘
```

### Run Locally

#### 1. Clone

```bash
git clone https://github.com/YOUR_USERNAME/ParkIQ.git
cd ParkIQ
```

#### 2. Configure Environment

Create a local `.env` file using:

```text
.env.example
```

as the template.

> ⚠️ Never commit real API keys, passwords, JWT secrets, or credentials.

#### 3. Start

```bash
docker compose up --build
```

#### 4. Stop

```bash
docker compose down
```

> ⚠️ Avoid `docker compose down -v` unless you intentionally want to remove persistent Docker volumes.

---

# 📁 Project Structure

```text
ParkIQ/
│
├── backend/
│   ├── app/
│   ├── tests/
│   └── ...
│
├── ai_service/
│   ├── app/
│   └── ...
│
├── frontend/
│   ├── src/
│   ├── public/
│   └── ...
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

# 🧪 Testing & Validation

ParkIQ has been validated across multiple layers of the application.

<table>
<tr>
<td align="center">

### ✅

**23 / 23**

Tests Passing

</td>

<td align="center">

### 🔐

**Security**

QR + Auth Validation

</td>

<td align="center">

### 🤖

**AI**

Prediction Validation

</td>

<td align="center">

### 🐳

**Docker**

Integration Validation

</td>
</tr>
</table>

### Tested Areas

- ✅ Authentication
- ✅ JWT authorization
- ✅ Vehicle registration
- ✅ Parking sessions
- ✅ Parking countdown
- ✅ Checkout workflow
- ✅ QR generation
- ✅ QR tamper protection
- ✅ QR replay protection
- ✅ Public QR privacy
- ✅ AI departure prediction
- ✅ Occupancy prediction
- ✅ Slot recommendation
- ✅ Fraud detection
- ✅ RAG assistant
- ✅ Admin dashboard
- ✅ Analytics
- ✅ Docker integration
- ✅ Frontend build
- ✅ End-to-end browser workflow

---

# 📊 Current Project Status

<table>
<tr>
<td width="33%" align="center">

🟢

### Core Platform

**Implemented**

</td>

<td width="33%" align="center">

🟢

### AI + RAG

**Implemented**

</td>

<td width="33%" align="center">

🟢

### Docker

**Validated**

</td>
</tr>

<tr>
<td align="center">

🟢

### Security

**Validated**

</td>

<td align="center">

🟢

### Testing

**23/23 Passing**

</td>

<td align="center">

🟡

### AWS Deployment

**Next Phase**

</td>
</tr>
</table>

---

# 🚀 Roadmap

### Phase 1 — Foundations

- [x] Backend architecture
- [x] Authentication
- [x] Vehicle management
- [x] Parking sessions
- [x] Database integration
- [x] Redis integration
- [x] Docker environment

### Phase 2 — Intelligence

- [x] Departure prediction
- [x] Occupancy prediction
- [x] Slot recommendation
- [x] Fraud detection
- [x] RAG assistant
- [x] AI service integration

### Phase 3 — Security

- [x] JWT authentication
- [x] RBAC
- [x] Secure QR
- [x] QR tamper protection
- [x] QR replay protection
- [x] Privacy-safe public scanning
- [x] Production configuration checks

### Phase 4 — Product Experience

- [x] Driver dashboard
- [x] Admin dashboard
- [x] Parking workflow
- [x] QR workflow
- [x] Analytics
- [ ] Final UI/UX polish
- [ ] Final demo preparation

### Phase 5 — Cloud

- [ ] AWS EC2 deployment
- [ ] PostgreSQL / RDS
- [ ] Redis / ElastiCache
- [ ] S3
- [ ] CloudFront
- [ ] CloudWatch
- [ ] HTTPS + domain
- [ ] CI/CD with GitHub Actions

### Phase 6 — Future

- [ ] React Native mobile application
- [ ] Real parking sensor integration
- [ ] Automatic number plate recognition
- [ ] Dynamic pricing
- [ ] EV charging prediction
- [ ] Advanced parking demand forecasting

---

# 💡 Why ParkIQ?

Traditional parking systems often focus on:

```text
Find Slot → Park → Pay → Leave
```

ParkIQ expands this into:

```text
        REAL-TIME DATA
              │
              ▼
        AI INTELLIGENCE
              │
              ▼
        PREDICTIONS
              │
              ▼
      SMART NOTIFICATIONS
              │
              ▼
      SECURE QR ECOSYSTEM
              │
              ▼
       BETTER OPERATIONS
```

The goal is to demonstrate how **AI/ML, backend engineering, security, real-time systems, RAG, and cloud infrastructure** can work together to solve a practical problem.

---

# 🎯 Project Highlights

<table>
<tr>
<td>

### 🅿️ Smart Parking

Real-time parking session management and occupancy intelligence.

</td>
<td>

### 🤖 AI-Driven

Predictions and recommendations instead of simple rule-based parking.

</td>
</tr>

<tr>
<td>

### 🔐 Privacy First

Public QR scanning without exposing sensitive owner information.

</td>
<td>

### 🧠 RAG Assistant

Knowledge-grounded AI for parking-related questions.

</td>
</tr>

<tr>
<td>

### 🐳 Containerized

Docker-based development and deployment architecture.

</td>
<td>

### ☁️ Cloud Ready

Architecture designed for AWS production deployment.

</td>
</tr>
</table>

---

# 🔮 Future Vision

ParkIQ can evolve into a complete intelligent parking ecosystem connecting:

```text
Vehicles
   │
   ▼
Physical QR
   │
   ▼
Parking Infrastructure
   │
   ├──────────────┐
   ▼              ▼
Sensors          Cameras
   │              │
   └──────┬───────┘
          ▼
     Data Platform
          │
          ▼
     AI Intelligence
          │
     ┌────┼────┐
     ▼    ▼    ▼
  Drivers Admin Operators
```

Future versions can incorporate **IoT sensors, computer vision, automatic number plate recognition, mobile applications, dynamic pricing, EV infrastructure, and large-scale cloud analytics.**

---

# 👩‍💻 Developer

<div align="center">

## Nishtha Bhushan

**B.Tech — Computer Science & Engineering (AI/ML)**  
**KIIT University, Odisha**

Building at the intersection of:

**AI/ML × Cloud × Software Engineering × Intelligent Systems**

</div>

---

# 📌 Project Status

<div align="center">

### 🚧 ACTIVE DEVELOPMENT

The core ParkIQ platform has been implemented and validated.

**23/23 tests passing**

Current focus:

**UI/UX → Cloud Deployment → CI/CD → Production Readiness**

<br>

⭐ **If you find this project interesting, consider starring the repository!**

</div>

---

<div align="center">

### 🚗 ParkIQ

**Making Parking Intelligent.**

<br>

`AI` • `RAG` • `Security` • `Real-Time Systems` • `Cloud`

</div>
