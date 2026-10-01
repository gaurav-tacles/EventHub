"""admin_portal.py - admin dashboard, event/registration/ticket management."""
import event_manager
import file_handler
import report_manager
import ticket_manager
import ui
import validation


def show_dashboard():
    ui.banner("EVENTHUB ADMIN", "DASHBOARD")
    print()
    report_manager.print_statistics(report_manager.get_statistics())


def manage_events():
    while True:
        ui.heading("MANAGE EVENTS")
        ui.show_menu(["Add Event", "View Events", "Search Events",
                      "Update Event", "Delete Event", "Return"])
        choice = validation.validate_choice("Enter choice: ", [str(n) for n in range(1, 7)])
        if choice == "1":
            event_manager.add_event()
        elif choice == "2":
            event_manager.view_events(title="ALL EVENTS")
            if validation.confirm("View details of an event?"):
                event_manager.ask_and_show_details()
        elif choice == "3":
            event_manager.search_events()
        elif choice == "4":
            event_manager.update_event()
        elif choice == "5":
            event_manager.delete_event()
        else:
            break


def view_registrations(search_by="all"):
    """Show registrations, optionally filtered. search_by is a column name or 'all'."""
    regs = file_handler.read_csv("registrations")
    keyword = ""
    if search_by != "all":
        keyword = validation.validate_required(f"Enter {search_by.replace('_', ' ')}: ").lower()
    rows = []
    for reg in regs:
        if search_by != "all" and keyword not in reg[search_by].lower():
            continue
        rows.append([reg["registration_id"], reg["ticket_id"],
                     ticket_manager.get_user_name(reg["user_email"]), reg["user_email"],
                     event_manager.event_name(reg["event_id"]),
                     validation.format_date(reg["registration_date"]), reg["status"]])
    ui.heading("REGISTRATIONS")
    if len(rows) == 0:
        ui.warning("No matching registrations found.")
        return
    ui.table(["Reg ID", "Ticket ID", "Name", "Email", "Event", "Date", "Status"],
             rows, max_width=22)
    print(f"\n  Total shown: {len(rows)}")


def registration_menu():
    while True:
        ui.heading("REGISTRATION MANAGEMENT")
        ui.show_menu(["View all registrations", "Search by Event ID", "Search by Email",
                      "Search by Ticket ID", "Search by Status (ACTIVE/CANCELLED)", "Return"])
        choice = validation.validate_choice("Enter choice: ", [str(n) for n in range(1, 7)])
        if choice == "1":
            view_registrations()
        elif choice == "2":
            view_registrations(search_by="event_id")
        elif choice == "3":
            view_registrations(search_by="user_email")
        elif choice == "4":
            view_registrations(search_by="ticket_id")
        elif choice == "5":
            view_registrations(search_by="status")
        else:
            break


def verify_ticket_admin():
    """Entry-gate verification: valid tickets can be marked as USED."""
    ui.heading("VERIFY TICKET")
    code = validation.validate_required("Enter Ticket ID or Verification Code: ")
    result, ticket = ticket_manager.verify_ticket(code)
    if result == "INVALID":
        ui.error("INVALID PASS")
    elif result == "USED":
        ui.warning("PASS ALREADY USED")
    elif result == "CANCELLED":
        ui.error("PASS CANCELLED")
    else:
        event = event_manager.find_event(ticket["event_id"])
        ui.success("VALID PASS")
        print(f"Ticket ID: {ticket['ticket_id']}")
        print(f"Name: {ticket_manager.get_user_name(ticket['user_email'])}")
        print(f"Event: {event['name'] if event else '(deleted event)'}")
        print(f"Date: {validation.format_date(event['date']) if event else '-'}")
        print(f"Venue: {event['venue'] if event else '-'}")
        print("Status: VALID")
        if validation.confirm("Mark this ticket as USED?"):
            ticket_manager.mark_ticket_used(ticket["ticket_id"])
            ui.success("Ticket marked as USED.")


def manage_tickets():
    while True:
        ui.heading("MANAGE TICKETS")
        ui.show_menu(["View all tickets", "Cancel a ticket", "Return"])
        choice = validation.validate_choice("Enter choice: ", ["1", "2", "3"])
        if choice == "1":
            ticket_manager.view_tickets(file_handler.read_csv("tickets"), "ALL TICKETS")
        elif choice == "2":
            code = validation.validate_required("Enter Ticket ID: ", "Ticket ID")
            ticket = ticket_manager.find_ticket(code)
            if ticket is None:
                ui.error("INVALID PASS")
            elif ticket["status"] != "ACTIVE":
                ui.warning(f"Ticket is already {ticket['status']}; cannot cancel.")
            elif validation.confirm("Cancel this ticket?"):
                ticket_manager.cancel_ticket(ticket["ticket_id"])
                ui.success("Ticket and registration cancelled; seat released.")
        else:
            break


def reports_menu():
    reports = [report_manager.overall_summary, report_manager.event_wise_registrations,
               report_manager.capacity_report, report_manager.most_popular_event,
               report_manager.category_report, report_manager.cancelled_report,
               report_manager.attendance_report, report_manager.status_summary]
    while True:
        ui.heading("REPORTS & STATISTICS")
        ui.show_menu(["Overall Summary", "Event-wise Registrations",
                      "Available / Occupied Seats", "Most Popular Event",
                      "Category-wise Registrations", "Cancelled Registrations",
                      "Ticket Usage / Attendance", "Event Status Summary", "Return"])
        choice = validation.validate_choice("Enter choice: ", [str(n) for n in range(1, 10)])
        if choice == "9":
            break
        reports[int(choice) - 1]()      # call the chosen report function


def run_admin_portal():
    while True:
        show_dashboard()
        ui.show_menu(["Manage Events", "View Registrations", "Verify Ticket",
                      "Manage Tickets", "Reports & Statistics", "Logout"])
        choice = validation.validate_choice("Enter choice: ", [str(n) for n in range(1, 7)])
        if choice == "1":
            manage_events()
        elif choice == "2":
            registration_menu()
        elif choice == "3":
            verify_ticket_admin()
        elif choice == "4":
            manage_tickets()
        elif choice == "5":
            reports_menu()
        else:
            ui.info("Admin logged out.")
            break
