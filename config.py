"""
BSGP Book Redistribution Platform - Configuration
Architectural Design: Modular Worksheet Schemas + Dynamic Header Generation + Feature Toggles
"""

from dataclasses import dataclass, field, fields
from typing import List

# ==============================================================================
# 1. APPLICATION CONFIGURATION
# ==============================================================================

@dataclass(frozen=True)
class AppConfig:
    """Application-wide configuration constants."""

    APP_TITLE: str = "BSGP Book Redistribution Platform"
    APP_SUBTITLE: str = "Dev Sanskriti Vishwavidyalaya — Bharatiya Sanskriti Gyaan Pariksha"
    APP_ICON: str = "📚"

    # Google Sheets Workbook Name
    SHEET_NAME: str = "BSGP_Book_Inventory"

    # Worksheet Names
    WORKSHEET_MASTER_CATALOG: str = "Master_Catalog"
    WORKSHEET_STOCK_LEDGER: str = "Stock_Ledger"
    WORKSHEET_REQUESTS: str = "Requests"
    WORKSHEET_DISTRIBUTION: str = "Distribution"
    WORKSHEET_VOLUNTEERS: str = "Volunteers"
    WORKSHEET_SANSKAR_LIST: str = "Sanskar_List"

    # Performance & API Settings
    MAX_API_CALLS_PER_MINUTE: int = 60
    CACHE_TTL_SECONDS: int = 30
    RATE_LIMIT_BACKOFF_SECONDS: float = 2.0

    # Business Logic Constants
    STATUS_AVAILABLE: str = "Available"
    STATUS_RESERVED: str = "Reserved"
    STATUS_DISTRIBUTED: str = "Distributed"
    STATUS_IN_TRANSIT: str = "In_Transit"

    # --- FEATURE TOGGLES (Control Page Visibility in Navigation) ---
    SHOW_HOME: bool = True
    SHOW_SANSKAR: bool = True
    SHOW_CATALOG: bool = False
    SHOW_REQUEST: bool = True
    SHOW_ADMIN: bool = False
    SHOW_ABOUT: bool = True

    CURRENCY: str = "₹"

    # Native default factories eliminate __post_init__ state mutation
    STATUS_ALL: List[str] = field(
        default_factory=lambda: [
            "Available",
            "Reserved",
            "In_Transit",
            "Distributed",
        ]
    )

    CLASSES: List[str] = field(
        default_factory=lambda: [
            "Class 5",
            "Class 6",
            "Class 7",
            "Class 8",
            "Class 9",
            "Class 10",
        ]
    )

    VOLUNTEER_TYPES: List[str] = field(
        default_factory=lambda: ["Expert Volunteer", "Volunteer", "Teacher"]
    )


# ==============================================================================
# 2. MODULAR WORKSHEET SCHEMAS (ZERO DUPLICATION)
# ==============================================================================

class BaseSchema:
    """Base class providing automatic dynamic header extraction for all schemas."""
    
    @property
    def headers(self) -> List[str]:
        """Dynamically inspects dataclass fields to generate an ordered list of headers."""
        return [getattr(self, f.name) for f in fields(self)]


@dataclass(frozen=True)
class MasterCatalogSchema(BaseSchema):
    """Schema for Master_Catalog worksheet (Product Master)."""
    CAT_ID: str = "Catalog_ID"
    CAT_TITLE: str = "Title"
    CAT_AUTHOR: str = "Author"
    CAT_GENRE: str = "Genre"
    CAT_CLASS: str = "Class"
    CAT_LANGUAGE: str = "Language"
    CAT_COST_PER_UNIT: str = "Cost_Per_Unit_INR"
    CAT_TOTAL_QTY: str = "Total_Qty"
    CAT_AVAILABLE_QTY: str = "Available_Qty"
    CAT_DISTRIBUTED_QTY: str = "Distributed_Qty"
    CAT_RESERVED_QTY: str = "Reserved_Qty"
    CAT_DONOR_NAME: str = "Donor_Name"
    CAT_DONOR_TYPE: str = "Donor_Type"
    CAT_NOTES: str = "Notes"


@dataclass(frozen=True)
class StockLedgerSchema(BaseSchema):
    """Schema for Stock_Ledger worksheet (Individual Copy Tracking)."""
    LEDGER_ID: str = "Copy_ID"
    LEDGER_CATALOG_ID: str = "Catalog_ID"
    LEDGER_TITLE: str = "Title"
    LEDGER_CLASS: str = "Class"
    LEDGER_STATUS: str = "Status"
    LEDGER_CURRENT_HOLDER: str = "Current_Holder"
    LEDGER_HOLDER_TYPE: str = "Holder_Type"
    LEDGER_ASSIGNED_DATE: str = "Assigned_Date"
    LEDGER_DISTRIBUTED_DATE: str = "Distributed_Date"
    LEDGER_RECIPIENT_NAME: str = "Recipient_Name"
    LEDGER_RECIPIENT_SCHOOL: str = "Recipient_School"
    LEDGER_RECIPIENT_CLASS: str = "Recipient_Class"
    LEDGER_NOTES: str = "Notes"


