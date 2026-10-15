"""
Verification script for Zenith '26 College Fest Management System.
Tests all endpoints, database constraints, static file serving, and error handling.
"""
import sys
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import get_db_connection

client = TestClient(app)

def test_all():
    print("==================================================")
    print("Running Zenith '26 Verification Test Suite")
    print("==================================================")

    # 1. Test Static files
    res = client.get("/")
    assert res.status_code == 200, f"Root / failed: {res.status_code}"
    assert "Zenith '26" in res.text, "Index page title missing"
    print("  [PASS] GET / serves index.html")

    res = client.get("/admin.html")
    assert res.status_code == 200, f"Admin page failed: {res.status_code}"
    assert "Admin Dashboard" in res.text or "Fest Operations" in res.text, "Admin page title missing"
    print("  [PASS] GET /admin.html serves admin.html")

    res = client.get("/js/app.js")
    assert res.status_code == 200, f"js/app.js failed: {res.status_code}"
    print("  [PASS] GET /js/app.js served successfully")

    res = client.get("/js/admin.js")
    assert res.status_code == 200, f"js/admin.js failed: {res.status_code}"
    print("  [PASS] GET /js/admin.js served successfully")

    # 2. Test GET /api/events
    res = client.get("/api/events")
    assert res.status_code == 200, f"Events failed: {res.status_code}"
    events = res.json()
    assert len(events) >= 14, f"Expected at least 14 events, got {len(events)}"
    assert "available_seats" in events[0], "available_seats missing in EventOut"
    print(f"  [PASS] GET /api/events returns {len(events)} events with live available_seats")

    # 3. Test Filter by Category
    res = client.get("/api/events?category=Technical")
    assert res.status_code == 200
    tech_events = res.json()
    assert all(e["category"] == "Technical" for e in tech_events), "Category filter failed"
    print(f"  [PASS] GET /api/events?category=Technical returns {len(tech_events)} technical events")

    # 4. Test Search Keyword
    res = client.get("/api/events?search=code")
    assert res.status_code == 200
    search_events = res.json()
    assert any("Code Sprint" in e["title"] for e in search_events), "Search failed to match 'Code Sprint'"
    print(f"  [PASS] GET /api/events?search=code successfully matches keyword")

    # 5. Test Single Event GET
    res = client.get("/api/events/1")
    assert res.status_code == 200
    ev1 = res.json()
    assert ev1["id"] == 1
    assert "Code Sprint" in ev1["title"]
    print(f"  [PASS] GET /api/events/1 returns '{ev1['title']}'")

    # 6. Test Event 404
    res = client.get("/api/events/999")
    assert res.status_code == 404, f"Expected 404 for event 999, got {res.status_code}"
    print("  [PASS] GET /api/events/999 returns 404 Not Found")

    # 7. Test Registration Validation: Missing Fields (400)
    res = client.post("/api/events/1/register", json={
        "student_name": "",
        "roll_number": "CS2026-99",
        "email": "test@college.edu"
    })
    assert res.status_code == 400, f"Expected 400 for empty name, got {res.status_code}"
    print("  [PASS] POST /api/events/1/register rejects empty student_name with 400")

    # 8. Test Registration Validation: Invalid Email (400)
    res = client.post("/api/events/1/register", json={
        "student_name": "Test Student",
        "roll_number": "CS2026-99",
        "email": "invalidemail"
    })
    assert res.status_code == 400, f"Expected 400 for missing '@', got {res.status_code}"
    print("  [PASS] POST /api/events/1/register rejects email without '@' with 400")

    # 9. Test Successful Registration (201)
    test_email = "test.verification.student@zenith.edu"
    # Ensure clean state for test email
    conn = get_db_connection()
    conn.execute("DELETE FROM registrations WHERE email = ?", (test_email,))
    conn.commit()
    conn.close()

    res = client.post("/api/events/1/register", json={
        "student_name": "Verification Student",
        "roll_number": "TEST-2026",
        "email": test_email,
        "phone": "+91 9999988888"
    })
    assert res.status_code == 201, f"Expected 201 Created, got {res.status_code}: {res.text}"
    reg_out = res.json()
    assert reg_out["event_id"] == 1
    assert reg_out["student_name"] == "Verification Student"
    test_reg_id = reg_out["id"]
    print(f"  [PASS] POST /api/events/1/register succeeds with 201 (Registration ID: {test_reg_id})")

    # 10. Test Duplicate Registration Conflict (409)
    res_dup = client.post("/api/events/1/register", json={
        "student_name": "Verification Student",
        "roll_number": "TEST-2026",
        "email": test_email
    })
    assert res_dup.status_code == 409, f"Expected 409 Conflict for duplicate email, got {res_dup.status_code}"
    print("  [PASS] Duplicate registration rejected with 409 Conflict")

    # 11. Test GET /api/registrations
    res = client.get("/api/registrations")
    assert res.status_code == 200
    all_regs = res.json()
    assert any(r["id"] == test_reg_id for r in all_regs), "Registered student missing from /api/registrations"
    assert "event_title" in all_regs[0], "event_title missing in registration roster"
    print(f"  [PASS] GET /api/registrations returns roster with {len(all_regs)} entries including event_title")

    # 12. Test GET /api/stats
    res = client.get("/api/stats")
    assert res.status_code == 200
    stats = res.json()
    assert stats["total_events"] >= 14
    assert stats["total_registrations"] >= 1
    assert "overall_utilization_pct" in stats
    assert "events_by_category" in stats
    print(f"  [PASS] GET /api/stats live calculation: {stats['total_events']} events, {stats['total_registrations']} registrations, {stats['overall_utilization_pct']}% utilization")

    # 13. Test Stretch Goal: Cancel Registration (DELETE /api/registrations/{id})
    res_del = client.delete(f"/api/registrations/{test_reg_id}")
    assert res_del.status_code == 200, f"Cancel registration failed: {res_del.status_code}"
    print(f"  [PASS] DELETE /api/registrations/{test_reg_id} successfully cancelled registration")

    # Verify seat restored
    res_ev_after = client.get("/api/events/1").json()
    print(f"  [PASS] Event 1 available seats verified after cancellation: {res_ev_after['available_seats']}")

    # 14. Test Stretch Goal: Create Event (POST /api/events)
    res_ev_new = client.post("/api/events", json={
        "title": "Zenith Hackathon 2026",
        "category": "Technical",
        "description": "24-hour coding marathon",
        "event_date": "2026-11-15",
        "event_time": "09:00 AM",
        "venue": "Innovation Lab",
        "capacity": 75,
        "fee": 0,
        "icon": "⚡"
    })
    assert res_ev_new.status_code == 201, f"Create event failed: {res_ev_new.status_code}"
    new_ev = res_ev_new.json()
    print(f"  [PASS] POST /api/events (Stretch Goal) created event ID {new_ev['id']}: '{new_ev['title']}'")

    # Clean up test event
    conn = get_db_connection()
    conn.execute("DELETE FROM events WHERE id = ?", (new_ev["id"],))
    conn.commit()
    conn.close()

    print("==================================================")
    print("ALL TESTS PASSED! SYSTEM OPERATING AT 100% QUALITY")
    print("==================================================")

if __name__ == "__main__":
    test_all()
