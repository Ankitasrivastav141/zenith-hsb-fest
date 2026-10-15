# Vibe-Coding Prompts: Build the Zenith '26 College Fest Management System

**Tool:** Google Antigravity
**Stack:** HTML + Tailwind CSS + JavaScript (frontend) · Python + FastAPI (backend) · SQLite (database) · Postman (API testing)
**Companion to:** PM2-01 (How Software Works) and PM2-02 (Front-End, Back-End & Mobile)
**Companion data file:** `events_seed.xlsx` — provided alongside this prompts file; Step 1 reads the 14 seed events from it, so keep it in the same folder as this file until you copy it into your project in Step 0.
**Companion testing guide:** `Postman-Testing-Commands-Zenith26.md` — every Postman request to run once Step 10 is done, with exact bodies and expected responses.

---

## How to use this file

Each numbered step below is one **prompt block** — copy the whole block (including the instructions inside it) and paste it into Antigravity's agent chat, inside your `zenith26-fest-system` project folder. Let the agent finish one step, run the app, confirm it works, *then* move to the next prompt. Don't paste multiple steps at once — vibe coding works best in small, checkable increments, which is also the point of the exercise: you're reviewing and testing like a PM would, not just trusting a black box.

This project comes with one companion data file, `events_seed.xlsx` — the 14 sample fest events, as a spreadsheet instead of text buried in a prompt. That's deliberate: it mirrors how real seed/import data usually arrives as a file, not hardcoded in application code, and it means you can edit the spreadsheet to re-theme the whole fest without touching any Python. Step 0 tells you exactly where to put it.

After every step, actually run the app and look at it. If something looks wrong, tell Antigravity what's wrong in plain language ("the register button doesn't do anything when I click it") rather than guessing at the fix yourself — that back-and-forth *is* vibe coding.

Keep this file open next to Antigravity the whole time.

---

## Step 0 — Project setup

```
Create a new project called "zenith26-fest-system" with this exact folder structure:

zenith26-fest-system/
  backend/
    main.py
    database.py
    models.py
    seed_data.py
  frontend/
    index.html
    admin.html
    js/
      app.js
      admin.js
  data/
  requirements.txt
  README.md

Create a Python virtual environment, add fastapi, uvicorn, pydantic, and
openpyxl to requirements.txt, and install them. Leave every file empty except
requirements.txt for now — we'll fill each one in with the next prompts.
Confirm the folder structure once it's created.
```

**Before moving to Step 1:** copy the companion data file, `events_seed.xlsx`
(provided alongside this prompts file), into `zenith26-fest-system/data/`. Step
1 reads the seed data from that exact file — Antigravity can't seed the
database without it in place.

---

## Step 1 — Database schema and seed data

```
In backend/database.py, write SQLite setup code that:

1. Connects to a local file called fest.db (create it if it doesn't exist).
2. Creates an "events" table with these exact columns:
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   title TEXT NOT NULL,
   category TEXT NOT NULL,
   description TEXT,
   event_date TEXT NOT NULL,
   event_time TEXT NOT NULL,
   venue TEXT NOT NULL,
   capacity INTEGER NOT NULL,
   fee INTEGER NOT NULL DEFAULT 0,
   icon TEXT

3. Creates a "registrations" table with these exact columns:
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   event_id INTEGER NOT NULL REFERENCES events(id),
   student_name TEXT NOT NULL,
   roll_number TEXT NOT NULL,
   email TEXT NOT NULL,
   phone TEXT,
   registered_at TEXT NOT NULL,
   UNIQUE(event_id, email)

4. Provide a get_db_connection() helper function other files can import.

In backend/seed_data.py, write a script that seeds the events table from the
companion data file at data/events_seed.xlsx (NOT hardcoded in the script):

1. Open data/events_seed.xlsx with openpyxl and read the "Events" sheet.
2. Row 1 is the header row: id, title, category, description, event_date,
   event_time, venue, capacity, fee, icon — in that exact order. Read every
   row after it as one event.
3. Insert each row into the events table, in order, matching each column
   to the matching events-table column.
4. Skip seeding if the table already has rows, so re-running the app
   doesn't duplicate events.
5. If data/events_seed.xlsx is missing, raise a clear error telling the
   user to copy the provided events_seed.xlsx file into the data/ folder
   before running this script — don't silently seed nothing and don't
   invent fallback data of your own.

Run the seed script once and show me the contents of the events table to
confirm all 14 rows came through correctly from the spreadsheet.
```

---

## Step 2 — Pydantic models

