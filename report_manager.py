"""report_manager.py - statistics and reports (registrations & attendance).
All numbers are calculated from the CSV files; nothing is hard-coded."""
import event_manager
import file_handler
import ui


def count_registrations_by_event():
    """Returns {event_id: {'ACTIVE': n, 'CANCELLED': n}}"""
    counts = {}
    for reg in file_handler.read_csv("registrations"):
        eid = reg["event_id"]
        if eid not in counts:
            counts[eid] = {"ACTIVE": 0, "CANCELLED": 0}
        if reg["status"] in counts[eid]:
            counts[eid][reg["status"]] += 1
    return counts


def get_statistics():
    """Collect the main numbers used by the dashboard and summary."""
    events = event_manager.get_events()
    regs = file_handler.read_csv("registrations")
    tickets = file_handler.read_csv("tickets")
    per_event = count_registrations_by_event()

    stats = {"total_events": len(events), "open_events": 0, "completed_events": 0,
             "available_seats": 0}
    for event in events:
        status = event_manager.get_event_status(event)
        if status == event_manager.STATUS_OPEN:
            stats["open_events"] += 1
        elif status == event_manager.STATUS_COMPLETED:
            stats["completed_events"] += 1
            continue            # completed events have no seats to offer
        active = per_event.get(event["event_id"], {}).get("ACTIVE", 0)
        stats["available_seats"] += event_manager.calculate_available_seats(event, active)

    stats["total_registrations"] = len(regs)
    stats["active_registrations"] = sum(1 for r in regs if r["status"] == "ACTIVE")
    stats["cancelled_registrations"] = sum(1 for r in regs if r["status"] == "CANCELLED")
    stats["total_tickets"] = len(tickets)
    stats["used_tickets"] = sum(1 for t in tickets if t["status"] == "USED")
    if stats["active_registrations"] > 0:
        stats["attendance"] = stats["used_tickets"] * 100 / stats["active_registrations"]
    else:
        stats["attendance"] = 0.0
    return stats


def print_statistics(stats):
    rows = [
        ("Total Events", stats["total_events"]),
        ("Open Events", stats["open_events"]),
        ("Completed Events", stats["completed_events"]),
        ("Total Registrations", stats["total_registrations"]),
        ("Active Registrations", stats["active_registrations"]),
        ("Cancelled Registrations", stats["cancelled_registrations"]),
        ("Total Tickets", stats["total_tickets"]),
        ("Used Tickets", stats["used_tickets"]),
        ("Available Seats", stats["available_seats"]),
        ("Overall Attendance", f"{stats['attendance']:.1f}%"),
    ]
    for label, value in rows:
        print(f"  {label + ':':<26}{value}")


def overall_summary():
    ui.heading("OVERALL SUMMARY")
    print_statistics(get_statistics())
    print()
    print("  Revenue: ₹0")
    print("  Reason: All EventHub events are free.")


def event_wise_registrations():
    ui.heading("EVENT-WISE REGISTRATIONS")
    events = event_manager.get_events()
    if len(events) == 0:
        ui.warning("No events available.")
        return
    per_event = count_registrations_by_event()
    rows = []
    for e in events:
        c = per_event.get(e["event_id"], {"ACTIVE": 0, "CANCELLED": 0})
        rows.append([e["event_id"], e["name"], c["ACTIVE"], c["CANCELLED"],
                     c["ACTIVE"] + c["CANCELLED"]])
    ui.table(["ID", "Event", "Active", "Cancelled", "Total"], rows, max_width=28)


def capacity_report():
    """Capacity, registered, available and occupancy % for every event."""
    ui.heading("AVAILABLE / OCCUPIED SEATS")
    events = event_manager.get_events()
    if len(events) == 0:
        ui.warning("No events available.")
        return
    per_event = count_registrations_by_event()
    for e in events:
        registered = per_event.get(e["event_id"], {}).get("ACTIVE", 0)
        available = event_manager.calculate_available_seats(e, registered)
        percent = event_manager.occupancy_percent(e, registered)
        print(f"\n{e['name']}")
        print(f"  Capacity: {e['capacity']}")
        print(f"  Registered: {registered}")
        print(f"  Available: {available}")
        print(f"  Occupancy: {percent:.0f}%")
        alert = event_manager.capacity_alert(e, registered)
        if alert == "EVENT FULL":
            ui.error(alert)
        elif alert != "":
            ui.warning(alert)


def most_popular_event():
    ui.heading("MOST POPULAR EVENT")
    per_event = count_registrations_by_event()
    best_id, best_count = None, 0
    for event_id, c in per_event.items():
        if c["ACTIVE"] > best_count:
            best_id, best_count = event_id, c["ACTIVE"]
    if best_id is None:
        ui.warning("No registration data available.")
        return
    print(f"  Event: {event_manager.event_name(best_id)} ({best_id})")
    print(f"  Active registrations: {best_count}")


def category_report():
    ui.heading("CATEGORY-WISE REGISTRATIONS")
    categories = {e["event_id"]: e["category"] for e in event_manager.get_events()}
    totals = {}
    for reg in file_handler.read_csv("registrations"):
        if reg["status"] != "ACTIVE":
            continue
        category = categories.get(reg["event_id"], "Unknown")
        totals[category] = totals.get(category, 0) + 1
    if len(totals) == 0:
        ui.warning("No registration data available.")
        return
    for category, count in sorted(totals.items(), key=lambda item: item[1], reverse=True):
        print(f"  {category:<18}{count:>4}  {'█' * count}")


def cancelled_report():
    ui.heading("CANCELLED REGISTRATIONS")
    rows = []
    for reg in file_handler.read_csv("registrations"):
        if reg["status"] == "CANCELLED":
            rows.append([reg["registration_id"], reg["ticket_id"], reg["user_email"],
                         event_manager.event_name(reg["event_id"])])
    if len(rows) == 0:
        ui.info("No cancelled registrations.")
        return
    ui.table(["Reg ID", "Ticket ID", "Email", "Event"], rows, max_width=26)
    print(f"\n  Total cancelled: {len(rows)}")


def attendance_report():
    ui.heading("TICKET USAGE / ATTENDANCE")
    events = event_manager.get_events()
    if len(events) == 0:
        ui.warning("No events available.")
        return
    tickets = file_handler.read_csv("tickets")
    rows = []
    for e in events:
        active = used = 0
        for t in tickets:
            if t["event_id"] == e["event_id"]:
                if t["status"] == "USED":
                    used += 1
                    active += 1
                elif t["status"] == "ACTIVE":
                    active += 1
        percent = used * 100 / active if active > 0 else 0
        rows.append([e["name"], active, used, f"{percent:.0f}%"])
    ui.table(["Event", "Valid Tickets", "Used", "Attendance"], rows, max_width=28)


def status_summary():
    ui.heading("EVENT STATUS SUMMARY")
    counts = {}
    for e in event_manager.get_events():
        status = event_manager.get_event_status(e)
        counts[status] = counts.get(status, 0) + 1
    if len(counts) == 0:
        ui.warning("No events available.")
        return
    for status, count in counts.items():
        print(f"  {status:<24}{count}")
