"""Automated checks for EventHub (run: python test_eventhub.py).
Uses a temporary data folder, so real data is never touched."""
import io, os, sys, tempfile, contextlib
from datetime import date, timedelta
from unittest.mock import patch

import file_handler
file_handler.DATA_DIR = tempfile.mkdtemp()
import auth, event_manager as em, ticket_manager as tm, report_manager as rm
import admin_portal, user_portal

file_handler.initialize_files(); auth.setup_admin()
passed = failed = 0

def run(func, inputs, passwords=(), *args, **kw):
    """Run func with scripted input()/password answers; return (result, printed text)."""
    out = io.StringIO()
    with patch("builtins.input", side_effect=list(inputs)), \
         patch("getpass.getpass", side_effect=list(passwords)), \
         contextlib.redirect_stdout(out):
        result = func(*args, **kw)
    return result, out.getvalue()

def check(name, condition, text=""):
    global passed, failed
    if condition: passed += 1; print("PASS", name)
    else: failed += 1; print("FAIL", name, "\n", text[-400:])

d = lambda n: (date.today() + timedelta(days=n)).isoformat()
# 1-4 registration
_, o = run(auth.register_user, ["Gaurav Patel", "gaurav@example.com"], ["Pass1234", "Pass1234"])
check("1 register valid", auth.find_user("gaurav@example.com") is not None, o)
_, o = run(auth.register_user, ["X", "gaurav@example.com", "x2@example.com"], ["Pass1234", "Pass1234"])
check("2 duplicate email", "already registered" in o, o)
_, o = run(auth.register_user, ["Y", "bademail", "y@example.com"], ["Pass1234", "Pass1234"])
check("3 invalid email", "Invalid email" in o, o)
_, o = run(auth.register_user, ["Z", "z@example.com"], ["Pass1234", "Nope1234", "Pass1234", "Pass1234"])
check("4 password mismatch", "do not match" in o, o)
_, o = run(auth.register_user, ["W", "w@example.com"], ["abc", "alllettersss", "Pass1234", "Pass1234"])
check("4b weak password", "at least 8" in o and "letters and numbers" in o, o)
# 5-6 login
user, o = run(auth.login_user, ["gaurav@example.com"], ["Pass1234"])
check("5 login", user is not None and "WELCOME TO EVENTHUB" in o, o)
user2, o = run(auth.login_user, ["gaurav@example.com"] * 3, ["bad"] * 3)
check("6 wrong password", user2 is None and "Incorrect" in o, o)
# 7-8 admin
ok, o = run(auth.admin_login, ["admin@eventhub.com"], ["Admin@12345"])
check("7 admin login", ok is True, o)
ok, o = run(auth.admin_login, ["admin@eventhub.com", "N"], ["wrong"])
check("8 wrong admin password", ok is False and "Invalid admin credentials." in o, o)
check("hash not plain", "Pass1234" not in open(file_handler.get_path("users")).read())
# 9-11 add/view/search events
_, o = run(em.add_event, ["Python Workshop", "1", "Learn Python", "bad-date", d(14), "25:00", "10:00",
                          "Silver Oak University", "CS Club", "abc", "-5", "2", d(20), d(10)])
check("9 add event", "EV001" in o and "Invalid date" in o and "Invalid time" in o
      and "valid number" in o and "after the event" in o, o)
