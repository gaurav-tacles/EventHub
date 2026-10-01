"""auth.py - user registration, user login, admin login and password hashing."""
import hashlib
from datetime import date

import file_handler
import ui
import validation

# Fixed administrator credentials (documented in README for demonstration)
ADMIN_EMAIL = "admin@eventhub.com"
ADMIN_PASSWORD = "Admin@12345"
MAX_LOGIN_ATTEMPTS = 3


def hash_password(password):
    """Turn a password into a SHA-256 hash. The same password always gives the
    same hash, so we can compare hashes instead of storing the password."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def setup_admin():
    """Make sure admins.csv contains exactly the one fixed administrator."""
    admins = file_handler.read_csv("admins")
    if len(admins) != 1 or admins[0]["email"] != ADMIN_EMAIL:
        file_handler.write_csv("admins", [{
            "admin_id": "AD001",
            "email": ADMIN_EMAIL,
            "password_hash": hash_password(ADMIN_PASSWORD),
        }])


def find_user(email):
    """Return the user dictionary for an email, or None."""
    for user in file_handler.read_csv("users"):
        if user["email"] == email:
            return user
    return None


def generate_user_id():
    return f"US{len(file_handler.read_csv('users')) + 1:03d}"


def register_user():
    """Create a new user account after validating every field."""
    ui.heading("USER REGISTRATION")
    name = validation.validate_required("Full Name: ", "Name")

    while True:
        email = validation.validate_email("Email: ")
        if find_user(email) is not None:
            ui.error("This email is already registered. Please use another.")
            continue
        break

    while True:
        password = validation.validate_password("Password: ")
        confirm = validation.read_password("Confirm Password: ")
        if password == confirm:
            break
        ui.error("Passwords do not match. Please try again.")

    file_handler.append_csv("users", {
        "user_id": generate_user_id(),
        "name": name,
        "email": email,
        "password_hash": hash_password(password),
        "created_at": date.today().isoformat(),
    })
    ui.success("Account created successfully! You can now log in.")


def login_user():
    """Ask for email and password. Returns the user dictionary or None."""
    ui.heading("USER LOGIN")
    for attempt in range(1, MAX_LOGIN_ATTEMPTS + 1):
        email = validation.validate_required("Email: ", "Email").lower()
        password = validation.read_password("Password: ")
        user = find_user(email)
        # compare the hash of the typed password with the stored hash
        if user is not None and user["password_hash"] == hash_password(password):
            ui.banner("WELCOME TO EVENTHUB", user["name"])
            return user
        ui.error("Incorrect email or password.")
        if attempt < MAX_LOGIN_ATTEMPTS:
            ui.info(f"Attempt {attempt} of {MAX_LOGIN_ATTEMPTS}. Try again.")
    ui.error("Too many failed attempts. Returning to main menu.")
    return None


def admin_login():
    """Separate admin login. Returns True on success, False otherwise."""
    ui.banner("EVENTHUB ADMIN")
    admin = file_handler.read_csv("admins")[0]
    while True:
        email = validation.validate_required("Email: ", "Email").lower()
        password = validation.read_password("Password: ")
        if email == admin["email"] and hash_password(password) == admin["password_hash"]:
            ui.success("Admin login successful.")
            return True
        ui.error("Invalid admin credentials.")
        if not validation.confirm("Try again?"):
            return False
