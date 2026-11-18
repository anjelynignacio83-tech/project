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
                "1": "Manage Residents (CRUD & Search)",
                "2": "Manage Certificate Requests (CRUD & Filter)",
                "3": "Print Certificate Document [GENERATOR]",
                "4": "Manage Certificate Types [ADMIN]",
                "5": "User Account Management [ADMIN]",
                "6": "Reports & Financial Summaries",
                "7": "System Settings (Themes & Password)",
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
            elif choice == "4":
                self.menu_reports()
            elif choice == "5":
                self.menu_settings()
            elif choice == "0":
                self.auth.logout()
                self.ui.print_success("Logged out successfully.")
                self.ui.pause()
            else:
                self.ui.print_error("Invalid command.")
                self.ui.pause()

    # RESIDENT CRUD
    def menu_residents(self):
        while True:
            self.ui.print_banner(self.auth.current_user)
            self.ui.print_menu("RESIDENT RECORDS MANAGEMENT", {
                "1": "View All Residents",
                "2": "Search Resident (Name / ID / Address)",
                "3": "Register New Resident",
                "4": "Update Resident Information",
                "5": "Delete Resident Record",
                "0": "Back to Dashboard"
            })
            choice = self.ui.prompt("Select option")
            if choice == "0":
                break
            elif choice == "1":
                rows = self.residents.get_all()
                formatted = [[r['resident_id'], r['full_name'], r['birthdate'], r['address'], r['contact']] for r in
                             rows]
                self.ui.display_table("REGISTERED BARANGAY RESIDENTS",
                                      ["ID", "Full Name", "Birthdate", "Address", "Contact"], formatted)
            elif choice == "2":
                kw = self.ui.prompt("Enter Name, ID, or Address keyword")
                rows = self.residents.search(kw)
                formatted = [[r['resident_id'], r['full_name'], r['birthdate'], r['address'], r['contact']] for r in
                             rows]
                self.ui.display_table(f"SEARCH RESULTS FOR '{kw}'",
                                      ["ID", "Full Name", "Birthdate", "Address", "Contact"], formatted)
            elif choice == "3":
                name = self.ui.prompt("Full Name")
                bdate = self.ui.prompt("Birthdate (YYYY-MM-DD)")
                addr = self.ui.prompt("Address (Purok/Street)")
                contact = self.ui.prompt("Contact Number")
                if not name or not self.validate_date(bdate):
                    self.ui.print_error("Invalid name or birthdate format (use YYYY-MM-DD).")
                elif self.residents.create(name, bdate, addr, contact):
                    self.ui.print_success("Resident registered successfully.")
            elif choice == "4":
                rid = self.ui.prompt("Enter Resident ID to update")
                existing = self.residents.get_by_id(rid)
                if not existing:
                    self.ui.print_error("Resident ID not found.")
                else:
                    self.ui.print_warning("Leave blank to keep current value.")
                    name = self.ui.prompt(f"Full Name [{existing['full_name']}]") or existing['full_name']
                    bdate = self.ui.prompt(f"Birthdate [{existing['birthdate']}]") or str(existing['birthdate'])
                    addr = self.ui.prompt(f"Address [{existing['address']}]") or existing['address']
                    contact = self.ui.prompt(f"Contact [{existing['contact']}]") or existing['contact']
                    if not self.validate_date(bdate):
                        self.ui.print_error("Invalid date format.")
                    elif self.residents.update(rid, name, bdate, addr, contact):
                        self.ui.print_success("Resident updated successfully.")
            elif choice == "5":
                rid = self.ui.prompt("Enter Resident ID to delete")
                if not self.residents.get_by_id(rid):
                    self.ui.print_error("Resident ID not found.")
                else:
                    confirm = self.ui.prompt("Confirm deletion? (Y/N)").upper()
                    if confirm == "Y" and self.residents.delete(rid):
                        self.ui.print_success("Resident deleted.")
            else:
                self.ui.print_error("Invalid option.")
            self.ui.pause()

    # PRINT & EDIT CERTIFICATE DOCUMENT
    def menu_print_certificate(self):
        from certificate_printer import generate_certificate, DEFAULT_CONFIG
        
        if not hasattr(self, "_cert_config"):
            self._cert_config = DEFAULT_CONFIG.copy()

        while True:
            self.ui.print_banner(self.auth.current_user)
            self.ui.print_menu("PRINT & EDIT CERTIFICATE DOCUMENT", {
                "1": "View Approved/Released Requests",
                "2": "Generate Printable Certificate File (.txt)",
                "3": f"Edit Header & Signatory Details (Current: {self._cert_config['barangay']})",
                "0": "Back to Dashboard"
            })
            choice = self.ui.prompt("Select option")
            if choice == "0":
                break
            elif choice == "1":
                rows = self.requests.filter_requests(status="Approved") + self.requests.filter_requests(status="Released")
                formatted = [[r['request_id'], r['control_no'], r['full_name'], r['cert_name'], r['status']] for r in rows]
                self.ui.display_table("PRINTABLE CERTIFICATE REQUESTS",
                                      ["Req ID", "Control No.", "Resident", "Certificate", "Status"], formatted)
            elif choice == "2":
                req_id = self.ui.prompt("Enter Request ID to generate certificate file")
                cert_data = self.requests.get_certificate_data(req_id)
                if not cert_data:
                    self.ui.print_error("Request ID not found.")
                else:
                    prepared_by = f"{self.auth.current_user['username']} ({self.auth.current_user['role']})"
                    try:
                        file_path = generate_certificate(cert_data, prepared_by=prepared_by, config=self._cert_config)
                        self.ui.print_success("Certificate generated successfully!")
                        self.ui.print_warning(f"Saved to: {file_path}")
                    except Exception as e:
                        self.ui.print_error(f"Failed to generate certificate: {e}")
            elif choice == "3":
                self.ui.print_warning("Leave blank to keep current value.")
                b = self.ui.prompt(f"Barangay Name [{self._cert_config['barangay']}]")
                c = self.ui.prompt(f"City/Municipality [{self._cert_config['city']}]")
                p = self.ui.prompt(f"Province [{self._cert_config['province']}]")
                s = self.ui.prompt(f"Signatory Name [{self._cert_config['signatory_name']}]")
                t = self.ui.prompt(f"Signatory Title [{self._cert_config['signatory_title']}]")

                if b: self._cert_config['barangay'] = b
                if c: self._cert_config['city'] = c
                if p: self._cert_config['province'] = p
                if s: self._cert_config['signatory_name'] = s
                if t: self._cert_config['signatory_title'] = t

                self.ui.print_success("Certificate header and signatory settings updated successfully!")
            else:
                self.ui.print_error("Invalid option.")
            self.ui.pause()

    # CERTIFICATE TYPES CRUD (ADMIN)
    def menu_certificates(self):
        while True:
            self.ui.print_banner(self.auth.current_user)
            self.ui.print_menu("CERTIFICATE TYPES & FEES [ADMIN]", {
                "1": "View All Certificate Types",
                "2": "Add New Certificate Type",
                "3": "Update Certificate Fee/Name",
                "4": "Delete Certificate Type",
                "0": "Back to Dashboard"
            })
            choice = self.ui.prompt("Select option")
            if choice == "0":
                break
            elif choice == "1":
                rows = self.certificates.get_all()
                formatted = [[c['cert_id'], c['cert_name'], f"PHP {c['fee']:.2f}"] for c in rows]
                self.ui.display_table("AVAILABLE CERTIFICATES", ["Cert ID", "Certificate Name", "Fee"], formatted)
            elif choice == "2":
                name = self.ui.prompt("Certificate Name")
                try:
                    fee = float(self.ui.prompt("Fee Amount (PHP)"))
                    if fee < 0: raise ValueError
                    if name and self.certificates.create(name, fee):
                        self.ui.print_success("Certificate type added.")
                except ValueError:
                    self.ui.print_error("Invalid fee amount.")
            elif choice == "3":
                cid = self.ui.prompt("Enter Certificate ID to update")
                existing = self.certificates.get_by_id(cid)
                if not existing:
                    self.ui.print_error("Certificate ID not found.")
                else:
                    name = self.ui.prompt(f"Name [{existing['cert_name']}]") or existing['cert_name']
                    fee_in = self.ui.prompt(f"Fee [{existing['fee']}]")
                    try:
                        fee = float(fee_in) if fee_in else float(existing['fee'])
                        if self.certificates.update(cid, name, fee):
                            self.ui.print_success("Certificate updated.")
                    except ValueError:
                        self.ui.print_error("Invalid fee.")
            elif choice == "4":
                cid = self.ui.prompt("Enter Certificate ID to delete")
                if self.certificates.get_by_id(cid) and self.certificates.delete(cid):
                    self.ui.print_success("Certificate deleted.")
                else:
                    self.ui.print_error("Certificate not found.")
            else:
                self.ui.print_error("Invalid option.")
            self.ui.pause()

    # CERTIFICATE REQUESTS CRUD & FILTER
    def menu_requests(self):
        while True:
            self.ui.print_banner(self.auth.current_user)
            self.ui.print_menu("CERTIFICATE REQUESTS & ISSUANCE", {
                "1": "View All Requests",
                "2": "Filter Requests (Status / Date / Resident)",
                "3": "Create New Certificate Request",
                "4": "Update Request Status (Approve / Release / Cancel)",
                "5": "Delete Request Record",
                "0": "Back to Dashboard"
            })
            choice = self.ui.prompt("Select option")
            if choice == "0":
                break
            elif choice == "1":
                rows = self.requests.get_all_joined()
                formatted = [[r['request_id'], r['full_name'], r['cert_name'], f"PHP {r['fee']:.2f}", r['request_date'],
                              r['status']] for r in rows]
                self.ui.display_table("ALL CERTIFICATE REQUESTS",
                                      ["Req ID", "Resident", "Certificate", "Fee", "Date", "Status"], formatted)
            elif choice == "2":
                self.ui.print_warning("Leave filters blank to skip.")
                status = self.ui.prompt("Status (Pending/Approved/Released/Cancelled)")
                date_str = self.ui.prompt("Date (YYYY-MM-DD)")
                rname = self.ui.prompt("Resident Name")
                rows = self.requests.filter_requests(status or None, date_str or None, rname or None)
                formatted = [[r['request_id'], r['full_name'], r['cert_name'], f"PHP {r['fee']:.2f}", r['request_date'],
                              r['status']] for r in rows]
                self.ui.display_table("FILTERED REQUESTS",
                                      ["Req ID", "Resident", "Certificate", "Fee", "Date", "Status"], formatted)
            elif choice == "3":
                res_list = self.residents.get_all()
                cert_list = self.certificates.get_all()
                self.ui.display_table("RESIDENTS", ["ID", "Name"],
                                      [[r['resident_id'], r['full_name']] for r in res_list])
                self.ui.display_table("CERTIFICATES", ["ID", "Name", "Fee"],
                                      [[c['cert_id'], c['cert_name'], f"PHP {c['fee']:.2f}"] for c in cert_list])

                rid = self.ui.prompt("Enter Resident ID")
                cid = self.ui.prompt("Enter Certificate ID")
                purpose = self.ui.prompt("Purpose / Remarks")
                today = datetime.now().strftime("%Y-%m-%d")
                rdate = self.ui.prompt(f"Request Date [{today}]") or today

                if not self.residents.get_by_id(rid) or not self.certificates.get_by_id(cid):
                    self.ui.print_error("Invalid Resident ID or Certificate ID.")
                elif not self.validate_date(rdate):
                    self.ui.print_error("Invalid date format.")
                elif self.requests.create(rid, cid, rdate, purpose, "Pending"):
                    self.ui.print_success("Certificate request logged (Status: Pending).")
            elif choice == "4":
                req_id = self.ui.prompt("Enter Request ID")
                if not self.requests.get_by_id(req_id):
                    self.ui.print_error("Request ID not found.")
                else:
                    status = self.ui.prompt("New Status (Pending / Approved / Released / Cancelled)").capitalize()
                    if status in ["Pending", "Approved", "Released", "Cancelled"]:
                        if self.requests.update_status(req_id, status):
                            self.ui.print_success(f"Request #{req_id} marked as {status}.")
                    else:
                        self.ui.print_error("Invalid status value.")
            elif choice == "5":
                req_id = self.ui.prompt("Enter Request ID to delete")
                if self.requests.get_by_id(req_id) and self.requests.delete(req_id):
                    self.ui.print_success("Request deleted.")
                else:
                    self.ui.print_error("Request not found.")
            else:
                self.ui.print_error("Invalid option.")
            self.ui.pause()

    # REPORTS
    def menu_reports(self):
        while True:
            self.ui.print_banner(self.auth.current_user)
            self.ui.print_menu("SYSTEM REPORTS & SUMMARIES", {
                "1": "Report 1: Complete Certificate Issuance History (3-Table JOIN)",
                "2": "Report 2: Revenue & Collection Summary per Certificate Type",
                "0": "Back to Dashboard"
            })
            choice = self.ui.prompt("Select report")
            if choice == "0":
                break
            elif choice == "1":
                self.ui.loading("GENERATING ISSUANCE REPORT...")
                rows = self.requests.get_all_joined()
                formatted = [[r['request_id'], r['request_date'], r['full_name'], r['cert_name'], f"PHP {r['fee']:.2f}",
                              r['status']] for r in rows]
                self.ui.display_table("OFFICIAL CERTIFICATE TRANSACTION HISTORY",
                                      ["Req #", "Date", "Resident Name", "Document Type", "Fee", "Status"], formatted)
            elif choice == "2":
                self.ui.loading("CALCULATING REVENUE TOTALS...")
                rows = self.requests.get_revenue_summary()
                grand_total = sum(float(r['total_collected']) for r in rows)
                formatted = [
                    [r['cert_name'], r['total_requests'], r['released_count'], f"PHP {r['total_collected']:.2f}"] for r
                    in rows]
                self.ui.display_table("REVENUE SUMMARY BY CERTIFICATE TYPE (RELEASED DOCS)",
                                      ["Certificate Type", "Total Requests", "Released", "Total Fees Collected"],
                                      formatted)
                self.ui.print_success(f"GRAND TOTAL COLLECTED REVENUE: PHP {grand_total:.2f}")
            else:
                self.ui.print_error("Invalid option.")
            self.ui.pause()

    # MANAGEMENT (ADMIN)
    def menu_users(self):
        while True:
            self.ui.print_banner(self.auth.current_user)
            self.ui.print_menu("USER ACCOUNT MANAGEMENT [ADMIN]", {
                "1": "List System Users",
                "2": "Create New Staff/Admin Account",
                "3": "Delete User Account",
                "0": "Back to Dashboard"
            })
            choice = self.ui.prompt("Select option")
            if choice == "0":
                break
            elif choice == "1":
                users = self.auth.get_all_users()
                formatted = [[u['user_id'], u['username'], u['role'], u['theme']] for u in users]
                self.ui.display_table("SYSTEM ACCOUNTS", ["User ID", "Username", "Role", "Saved Theme"], formatted)
            elif choice == "2":
                uname = self.ui.prompt("New Username")
                pwd = getpass.getpass("  New Password: ")
                role = self.ui.prompt("Role (Admin / Staff)").capitalize()
                if role not in ["Admin", "Staff"] or not uname or not pwd:
                    self.ui.print_error("Invalid username, password, or role.")
                elif self.auth.create_user(uname, pwd, role):
                    self.ui.print_success(f"User '{uname}' ({role}) created.")
            elif choice == "3":
                uid = self.ui.prompt("Enter User ID to delete")
                if self.auth.delete_user(uid):
                    self.ui.print_success("User deleted.")
                else:
                    self.ui.print_error("Cannot delete user (invalid ID or currently logged in).")
            else:
                self.ui.print_error("Invalid option.")
            self.ui.pause()

    # SYSTEM SETTINGS
    def menu_settings(self):
        while True:
            self.ui.print_banner(self.auth.current_user)
            self.ui.print_menu("TERMINAL & ACCOUNT SETTINGS", {
                "1": "Theme: Retro Phosphor Green (Dark)",
                "2": "Theme: Classic Amber CRT (Dark)",
                "3": "Theme: IBM Mainframe Blue",
                "4": "Change My Password",
                "0": "Back to Dashboard"
            })
            choice = self.ui.prompt("Select option")
            if choice == "0":
                break
            elif choice in ["1", "2", "3"]:
                theme_map = {"1": "retro_green", "2": "amber_crt", "3": "cyber_blue"}
                selected = theme_map[choice]
                self.ui.set_theme(selected)
                self.auth.update_theme(selected)
                self.ui.print_success(f"Terminal theme switched to {self.ui.THEMES[selected]['name']}.")
            elif choice == "4":
                new_pwd = getpass.getpass("  Enter New Password: ")
                confirm_pwd = getpass.getpass("  Confirm New Password: ")
                if not new_pwd or new_pwd != confirm_pwd:
                    self.ui.print_error("Passwords do not match or are empty.")
                elif len(new_pwd) < 6:
                    self.ui.print_error("Password must be at least 6 characters.")
                elif self.auth.change_password(new_pwd):
                    self.ui.print_success("Password changed successfully.")
                else:
                    self.ui.print_error("Failed to change password.")
            else:
                self.ui.print_error("Invalid option.")
            self.ui.pause()


if __name__ == "__main__":
    try:
        app = BarangayApp()
        app.run()
    except KeyboardInterrupt:
        print("\n\n  Terminal interrupted. Goodbye!")
    except Exception as e:
        print(f"\n  Fatal error: {e}")