run(em.add_event, ["Hack Night", "5", "24h hack", d(30), "09:00", "Lab", "Dev Club", "1", d(25)])
run(em.add_event, ["Old Fest", "6", "x", d(5), "09:00", "Hall", "Cul", "10", d(3)])
_, o = run(em.view_events, [])
check("10 view events", "Python Workshop" in o and "Hack Night" in o, o)
res, o = run(em.search_events, ["2", "work"])
check("11 search found", len(res) == 1, o)
res, o = run(em.search_events, ["3", "zzz"])
check("11b search none", "No matching events found." in o, o)
# 14-15 register
user = auth.find_user("gaurav@example.com")
r, o = run(user_portal.register_for_event, [], [], user, "EV001")
check("14 register + pass", r and "EVENTHUB PASS" in o and "EH-" in o, o)
r, o = run(user_portal.register_for_event, [], [], user, "ev001")
check("15 duplicate registration", not r and "already registered" in o, o)
# 16 full
run(auth.register_user, ["Second", "second@example.com"], ["Pass1234", "Pass1234"])
u2 = auth.find_user("second@example.com")
run(user_portal.register_for_event, [], [], u2, "EV002")
u3 = {"email": "second@example.com", "name": "Second"}
run(auth.register_user, ["Third", "third@example.com"], ["Pass1234", "Pass1234"])
u3 = auth.find_user("third@example.com")
r, o = run(user_portal.register_for_event, [], [], u3, "EV002")
check("16 full event", not r and "FULL" in o, o)
check("16b status FULL", em.get_event_status(em.find_event("EV002")) == "FULL")
# 17-18 cancel + seats restored
t = tm.get_user_tickets("second@example.com")[0]
before = em.calculate_available_seats(em.find_event("EV002"))
_, o = run(user_portal.cancel_registration, [t["ticket_id"], "Y"], [], u2)
after = em.calculate_available_seats(em.find_event("EV002"))
check("17 cancel", "cancelled" in o.lower() and tm.find_ticket(t["ticket_id"])["status"] == "CANCELLED", o)
check("18 seat restored", before == 0 and after == 1)
r, o = run(user_portal.register_for_event, [], [], u3, "EV002")
check("18b freed seat usable", r)
# 19-23 tickets
t1 = tm.get_user_tickets("gaurav@example.com")[0]
check("19 ticket saved", t1["status"] == "ACTIVE" and t1["verification_code"].startswith("EH"))
_, o = run(admin_portal.verify_ticket_admin, [t1["verification_code"], "N"])
check("20 verify valid", "VALID PASS" in o, o)
_, o = run(admin_portal.verify_ticket_admin, [t["ticket_id"]])
check("21 verify cancelled", "PASS CANCELLED" in o, o)
_, o = run(admin_portal.verify_ticket_admin, [t1["ticket_id"], "Y"])
_, o2 = run(admin_portal.verify_ticket_admin, [t1["ticket_id"]])
check("22 mark used then already used", "marked as USED" in o and "ALREADY USED" in o2, o + o2)
_, o = run(admin_portal.verify_ticket_admin, ["NOPE"])
check("23 invalid ticket", "INVALID PASS" in o, o)
_, o = run(user_portal.verify_my_pass, [t1["ticket_id"]], [], u2)
check("23b user cannot see others' pass", "PASS NOT FOUND" in o, o)
# 12 update, 13 delete
_, o = run(em.update_event, ["EV002", "8", "5", "10"])
check("12 update capacity", em.find_event("EV002")["capacity"] == 5, o)
run(user_portal.register_for_event, [], [], u2, "EV001")        # EV001 now has 2 active
_, o = run(em.update_event, ["EV001", "8", "1", "10"])
check("12b capacity below active rejected", "Cannot reduce capacity" in o and em.find_event("EV001")["capacity"] == 2, o)
_, o = run(em.update_event, ["EV001", "6", "New Venue", "10"])
check("12c update venue keeps tickets", em.find_event("EV001")["venue"] == "New Venue" and len(tm.get_user_tickets("gaurav@example.com")) == 1, o)
_, o = run(em.delete_event, ["EV001"])
check("13 delete blocked with active regs", "not allowed" in o and em.find_event("EV001"), o)
_, o = run(em.delete_event, ["EV003", "Y"])
check("13b delete empty event", em.find_event("EV003") is None, o)
# 24 reports
for fn in [rm.overall_summary, rm.event_wise_registrations, rm.capacity_report, rm.most_popular_event,
           rm.category_report, rm.cancelled_report, rm.attendance_report, rm.status_summary]:
    _, o = run(fn, [])
    check("24 report " + fn.__name__, len(o) > 10 and "Traceback" not in o, o)
_, o = run(rm.overall_summary, [])
check("24b revenue text", "Revenue: ₹0" in o and "free" in o)
# 25 status
run(em.update_event, ["EV001", "8", "25", "10"])
ev = em.find_event("EV001")
check("25 status open", em.get_event_status(ev) == "OPEN FOR REGISTRATION")
check("25 status closed", em.get_event_status(ev, today=date.today() + timedelta(days=11)) == "REGISTRATION CLOSED")
check("25 status ongoing", em.get_event_status(ev, today=date.today() + timedelta(days=14)) == "ONGOING")
check("25 status completed", em.get_event_status(ev, today=date.today() + timedelta(days=15)) == "COMPLETED")
check("alert threshold", em.capacity_alert({"event_id": "EV001", "capacity": 1}) == "EVENT FULL")
# registrations search
_, o = run(admin_portal.view_registrations, ["gaurav"], [], "user_email")
check("admin reg search", "gaurav@example.com" in o, o)
print(f"\n{passed} passed, {failed} failed"); sys.exit(1 if failed else 0)
