"""
BSGP Book Request Data Model
"""

from dataclasses import dataclass


@dataclass
class BookRequest:
    """Represents a book request."""

    request_id: str
    timestamp: str
    book_id: str
    book_title: str
    requester_name: str
    requester_contact: str
    requester_type: str = "Student"
    school_name: str = ""
    class_needed: str = ""
    quantity: int = 1
    status: str = "Pending"
    assigned_volunteer: str = ""
    delivery_date: str = ""
    notes: str = ""

    @property
    def is_pending(self) -> bool:
        return self.status == "Pending"

    @property
    def is_approved(self) -> bool:
        return self.status == "Approved"

    @property
    def is_fulfilled(self) -> bool:
        return self.status == "Fulfilled"

    @classmethod
    def from_row(cls, row: dict) -> "BookRequest":
        return cls(
            request_id=str(row.get("Request_ID", "")),
            timestamp=str(row.get("Timestamp", "")),
            book_id=str(row.get("Book_ID", "")),
            book_title=str(row.get("Book_Title", "")),
            requester_name=str(row.get("Requester_Name", "")),
            requester_contact=str(row.get("Requester_Contact", "")),
            requester_type=str(row.get("Requester_Type", "Student")),
            school_name=str(row.get("School_Name", "")),
            class_needed=str(row.get("Class_Needed", "")),
            quantity=int(row.get("Quantity", 1) or 1),
            status=str(row.get("Request_Status", "Pending")),
            assigned_volunteer=str(row.get("Assigned_Volunteer", "")),
            delivery_date=str(row.get("Delivery_Date", "")),
            notes=str(row.get("Notes", "")),
        )

    def to_row(self) -> list:
        return [
            self.request_id, self.timestamp, self.book_id, self.book_title,
            self.requester_name, self.requester_contact, self.requester_type,
            self.school_name, self.class_needed, self.quantity, self.status,
            self.assigned_volunteer, self.delivery_date, self.notes,
        ]
