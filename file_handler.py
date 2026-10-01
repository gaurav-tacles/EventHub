"""file_handler.py - reusable CSV operations and data folder setup."""
import csv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Header (column names) of every CSV file
HEADERS = {
    "users": ["user_id", "name", "email", "password_hash", "created_at"],
    "admins": ["admin_id", "email", "password_hash"],
    "events": ["event_id", "name", "category", "description", "date", "time",
               "venue", "organizer", "capacity", "registration_deadline"],
    "registrations": ["registration_id", "user_email", "event_id",
                      "registration_date", "status", "ticket_id"],
    "tickets": ["ticket_id", "verification_code", "user_email", "event_id",
                "issue_date", "status"],
}


def ensure_data_directory():
    """Create the data folder if it does not exist."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def get_path(name):
    return os.path.join(DATA_DIR, name + ".csv")


def write_csv(name, rows):
    """Overwrite a CSV file with the given list of dictionaries."""
    ensure_data_directory()
    with open(get_path(name), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS[name])
        writer.writeheader()
        writer.writerows(rows)


def initialize_files():
    """Create every CSV file (with headers) if missing or empty."""
    ensure_data_directory()
    for name in HEADERS:
        path = get_path(name)
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            write_csv(name, [])


def read_csv(name):
    """Return all rows of a CSV file as a list of dictionaries."""
    path = get_path(name)
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        initialize_files()
        return []
    rows = []
    try:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                rows.append(row)
    except (OSError, csv.Error):
        print("Warning: could not read", path)
    return rows


def append_csv(name, row):
    """Add one new row (dictionary) at the end of a CSV file."""
    read_csv(name)  # makes sure the file and header exist
    with open(get_path(name), "a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=HEADERS[name]).writerow(row)


def update_csv(name, key_field, key_value, changes):
    """Update rows where key_field == key_value. Returns True if found."""
    rows = read_csv(name)
    found = False
    for row in rows:
        if row[key_field] == key_value:
            row.update(changes)
            found = True
    if found:
        write_csv(name, rows)
    return found


def delete_csv(name, key_field, key_value):
    """Remove rows where key_field == key_value. Returns True if removed."""
    rows = read_csv(name)
    remaining = [r for r in rows if r[key_field] != key_value]
    if len(remaining) != len(rows):
        write_csv(name, remaining)
        return True
    return False
