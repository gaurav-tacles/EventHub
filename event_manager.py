"""event_manager.py - add/view/search/update/delete events, event status
and seat (capacity) calculations."""
from datetime import date, datetime

import file_handler
import ui
import validation

# ---- Event statuses ----
STATUS_OPEN = "OPEN FOR REGISTRATION"
STATUS_FULL = "FULL"
STATUS_CLOSED = "REGISTRATION CLOSED"
STATUS_ONGOING = "ONGOING"
STATUS_COMPLETED = "COMPLETED"

NEARLY_FULL_PERCENT = 80   # capacity alert threshold (80% or more)

CATEGORIES = ["Workshop", "Seminar", "College Event", "Competition", "Hackathon",
              "Cultural", "Technical", "Sports", "Conference", "Other"]


def parse_date(text):
    return datetime.strptime(text, "%Y-%m-%d").date()


# ---------------- reading data ----------------
def get_events():
    """Read all events; capacity is converted from text to a number."""
    events = file_handler.read_csv("events")
    for event in events:
        try:
            event["capacity"] = int(event["capacity"])
        except ValueError:
            event["capacity"] = 0
    return events


def find_event(event_id):
    """Return the event with this ID (case-insensitive) or None."""
    for event in get_events():
        if event["event_id"] == event_id.strip().upper():
            return event
    return None


def event_name(event_id):
    event = find_event(event_id)
    return event["name"] if event is not None else "(deleted event)"


# ---------------- capacity ----------------
def count_active_registrations(event_id):
    """Count registrations of this event whose status is ACTIVE."""
    total = 0
    for reg in file_handler.read_csv("registrations"):
        if reg["event_id"] == event_id and reg["status"] == "ACTIVE":
            total += 1
    return total


def calculate_available_seats(event, registered=None):
    """available_seats = capacity - active registrations"""
    if registered is None:
        registered = count_active_registrations(event["event_id"])
    return max(event["capacity"] - registered, 0)


def occupancy_percent(event, registered=None):
    if registered is None:
        registered = count_active_registrations(event["event_id"])
    if event["capacity"] == 0:
        return 0.0
    return registered * 100 / event["capacity"]


def capacity_alert(event, registered=None):
    """Return an alert message when the event is (nearly) full, else ''."""
    percent = occupancy_percent(event, registered)
    if percent >= 100:
        return "EVENT FULL"
    elif percent >= NEARLY_FULL_PERCENT:
        return "WARNING: Event is nearly full."
    return ""


# ---------------- status ----------------
def get_event_status(event, today=None):
    """Work out the status automatically (nobody updates it by hand):
       1. today is after the event date           -> COMPLETED
       2. today is the event date                 -> ONGOING
       3. no seats left                           -> FULL
       4. today is after registration deadline    -> REGISTRATION CLOSED
       5. otherwise                               -> OPEN FOR REGISTRATION
    (An event whose registration is still open is shown as open; there is no
    separate 'opening date', so UPCOMING is covered by status 5.)"""
    if today is None:
        today = date.today()
    try:
        event_date = parse_date(event["date"])
        deadline = parse_date(event["registration_deadline"])
    except (ValueError, KeyError):
        return "UNKNOWN"

    if today > event_date:
        return STATUS_COMPLETED
    elif today == event_date:
        return STATUS_ONGOING
    elif calculate_available_seats(event) <= 0:
        return STATUS_FULL
    elif today > deadline:
        return STATUS_CLOSED
    return STATUS_OPEN


# ---------------- generating ID ----------------
def generate_event_id():
    """EV001, EV002 ... (highest existing number + 1)."""
    highest = 0
    for event in get_events():
        number = int(event["event_id"][2:]) if event["event_id"][2:].isdigit() else 0
        if number > highest:
            highest = number
    return f"EV{highest + 1:03d}"


# ---------------- viewing ----------------
def view_events(events=None, title="EVENTS"):
    """Show events in a table. If no list is given, show all events."""
    if events is None:
        events = get_events()
    ui.heading(title)
    if len(events) == 0:
        ui.warning("No matching events found.")
        return
    rows = []
    for e in events:
        rows.append([e["event_id"], e["name"], e["category"],
                     validation.format_date(e["date"]),
                     get_event_status(e), calculate_available_seats(e)])
    ui.table(["ID", "Event", "Category", "Date", "Status", "Seats Left"], rows)


def show_event_details(event):
    registered = count_active_registrations(event["event_id"])
    details = [
        ("Event ID", event["event_id"]),
        ("Event Name", event["name"]),
        ("Category", event["category"]),
        ("Description", event["description"]),
        ("Date", validation.format_date(event["date"])),
        ("Time", validation.format_time(event["time"])),
        ("Venue", event["venue"]),
        ("Organizer", event["organizer"]),
        ("Capacity", event["capacity"]),
        ("Registered", registered),
        ("Available Seats", calculate_available_seats(event, registered)),
        ("Registration Deadline", validation.format_date(event["registration_deadline"])),
        ("Status", get_event_status(event)),
    ]
    ui.heading("EVENT DETAILS")
    for label, value in details:
        print(f"{label + ':':<24}{value}")
    alert = capacity_alert(event, registered)
    if alert != "":
        ui.warning(alert)


