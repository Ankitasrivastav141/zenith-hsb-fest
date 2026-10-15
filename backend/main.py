import os
import sqlite3
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional, Dict
from pydantic import BaseModel

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.database import get_db_connection, init_db
from backend.models import (
    EventOut,
    EventDetail,
    RegistrationIn,
    RegistrationOut,
    RegistrationDetailOut,
    StatsOut,
    EventIn,
)
from backend.seed_data import seed_events

app = FastAPI(
    title="Zenith '26 Fest Management System API",
    description="Backend API for Zenith '26 College Fest Management System",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


@app.on_event("startup")
def startup_event():
    """Ensure database schema is initialized and seeded on startup."""
    init_db()
    try:
        seed_events()
    except Exception as e:
        print(f"Warning during seed: {e}")


# ---------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------

@app.get("/api/events", response_model=List[EventOut])
def get_events(
    category: Optional[str] = Query(None, description="Filter by event category"),
    search: Optional[str] = Query(None, description="Search in event title (case-insensitive)")
):
    """
    Get all events with calculated available_seats.
    Supports filtering by category and searching by title.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT 
            e.id, e.title, e.category, e.description, e.event_date, e.event_time, 
            e.venue, e.capacity, e.fee, e.icon,
            (e.capacity - COUNT(r.id)) AS available_seats
        FROM events e
        LEFT JOIN registrations r ON e.id = r.event_id
    """
    conditions = []
    params = []

    if category and category.strip() and category.lower() != "all":
        conditions.append("LOWER(e.category) = LOWER(?)")
        params.append(category.strip())

    if search and search.strip():
        conditions.append("LOWER(e.title) LIKE LOWER(?)")
        params.append(f"%{search.strip()}%")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " GROUP BY e.id ORDER BY e.id ASC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    events = []
    for row in rows:
        events.append(EventOut(
            id=row["id"],
            title=row["title"],
            category=row["category"],
            description=row["description"],
            event_date=row["event_date"],
            event_time=row["event_time"],
            venue=row["venue"],
            capacity=row["capacity"],
            fee=row["fee"],
            icon=row["icon"],
            available_seats=max(0, row["available_seats"])
        ))
    return events


@app.get("/api/events/{event_id}", response_model=EventDetail)
def get_event_detail(event_id: int):
    """
    Get single event detail by ID with available_seats.
    Returns 404 if event does not exist.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT 
            e.id, e.title, e.category, e.description, e.event_date, e.event_time, 
            e.venue, e.capacity, e.fee, e.icon,
            (e.capacity - COUNT(r.id)) AS available_seats
        FROM events e
        LEFT JOIN registrations r ON e.id = r.event_id
        WHERE e.id = ?
        GROUP BY e.id
    """
    cursor.execute(query, (event_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID {event_id} not found"
        )

    return EventDetail(
        id=row["id"],
        title=row["title"],
        category=row["category"],
        description=row["description"],
        event_date=row["event_date"],
        event_time=row["event_time"],
        venue=row["venue"],
        capacity=row["capacity"],
        fee=row["fee"],
        icon=row["icon"],
        available_seats=max(0, row["available_seats"])
    )


@app.post("/api/events/{event_id}/register", response_model=RegistrationOut, status_code=status.HTTP_201_CREATED)
def register_for_event(event_id: int, reg_data: RegistrationIn):
    """
    Register a student for an event with rigorous server-side validation.
    """
    student_name = reg_data.student_name.strip() if reg_data.student_name else ""
    roll_number = reg_data.roll_number.strip() if reg_data.roll_number else ""
    email = reg_data.email.strip() if reg_data.email else ""
    phone = reg_data.phone.strip() if reg_data.phone else None

    # Server-side validation: Required fields must not be empty
    if not student_name or not roll_number or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student name, roll number, and email are required and cannot be empty"
        )

    # Server-side validation: Email must contain '@'
    if "@" not in email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address: must contain '@'"
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    # Server-side validation: event_id must exist
    cursor.execute("SELECT id, capacity, title FROM events WHERE id = ?", (event_id,))
    event = cursor.fetchone()
    if not event:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID {event_id} does not exist"
        )

    # Server-side validation: event must not be at capacity
    cursor.execute("SELECT COUNT(*) FROM registrations WHERE event_id = ?", (event_id,))
    current_reg_count = cursor.fetchone()[0]
    if current_reg_count >= event["capacity"]:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Event is full"
        )

    # Server-side validation: same email must not already be registered for this event
    cursor.execute(
        "SELECT id FROM registrations WHERE event_id = ? AND LOWER(email) = LOWER(?)",
        (event_id, email)
    )
    if cursor.fetchone():
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already registered for this event with this email"
        )

    # On success: insert registration with registered_at timestamp
    registered_at = datetime.now().isoformat()
    try:
        cursor.execute("""
            INSERT INTO registrations (event_id, student_name, roll_number, email, phone, registered_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (event_id, student_name, roll_number, email, phone, registered_at))
        conn.commit()
        new_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already registered"
        )
    finally:
        conn.close()

    return RegistrationOut(
        id=new_id,
        event_id=event_id,
        student_name=student_name,
        registered_at=registered_at
    )


@app.get("/api/registrations", response_model=List[RegistrationDetailOut])
def get_registrations(event_id: Optional[int] = Query(None, description="Filter by event ID")):
    """
    Get all registrations, optionally filtered by event_id.
    Includes event title for convenience on admin dashboard.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT 
            r.id, r.event_id, r.student_name, r.roll_number, r.email, r.phone, r.registered_at,
            e.title AS event_title
        FROM registrations r
        JOIN events e ON r.event_id = e.id
    """
    params = []
    if event_id is not None:
        query += " WHERE r.event_id = ?"
        params.append(event_id)

    query += " ORDER BY r.id DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    registrations = []
    for row in rows:
        registrations.append(RegistrationDetailOut(
            id=row["id"],
            event_id=row["event_id"],
            student_name=row["student_name"],
            roll_number=row["roll_number"],
            email=row["email"],
            phone=row["phone"],
            registered_at=row["registered_at"],
            event_title=row["event_title"]
        ))
    return registrations


@app.get("/api/stats", response_model=StatsOut)
def get_stats():
    """
    Returns live statistics computed on demand directly from the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total events
    cursor.execute("SELECT COUNT(*) FROM events")
    total_events = cursor.fetchone()[0]

    # Total registrations
    cursor.execute("SELECT COUNT(*) FROM registrations")
    total_registrations = cursor.fetchone()[0]

    # Total capacity
    cursor.execute("SELECT COALESCE(SUM(capacity), 0) FROM events")
    total_capacity = cursor.fetchone()[0]

    # Overall utilization percentage
    if total_capacity > 0:
        overall_utilization_pct = round((total_registrations / total_capacity) * 100.0, 1)
    else:
        overall_utilization_pct = 0.0

    # Upcoming events count: event_date today or later
    # Format dates in seed data: YYYY-MM-DD
    today_str = date.today().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*) FROM events WHERE event_date >= ?", (today_str,))
    upcoming_events_count = cursor.fetchone()[0]

    # Events by category
    cursor.execute("SELECT category, COUNT(*) as count FROM events GROUP BY category")
    category_rows = cursor.fetchall()
    events_by_category = {row["category"]: row["count"] for row in category_rows}

    conn.close()

    return StatsOut(
        total_events=total_events,
        total_registrations=total_registrations,
        total_capacity=total_capacity,
        overall_utilization_pct=overall_utilization_pct,
        upcoming_events_count=upcoming_events_count,
        events_by_category=events_by_category
    )


