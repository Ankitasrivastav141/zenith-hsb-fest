# Postman Testing Guide: Zenith '26 Fest Management System

**Companion to:** PM2-01 (How Software Works) & PM2-02 (Front-End, Back-End & Mobile)  
**API Server Base URL:** `http://localhost:8001`

---

## 🚀 Postman Desktop Setup Steps

1. **Install / Launch Postman**: Open the Postman Desktop App (free, works signed out).
2. **Import Collection**:
   - Click **Import** in the top left.
   - Drag and drop `zenith26-api.postman_collection.json` (found in the project root).
3. **Environment Setup**:
   - The collection includes a `baseUrl` variable defaulted to `http://127.0.0.1:8001`.
   - Ensure your FastAPI server is running:
     ```powershell
     cd zenith26-fest-system
     .\.venv\Scripts\uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
     ```
4. **Testing Discipline**:
   - For every request, look at the **Status Code** first (e.g., `200 OK`, `201 Created`, `400 Bad Request`, `404 Not Found`, `409 Conflict`).
   - Then inspect the response JSON body and verify field values and data types.

---

## 📋 The 18 Test Requests & Expected Behaviors

### Folder 1: Events Endpoints (`GET /api/events`)

#### Request 1: List All Events
- **Method:** `GET`
- **URL:** `{{baseUrl}}/api/events`
- **Expected Status:** `200 OK`
- **Expected Response:** JSON array with 14 event objects. Each object contains `available_seats` computed live as `capacity` minus current registrations.

#### Request 2: Filter by Category
- **Method:** `GET`
- **URL:** `{{baseUrl}}/api/events?category=Technical`
- **Expected Status:** `200 OK`
- **Expected Response:** JSON array containing only technical events (e.g., *Code Sprint 2.0*, *Robo Race*, *AI Pitch Fest*, *Web Design Rumble*).

#### Request 3: Search by Title Keyword
- **Method:** `GET`
- **URL:** `{{baseUrl}}/api/events?search=sprint`
- **Expected Status:** `200 OK`
- **Expected Response:** JSON array containing events whose title matches "sprint" (*Code Sprint 2.0*).

#### Request 4: Combined Filter and Search
- **Method:** `GET`
- **URL:** `{{baseUrl}}/api/events?category=Cultural&search=dance`
- **Expected Status:** `200 OK`
- **Expected Response:** Array containing *Dance Fiesta*.

#### Request 5: Get Event by ID (Success)
- **Method:** `GET`
- **URL:** `{{baseUrl}}/api/events/1`
- **Expected Status:** `200 OK`
- **Expected Response:**
```json
{
  "id": 1,
  "title": "Code Sprint 2.0",
  "category": "Technical",
  "description": "Competitive speed programming showdown...",
  "event_date": "2026-11-14",
  "event_time": "10:00 AM",
  "venue": "Main Auditorium",
  "capacity": 100,
  "fee": 0,
  "icon": "💻",
  "available_seats": 100
}
```

#### Request 6: Get Event by ID (404 Not Found)
- **Method:** `GET`
- **URL:** `{{baseUrl}}/api/events/999`
- **Expected Status:** `404 Not Found`
- **Expected Response:**
```json
{
  "detail": "Event with id 999 not found"
}
```

---

### Folder 2: Student Registration Endpoints (`POST /api/events/{id}/register`)

#### Request 7: Valid Registration (201 Created)
- **Method:** `POST`
- **URL:** `{{baseUrl}}/api/events/1/register`
- **Headers:** `Content-Type: application/json`
- **Body:**
```json
{
  "student_name": "Aarav Patel",
  "roll_number": "CS2026-088",
  "email": "aarav.patel@college.edu",
  "phone": "+91 9876543210"
}
```
- **Expected Status:** `201 Created`
- **Expected Response:**
```json
{
  "id": 1,
  "event_id": 1,
  "student_name": "Aarav Patel",
  "registered_at": "..."
}
```

#### Request 8: Verify Seat Count Decrement
- **Method:** `GET`
- **URL:** `{{baseUrl}}/api/events/1`
- **Expected Status:** `200 OK`
- **Expected Response:** `available_seats` is now `99` (proves live calculation from database!).

#### Request 9: Missing Student Name (400 Bad Request)
- **Method:** `POST`
- **URL:** `{{baseUrl}}/api/events/1/register`
- **Headers:** `Content-Type: application/json`
- **Body:**
```json
{
  "student_name": "",
  "roll_number": "CS2026-088",
  "email": "student@college.edu"
}
```
- **Expected Status:** `400 Bad Request`
- **Expected Response:**
```json
{
  "detail": "Student name, roll number, and email are required fields"
}
```

