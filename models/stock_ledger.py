from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from config import CONFIG, SCHEMA


@dataclass
class StockLedgerItem:
    """Represents one physical copy of a book mapped to SCHEMA.LEDGER."""

    copy_id: str
    catalog_id: str
    title: str
    target_class: str
    status: str = CONFIG.STATUS_AVAILABLE
    current_holder: str = "Stock"
    holder_type: str = "Stock"
    assigned_date: str = ""
    distributed_date: str = ""
    recipient_name: str = ""
    recipient_school: str = ""
    recipient_class: str = ""
    notes: str = ""
    row_index: Optional[int] = None

    @property
    def status_clean(self) -> str:
        return self.status.strip().title()

    @property
    def is_available(self) -> bool:
        return self.status_clean == CONFIG.STATUS_AVAILABLE.title()

    @property
    def is_with_volunteer(self) -> bool:
        return (
            self.status_clean == CONFIG.STATUS_IN_TRANSIT.title()
            and self.holder_type in ["Volunteer", "Teacher"]
        )

    @property
    def is_distributed(self) -> bool:
        return self.status_clean == CONFIG.STATUS_DISTRIBUTED.title()

    @classmethod
    def from_row(
        cls, row: Dict[str, Any], row_idx: Optional[int] = None
    ) -> "StockLedgerItem":
        """Constructs a StockLedgerItem safely from a gspread dict record."""
        S = SCHEMA.LEDGER

        return cls(
            copy_id=str(row.get(S.LEDGER_ID, "")),
            catalog_id=str(row.get(S.LEDGER_CATALOG_ID, "")),
            title=str(row.get(S.LEDGER_TITLE, "")),
            target_class=str(row.get(S.LEDGER_CLASS, "")),
            status=str(row.get(S.LEDGER_STATUS, CONFIG.STATUS_AVAILABLE)),
            current_holder=str(row.get(S.LEDGER_CURRENT_HOLDER, "Stock")),
            holder_type=str(row.get(S.LEDGER_HOLDER_TYPE, "Stock")),
            assigned_date=str(row.get(S.LEDGER_ASSIGNED_DATE, "")),
            distributed_date=str(row.get(S.LEDGER_DISTRIBUTED_DATE, "")),
            recipient_name=str(row.get(S.LEDGER_RECIPIENT_NAME, "")),
            recipient_school=str(row.get(S.LEDGER_RECIPIENT_SCHOOL, "")),
            recipient_class=str(row.get(S.LEDGER_RECIPIENT_CLASS, "")),
            notes=str(row.get(S.LEDGER_NOTES, "")),
            row_index=row_idx,
        )

    def to_row(self) -> List[Any]:
        """Returns values in the EXACT order of SCHEMA.LEDGER.headers."""
        return [
            self.copy_id,
            self.catalog_id,
            self.title,
            self.target_class,
            self.status,
            self.current_holder,
            self.holder_type,
            self.assigned_date,
            self.distributed_date,
            self.recipient_name,
            self.recipient_school,
            self.recipient_class,
            self.notes,
        ]

    # --- STATE TRANSITION METHODS ---

    def assign_to_volunteer(self, volunteer_name: str, date: str, holder_type: str = "Volunteer"):
        """Hand over copy to volunteer/teacher for distribution."""
        self.status = CONFIG.STATUS_IN_TRANSIT
        self.current_holder = volunteer_name
        self.holder_type = holder_type
        self.assigned_date = date

    def distribute_to_student(
        self, student_name: str, school: str, student_class: str, date: str
    ):
        """Final distribution to student."""
        self.status = CONFIG.STATUS_DISTRIBUTED
        self.current_holder = student_name
        self.holder_type = "Student"
        self.recipient_name = student_name
        self.recipient_school = school
        self.recipient_class = student_class
        self.distributed_date = date

    def return_to_stock(self):
        """Return copy to central stock inventory."""
        self.status = CONFIG.STATUS_AVAILABLE
        self.current_holder = "Stock"
        self.holder_type = "Stock"
        self.assigned_date = ""
        self.distributed_date = ""
        self.recipient_name = ""
        self.recipient_school = ""
        self.recipient_class = ""
