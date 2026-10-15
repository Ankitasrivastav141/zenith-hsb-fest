import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

def get_openai_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or not OpenAI:
        return None
    return OpenAI(api_key=api_key)

def get_live_events_context(conn):
    """Retrieves current events and live available seats from database for AI context."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            e.id, e.title, e.category, e.description, e.event_date, e.event_time, 
            e.venue, e.capacity, e.fee, e.icon,
            (e.capacity - COUNT(r.id)) AS available_seats
        FROM events e
        LEFT JOIN registrations r ON e.id = r.event_id
        GROUP BY e.id
        ORDER BY e.id ASC
    """)
    rows = cursor.fetchall()
    
    events_summary = []
    for r in rows:
        events_summary.append({
            "id": r["id"],
            "title": r["title"],
            "category": r["category"],
            "icon": r["icon"],
            "date": r["event_date"],
            "time": r["event_time"],
            "venue": r["venue"],
            "fee": f"₹{r['fee']}" if r["fee"] > 0 else "Free",
            "available_seats": max(0, r["available_seats"]),
            "capacity": r["capacity"],
            "description": r["description"]
        })
    return events_summary

def chat_with_copilot(user_message: str, history: list, conn) -> str:
    """Interacts with OpenAI gpt-4o-mini with live fest database context."""
    client = get_openai_client()
    if not client:
        return (
            "⚠️ Zenith AI Copilot is currently offline because no OPENAI_API_KEY was found. "
            "Please configure your OpenAI API key in your environment or .env file."
        )

    events = get_live_events_context(conn)
    events_json_str = json.dumps(events, indent=2)

    system_prompt = f"""You are 'Zenith AI', the energetic and helpful AI Student Copilot for the Zenith '26 College Fest (held on Nov 14–15, 2026).
You have real-time live access to all events, schedules, venues, entry fees, and available seats from the database.

CURRENT LIVE EVENTS DATA:
{events_json_str}

GUIDELINES:
1. Be enthusiastic, energetic, helpful, and concise. Use relevant emojis (⚡, 💻, 🎭, 🎮, 🏆).
2. Recommend events matching student interests (e.g. coding, music, dance, football, chess, esports, design).
3. If an event has 0 available seats, inform the user that it is completely FULL / sold out.
4. Mention venue, date, time, and fee (highlight if Free!) whenever suggesting an event.
5. Provide clear, direct answers formatted cleanly in markdown with bullet points.
6. When helpful, encourage them to click 'View Details' on that event card to register instantly."""

    messages = [{"role": "system", "content": system_prompt}]
    
    # Append recent conversation history (max 8 messages for context)
    if history and isinstance(history, list):
        for msg in history[-8:]:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                messages.append({"role": msg["role"], "content": str(msg["content"])})

    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error communicating with OpenAI: {str(e)}"

def generate_event_from_prompt(idea_prompt: str) -> dict:
    """Generates structured event fields from a short idea prompt using AI."""
    client = get_openai_client()
    if not client:
        raise ValueError("OPENAI_API_KEY is not configured.")

    system_prompt = """You are an expert college fest organizer. The admin will give you a brief idea or theme for a new fest event.
Return a clean, valid JSON object with these exact keys:
- "title": (string) Catchy title
- "category": (string) Must be one of: "Technical", "Cultural", "Sports", "Gaming", "Workshop"
- "icon": (string) A single matching emoji
- "venue": (string) Realistic college venue (e.g. "Main Auditorium", "Computer Lab 2", "Amphitheatre", "Sports Arena")
- "event_date": (string) "2026-11-14" or "2026-11-15"
- "event_time": (string) e.g. "11:00 AM - 1:00 PM"
- "capacity": (integer) Recommended capacity between 20 and 200
- "fee": (integer) 0 for free, or 50/100/150
- "description": (string) 2-3 sentence exciting description and rule summary

Respond ONLY with raw JSON, no markdown formatting or backticks."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Create a fest event based on: {idea_prompt}"}
        ],
        max_tokens=400,
        temperature=0.7
    )
    content = response.choices[0].message.content.strip()
    if content.startswith("```"):
        content = content.strip("`").replace("json", "").strip()
    return json.loads(content)

def generate_fest_insights(conn) -> str:
    """Generates an executive briefing report for fest coordinators analyzing live data."""
    client = get_openai_client()
    if not client:
        return "OpenAI API key not configured. Please set OPENAI_API_KEY."

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM events")
    total_events = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM registrations")
    total_regs = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(capacity), 0) FROM events")
    total_capacity = cursor.fetchone()[0]

    cursor.execute("""
        SELECT e.title, e.category, e.capacity, COUNT(r.id) as registered
        FROM events e
        LEFT JOIN registrations r ON e.id = r.event_id
        GROUP BY e.id
        ORDER BY registered DESC
    """)
    event_stats = [dict(row) for row in cursor.fetchall()]

    utilization = round((total_regs / total_capacity * 100), 1) if total_capacity > 0 else 0

    system_prompt = """You are a senior Operations and Product Management consultant analyzing college fest operations data.
Write a crisp, high-impact Executive Briefing for fest coordinators with:
1. 📊 Key Operational Metrics (Registrations, Capacity Utilization, Health)
2. 🔥 High Demand Events & Bottlenecks
3. 💡 Strategic Recommendations for Coordinators (marketing, crowd management, scheduling adjustments)
Keep it sharp, data-driven, and formatted cleanly with markdown bullets and bold highlights."""

    user_content = f"""Fest Live Operations Data:
- Total Events: {total_events}
- Total Registrations: {total_regs} / {total_capacity} total capacity
- Overall Utilization: {utilization}%
- Event breakdown:
{json.dumps(event_stats, indent=2)}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        max_tokens=600,
        temperature=0.6
    )
    return response.choices[0].message.content
