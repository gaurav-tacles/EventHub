"""ticket_manager.py - create, view, cancel and verify tickets/passes."""
import random
import string
from datetime import date

import event_manager
import file_handler
import ui
import validation

CODE_LENGTH = 6   # verification code = "EH" + 6 letters/digits


# ---------------- helpers ----------------
def get_user_name(email):
    for user in file_handler.read_csv("users"):
        if user["email"] == email:
            return user["name"]
    return "Unknown"


def generate_ticket_id():
    """EH-<year>-<number>, e.g. EH-2026-0001 (highest number + 1)."""
    highest = 0
    for ticket in file_handler.read_csv("tickets"):
        last_part = ticket["ticket_id"].split("-")[-1]
        if last_part.isdigit() and int(last_part) > highest:
            highest = int(last_part)
    return f"EH-{date.today().year}-{highest + 1:04d}"


def generate_verification_code():
    """Random code like EH7K92P4. Repeats until it is not already used."""
    used = [t["verification_code"] for t in file_handler.read_csv("tickets")]
    characters = string.ascii_uppercase + string.digits
    while True:
        code = "EH" + "".join(random.choice(characters) for _ in range(CODE_LENGTH))
        if code not in used:
            return code


def generate_registration_id():
    highest = 0
    for reg in file_handler.read_csv("registrations"):
        number = reg["registration_id"][3:]
        if number.isdigit() and int(number) > highest:
            highest = int(number)
    return f"REG{highest + 1:04d}"


# ---------------- creating ----------------
def generate_ticket(user_email, event_id):
    """Create the ticket AND its registration record. Returns the ticket."""
    ticket = {
        "ticket_id": generate_ticket_id(),
        "verification_code": generate_verification_code(),
        "user_email": user_email,
        "event_id": event_id,
        "issue_date": date.today().isoformat(),
        "status": "ACTIVE",
    }
    file_handler.append_csv("tickets", ticket)
    file_handler.append_csv("registrations", {
        "registration_id": generate_registration_id(),
        "user_email": user_email,
        "event_id": event_id,
        "registration_date": ticket["issue_date"],
        "status": "ACTIVE",
        "ticket_id": ticket["ticket_id"],
    })
    return ticket


# ---------------- finding ----------------
def find_active_registration(user_email, event_id):
    """Return the user's ACTIVE registration for this event, or None."""
    for reg in file_handler.read_csv("registrations"):
        if (reg["user_email"] == user_email and reg["event_id"] == event_id
                and reg["status"] == "ACTIVE"):
            return reg
    return None


def get_registration_by_ticket(ticket_id):
    for reg in file_handler.read_csv("registrations"):
        if reg["ticket_id"] == ticket_id:
            return reg
    return None


def get_user_tickets(user_email):
    return [t for t in file_handler.read_csv("tickets") if t["user_email"] == user_email]


def find_ticket(code):
    """Find a ticket by Ticket ID or Verification Code (case-insensitive)."""
    code = code.strip().upper()
    for ticket in file_handler.read_csv("tickets"):
        if code == ticket["ticket_id"].upper() or code == ticket["verification_code"]:
            return ticket
    return None


def verify_ticket(code):
    """Returns (result, ticket). result is INVALID, ACTIVE, USED or CANCELLED."""
    ticket = find_ticket(code)
    if ticket is None:
        return "INVALID", None
    return ticket["status"], ticket


# ---------------- changing status ----------------
def mark_ticket_used(ticket_id):
    return file_handler.update_csv("tickets", "ticket_id", ticket_id, {"status": "USED"})


def cancel_ticket(ticket_id):
    """Cancel ticket + registration. Rows are kept (not deleted) for reports.
    The seat is freed automatically because seats count only ACTIVE registrations."""
    file_handler.update_csv("tickets", "ticket_id", ticket_id, {"status": "CANCELLED"})
    file_handler.update_csv("registrations", "ticket_id", ticket_id, {"status": "CANCELLED"})


# ---------------- display ----------------
def print_pass(ticket):
    event = event_manager.find_event(ticket["event_id"])
    reg = get_registration_by_ticket(ticket["ticket_id"])
    reg_status = reg["status"] if reg is not None else "UNKNOWN"
    bar = "=" * 40
    print()
    print(ui.paint(bar, ui.CYAN))
    print("EVENTHUB PASS".center(40))
    print()
    print(f"Ticket ID: {ticket['ticket_id']}")
    print(f"Verification Code: {ticket['verification_code']}")
    print()
    print(f"Name: {get_user_name(ticket['user_email'])}")
    print(f"Email: {ticket['user_email']}")
    print()
    if event is not None:
        print(f"Event: {event['name']} ({event['event_id']})")
        print(f"Category: {event['category']}")
        print(f"Date: {validation.format_date(event['date'])}")
        print(f"Time: {validation.format_time(event['time'])}")
        print(f"Venue: {event['venue']}")
    else:
        print(f"Event: (deleted event) {ticket['event_id']}")
    print()
    print(f"Registration Status: {reg_status}")
    print(f"Ticket Status: {ticket['status']}")
    print(ui.paint(bar, ui.CYAN))


def view_tickets(tickets, title="TICKETS"):
    ui.heading(title)
    if len(tickets) == 0:
        ui.warning("No tickets found.")
        return
    rows = []
    for t in tickets:
        rows.append([t["ticket_id"], t["verification_code"], t["user_email"],
                     event_manager.event_name(t["event_id"]), t["status"]])
    ui.table(["Ticket ID", "Code", "Email", "Event", "Status"], rows)
