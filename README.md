# ⚡ Zenith '26 College Fest Management System

> A high-performance, full-stack college fest operations platform with student self-service event registration and a real-time coordinator dashboard.  
> **Course:** HSB — Product Management II: Technology & Agile Execution (`PM2-01` & `PM2-02`).

---

## 📖 Overview

**Zenith '26** is the flagship annual college fest happening **November 14–15, 2026**. This system powers both sides of the fest operations:

1. **Student Event Portal (`/` or `index.html`)**:
   - Real-time catalog of 14 seed events across 5 categories (*Technical, Cultural, Sports, Gaming, Workshop*).
   - Live seat-capacity computation (`available_seats = capacity - registrations`).
   - Server-side category filtering and instant keyword search.
   - Self-service registration modal with client-side feedback and atomic server-side validation.
   - Distinct badges for event capacity, fees, categories, and `"FULL"` sold-out events.

2. **Coordinator Admin Dashboard (`/admin.html`)**:
   - Live key metrics: *Total Events, Total Registrations, Overall Capacity Utilization %, Upcoming Events*.
   - Visual breakdown of events by category.
   - Utilization ranking table sorted by highest demand descending, highlighting events above **90% capacity** in warning colors.
   - Comprehensive student roster (`GET /api/registrations`) filterable by event.
   - **Stretch Capabilities**: Add new events (`POST /api/events`) and cancel registrations (`DELETE /api/registrations/{id}`) with instant seat liberation.

---

## 🛠️ Tech Stack & Architecture

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | HTML5, Tailwind CSS (Play CDN), Vanilla JavaScript (ES6+) | Mobile-first UI, responsive grid, dynamic DOM rendering, client-side validation |
| **Backend** | Python 3.10+, FastAPI, Uvicorn, Pydantic v2 | RESTful API, asynchronous server, strict request/response validation, static file serving |
| **Database** | SQLite3 (`fest.db`) | Relational persistence, foreign key enforcement, unique constraints (`event_id`, `email`) |
| **Data Seed** | `openpyxl`, `data/events_seed.xlsx` | Reads 14 fest events from companion Excel sheet on initial startup without hardcoding |
| **Testing** | Postman Desktop App | Automated collection of 18 test requests verifying status codes and error models |

---

## 📂 Project Directory Structure

```text
zenith26-fest-system/
├── backend/
│   ├── __init__.py
│   ├── database.py       # SQLite connection, schema tables (events, registrations)
│   ├── main.py           # FastAPI routes, CORS, validation, static mounting
│   ├── models.py         # Pydantic schemas (EventOut, RegistrationIn, StatsOut, etc.)
│   └── seed_data.py      # openpyxl loader reading data/events_seed.xlsx
├── data/
│   └── events_seed.xlsx  # 14 seed fest events (Source of Truth)
├── frontend/
│   ├── index.html        # Student event discovery & registration portal
│   ├── admin.html        # Fest coordinator operations & analytics dashboard
│   └── js/
│       ├── app.js        # Student portal logic: fetch, filter, search, register
│       └── admin.js      # Admin dashboard logic: stats, sorting, table rendering
├── Postman-Testing-Commands-Zenith26.md    # Step-by-step test guide (18 cases)
├── zenith26-api.postman_collection.json   # Ready-to-import Postman collection
├── requirements.txt      # fastapi, uvicorn, pydantic, openpyxl
└── README.md             # Project documentation and execution instructions
```

---

## 🚀 Getting Started: How to Run the App

### Prerequisites
- Python 3.10 or higher installed (`python --version`)
- Modern web browser (Chrome, Edge, Firefox, Safari)

### 1. Open Terminal & Navigate to Project
```powershell
cd zenith26-fest-system
```

### 2. Activate Virtual Environment & Install Dependencies
```powershell
# Create virtual environment if not already created
python -m venv .venv

# Activate on Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### 3. Ensure Companion Seed File is in Place
Verify `events_seed.xlsx` is inside `data/events_seed.xlsx`. (The app will automatically initialize and populate the SQLite database `fest.db` upon starting).

### 4. Start the FastAPI Server
```powershell
uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload
```

### 5. Access the Web Applications
- **Student Event Portal:** [http://127.0.0.1:8001/](http://127.0.0.1:8001/)
- **Admin Dashboard:** [http://127.0.0.1:8001/admin.html](http://127.0.0.1:8001/admin.html)
- **Interactive Swagger API Docs:** [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
- **ReDoc Alternative Docs:** [http://127.0.0.1:8001/redoc](http://127.0.0.1:8001/redoc)

---

## 🔌 API Endpoints Contract

| Method | Endpoint | Description | Response Status |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/events` | List all events with computed `available_seats`. Optional query params: `?category=...&search=...` | `200 OK` |
| `GET` | `/api/events/{event_id}` | Single event details with live seat availability. Returns 404 if ID does not exist. | `200 OK`, `404 Not Found` |
| `POST` | `/api/events/{event_id}/register` | Registers student. Server checks: required fields, `@` in email, event capacity (409 if full), duplicate registration (409). | `201 Created`, `400 Bad Request`, `404 Not Found`, `409 Conflict` |
| `GET` | `/api/registrations` | List student registrations with event title. Optional query param: `?event_id=...` | `200 OK` |
| `GET` | `/api/stats` | Live computed operations stats: `total_events`, `total_registrations`, `overall_utilization_pct`, etc. | `200 OK` |
| `POST` | `/api/events` *(Stretch)* | Admin adds a new fest event with capacity & fee validation. | `201 Created`, `400 Bad Request` |
| `DELETE` | `/api/registrations/{id}` *(Stretch)* | Admin cancels registration and restores available seat count. | `200 OK`, `404 Not Found` |

---

## 🧪 Postman API Testing

1. Open Postman Desktop.
2. Click **Import** and select `zenith26-api.postman_collection.json`.
3. The collection is pre-configured with `{{baseUrl}} = http://127.0.0.1:8001`.
4. Follow the test guide in `Postman-Testing-Commands-Zenith26.md` covering all 18 test cases across status codes `200`, `201`, `400`, `404`, and `409`.

---

## 🛡️ "Never Trust the Client" Validation Architecture

This project implements dual-layer validation to illustrate critical product security principles:
1. **Client-Side UX Validation (`app.js`)**: Prevents empty submissions and malformed emails directly in the browser to give instant user feedback.
2. **Server-Side Truth Validation (`main.py`)**: Re-verifies every single field, queries capacity limits from `fest.db`, and enforces database uniqueness constraints. Even if an API request bypasses the web form (via curl, Postman, or malicious script), invalid data can never corrupt the database state.
