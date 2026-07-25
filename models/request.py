from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from config import SCHEMA

@dataclass
class BookRequest:
    request_id: str
    timestamp: str
    catalog_id: str
    book_title: str
    class_needed: str = ""
    qty_requested: int = 1
    requester_name: str = ""
    requester_contact: str = ""
    requester_type: str = "Student"
    school_name: str = ""
    status: str = "Pending"
    assigned_volunteer: str = ""
    qty_fulfilled: int = 0
    notes: str = ""
    row_index: Optional[int] = None

    @property
    def status_clean(self) -> str:
        return self.status.strip().title()

    @classmethod
    def from_row(cls, row: Dict[str, Any], row_idx: Optional[int] = None) -> "BookRequest":
        s = SCHEMA.REQUESTS
        parse_int = lambda key, default: int(row.get(key) or default) if str(row.get(key, "")).isdigit() else default
        
        return cls(
            request_id=str(row.get(s.REQ_ID, "")),
            timestamp=str(row.get(s.REQ_TIMESTAMP, "")),
            catalog_id=str(row.get(s.REQ_CATALOG_ID) or row.get("Book_ID", "")),
            book_title=str(row.get(s.REQ_TITLE, "")),
            class_needed=str(row.get(s.REQ_CLASS_NEEDED, "")),
            qty_requested=parse_int(s.REQ_QTY_REQUESTED, 1),
            requester_name=str(row.get(s.REQ_REQUESTER_NAME, "")),
            requester_contact=str(row.get(s.REQ_REQUESTER_CONTACT, "")),
            requester_type=str(row.get(s.REQ_REQUESTER_TYPE, "Student")),
            school_name=str(row.get(s.REQ_SCHOOL_NAME, "")),
            status=str(row.get(s.REQ_STATUS, "Pending")),
            assigned_volunteer=str(row.get(s.REQ_ASSIGNED_VOLUNTEER, "")),
            qty_fulfilled=parse_int(s.REQ_QTY_FULFILLED, 0),
            notes=str(row.get(s.REQ_NOTES, "")),
            row_index=row_idx,
        )

    def to_row(self) -> List[Any]:
        return [
            self.request_id, self.timestamp, self.catalog_id, self.book_title,
            self.class_needed, self.qty_requested, self.requester_name,
            self.requester_contact, self.requester_type, self.school_name,
            self.status, self.assigned_volunteer, self.qty_fulfilled, self.notes
        ]
