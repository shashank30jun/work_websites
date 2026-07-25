"""
Stock Ledger Data Model
One row per physical book copy - tracks individual copy journey
"""

from dataclasses import dataclass


@dataclass
class StockLedgerItem:
    """Represents one physical copy of a book."""

    copy_id: str         # e.g., CAT001-01, CAT001-02
    catalog_id: str      # Links to Master_Catalog
    title: str
    target_class: str
    status: str = "Available"  # Available / In_Transit / Distributed
    current_holder: str = "Stock"  # "Stock" or volunteer/teacher name
    holder_type: str = "Stock"     # Stock / Volunteer / Teacher / Student
    assigned_date: str = ""
    distributed_date: str = ""
    recipient_name: str = ""
    recipient_school: str = ""
    recipient_class: str = ""
    notes: str = ""

    @property
    def is_available(self) -> bool:
        return self.status == "Available"

    @property
    def is_with_volunteer(self) -> bool:
        return self.status == "In_Transit" and self.holder_type in ["Volunteer", "Teacher"]

    @property
    def is_distributed(self) -> bool:
        return self.status == "Distributed"

    @classmethod
    def from_row(cls, row: dict) -> "StockLedgerItem":
        return cls(
            copy_id=str(row.get("Copy_ID", "")),
            catalog_id=str(row.get("Catalog_ID", "")),
            title=str(row.get("Title", "")),
            target_class=str(row.get("Class", "")),
            status=str(row.get("Status", "Available")),
            current_holder=str(row.get("Current_Holder", "Stock")),
            holder_type=str(row.get("Holder_Type", "Stock")),
            assigned_date=str(row.get("Assigned_Date", "")),
            distributed_date=str(row.get("Distributed_Date", "")),
            recipient_name=str(row.get("Recipient_Name", "")),
            recipient_school=str(row.get("Recipient_School", "")),
            recipient_class=str(row.get("Recipient_Class", "")),
            notes=str(row.get("Notes", "")),
        )

    def to_row(self) -> list:
        return [
            self.copy_id, self.catalog_id, self.title, self.target_class,
            self.status, self.current_holder, self.holder_type,
            self.assigned_date, self.distributed_date,
            self.recipient_name, self.recipient_school, self.recipient_class, self.notes
        ]

    def assign_to_volunteer(self, volunteer_name: str, date: str):
        """Hand over to volunteer/teacher for distribution."""
        self.status = "In_Transit"
        self.current_holder = volunteer_name
        self.holder_type = "Volunteer"
        self.assigned_date = date

    def distribute_to_student(self, student_name: str, school: str, student_class: str, date: str):
        """Final distribution to student."""
        self.status = "Distributed"
        self.current_holder = student_name
        self.holder_type = "Student"
        self.recipient_name = student_name
        self.recipient_school = school
        self.recipient_class = student_class
        self.distributed_date = date

    def return_to_stock(self):
        """Return to inventory."""
        self.status = "Available"
        self.current_holder = "Stock"
        self.holder_type = "Stock"
        self.assigned_date = ""
        self.distributed_date = ""
        self.recipient_name = ""
        self.recipient_school = ""
        self.recipient_class = ""