def ask_and_show_details():
    event_id = validation.validate_required("Enter Event ID: ", "Event ID")
    event = find_event(event_id)
    if event is None:
        ui.error("Event not found.")
    else:
        show_event_details(event)


# ---------------- searching ----------------
def search_events():
    """Search by name, category, venue or date using simple string matching."""
    ui.heading("SEARCH EVENTS")
    ui.show_menu(["Event name", "Category", "Venue", "Date (YYYY-MM-DD)"])
    choice = validation.validate_choice("Search by: ", ["1", "2", "3", "4"])
    field = {"1": "name", "2": "category", "3": "venue", "4": "date"}[choice]
    keyword = validation.validate_required("Enter search text: ", "Search text").lower()

    matches = []
    for event in get_events():
        if keyword in event[field].lower():   # 'in' checks for partial match
            matches.append(event)
    if len(matches) == 0:
        ui.warning("No matching events found.")
    else:
        view_events(matches, title="SEARCH RESULTS")
    return matches


# ---------------- add ----------------
def choose_category():
    for number, name in enumerate(CATEGORIES, start=1):
        print(f"  {number}. {name}")
    choice = validation.validate_choice(
        "Choose category number: ", [str(n) for n in range(1, len(CATEGORIES) + 1)])
    category = CATEGORIES[int(choice) - 1]
    if category == "Other":
        category = validation.validate_required("Enter category name: ", "Category")
    return category


def ask_deadline(event_date):
    """Deadline must be today or later, and not after the event date."""
    while True:
        deadline = validation.validate_date(
            "Registration Deadline (YYYY-MM-DD): ", allow_past=False)
        if deadline > event_date:
            ui.error("Deadline cannot be after the event date.")
            continue
        return deadline


def add_event():
    ui.heading("ADD EVENT")
    name = validation.validate_required("Event Name: ", "Event name")
    category = choose_category()
    description = validation.validate_required("Description: ", "Description")
    event_date = validation.validate_date("Date (YYYY-MM-DD): ", allow_past=False)
    time_text = validation.validate_time("Time (HH:MM, 24-hour): ")
    venue = validation.validate_required("Venue: ", "Venue")
    organizer = validation.validate_required("Organizer: ", "Organizer")
    capacity = validation.validate_positive_integer("Capacity (seats): ")
    deadline = ask_deadline(event_date)

    event = {
        "event_id": generate_event_id(), "name": name, "category": category,
        "description": description, "date": event_date, "time": time_text,
        "venue": venue, "organizer": organizer, "capacity": capacity,
        "registration_deadline": deadline,
    }
    file_handler.append_csv("events", event)
    ui.success(f"Event added successfully with ID {event['event_id']}.")


# ---------------- update ----------------
def update_event():
    ui.heading("UPDATE EVENT")
    event = find_event(validation.validate_required("Enter Event ID: ", "Event ID"))
    if event is None:
        ui.error("Event not found.")
        return
    show_event_details(event)
    fields = ["Name", "Category", "Description", "Date", "Time", "Venue",
              "Organizer", "Capacity", "Registration Deadline"]
    keys = ["name", "category", "description", "date", "time", "venue",
            "organizer", "capacity", "registration_deadline"]

    while True:
        print("\nWhich field do you want to update?")
        ui.show_menu(fields + ["Finish updating"])
        choice = validation.validate_choice(
            "Choice: ", [str(n) for n in range(1, len(fields) + 2)])
        if choice == str(len(fields) + 1):
            break
        key = keys[int(choice) - 1]
        event = find_event(event["event_id"])      # reload latest data
        new_value = ask_new_value(event, key)
        if new_value is None:
            continue
        file_handler.update_csv("events", "event_id", event["event_id"], {key: new_value})
        ui.success("Event updated. Existing registrations and tickets are unchanged.")


def ask_new_value(event, key):
    """Ask for a new value of one field. Returns None if the update is rejected."""
    if key == "capacity":
        new_capacity = validation.validate_positive_integer("New capacity: ")
        active = count_active_registrations(event["event_id"])
        if new_capacity < active:
            ui.error("Cannot reduce capacity below current active registrations.")
            return None
        return new_capacity
    if key == "category":
        return choose_category()
    if key == "date":
        new_date = validation.validate_date("New date (YYYY-MM-DD): ", allow_past=False)
        if new_date < event["registration_deadline"]:
            ui.error("Event date cannot be before the registration deadline. "
                     "Update the deadline first.")
            return None
        return new_date
    if key == "time":
        return validation.validate_time("New time (HH:MM): ")
    if key == "registration_deadline":
        return ask_deadline(event["date"])
    return validation.validate_required(f"New {key}: ", key.capitalize())


# ---------------- delete ----------------
def delete_event():
    ui.heading("DELETE EVENT")
    event = find_event(validation.validate_required("Enter Event ID: ", "Event ID"))
    if event is None:
        ui.error("Event not found.")
        return
    active = count_active_registrations(event["event_id"])
    if active > 0:
        ui.warning(f"This event has {active} active registration(s). "
                   "Deletion is not allowed.")
        return
    if validation.confirm("Are you sure you want to delete this event?"):
        file_handler.delete_csv("events", "event_id", event["event_id"])
        ui.success("Event deleted.")
    else:
        ui.info("Deletion cancelled.")