# ---------------------------------------------------------
# Stretch Goals: Admin Endpoints
# ---------------------------------------------------------

@app.post("/api/events", response_model=EventOut, status_code=status.HTTP_201_CREATED)
def create_event(event_data: EventIn):
    """
    Stretch goal: Admin creates a new event with server-side validation.
    """
    title = event_data.title.strip()
    category = event_data.category.strip()
    venue = event_data.venue.strip()
    event_date = event_data.event_date.strip()
    event_time = event_data.event_time.strip()

    if not title or not category or not venue or not event_date or not event_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title, category, venue, date, and time are required"
        )
    if event_data.capacity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Capacity must be greater than 0"
        )
    if event_data.fee < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fee cannot be negative"
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO events (title, category, description, event_date, event_time, venue, capacity, fee, icon)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        title,
        category,
        event_data.description.strip() if event_data.description else None,
        event_date,
        event_time,
        venue,
        event_data.capacity,
        event_data.fee,
        event_data.icon or "📅"
    ))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return EventOut(
        id=new_id,
        title=title,
        category=category,
        description=event_data.description,
        event_date=event_date,
        event_time=event_time,
        venue=venue,
        capacity=event_data.capacity,
        fee=event_data.fee,
        icon=event_data.icon or "📅",
        available_seats=event_data.capacity
    )


@app.delete("/api/registrations/{registration_id}", status_code=status.HTTP_200_OK)
def delete_registration(registration_id: int):
    """
    Stretch goal: Admin cancels a registration by ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, event_id, student_name FROM registrations WHERE id = ?", (registration_id,))
    reg = cursor.fetchone()
    if not reg:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registration with ID {registration_id} not found"
        )

    cursor.execute("DELETE FROM registrations WHERE id = ?", (registration_id,))
    conn.commit()
    conn.close()

# ---------------------------------------------------------
# AI Copilot Endpoints (Zenith AI)
# ---------------------------------------------------------

class AIChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = None

class AIGenerateEventRequest(BaseModel):
    prompt: str

@app.post("/api/ai/chat")
def ai_chat_endpoint(chat_req: AIChatRequest):
    """
    AI Student Copilot: answers questions with live real-time fest context.
    """
    if not chat_req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    from backend.ai_service import chat_with_copilot
    conn = get_db_connection()
    try:
        reply = chat_with_copilot(chat_req.message.strip(), chat_req.history or [], conn)
    finally:
        conn.close()
    return {"reply": reply}


@app.post("/api/ai/generate-event")
def ai_generate_event_endpoint(gen_req: AIGenerateEventRequest):
    """
    Admin AI Copilot: generates full event attributes from an idea prompt.
    """
    if not gen_req.prompt.strip():
        raise HTTPException(status_code=400, detail="Idea prompt cannot be empty")
    from backend.ai_service import generate_event_from_prompt
    try:
        event_dict = generate_event_from_prompt(gen_req.prompt.strip())
        return event_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")


@app.get("/api/ai/insights")
def ai_insights_endpoint():
    """
    Admin AI Copilot: generates live executive operations briefing.
    """
    from backend.ai_service import generate_fest_insights
    conn = get_db_connection()
    try:
        insights = generate_fest_insights(conn)
    finally:
        conn.close()
    return {"insights": insights}


# ---------------------------------------------------------
# Static File Mounting (Step 4)
# ---------------------------------------------------------

@app.get("/", response_class=FileResponse)
def serve_root():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Welcome to Zenith '26 API. Visit /docs for API documentation."}


@app.get("/admin.html", response_class=FileResponse)
def serve_admin():
    admin_path = FRONTEND_DIR / "admin.html"
    if admin_path.exists():
        return FileResponse(admin_path)
    raise HTTPException(status_code=404, detail="admin.html not found")


# Mount JS directory
if (FRONTEND_DIR / "js").exists():
    app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")

# Mount general frontend folder
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend-static")
