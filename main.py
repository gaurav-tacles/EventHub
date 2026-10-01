"""main.py - EventHub entry point: main menu and portal selection."""
import admin_portal
import auth
import file_handler
import ui
import user_portal
import validation


def main():
    file_handler.initialize_files()   # create data folder + CSV files
    auth.setup_admin()                # make sure the admin account exists

    while True:
        ui.banner("EVENTHUB", "EVENT & TICKET MANAGEMENT SYSTEM")
        ui.show_menu(["User Registration", "User Login", "Admin Login", "Exit"])
        choice = validation.validate_choice("Enter choice: ", ["1", "2", "3", "4"])

        if choice == "1":
            auth.register_user()
        elif choice == "2":
            user = auth.login_user()
            if user is not None:
                user_portal.run_user_portal(user)
        elif choice == "3":
            if auth.admin_login():
                admin_portal.run_admin_portal()
        else:
            ui.info("Thank you for using EventHub!")
            break


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print()
        ui.info("Thank you for using EventHub!")
