import getpass
from datetime import datetime
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich import box

from database import Database
from auth import AuthManager
from ui import TerminalUI
from models import ResidentModel, CertificateModel, RequestModel


class BarangayApp:
    def __init__(self):
        self.db = Database()
        self.auth = AuthManager(self.db)
        self.ui = TerminalUI()
        self.residents = ResidentModel(self.db)
        self.certificates = CertificateModel(self.db)
        self.requests = RequestModel(self.db)

    def validate_date(self, date_str):
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def run(self):
        while True:
            if not self.auth.current_user:
                if not self.login_screen():
                    break
            else:
                self.main_dashboard()

    def login_screen(self):
        self.ui.set_theme("retro_green")
        self.ui.print_banner()
        self.ui.print_menu("SYSTEM AUTHENTICATION", {
            "1": "Login to Terminal",
            "0": "Exit System"
        })
        choice = self.ui.prompt("Select option")
        if choice == "0":
            self.ui.print_success("Shutting down terminal. Goodbye!")
            return False
        elif choice == "1":
            username = self.ui.prompt("Username")
            password = getpass.getpass("  Password: ")
            self.ui.loading("AUTHENTICATING CREDENTIALS...")
            if self.auth.login(username, password):
                self.ui.set_theme(self.auth.current_user['theme'])
                self.ui.print_success(f"Access Granted. Welcome, {username}!")
                self.ui.pause()
            else:
                self.ui.print_error("Invalid username or password.")
                self.ui.pause()
        else:
            self.ui.print_error("Invalid selection.")
            self.ui.pause()
        return True

    def main_dashboard(self):
        user = self.auth.current_user
        self.ui.print_banner(user)

        # Dashboard Statistics Cards
        stats = self.requests.get_dashboard_stats()
        cards = [
            Panel(Text(f"TOTAL RESIDENTS\n{stats['residents']}", justify="center", style=self.ui.theme['primary']),
                  border_style=self.ui.theme['border']),
            Panel(Text(f"CERTIFICATE TYPES\n{stats['certificates']}", justify="center", style=self.ui.theme['primary']),
                  border_style=self.ui.theme['border']),
            Panel(Text(f"PENDING REQUESTS\n{stats['pending']}", justify="center", style=self.ui.theme['warning']),
                  border_style=self.ui.theme['border']),
            Panel(Text(f"RELEASED DOCS\n{stats['released']}", justify="center", style=self.ui.theme['primary']),
                  border_style=self.ui.theme['border']),
        ]
        self.ui.console.print(Columns(cards, equal=True, expand=True))

        options = {
            "1": "Manage Residents (CRUD & Search)",
            "2": "Manage Certificate Requests (CRUD & Filter)",
            "3": "Print Certificate Document [GENERATOR]",
            "4": "Reports & Financial Summaries",
            "5": "System Settings (Themes & Password)",
            "0": "Logout"
        }
        if user['role'] == 'Admin':
            options = {
                "1": "Manage Residents ( Search)",
                "2": "Manage Certificate Requests ( Filter)",
                "3": "Print Certificate Document ",
                "4": "Manage Certificate Types [ADMIN]",
                "5": "User Account Management [ADMIN]",
                "6": "Reports & Financial Summaries",
                "7": "System Settings ",
                "0": "Logout"
            }

        self.ui.print_menu("MAIN COMMAND DASHBOARD", options)
        choice = self.ui.prompt("Enter command")

        if user['role'] == 'Admin':
            if choice == "1":
                self.menu_residents()
            elif choice == "2":
                self.menu_requests()
            elif choice == "3":
                self.menu_print_certificate()
            elif choice == "4":
                self.menu_certificates()
            elif choice == "5":
                self.menu_users()
            elif choice == "6":
                self.menu_reports()
            elif choice == "7":
                self.menu_settings()
            elif choice == "0":
                self.auth.logout()
                self.ui.print_success("Logged out successfully.")
                self.ui.pause()
            else:
                self.ui.print_error("Invalid command.")
                self.ui.pause()
        else:
            if choice == "1":
                self.menu_residents()
            elif choice == "2":
                self.menu_requests()
            elif choice == "3":
                self.menu_print_certificate()
    
