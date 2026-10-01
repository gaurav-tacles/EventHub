"""validation.py - reusable input functions. Each one keeps asking (while loop)
until the user types something valid, so bad input never crashes the program."""
import getpass
import re
from datetime import datetime, date

import ui

EMAIL_PATTERN = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$"


def validate_required(prompt, field="This field"):
    """Ask until the user types something non-empty."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        ui.error(f"{field} cannot be empty.")


def is_valid_email(email):
    return re.match(EMAIL_PATTERN, email) is not None


def validate_email(prompt="Email: "):
    """Ask until a correctly formatted email is entered (returned in lowercase)."""
    while True:
        email = input(prompt).strip().lower()
        if is_valid_email(email):
            return email
        ui.error("Invalid email format (example: name@example.com).")


def read_password(prompt="Password: "):
    """Read a password without echoing it on the screen."""
    return getpass.getpass(prompt)


def password_problem(password):
    """Return a message describing what is wrong, or '' if the password is OK."""
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    has_letter = has_digit = False
    for ch in password:
        if ch.isalpha():
            has_letter = True
        elif ch.isdigit():
            has_digit = True
    if not (has_letter and has_digit):
        return "Password must contain both letters and numbers."
    return ""


def validate_password(prompt="Password: "):
    """Ask until a reasonably strong password is entered."""
    while True:
        password = read_password(prompt)
        problem = password_problem(password)
        if problem == "":
            return password
        ui.error(problem)


def validate_positive_integer(prompt):
    """Ask until a whole number greater than 0 is entered."""
    while True:
        text = input(prompt).strip()
        try:
            number = int(text)
        except ValueError:
            ui.error("Invalid input. Please enter a valid number.")
            continue
        if number <= 0:
            ui.error("Number must be greater than 0.")
            continue
        return number


def validate_date(prompt="Date (YYYY-MM-DD): ", allow_past=True, allow_blank=False):
    """Ask until a valid YYYY-MM-DD date is entered. Returns the date as text."""
    while True:
        text = input(prompt).strip()
        if text == "" and allow_blank:
            return ""
        try:
            chosen = datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            ui.error("Invalid date. Use YYYY-MM-DD (example: 2026-10-15).")
            continue
        if not allow_past and chosen < date.today():
            ui.error("Date cannot be in the past.")
            continue
        return chosen.strftime("%Y-%m-%d")


def validate_time(prompt="Time (HH:MM, 24-hour): ", allow_blank=False):
    """Ask until a valid HH:MM time is entered."""
    while True:
        text = input(prompt).strip()
        if text == "" and allow_blank:
            return ""
        try:
            chosen = datetime.strptime(text, "%H:%M")
        except ValueError:
            ui.error("Invalid time. Use HH:MM in 24-hour format (example: 14:30).")
            continue
        return chosen.strftime("%H:%M")


def validate_choice(prompt, valid_choices):
    """Ask until the answer is one of valid_choices (menu validation)."""
    while True:
        choice = input(prompt).strip()
        if choice in valid_choices:
            return choice
        ui.error("Invalid choice. Please select one of: " + ", ".join(valid_choices))


def confirm(prompt):
    """Ask a Y/N question. Returns True for yes, False for no."""
    while True:
        answer = input(prompt + " (Y/N): ").strip().upper()
        if answer in ("Y", "N"):
            return answer == "Y"
        ui.error("Please enter Y or N.")


# ---- display helpers (dates are stored as YYYY-MM-DD / HH:MM) ----
def format_date(text):
    """2026-10-15 -> 15-10-2026"""
    try:
        return datetime.strptime(text, "%Y-%m-%d").strftime("%d-%m-%Y")
    except ValueError:
        return text


def format_time(text):
    """14:30 -> 02:30 PM"""
    try:
        t = datetime.strptime(text, "%H:%M")
    except ValueError:
        return text
    hour12 = t.hour % 12          # modulo converts 24-hour to 12-hour
    if hour12 == 0:
        hour12 = 12
    suffix = "AM" if t.hour < 12 else "PM"
    return f"{hour12:02d}:{t.minute:02d} {suffix}"
