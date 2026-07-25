"""
Display formatting utilities
Formatting and Identifier Utilities
"""

from datetime import datetime


def generate_sequential_id(
    prefix: str, records: list, id_attribute: str = "req_id"
) -> str:
    """
    Generic sequential ID generator.
    Format: <PREFIX>_<SEQ_4DIGIT>_<DDMMYYYY>
    Example: SNKQR_0001_26072026
    """
    date_str = datetime.now().strftime("%d%m%Y")
    max_seq = 0

    if records:
        for r in records:
            req_id = r.get(id_attribute, "") if isinstance(r, dict) else getattr(r, id_attribute, "")
            if req_id and isinstance(req_id, str) and "_" in req_id:
                parts = req_id.split("_")
                if len(parts) >= 2 and parts[1].isdigit():
                    max_seq = max(max_seq, int(parts[1]))

        if max_seq == 0:
            max_seq = len(records)

    next_seq = max_seq + 1
    formatted_seq = str(next_seq).zfill(4)  # 0001, 0002, 0003...

    return f"{prefix}_{formatted_seq}_{date_str}"

def get_status_badge(status: str) -> str:
    colors = {
        "Available": ("#e8f5e9", "#2e7d32"),
        "Reserved": ("#fff3e0", "#ef6c00"),
        "Distributed": ("#e3f2fd", "#1565c0"),
        "Pending": ("#fff3e0", "#ef6c00"),
        "Approved": ("#e8f5e9", "#2e7d32"),
        "Rejected": ("#ffebee", "#c62828"),
        "Fulfilled": ("#e8f5e9", "#2e7d32"),
    }
    bg, fg = colors.get(status, ("#f5f5f5", "#616161"))
    return f'<span style="background:{bg};color:{fg};padding:4px 12px;border-radius:20px;font-size:11px;font-weight:600;">{status}</span>'


def get_class_badge(class_name: str) -> str:
    class_colors = {
        "Class 5": "#4caf50",
        "Class 6": "#2196f3", 
        "Class 7": "#ff9800",
        "Class 8": "#9c27b0",
        "Class 9": "#f44336",
        "Class 10": "#795548",
    }
    color = class_colors.get(class_name, "#616161")
    return f'<span style="background:{color}15;color:{color};padding:4px 10px;border-radius:20px;font-size:11px;font-weight:600;border:1px solid {color}30;">{class_name}</span>'


def format_currency(amount: float) -> str:
    return f"₹{amount:,.2f}"


def get_volunteer_badge(vol_type: str) -> str:
    badges = {
        "Expert Volunteer": ("#1a3a2f", "⭐ Expert"),
        "Volunteer": ("#2d5a4a", "🤝 Volunteer"),
        "Teacher": ("#c9a227", "👨‍🏫 Teacher"),
    }
    color, label = badges.get(vol_type, ("#616161", vol_type))
    return f'<span style="background:{color};color:white;padding:3px 10px;border-radius:6px;font-size:11px;font-weight:600;">{label}</span>'
