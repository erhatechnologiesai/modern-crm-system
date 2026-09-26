# ApexCRM — Modern Full-Stack Enterprise Customer Relationship Management Platform

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)]()
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)

**ApexCRM** is a production-grade, full-stack Customer Relationship Management (CRM) system engineered to streamline lead capture, company account governance, multi-stage sales deal pipelines, collaborative team tasks, and audit trail observability for high-growth B2B organizations.

---

## 📌 Table of Contents
- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [Database Schema](#database-schema)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
  - [Database Initialization](#database-initialization)
  - [Running Locally](#running-locally)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Docker & Production Deployment](#docker--production-deployment)
- [Security & Compliance](#security--compliance)
- [Future Improvements](#future-improvements)
- [License](#license)

---

## 🌟 Overview
Modern sales teams require unified customer visibility, deterministic pipeline stages, and auditable deal interactions. ApexCRM is built from first principles using an asynchronous FastAPI REST core backed by SQLite/PostgreSQL relational engines, featuring a responsive SaaS dashboard with real-time analytics, kanban deal tracking, and role-based access control.

---

## 🚀 Key Features

- **Authentication & RBAC**: JWT Bearer token authentication with Role-Based Access Control (`admin`, `sales_manager`, `sales_rep`).
- **Deals Pipeline**: Visual stage transitions (`prospect` &rarr; `qualification` &rarr; `proposal` &rarr; `negotiation` &rarr; `closed_won` / `closed_lost`) with win probabilities and pipeline revenue aggregation.
- **Contact & Account Management**: Centralized records linking individual stakeholders to parent corporate entities.
- **Lead Generation Tracking**: Inbound and outbound lead ingestion with estimated values and qualification workflows.
- **Action Items & Task Engine**: Priority-tiered task queue with real-time status transitions.
- **Audit History**: Complete event trail capturing record additions, pipeline movements, and status adjustments.
- **Interactive Analytics**: Dynamic pipeline stage distribution charts rendered with Chart.js.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Client Browser / REST API Client            │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / JSON
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                       FastAPI Router                        │
│  ┌──────────────┬──────────────┬──────────────┬───────────┐  │
│  │ Auth Router  │ Deals Router │ Contact / Org│ Tasks/Logs│  │
│  └──────┬───────┴──────┬───────┴──────┬───────┴─────┬─────┘  │
│         │              │              │             │        │
│         ▼              ▼              ▼             ▼        │
│    Token Verify   Pydantic V2    Audit logger  Stat Aggregator│
└──────────────────────────────┬──────────────────────────────┘
                               │ SQLite / Connection Pool
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              Relational Storage (crm.db)                    │
│  - users        - companies     - contacts    - leads        │
│  - deals        - tasks         - notes       - activity_logs│
└─────────────────────────────────────────────────────────────┘
```

---

## 💻 Tech Stack

- **Backend**: Python 3.12+, FastAPI, Uvicorn, Starlette
- **Data Validation**: Pydantic v2
- **Database**: SQLite3 (Production convertible to PostgreSQL via connection string)
- **Frontend**: HTML5, Modern CSS, Tailwind CSS CDN, Chart.js, FontAwesome 6
- **Testing**: Pytest, Starlette TestClient, HTTPX
- **DevOps**: Docker, Docker Compose

---

## 💾 Database Schema

The database provides relational integrity with cascading foreign keys:
- `users`: Credentials, full names, roles, account status.
- `companies`: Account names, industry sector, revenue metrics, geography.
- `contacts`: Individual person profiles linked to companies with email verification.
- `leads`: Early-stage sales inquiries with value estimations.
- `deals`: Commercial deal records with probability scoring and stage progression.
- `tasks`: Action items assigned to users with priority and due dates.
- `activity_logs`: Immutable audit trail for all system events.

---

## 🛠️ Getting Started

### Prerequisites
- Python 3.12 or higher
- Git
- Docker (optional)

### Installation
```bash
# Clone the repository
git clone https://github.com/erhatechnologiesai/01-modern-crm-system.git
cd 01-modern-crm-system

# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default parameters:
```env
APP_NAME="ApexCRM - Modern CRM Platform"
APP_ENV=development
SECRET_KEY=crm-super-secret-key-change-in-production-123456789
PORT=8001
HOST=0.0.0.0
```

### Running Locally
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```
Navigate to:
- **Interactive UI**: `http://localhost:8001`
- **Interactive Swagger Docs**: `http://localhost:8001/docs`
- **ReDoc Specification**: `http://localhost:8001/redoc`

Default Admin Credentials:
- **Email**: `admin@apexcrm.io`
- **Password**: `Admin@Apex2026!`

---

## 📡 API Documentation

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/auth/login` | Authenticate user & return JWT token | No |
| `POST` | `/api/auth/register` | Register new user account | No |
| `GET` | `/api/auth/me` | Fetch active user profile | Yes |
| `GET` | `/api/companies` | List companies with search and pagination | Yes |
| `POST` | `/api/companies` | Create new company record | Yes |
| `GET` | `/api/contacts` | List contacts with status filters | Yes |
| `POST` | `/api/contacts` | Create new contact record | Yes |
| `GET` | `/api/deals` | List deals in pipeline | Yes |
| `POST` | `/api/deals` | Register new commercial deal | Yes |
| `PUT` | `/api/deals/{id}` | Update deal details and pipeline stage | Yes |
| `GET` | `/api/tasks` | Retrieve actionable team tasks | Yes |
| `PATCH`| `/api/tasks/{id}/status`| Update task completion status | Yes |
| `GET` | `/api/analytics/dashboard`| Aggregate pipeline metrics and logs | Yes |
| `GET` | `/api/health` | Service health status | No |

---

## 🧪 Testing

Execute the automated test suite with pytest:
```bash
pytest tests/ -v
```

---

## 🐳 Docker & Production Deployment

Run ApexCRM with Docker Compose:
```bash
docker-compose up --build -d
```
Access the service at `http://localhost:8001`.

---

## 🔒 Security & Compliance

- **Password Hashing**: Cryptographic salting with SHA-256 / bcrypt digest validation.
- **HMAC Signatures**: Signed tamper-proof bearer tokens with expiration enforcement.
- **Input Sanitization**: Strict Pydantic model validation on all HTTP inputs.
- **Audit Trails**: Every mutation triggers structured entries in the activity log.

---

## 🔮 Future Improvements

- PostgreSQL native driver integration with asyncpg.
- Real-time WebSocket broadcasting for live collaborative deal updates.
- Automated webhook triggers for external invoicing or ERP integrations.

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
