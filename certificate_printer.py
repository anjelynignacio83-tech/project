""" creates a printable certificate (.txt) for a request."""
import os
import textwrap
from datetime import datetime


BARANGAY_NAME = "BARANGAY (YOUR BARANGAY)"
CITY_MUNICIPALITY = "City/Municipality of (YOUR CITY)"
PROVINCE = "Province of (YOUR PROVINCE)"
SIGNATORY_NAME = "(NAME OF PUNONG BARANGAY)"
SIGNATORY_TITLE = "Punong Barangay"


OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certificates")
WIDTH = 70


def _age(birthdate):
    try:
        born = datetime.strptime(str(birthdate), "%Y-%m-%d")
    except ValueError:
        return None
    today = datetime.now()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def _ordinal(n):
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}" + {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def generate_certificate(data, prepared_by=""):
    """Write the certificate to certificates/<control no>.txt and return the file path."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    control_no = data["control_no"] or f"REQ-{data['request_id']:04d}"
    age = _age(data["birthdate"])
    age_text = f", {age} years old," if age is not None else ","
    purpose = data["purpose"] or "whatever legal purpose it may serve"
    now = datetime.now()
    issued = f"{_ordinal(now.day)} day of {now.strftime('%B %Y')}"

    body = (f"This is to certify that {data['full_name'].upper()}{age_text} "
            f"a resident of {data['address']}, is known to this office. "
            f"This {data['cert_name']} is being issued upon the request of the "
            f"above-named person for the purpose of: {purpose}.")

    line = "=" * WIDTH
    out = [
        line,
        "Republic of the Philippines".center(WIDTH),
        PROVINCE.center(WIDTH),
        CITY_MUNICIPALITY.center(WIDTH),
        BARANGAY_NAME.center(WIDTH),
        "OFFICE OF THE PUNONG BARANGAY".center(WIDTH),
        line,
        "",
        data["cert_name"].upper().center(WIDTH),
        "",
        f"Control No.: {control_no}",
        "",
        "TO WHOM IT MAY CONCERN:",
        "",
        *textwrap.wrap(body, WIDTH, initial_indent="    ", subsequent_indent=""),
        "",
        *textwrap.wrap(f"Issued this {issued}.", WIDTH, initial_indent="    "),
        "",
        "",
        "",
        SIGNATORY_NAME.rjust(WIDTH - 5),
        SIGNATORY_TITLE.rjust(WIDTH - 5),
        "",
        f"Fee: PHP {float(data['fee']):.2f}",
        f"Prepared by: {prepared_by}" if prepared_by else "",
        line,
    ]

    path = os.path.join(OUTPUT_DIR, f"{control_no}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    return path