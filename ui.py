"""ui.py - all terminal output (themes, banners, menus, tables) using rich."""
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box


class TerminalUI:
    THEMES = {
        "retro_green": {"name": "Retro Phosphor Green", "primary": "bold green", "border": "green",
                        "warning": "yellow", "error": "bold red", "success": "bold bright_green",
                        "header": "bold black on green"},
        "amber_crt":   {"name": "Classic Amber CRT", "primary": "bold yellow", "border": "dark_orange",
                        "warning": "bright_red", "error": "bold red", "success": "bold yellow",
                        "header": "bold black on dark_orange"},
        "cyber_blue":  {"name": "IBM Mainframe Blue", "primary": "bold bright_cyan", "border": "blue",
                        "warning": "yellow", "error": "bold red", "success": "bold bright_cyan",
                        "header": "bold white on blue"},
    }

    def __init__(self):
        self.console = Console()
        self.theme = self.THEMES["retro_green"]

    def set_theme(self, key):
        self.theme = self.THEMES.get(key, self.THEMES["retro_green"])

    # NOTE: Text(...) is used everywhere so characters like [ ] in user data are never read as rich markup.
    def print_banner(self, user=None):
        self.console.clear()
        title = Text("BARANGAY CERTIFICATE MANAGEMENT SYSTEM", style=self.theme["primary"], justify="center")
        if user:
            title.append(f"\nLogged in: {user['username']} [{user['role']}]", style=self.theme["warning"])
        self.console.print(Panel(title, border_style=self.theme["border"], box=box.DOUBLE))

    def print_menu(self, title, options):
        grid = Table.grid(padding=(0, 2))
        for key, label in options.items():
            grid.add_row(Text(f"[{key}]", style=self.theme["primary"]), Text(label))
        self.console.print(Panel(grid, title=Text(title, style=self.theme["primary"]),
                                 border_style=self.theme["border"], box=box.ROUNDED))

    def prompt(self, label):
        return self.console.input(Text(f"  {label}: ", style=self.theme["primary"])).strip()

    def display_table(self, title, columns, rows):
        table = Table(title=Text(title, style=self.theme["primary"]), box=box.SIMPLE_HEAVY,
                      border_style=self.theme["border"], header_style=self.theme["header"])
        for col in columns:
            table.add_column(col)
        for row in rows:
            table.add_row(*[Text(str(v) if v is not None else "") for v in row])
        self.console.print(table)
        if not rows:
            self.print_warning("No records found.")

    def print_success(self, msg):
        self.console.print(Text(f"  [OK] {msg}", style=self.theme["success"]))

    def print_error(self, msg):
        self.console.print(Text(f"  [ERROR] {msg}", style=self.theme["error"]))

    def print_warning(self, msg):
        self.console.print(Text(f"  [!] {msg}", style=self.theme["warning"]))

    def loading(self, msg):
        with self.console.status(Text(msg, style=self.theme["primary"]), spinner="dots"):
            time.sleep(0.8)

    def pause(self):
        self.console.input(Text("\n  Press Enter to continue...", style=self.theme["warning"]))
