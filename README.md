# FreeGameFinder 🎮

![Screenshot do FreeGameFinder](./screenshot.png)

**FreeGameFinder** is a full-stack application designed to track and notify you about temporarily free games from the Epic Games Store and Steam.

## 🚀 The Goal
Tracking free games across multiple platforms is tedious. You often miss limited-time offers or forget to check the stores. **FreeGameFinder** solves this by:
- Centralizing active giveaways in one place.
- Automatically scanning for new deals every 30 minutes.
- Sending email alerts directly to verified subscribers so you never miss a game.

## 🛠 Tech Stack
- **Backend:** FastAPI (Python), SQLAlchemy, APScheduler, httpx.
- **Frontend:** React, Vite, Tailwind CSS.
- **Database:** PostgreSQL.
- **Infrastructure:** Docker & Docker Compose.

## ⚡ Quick Start

### 1. Requirements
- Docker and Docker Compose.

### 2. Setup Environment
Copy the example environment file and fill in your SMTP credentials (for email alerts):
```bash
cp .env.example .env
```
> **Note:** For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833).

### 3. Run with Docker
```bash
docker compose up -d
```
The application will be available at:
- **Frontend:** `http://localhost:5173`
- **Backend API:** `http://localhost:8000`

## 📡 API Endpoints
- `GET /api/v1/games`: List all found free games.
- `POST /api/v1/subscribe`: Register a new email for alerts.
- `GET /api/v1/health`: Check database and API status.

---
Built to ensure you never miss a free "masterpiece" (or just another simulator) again.
