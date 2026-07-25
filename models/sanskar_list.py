from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from config import SCHEMA


@dataclass
class SanskarRecord:
    """Represents a Sanskar record mapped to SCHEMA.SANSKAR."""

    sanskar_name: str
    timestamp: str
    occasion: str
    requester_name: str
    requester_contact: str
    requester_type: str = "Student"
    no_of_people: str = ""
    status: str = "Pending"
    assigned_volunteer: str = ""
    notes: str = ""
    row_index: Optional[int] = None

    @property
    def status_clean(self) -> str:
        return self.status.strip().title()

    @property
    def is_pending(self) -> bool:
        return self.status_clean == "Pending"

    @property
    def is_approved(self) -> bool:
        return self.status_clean == "Approved"

    @property
    def is_fulfilled(self) -> bool:
        return self.status_clean == "Fulfilled"

    @classmethod
    def from_row(
        cls, row: Dict[str, Any], row_idx: Optional[int] = None
    ) -> "SanskarRecord":
        """Constructs a SanskarRecord safely from a gspread dict record."""
        S = SCHEMA.SANSKAR

        return cls(
            sanskar_name=str(row.get(S.SANSKAR_NAME, "")),
            timestamp=str(row.get(S.SANSKAR_TIMESTAMP, "")),
            occasion=str(
                row.get(S.SANSKAR_OCCASION) or row.get("Occassion", "")
            ),
            requester_name=str(row.get(S.SANSKAR_REQUESTER_NAME, "")),
            requester_contact=str(row.get(S.SANSKAR_REQUESTER_CONTACT, "")),
            requester_type=str(row.get(S.SANSKAR_REQUESTER_TYPE, "Student")),
            no_of_people=str(row.get(S.SANSKAR_NO_OF_PEOPLE, "")),
            status=str(row.get(S.SANSKAR_STATUS, "Pending")),
            assigned_volunteer=str(
                row.get(S.SANSKAR_ASSIGNED_VOLUNTEER, "")
            ),
            notes=str(row.get(S.SANSKAR_NOTES, "")),
            row_index=row_idx,
        )

    def to_row(self) -> List[Any]:
        """Returns values in the EXACT order of SCHEMA.SANSKAR.headers."""
        return [
            self.sanskar_name,
            self.timestamp,
            self.occasion,
            self.requester_name,
            self.requester_contact,
            self.requester_type,
            self.no_of_people,
            self.status,
            self.assigned_volunteer,
            self.notes,
        ]
