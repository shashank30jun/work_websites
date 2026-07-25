"""
BSGP Book Redistribution Platform - Configuration
Updated: Added Master Catalog + Stock Ledger architecture
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class AppConfig:
    """Application-wide configuration constants."""

    APP_TITLE: str = "BSGP Book Redistribution Platform"
    APP_SUBTITLE: str = "Dev Sanskriti Vishwavidyalaya — Bharatiya Sanskriti Gyaan Pariksha"
    APP_ICON: str = "📚"

    SHEET_NAME: str = "BSGP_Book_Inventory"

    # NEW: Master Catalog - unique book titles with quantities
    WORKSHEET_MASTER_CATALOG: str = "Master_Catalog"
    # NEW: Stock Ledger - individual copy tracking (barcode/serial level)
    WORKSHEET_STOCK_LEDGER: str = "Stock_Ledger"
    # Requests from students/schools
    WORKSHEET_REQUESTS: str = "Requests"
    # Distribution log - when books actually go out
    WORKSHEET_DISTRIBUTION: str = "Distribution"
    # Volunteers/Teachers master list
    WORKSHEET_VOLUNTEERS: str = "Volunteers"

    MAX_API_CALLS_PER_MINUTE: int = 60
    CACHE_TTL_SECONDS: int = 30
    RATE_LIMIT_BACKOFF_SECONDS: float = 2.0

    STATUS_AVAILABLE: str = "Available"
    STATUS_RESERVED: str = "Reserved"
    STATUS_DISTRIBUTED: str = "Distributed"
    STATUS_IN_TRANSIT: str = "In_Transit"  # NEW: with volunteer/teacher
    STATUS_ALL: List[str] = None

    CLASSES: List[str] = None
    VOLUNTEER_TYPES: List[str] = None
    CURRENCY: str = "₹"

    def __post_init__(self):
        object.__setattr__(self, 'STATUS_ALL', [
            self.STATUS_AVAILABLE,
            self.STATUS_RESERVED,
            self.STATUS_IN_TRANSIT,
            self.STATUS_DISTRIBUTED
        ])
        object.__setattr__(self, 'CLASSES', [
            "Class 5", "Class 6", "Class 7", 
            "Class 8", "Class 9", "Class 10"
        ])
        object.__setattr__(self, 'VOLUNTEER_TYPES', [
            "Expert Volunteer",
            "Volunteer", 
            "Teacher"
        ])


@dataclass(frozen=True)
class ColumnSchema:
    """Google Sheets column definitions."""

    # === MASTER CATALOG: One row per unique book title ===
    # This is your "product master" - title, class, genre, cost, total qty
    CAT_ID: str = "Catalog_ID"           # e.g., CAT001
    CAT_TITLE: str = "Title"
    CAT_AUTHOR: str = "Author"
    CAT_GENRE: str = "Genre"
    CAT_CLASS: str = "Class"
    CAT_LANGUAGE: str = "Language"
    CAT_COST_PER_UNIT: str = "Cost_Per_Unit_INR"
    CAT_TOTAL_QTY: str = "Total_Qty"     # Total copies received
    CAT_AVAILABLE_QTY: str = "Available_Qty"  # Currently in stock
    CAT_DISTRIBUTED_QTY: str = "Distributed_Qty"  # Given out
    CAT_RESERVED_QTY: str = "Reserved_Qty"  # With volunteers/teachers
    CAT_DONOR_NAME: str = "Donor_Name"
    CAT_DONOR_TYPE: str = "Donor_Type"
    CAT_NOTES: str = "Notes"

    # === STOCK LEDGER: One row per physical copy ===
    # This tracks each individual book copy
    LEDGER_ID: str = "Copy_ID"           # e.g., BSGP001-01, BSGP001-02
    LEDGER_CATALOG_ID: str = "Catalog_ID"  # Links to Master_Catalog
    LEDGER_TITLE: str = "Title"
    LEDGER_CLASS: str = "Class"
    LEDGER_STATUS: str = "Status"         # Available / In_Transit / Distributed
    LEDGER_CURRENT_HOLDER: str = "Current_Holder"  # Volunteer/Teacher name or "Stock"
    LEDGER_HOLDER_TYPE: str = "Holder_Type"  # Stock / Volunteer / Teacher / Student
    LEDGER_ASSIGNED_DATE: str = "Assigned_Date"
    LEDGER_DISTRIBUTED_DATE: str = "Distributed_Date"
    LEDGER_RECIPIENT_NAME: str = "Recipient_Name"  # Student who received it
    LEDGER_RECIPIENT_SCHOOL: str = "Recipient_School"
    LEDGER_RECIPIENT_CLASS: str = "Recipient_Class"
    LEDGER_NOTES: str = "Notes"

    # === REQUESTS: Students/schools asking for books ===
    REQ_ID: str = "Request_ID"
    REQ_TIMESTAMP: str = "Timestamp"
    REQ_CATALOG_ID: str = "Catalog_ID"
    REQ_TITLE: str = "Book_Title"
    REQ_CLASS_NEEDED: str = "Class_Needed"
    REQ_QTY_REQUESTED: str = "Qty_Requested"
    REQ_REQUESTER_NAME: str = "Requester_Name"
    REQ_REQUESTER_CONTACT: str = "Requester_Contact"
    REQ_REQUESTER_TYPE: str = "Requester_Type"  # Student / Teacher / School / Volunteer
    REQ_SCHOOL_NAME: str = "School_Name"
    REQ_STATUS: str = "Request_Status"   # Pending / Approved / Fulfilled / Rejected
    REQ_ASSIGNED_VOLUNTEER: str = "Assigned_Volunteer"
    REQ_QTY_FULFILLED: str = "Qty_Fulfilled"
    REQ_NOTES: str = "Notes"

    # === DISTRIBUTION LOG: Record of every handover ===
    DIST_ID: str = "Distribution_ID"
    DIST_TIMESTAMP: str = "Timestamp"
    DIST_CATALOG_ID: str = "Catalog_ID"
    DIST_COPY_IDS: str = "Copy_IDs"      # Comma-separated ledger IDs
    DIST_FROM: str = "From"              # Stock / Volunteer name
    DIST_TO: str = "To"                 # Volunteer / Teacher / Student name
    DIST_TO_TYPE: str = "To_Type"        # Volunteer / Teacher / Student
    DIST_SCHOOL: str = "School"
    DIST_QTY: str = "Qty"
    DIST_CLASS: str = "Class"
    DIST_VOLUNTEER: str = "Volunteer_Involved"
    DIST_NOTES: str = "Notes"

    # === VOLUNTEERS ===
    VOL_ID: str = "Volunteer_ID"
    VOL_NAME: str = "Name"
    VOL_TYPE: str = "Type"
    VOL_CONTACT: str = "Contact"
    VOL_EMAIL: str = "Email"
    VOL_CITY: str = "City"
    VOL_ACTIVE: str = "Is_Active"
    VOL_BOOKS_HOLDING: str = "Books_Holding"  # Current count
    VOL_BOOKS_DISTRIBUTED: str = "Books_Distributed_Lifetime"


# === HEADERS FOR EACH WORKSHEET ===

MASTER_CATALOG_HEADERS = [
    "Catalog_ID", "Title", "Author", "Genre", "Class", "Language",
    "Cost_Per_Unit_INR", "Total_Qty", "Available_Qty", "Distributed_Qty",
    "Reserved_Qty", "Donor_Name", "Donor_Type", "Notes"
]

STOCK_LEDGER_HEADERS = [
    "Copy_ID", "Catalog_ID", "Title", "Class", "Status",
    "Current_Holder", "Holder_Type", "Assigned_Date", "Distributed_Date",
    "Recipient_Name", "Recipient_School", "Recipient_Class", "Notes"
]

REQUESTS_HEADERS = [
    "Request_ID", "Timestamp", "Catalog_ID", "Book_Title", "Class_Needed",
    "Qty_Requested", "Requester_Name", "Requester_Contact", "Requester_Type",
    "School_Name", "Request_Status", "Assigned_Volunteer", "Qty_Fulfilled", "Notes"
]

DISTRIBUTION_HEADERS = [
    "Distribution_ID", "Timestamp", "Catalog_ID", "Copy_IDs",
    "From", "To", "To_Type", "School", "Qty", "Class",
    "Volunteer_Involved", "Notes"
]

VOLUNTEERS_HEADERS = [
    "Volunteer_ID", "Name", "Type", "Contact", "Email", "City",
    "Is_Active", "Books_Holding", "Books_Distributed_Lifetime"
]

CONFIG = AppConfig()
SCHEMA = ColumnSchema()
