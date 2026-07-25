"""
BSGP Book Redistribution Platform - Configuration
"""

import os
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class AppConfig:
    """Application-wide configuration constants."""

    APP_TITLE: str = "BSGP Book Redistribution Platform"
    APP_SUBTITLE: str = "Dev Sanskriti Vishwavidyalaya — Bharatiya Sanskriti Gyaan Pariksha"
    APP_ICON: str = "📚"

    SHEET_NAME: str = "BSGP_Book_Inventory"
    WORKSHEET_INVENTORY: str = "Inventory"
    WORKSHEET_REQUESTS: str = "Requests"
    WORKSHEET_VOLUNTEERS: str = "Volunteers"

    MAX_API_CALLS_PER_MINUTE: int = 60
    CACHE_TTL_SECONDS: int = 30
    RATE_LIMIT_BACKOFF_SECONDS: float = 2.0

    STATUS_AVAILABLE: str = "Available"
    STATUS_RESERVED: str = "Reserved"
    STATUS_DISTRIBUTED: str = "Distributed"
    STATUS_ALL: List[str] = None

    CLASSES: List[str] = None
    VOLUNTEER_TYPES: List[str] = None
    CURRENCY: str = "₹"

    def __post_init__(self):
        object.__setattr__(self, 'STATUS_ALL', [
            self.STATUS_AVAILABLE,
            self.STATUS_RESERVED,
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

    INV_ID: str = "Book_ID"
    INV_TIMESTAMP: str = "Timestamp"
    INV_TITLE: str = "Title"
    INV_AUTHOR: str = "Author"
    INV_GENRE: str = "Genre"
    INV_CLASS: str = "Class"
    INV_LANGUAGE: str = "Language"
    INV_COST: str = "Cost_INR"
    INV_DONOR_NAME: str = "Donor_Name"
    INV_DONOR_CONTACT: str = "Donor_Contact"
    INV_DONOR_TYPE: str = "Donor_Type"
    INV_STATUS: str = "Status"
    INV_VOLUNTEER: str = "Assigned_Volunteer"
    INV_NOTES: str = "Notes"
    INV_LOCATION: str = "Current_Location"

    REQ_ID: str = "Request_ID"
    REQ_TIMESTAMP: str = "Timestamp"
    REQ_BOOK_ID: str = "Book_ID"
    REQ_BOOK_TITLE: str = "Book_Title"
    REQ_REQUESTER_NAME: str = "Requester_Name"
    REQ_REQUESTER_CONTACT: str = "Requester_Contact"
    REQ_REQUESTER_TYPE: str = "Requester_Type"
    REQ_SCHOOL_NAME: str = "School_Name"
    REQ_CLASS_NEEDED: str = "Class_Needed"
    REQ_QUANTITY: str = "Quantity"
    REQ_STATUS: str = "Request_Status"
    REQ_VOLUNTEER: str = "Assigned_Volunteer"
    REQ_DELIVERY_DATE: str = "Delivery_Date"
    REQ_NOTES: str = "Notes"

    VOL_ID: str = "Volunteer_ID"
    VOL_NAME: str = "Name"
    VOL_TYPE: str = "Type"
    VOL_CONTACT: str = "Contact"
    VOL_EMAIL: str = "Email"
    VOL_CITY: str = "City"
    VOL_ACTIVE: str = "Is_Active"
    VOL_BOOKS_DISTRIBUTED: str = "Books_Distributed"


GOOGLE_FORM_MAPPING = {
    "entry.123456789": "Timestamp",
    "entry.987654321": "Title",
    "entry.456789123": "Author",
    "entry.789123456": "Genre",
    "entry.321654987": "Class",
    "entry.654987321": "Language",
    "entry.147258369": "Cost_INR",
    "entry.258369147": "Donor_Name",
    "entry.369147258": "Donor_Contact",
    "entry.741852963": "Donor_Type",
    "entry.852963741": "Current_Location",
    "entry.963741852": "Notes",
}

INVENTORY_HEADERS = [
    "Book_ID", "Timestamp", "Title", "Author", "Genre", "Class",
    "Language", "Cost_INR", "Donor_Name", "Donor_Contact", "Donor_Type",
    "Status", "Assigned_Volunteer", "Notes", "Current_Location",
]

REQUESTS_HEADERS = [
    "Request_ID", "Timestamp", "Book_ID", "Book_Title", "Requester_Name",
    "Requester_Contact", "Requester_Type", "School_Name", "Class_Needed",
    "Quantity", "Request_Status", "Assigned_Volunteer", "Delivery_Date", "Notes",
]

VOLUNTEERS_HEADERS = [
    "Volunteer_ID", "Name", "Type", "Contact", "Email", "City",
    "Is_Active", "Books_Distributed",
]

CONFIG = AppConfig()
SCHEMA = ColumnSchema()
