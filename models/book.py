"""
BSGP Book Data Model
"""

from dataclasses import dataclass


@dataclass
class Book:
    """Represents a book in the inventory."""

    book_id: str
    timestamp: str
    title: str
    author: str
    genre: str
    target_class: str
    # language: str = "Hindi"
    cost_inr: float = 0.0
    donor_name: str = ""
    donor_contact: str = ""
    donor_type: str = "Individual"
    status: str = "Available"
    assigned_volunteer: str = ""
    notes: str = ""
    current_location: str = ""

    @property
    def is_available(self) -> bool:
        return self.status == "Available"

    @property
    def display_title(self) -> str:
        return f"{self.title} ({self.target_class})"

    @property
    def formatted_cost(self) -> str:
        return f"₹{self.cost_inr:,.2f}" if self.cost_inr > 0 else "Free"

    @classmethod
    def from_row(cls, row: dict) -> "Book":
        return cls(
            book_id=str(row.get("Book_ID", "")),
            timestamp=str(row.get("Timestamp", "")),
            title=str(row.get("Title", "")),
            author=str(row.get("Author", "")),
            genre=str(row.get("Genre", "")),
            target_class=str(row.get("Class", "")),
            # language=str(row.get("Language", "Hindi")),
            cost_inr=float(row.get("Cost_INR", 0) or 0),
            donor_name=str(row.get("Donor_Name", "")),
            donor_contact=str(row.get("Donor_Contact", "")),
            donor_type=str(row.get("Donor_Type", "Individual")),
            status=str(row.get("Status", "Available")),
            assigned_volunteer=str(row.get("Assigned_Volunteer", "")),
            notes=str(row.get("Notes", "")),
            current_location=str(row.get("Current_Location", "")),
        )

    def to_row(self) -> list:
        return [
            self.book_id, self.timestamp, self.title, self.author,
            self.genre, self.target_class, #self.language, 
            self.cost_inr,
            self.donor_name, self.donor_contact, self.donor_type,
            self.status, self.assigned_volunteer, self.notes, self.current_location,
        ]
