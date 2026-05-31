# FinLit — Personal Finance Platform

Platform for improving financial literacy with personal finance tools.

## Quick Start

### Prerequisites
- **Docker Desktop** (for MongoDB)
- **Python 3.10+**
- **Node.js 18+**

### 1. Start MongoDB (Docker)
```bash
cd Diploma
docker-compose up -d
```
This starts MongoDB on `localhost:27017`.  
Redis is optional — the app works without it (caching disabled).

### 2. Start Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```
Backend API runs at: **http://localhost:8000**  
Swagger docs: **http://localhost:8000/docs**

### 3. Start Frontend (Vue.js)
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at: **http://localhost:5173** ← **Open this in your browser!**

### Endpoints
| URL | Description |
|-----|-------------|
| http://localhost:5173 | **Main app** (open this!) |
| http://localhost:8000/docs | API Swagger documentation |
| http://localhost:8000/health | Health check |

## Architecture
- **Frontend**: Vue.js 3 + Vite + Bootstrap 5 + Chart.js
- **Backend**: Python FastAPI (async)
- **Database**: MongoDB (NoSQL)
- **Cache**: Redis (optional)

## Budget Balancing Algorithm
```
unaccounted_expense = total_expense - sum(category_amounts)
surplus = total_income - total_expense
```
The system automatically calculates unaccounted expenses (cash, transfers, etc.)
and the budget surplus on both client and server side.

## Environment Variables
See `.env.example` for all config options. Key variables:
- `MONGODB_URI`: MongoDB connection string
- `OPENAI_API_KEY`: server-side OpenAI API key for AI chats
- `OPENAI_ASSISTANT_ID`: id of the already-created OpenAI Assistant
