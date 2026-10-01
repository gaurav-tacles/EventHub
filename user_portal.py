"""user_portal.py - everything a logged-in normal user can do."""
import event_manager
import ticket_manager
import ui
import validation
from event_manager import STATUS_FULL, STATUS_OPEN


def register_for_event(user, event_id):
    """Register the user for an event if every rule is satisfied."""
    event = event_manager.find_event(event_id)
    if event is None:
        ui.error("Event not found.")
        return False
    # one active registration per email per event
    if ticket_manager.find_active_registration(user["email"], event["event_id"]) is not None:
        ui.warning("You are already registered for this event.")
        return False
    status = event_manager.get_event_status(event)
    if status == STATUS_FULL:
        ui.error("EVENT FULL. No seats are available.")
        return False
    elif status != STATUS_OPEN:
        ui.error(f"Registration is not available (status: {status}).")
        return False

    ticket = ticket_manager.generate_ticket(user["email"], event["event_id"])
    ui.success("Registration successful! Your digital pass:")
    ticket_manager.print_pass(ticket)
    return True


def show_my_passes(user):
    tickets = ticket_manager.get_user_tickets(user["email"])
    ui.heading("MY PASSES")
    if len(tickets) == 0:
        ui.warning("You have no passes yet.")
        return
    rows = []
    for t in tickets:
        event = event_manager.find_event(t["event_id"])
        reg = ticket_manager.get_registration_by_ticket(t["ticket_id"])
        rows.append([
            t["ticket_id"],
            event["name"] if event else "(deleted event)",
            validation.format_date(event["date"]) if event else "-",
            event["venue"] if event else "-",
            reg["status"] if reg else "-",
            t["status"],
        ])
    ui.table(["Ticket ID", "Event", "Date", "Venue", "Pass", "Ticket"], rows)


def get_own_ticket(user, code):
    """Return the ticket only if it belongs to this user, else None."""
    ticket = ticket_manager.find_ticket(code)
    if ticket is not None and ticket["user_email"] == user["email"]:
        return ticket
    return None


def view_pass_details(user):
    code = validation.validate_required("Enter Ticket ID or Verification Code: ")
    ticket = get_own_ticket(user, code)
    if ticket is None:
        ui.error("PASS NOT FOUND")
    else:
        ticket_manager.print_pass(ticket)


def cancel_registration(user):
    code = validation.validate_required("Enter Ticket ID to cancel: ", "Ticket ID")
    ticket = get_own_ticket(user, code)
    if ticket is None:
        ui.error("PASS NOT FOUND")
        return
    if ticket["status"] != "ACTIVE":
        ui.warning(f"This pass is already {ticket['status']} and cannot be cancelled.")
        return
    if validation.confirm("Are you sure you want to cancel this registration?"):
        ticket_manager.cancel_ticket(ticket["ticket_id"])
        ui.success("Registration cancelled. Your seat has been released.")
    else:
        ui.info("Cancellation aborted.")


def verify_my_pass(user):
    code = validation.validate_required("Enter Ticket ID or Verification Code: ")
    ticket = get_own_ticket(user, code)
    if ticket is None:
        ui.error("PASS NOT FOUND")
        return
    ui.success("PASS FOUND")
    print(f"Ticket ID: {ticket['ticket_id']}")
    print(f"Event: {event_manager.event_name(ticket['event_id'])}")
    print(f"Status: {ticket['status']}")


def run_user_portal(user):
    while True:
        ui.banner("EVENTHUB", "USER PORTAL")
        ui.show_menu(["Browse Events", "Search Events", "View Event Details",
                      "Register for Event", "My Passes", "View Pass Details",
                      "Cancel Registration", "Verify My Pass", "Logout"])
        choice = validation.validate_choice("Enter choice: ", [str(n) for n in range(1, 10)])

        if choice == "1":
            event_manager.view_events(title="BROWSE EVENTS")
        elif choice == "2":
            event_manager.search_events()
        elif choice == "3":
            event_manager.ask_and_show_details()
        elif choice == "4":
            event_manager.view_events(title="AVAILABLE EVENTS")
            event_id = validation.validate_required("Enter Event ID to register: ", "Event ID")
            register_for_event(user, event_id)
        elif choice == "5":
            show_my_passes(user)
        elif choice == "6":
            view_pass_details(user)
        elif choice == "7":
            cancel_registration(user)
        elif choice == "8":
            verify_my_pass(user)
        else:
            ui.info("Logged out successfully.")
            break