```
In backend/models.py, define Pydantic models for:

1. EventOut — what we send back for an event: id, title, category, description,
   event_date, event_time, venue, capacity, fee, icon, available_seats (int).
2. EventDetail — same as EventOut (an event detail screen uses the same shape
   for this project).
3. RegistrationIn — what the frontend sends to register: student_name,
   roll_number, email, phone (phone optional).
4. RegistrationOut — confirmation sent back: id, event_id, student_name,
   registered_at.
5. StatsOut — total_events, total_registrations, total_capacity,
   overall_utilization_pct (float), upcoming_events_count,
   events_by_category (a dict of category -> count).

Use type hints throughout so FastAPI's automatic docs show clean types.
```

---

## Step 3 — API endpoints

```
In backend/main.py, build a FastAPI app with these exact endpoints. Match this
contract precisely — the frontend prompts later in this project assume these
exact paths, methods, and response shapes.

GET /api/events
  - Optional query params: category, search (matches title, case-insensitive)
  - Returns a list of EventOut, each with available_seats computed as
    capacity minus the count of rows in registrations for that event_id

GET /api/events/{event_id}
  - Returns one EventDetail, or a 404 with a clear error message if the id
    doesn't exist

POST /api/events/{event_id}/register
  - Body: RegistrationIn
  - Server-side validation (do NOT trust that the frontend already checked
    this — re-check everything here, this is the whole point of the exercise):
      - event_id must exist (404 if not)
      - student_name, roll_number, email must not be empty (400 if missing)
      - email must contain "@" (400 if invalid)
      - the event must not be at capacity already (409 "Event is full" if so)
      - the same email must not already be registered for this event
        (409 "Already registered" if so)
  - On success: insert the registration with registered_at set to the current
    timestamp, return 201 with RegistrationOut

GET /api/registrations
  - Optional query param: event_id (filter to one event)
  - Returns a list of registrations, each including the event's title so the
    admin dashboard doesn't need a second lookup

GET /api/stats
  - Returns StatsOut: computed live from the database every time it's called,
    never from a stored/cached number
  - upcoming_events_count = events with event_date today or later
  - overall_utilization_pct = total_registrations / total_capacity * 100,
    rounded to 1 decimal

Enable CORS for local development. Call the seed function from seed_data.py
on startup so the database is always ready. Run the server with
"uvicorn backend.main:app --reload" and confirm it starts without errors.
Open the automatic docs at /docs and confirm all five endpoints are listed.
```

---

## Step 4 — Serve the frontend from FastAPI

```
Update backend/main.py to mount the frontend/ folder as static files, so that:
  - Visiting http://localhost:8000/ serves frontend/index.html
  - Visiting http://localhost:8000/admin.html serves frontend/admin.html
  - Files in frontend/js/ are reachable at /js/app.js and /js/admin.js

Make sure this doesn't conflict with the /api/... routes — API routes should
still work exactly as before. Confirm by visiting both pages in a browser.
```

---

## Step 5 — Base layout and Tailwind

```
In frontend/index.html, set up the HTML skeleton:
  - Include Tailwind CSS via the Play CDN script tag (fine for this local
    classroom project; note in a comment that a production app would use a
    compiled stylesheet instead)
  - A simple top navbar with the fest name "Zenith '26" and a small link to
    "Admin Dashboard" (admin.html)
  - A hero section with the fest name, dates (Nov 14-15, 2026), and a short
    tagline
  - An empty <div id="events-grid"> where event cards will be rendered by
    JavaScript
  - Link to js/app.js at the bottom

Keep it mobile-friendly: the navbar should collapse sensibly on a narrow
screen and the hero text should resize down on mobile. Use a simple,
appealing color palette of your choice — this is a college fest, so it can be
energetic, not corporate.
```

---

## Step 6 — Student event portal: cards, search, filters

```
In frontend/js/app.js, write JavaScript that:

1. On page load, fetches GET /api/events and renders each event as a card
   inside #events-grid. Each card shows: icon, title, category badge, date +
   time, venue, available_seats out of capacity, fee (or "Free"), and a
   "View Details" button.
2. If available_seats is 0, show a clear "FULL" badge on the card instead of
   making the seats count look normal.
3. Add a search input and category filter buttons (All, Technical, Cultural,
   Sports, Gaming, Workshop) above the grid. Changing either one re-fetches
   GET /api/events with the right query params and re-renders the grid —
   don't filter client-side only, since the point is to exercise the real
   API query parameters.
4. Style everything with Tailwind utility classes: responsive grid (1 column
   on mobile, 2-3 on tablet/desktop), rounded cards with a subtle shadow, a
   hover effect on cards.

Test it: confirm all 14 events show up, confirm the category filters work,
confirm the search box narrows results as you'd expect.
```

---

## Step 7 — Event detail and registration form

