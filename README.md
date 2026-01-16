# ConfAI – Smart Conference & Meeting Room Management System

ConfAI is an AI-assisted conference and meeting room booking system.  
It allows users to book rooms, manage schedules, check in to meetings, and interact using a chat-based assistant.


---

## Features

- JWT-based authentication
- Room listing with capacity
- Slot-based room availability (day-wise)
- Chat-based meeting booking assistant
- Online & offline meetings
- Overlap and conflict detection
- Auto-cancel if no check-in
- Participant schedules
- Check-in system (host + participants)
- Dashboard with real-time statistics
- Minimal, clean UI

---

## Tech Stack

### Backend
- Python
- FastAPI
- SQLAlchemy
- SQLite
- JWT Authentication

### Frontend
- React (Vite)
- Tailwind CSS

---

## Prerequisites

- Python 3.10+
- Node.js 18+
- Git

Ensure Python and Node are added to PATH.

---

## Project Structure

```
confai/
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── requirements.txt
│   └── ...
├── frontend/
│   ├── src/
│   ├── package.json
│   └── ...
└── README.md
```

---

## Setup Instructions

### Clone the Repository

```bash
git clone <your-repo-url>
cd confai
```

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

download ollama from https://ollama.com/download 
ollama pull phi3:mini

uvicorn main:app --reload
```

Backend runs at http://127.0.0.1:8000

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://127.0.0.1:5173

---

## Usage Flow

1. Register a user
2. Login through the UI
3. View available rooms
4. Navigate room slots by date
5. Book meetings using slots or chat
6. View personal schedules
7. Check in during meeting time

---

## Notes

- Start backend before frontend
- SQLite database auto-creates
- Local demo only, not production-ready

---

## Author

ConfAI – Final Year Project
