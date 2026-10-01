# EventHub — Event & Ticket Management System

**Course:** Python Development (CIM2013C) · Semester III · 2026–27
A menu-driven console application for free events: browse, register, get a digital pass, and verify entry.

## Features
- User portal: register/login, browse & search events, event details, register, digital pass, my passes, cancel, verify own pass
- Admin portal: dashboard, add/view/search/update/delete events, registration search, ticket verification (mark USED), ticket management, 8 reports
- Automatic event status (OPEN FOR REGISTRATION / FULL / REGISTRATION CLOSED / ONGOING / COMPLETED) from date, deadline and capacity
- Per-event capacity; cancelling frees the seat; capacity alert at 80% and 100%
- Passwords stored as SHA-256 hashes; all input validated; coloured console UI (falls back to plain text)

## Technologies
Python 3 standard library only: `csv`, `os`, `hashlib`, `datetime`, `random`, `string`, `re`, `getpass`.

## Project structure
```
EventHub/
├── main.py            entry point, main menu
├── auth.py            registration, login, admin login, hashing
├── user_portal.py     user menu and actions
├── admin_portal.py    admin menu, registrations, verification
├── event_manager.py   event CRUD, status, capacity
├── ticket_manager.py  tickets, codes, cancel, verify
├── report_manager.py  statistics and reports
├── validation.py      reusable input validation
├── file_handler.py    CSV read/write/append/update/delete
├── ui.py              colours, boxes, tables (display helpers)
├── test_eventhub.py   automated tests (47 checks)
└── data/              CSV files (created automatically)
```

## How to run
```
python main.py
```
Run tests: `python test_eventhub.py` (uses a temporary data folder).

## Admin credentials (demonstration only)
- Email: `admin@eventhub.com`
- Password: `Admin@12345`

## CSV storage
| File | Columns |
|---|---|
| users.csv | user_id, name, email, password_hash, created_at |
| admins.csv | admin_id, email, password_hash |
| events.csv | event_id, name, category, description, date, time, venue, organizer, capacity, registration_deadline |
| registrations.csv | registration_id, user_email, event_id, registration_date, status, ticket_id |
| tickets.csv | ticket_id, verification_code, user_email, event_id, issue_date, status |

Dates are stored as `YYYY-MM-DD`, times as `HH:MM`, and shown to users as `DD-MM-YYYY` / `hh:MM AM/PM`.
Cancelled registrations and tickets are never deleted, so reports can count them.

## User flow
Register → Login → Browse/Search → Register for event → Digital pass (saved in tickets.csv) → My Passes → Cancel (optional).

## Admin flow
Admin login → Add events (set capacity) → View registrations → Verify ticket at entry (mark USED) → Reports.

## Key rules
- Available seats = capacity − ACTIVE registrations
- One active registration per email per event
- Capacity cannot be reduced below current active registrations
- An event with active registrations cannot be deleted
- Revenue is always ₹0 because all events are free

## Testing
`test_eventhub.py` covers registration (valid, duplicate, invalid email, mismatch, weak password), logins, event add/view/search/update/delete, registration, duplicate, full event, cancel, seat restoration, ticket verification (valid/cancelled/used/invalid), all reports and status changes.

## Limitations
- Academic project: SHA-256 without salt, fixed admin account, no network access, CSV is not safe for many simultaneous users.
- No separate "UPCOMING" status: an event with open registration is shown as OPEN FOR REGISTRATION.
- Recursion is not used: no part of this problem (loops over CSV rows) naturally needs it.
- Bitwise operators are not used because the business logic has no meaningful use for them.