```
Add event detail + registration to the student portal:

1. Clicking "View Details" on a card opens a modal (or a detail panel) showing
   the full event description plus a registration form: Student Name, Roll
   Number, Email, Phone.
2. Before submitting, do basic client-side checks (required fields filled in,
   email looks like an email) and show inline error text if something's
   missing — but remember the server will check everything again
   independently, so don't skip Step 3's server-side validation.
3. On submit, POST to /api/events/{event_id}/register with the form data.
4. On success (201), show a clear confirmation message with the event name
   and close the form after a moment. Re-fetch that event's data so the
   available seats count updates immediately on screen.
5. On failure (400/409), show the exact error message the server sent back
   (e.g. "Event is full" or "Already registered") in the form itself — don't
   swallow it into a generic "Something went wrong."

Test it end to end: register for an event, confirm the seat count drops by
one, try registering the same email twice and confirm you get a clear
"already registered" error, not a crash.
```

---

## Step 8 — Admin dashboard

```
Build frontend/admin.html and frontend/js/admin.js:

1. On load, fetch GET /api/stats and show four stat cards at the top: Total
   Events, Total Registrations, Overall Capacity Utilization (as a
   percentage), Upcoming Events.
2. Below that, show a breakdown by category (events_by_category) as a simple
   bar or a row of labeled counts.
3. Below that, fetch GET /api/events and list every event in a table with
   columns: Title, Category, Date, Venue, Registered / Capacity, Utilization %
   for that event. Sort by utilization percentage descending by default, so
   the admin sees the most in-demand events first.
4. Highlight any event over 90% capacity in a warning color so admins can
   spot it instantly.
5. Add a simple link or tab to view the raw registration list (GET
   /api/registrations), with the student's name, roll number, email, and
   which event, filterable by event using a dropdown.

Style it like a real dashboard: clean cards, a proper data table, consistent
spacing — this is the screen a fest coordinator would actually use during the
event, so it needs to be scannable at a glance, not just functional.
```

---

## Step 9 — Error states and loading states

```
Go back through both index.html and admin.html and make sure every fetch call
has:
  - A visible loading state (a spinner or "Loading..." text) while the
    request is in flight
  - A visible error state if the fetch fails entirely (e.g. the backend isn't
    running) — don't let the page just sit blank with no explanation
  - An empty state if a filter/search returns zero events ("No events match
    your search" rather than a blank grid)

This matters because in the real world, the network is never 100% reliable,
and a PM should expect to see and call out exactly this kind of gap in a
review.
```

---

## Step 10 — Testing with Postman

```
Generate a Postman collection as a JSON file called
zenith26-api.postman_collection.json in the project root, with one request
for each endpoint:
  - GET /api/events (with example category and search query params)
  - GET /api/events/{event_id} (using id 1 as an example)
  - POST /api/events/{event_id}/register (using id 1, with example body data)
  - GET /api/registrations
  - GET /api/stats

For the POST request, include two saved example bodies: one that should
succeed, and one that's missing a required field so it should return a 400 —
label them clearly in the request name.
```

Once this file exists, open Postman yourself (this part isn't a prompt —
it's something you do by hand, which is the point): import the collection,
run each request with the server running, and actually read the response
status codes and bodies. This is the step where you stop trusting that the
UI "looks like it worked" and check the API contract directly — exactly the
muscle PM2-02's "API Contracts" lesson was building.

The companion file **Postman-Testing-Commands-Zenith26.md** has the full set
of requests to run — 18 of them, covering every endpoint's success and
failure cases, with exact bodies and expected responses — plus setup steps
for the Postman desktop app and a collection/environment structure to use.
Work through it folder by folder once the generated collection is imported.

---

## Step 11 — Polish pass

```
Do a final polish pass on the whole app:
  1. Add a subtle fade-in animation to event cards as they load.
  2. Make sure every page works cleanly on a phone-sized screen (test by
     shrinking the browser window) — no horizontal scrolling, no overlapping
     text.
  3. Add a favicon and a proper <title> to both pages.
  4. Double check every button has a visible hover/active state so the UI
     doesn't feel static.
  5. Write a short README.md at the project root explaining: what this
     project is, the tech stack used, how to run it (the exact commands),
     and the list of API endpoints.

Run the whole app one more time from a clean restart (stop the server,
restart it, reload the browser) to confirm nothing broke.
```

---

## Stretch goals (optional, for students who finish early)

```
Add two admin-only capabilities:

1. POST /api/events — lets the admin add a new event from a form on
   admin.html, with the same server-side validation discipline as
   registration (required fields, sensible capacity > 0, etc).

2. DELETE /api/registrations/{registration_id} — lets the admin cancel a
   registration from the registration list, with a confirmation step before
   it actually deletes, and the event's available seat count updating
   immediately after.

Keep both consistent with the existing API and UI style rather than
introducing a new pattern.
```

---

## If something breaks

Tell Antigravity exactly what you see, not what you think the cause is:
- "The event list is empty and the console shows a 404 on /api/events" is a
  great bug report.
- "It's broken" is not — the agent will just guess, the same way a junior
  engineer would if you gave them that little to go on.

Check the browser console (F12 → Console tab) and the terminal running
`uvicorn` first — most errors show up in one of those two places.
