from datetime import datetime, timedelta
import re

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "jun": 6, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12
}

def extract_date_time(message: str):
    msg = message.lower()
    now = datetime.now()

    date = None
    start_time = None
    end_time = None

    # -------------------------
    # DATE PARSING
    # -------------------------

    if "tomorrow" in msg:
        date = (now + timedelta(days=1)).strftime("%Y-%m-%d")

    elif "today" in msg:
        date = now.strftime("%Y-%m-%d")

    else:
        # matches: "4th january 2026", "4 january", "4 jan 2026"
        date_match = re.search(
            r"(\d{1,2})(st|nd|rd|th)?\s+([a-z]+)\s*(\d{4})?",
            msg
        )
        if date_match:
            day = int(date_match.group(1))
            month_name = date_match.group(3)
            year = int(date_match.group(4)) if date_match.group(4) else now.year

            month = MONTHS.get(month_name)
            if month:
                date = f"{year:04d}-{month:02d}-{day:02d}"

    # -------------------------
    # TIME RANGE (HH:MM am/pm to HH:MM am/pm)
    # -------------------------

    range_match = re.search(
        r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)\s*to\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)",
        msg
    )

    if range_match:
        sh, sm, sap = range_match.group(1), range_match.group(2), range_match.group(3)
        eh, em, eap = range_match.group(4), range_match.group(5), range_match.group(6)

        start_hour = int(sh)
        start_min = int(sm) if sm else 0
        end_hour = int(eh)
        end_min = int(em) if em else 0

        if sap == "pm" and start_hour != 12:
            start_hour += 12
        if sap == "am" and start_hour == 12:
            start_hour = 0

        if eap == "pm" and end_hour != 12:
            end_hour += 12
        if eap == "am" and end_hour == 12:
            end_hour = 0

        start_time = f"{start_hour:02d}:{start_min:02d}"
        end_time = f"{end_hour:02d}:{end_min:02d}"

        return date, start_time, end_time

    # -------------------------
    # SINGLE TIME (HH:MM am/pm)
    # -------------------------

    single_match = re.search(
        r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)",
        msg
    )

    if single_match:
        hour = int(single_match.group(1))
        minute = int(single_match.group(2)) if single_match.group(2) else 0
        period = single_match.group(3)

        if period == "pm" and hour != 12:
            hour += 12
        if period == "am" and hour == 12:
            hour = 0

        start_time = f"{hour:02d}:{minute:02d}"

    return date, start_time, end_time