@dataclass(frozen=True)
class RequestsSchema(BaseSchema):
    """Schema for Requests worksheet (Incoming Orders/Demands)."""
    REQ_ID: str = "Request_ID"
    REQ_TIMESTAMP: str = "Timestamp"
    REQ_CATALOG_ID: str = "Catalog_ID"
    REQ_TITLE: str = "Book_Title"
    REQ_CLASS_NEEDED: str = "Class_Needed"
    REQ_QTY_REQUESTED: str = "Qty_Requested"
    REQ_REQUESTER_NAME: str = "Requester_Name"
    REQ_REQUESTER_CONTACT: str = "Requester_Contact"
    REQ_REQUESTER_TYPE: str = "Requester_Type"
    REQ_SCHOOL_NAME: str = "School_Name"
    REQ_STATUS: str = "Request_Status"
    REQ_ASSIGNED_VOLUNTEER: str = "Assigned_Volunteer"
    REQ_QTY_FULFILLED: str = "Qty_Fulfilled"
    REQ_NOTES: str = "Notes"


@dataclass(frozen=True)
class DistributionSchema(BaseSchema):
    """Schema for Distribution worksheet (Handover Ledger)."""
    DIST_ID: str = "Distribution_ID"
    DIST_TIMESTAMP: str = "Timestamp"
    DIST_CATALOG_ID: str = "Catalog_ID"
    DIST_COPY_IDS: str = "Copy_IDs"
    DIST_FROM: str = "From"
    DIST_TO: str = "To"
    DIST_TO_TYPE: str = "To_Type"
    DIST_SCHOOL: str = "School"
    DIST_QTY: str = "Qty"
    DIST_CLASS: str = "Class"
    DIST_VOLUNTEER: str = "Volunteer_Involved"
    DIST_NOTES: str = "Notes"


@dataclass(frozen=True)
class VolunteersSchema(BaseSchema):
    """Schema for Volunteers worksheet (User Directory)."""
    VOL_ID: str = "Volunteer_ID"
    VOL_NAME: str = "Name"
    VOL_TYPE: str = "Type"
    VOL_CONTACT: str = "Contact"
    VOL_EMAIL: str = "Email"
    VOL_CITY: str = "City"
    VOL_ACTIVE: str = "Is_Active"
    VOL_BOOKS_HOLDING: str = "Books_Holding"
    VOL_BOOKS_DISTRIBUTED: str = "Books_Distributed_Lifetime"


@dataclass(frozen=True)
class SanskarListSchema(BaseSchema):
    """Schema for Sanskar_List worksheet (Event Tracking)."""
    SANSKAR_NAME: str = "Sanskar_Name"
    SANSKAR_TIMESTAMP: str = "Timestamp"
    SANSKAR_OCCASION: str = "Occasion"
    SANSKAR_REQUESTER_NAME: str = "Requester_Name"
    SANSKAR_REQUESTER_CONTACT: str = "Requester_Contact"
    SANSKAR_REQUESTER_TYPE: str = "Requester_Type"
    SANSKAR_NO_OF_PEOPLE: str = "No_of_People"
    SANSKAR_STATUS: str = "Request_Status"
    SANSKAR_ASSIGNED_VOLUNTEER: str = "Assigned_Volunteer"
    SANSKAR_NOTES: str = "Notes"


# ==============================================================================
# 3. UNIFIED CONTAINER & SINGLETON INSTANTIATION
# ==============================================================================

class ColumnSchema:
    """Master Column Schema Container linking all individual worksheet schemas."""
    CATALOG = MasterCatalogSchema()
    LEDGER = StockLedgerSchema()
    REQUESTS = RequestsSchema()
    DISTRIBUTION = DistributionSchema()
    VOLUNTEERS = VolunteersSchema()
    SANSKAR = SanskarListSchema()


# App Singletons to import across services
CONFIG = AppConfig()
SCHEMA = ColumnSchema()

# Convenient dynamic header exports for Sheet Initialization
MASTER_CATALOG_HEADERS = SCHEMA.CATALOG.headers
STOCK_LEDGER_HEADERS = SCHEMA.LEDGER.headers
REQUESTS_HEADERS = SCHEMA.REQUESTS.headers
DISTRIBUTION_HEADERS = SCHEMA.DISTRIBUTION.headers
VOLUNTEERS_HEADERS = SCHEMA.VOLUNTEERS.headers
SANSKAR_HEADERS = SCHEMA.SANSKAR.headers
