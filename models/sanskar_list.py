"""
SanskarRecord Data Model
Supports smooth schema migration with fallbacks for legacy rows.
"""

from dataclasses import dataclass
from config import SCHEMA


@dataclass
class SanskarRecord:
    req_id: str
    sanskar_name: str
    sanskar_date: str
    created_timestamp: str
    requester_name: str
    relation_type: str
    guardian_name: str
    requester_contact: str
    requester_type: str
    address: str
    pin_code: str
    no_of_people: str
    status: str
    assigned_volunteer: str
    notes: str

    @classmethod
    def from_row(cls, row: dict):
        """Constructs SanskarRecord with fallbacks for legacy sheet schemas."""
        return cls(
            req_id=row.get(SCHEMA.SANSKAR.REQ_ID, row.get("Req_ID", "SNKQR_0000_LEGACY")),
            sanskar_name=row.get(
                SCHEMA.SANSKAR.SANSKAR_NAME, row.get("Occasion", "")
            ),
            sanskar_date=row.get(SCHEMA.SANSKAR.SANSKAR_DATE, ""),
            created_timestamp=row.get(
                SCHEMA.SANSKAR.CREATED_TIMESTAMP, row.get("Timestamp", "")
            ),
            requester_name=row.get(SCHEMA.SANSKAR.REQUESTER_NAME, ""),
            relation_type=row.get(SCHEMA.SANSKAR.RELATION_TYPE, "S/O"),
            guardian_name=row.get(SCHEMA.SANSKAR.GUARDIAN_NAME, ""),
            requester_contact=row.get(SCHEMA.SANSKAR.REQUESTER_CONTACT, ""),
            requester_type=row.get(SCHEMA.SANSKAR.REQUESTER_TYPE, "Student"),
            address=row.get(SCHEMA.SANSKAR.ADDRESS, ""),
            pin_code=row.get(SCHEMA.SANSKAR.PIN_CODE, ""),
            no_of_people=str(row.get(SCHEMA.SANSKAR.NO_OF_PEOPLE, "10")),
            status=row.get(SCHEMA.SANSKAR.SANSKAR_STATUS, "Pending"),
            assigned_volunteer=row.get(SCHEMA.SANSKAR.ASSIGNED_VOLUNTEER, ""),
            notes=row.get(SCHEMA.SANSKAR.NOTES, ""),
        )

    def to_row(self) -> list:
        """Exports data ordered according to the latest SanskarListSchema."""
        return [
            self.req_id,
            self.sanskar_name,
            self.sanskar_date,
            self.created_timestamp,
            self.requester_name,
            self.relation_type,
            self.guardian_name,
            self.requester_contact,
            self.requester_type,
            self.address,
            self.pin_code,
            self.no_of_people,
            self.status,
            self.assigned_volunteer,
            self.notes,
        ]

    @property
    def is_pending(self) -> bool:
        return str(self.status).lower() == "pending"

    @property
    def is_fulfilled(self) -> bool:
        return str(self.status).lower() == "fulfilled"