#### Request 10: Missing Roll Number (400 Bad Request)
- **Method:** `POST`
- **URL:** `{{baseUrl}}/api/events/1/register`
- **Headers:** `Content-Type: application/json`
- **Body:**
```json
{
  "student_name": "Rohan Das",
  "roll_number": "",
  "email": "rohan@college.edu"
}
```
- **Expected Status:** `400 Bad Request`

#### Request 11: Missing Email (400 Bad Request)
- **Method:** `POST`
- **URL:** `{{baseUrl}}/api/events/1/register`
- **Headers:** `Content-Type: application/json`
- **Body:**
```json
{
  "student_name": "Rohan Das",
  "roll_number": "ME2026-012",
  "email": ""
}
```
- **Expected Status:** `400 Bad Request`

#### Request 12: Invalid Email Missing '@' (400 Bad Request)
- **Method:** `POST`
- **URL:** `{{baseUrl}}/api/events/1/register`
- **Headers:** `Content-Type: application/json`
- **Body:**
```json
{
  "student_name": "Rohan Das",
  "roll_number": "ME2026-012",
  "email": "rohandas-no-at-sign.edu"
}
```
- **Expected Status:** `400 Bad Request`
- **Expected Response:**
```json
{
  "detail": "Invalid email address: must contain '@'"
}
```

#### Request 13: Duplicate Registration for Same Event (409 Conflict)
- **Method:** `POST`
- **URL:** `{{baseUrl}}/api/events/1/register`
- **Headers:** `Content-Type: application/json`
- **Body (Same email as Request 7):**
```json
{
  "student_name": "Aarav Patel",
  "roll_number": "CS2026-088",
  "email": "aarav.patel@college.edu"
}
```
- **Expected Status:** `409 Conflict`
- **Expected Response:**
```json
{
  "detail": "Already registered for this event with this email address"
}
```

#### Request 14: Register for Non-Existent Event (404 Not Found)
- **Method:** `POST`
- **URL:** `{{baseUrl}}/api/events/999/register`
- **Headers:** `Content-Type: application/json`
- **Body:**
```json
{
  "student_name": "Sneha Sen",
  "roll_number": "EE2026-020",
  "email": "sneha@college.edu"
}
```
- **Expected Status:** `404 Not Found`

---

### Folder 3: Admin & Registrations Inspection (`GET /api/registrations`, `GET /api/stats`)

#### Request 15: List All Registrations
- **Method:** `GET`
- **URL:** `{{baseUrl}}/api/registrations`
- **Expected Status:** `200 OK`
- **Expected Response:** JSON array with registration records, each containing `student_name`, `roll_number`, `email`, and `event_title`.

#### Request 16: Filter Registrations by Event ID
- **Method:** `GET`
- **URL:** `{{baseUrl}}/api/registrations?event_id=1`
- **Expected Status:** `200 OK`
- **Expected Response:** Filtered array of registrations specifically for event ID 1.

#### Request 17: Live Fest Statistics
- **Method:** `GET`
- **URL:** `{{baseUrl}}/api/stats`
- **Expected Status:** `200 OK`
- **Expected Response:**
```json
{
  "total_events": 14,
  "total_registrations": 1,
  "total_capacity": 1507,
  "overall_utilization_pct": 0.1,
  "upcoming_events_count": 14,
  "events_by_category": {
    "Cultural": 5,
    "Technical": 4,
    "Sports": 2,
    "Workshop": 2,
    "Gaming": 1
  }
}
```

---

### Folder 4: Admin Stretch Goals (`POST /api/events`, `DELETE /api/registrations/{id}`)

#### Request 18A: Admin Create Event (201 Created)
- **Method:** `POST`
- **URL:** `{{baseUrl}}/api/events`
- **Headers:** `Content-Type: application/json`
- **Body:**
```json
{
  "title": "Drone Racing Derby",
  "category": "Technical",
  "description": "FPV high-speed indoor drone navigation obstacle course.",
  "event_date": "2026-11-15",
  "event_time": "03:00 PM",
  "venue": "Aerospace Hangar",
  "capacity": 30,
  "fee": 50,
  "icon": "🛸"
}
```
- **Expected Status:** `201 Created`

#### Request 18B: Admin Cancel Registration (200 OK)
- **Method:** `DELETE`
- **URL:** `{{baseUrl}}/api/registrations/1`
- **Expected Status:** `200 OK`
- **Expected Response:**
```json
{
  "message": "Registration cancelled successfully",
  "registration_id": 1,
  "event_id": 1,
  "student_name": "Aarav Patel"
}
```
- **Verification:** Re-running `GET /api/events/1` immediately shows `available_seats` restored back to `100`!
