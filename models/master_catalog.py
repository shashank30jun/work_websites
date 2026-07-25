from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from config import CONFIG, SCHEMA


@dataclass
class MasterCatalogItem:
    """Represents a unique book title in the master catalog mapped to SCHEMA.CATALOG."""

    catalog_id: str
    title: str
    author: str
    genre: str
    target_class: str
    language: str = "Hindi"
    cost_per_unit: float = 0.0
    total_qty: int = 0
    available_qty: int = 0
    distributed_qty: int = 0
    reserved_qty: int = 0
    donor_name: str = ""
    donor_type: str = "Individual"
    notes: str = ""
    row_index: Optional[int] = None

    # --- COMPUTED PROPERTIES ---

    @property
    def is_in_stock(self) -> bool:
        return self.available_qty > 0

    @property
    def formatted_cost(self) -> str:
        return f"{CONFIG.CURRENCY}{self.cost_per_unit:,.2f}" if self.cost_per_unit > 0 else "Free"

    @property
    def display_title(self) -> str:
        return f"{self.title} ({self.target_class})"

    @property
    def stock_status(self) -> str:
        if self.available_qty == 0:
            return "Out of Stock"
        return "Low Stock" if self.available_qty <= 5 else "In Stock"

    # --- CONSTRUCTOR & SERIALIZERS ---

    @classmethod
    def from_row(cls, row: Dict[str, Any], row_idx: Optional[int] = None) -> "MasterCatalogItem":
        """Constructs a MasterCatalogItem safely from a gspread dict record."""
        S = SCHEMA.CATALOG
        parse_num = lambda key, target_type, default: target_type(row.get(key) or default) if str(row.get(key, "")).replace(".", "", 1).isdigit() else default

        return cls(
            catalog_id=str(row.get(S.CAT_ID, "")),
            title=str(row.get(S.CAT_TITLE, "")),
            author=str(row.get(S.CAT_AUTHOR, "")),
            genre=str(row.get(S.CAT_GENRE, "")),
            target_class=str(row.get(S.CAT_CLASS, "")),
            language=str(row.get(S.CAT_LANGUAGE, "Hindi")),
            cost_per_unit=parse_num(S.CAT_COST_PER_UNIT, float, 0.0),
            total_qty=parse_num(S.CAT_TOTAL_QTY, int, 0),
            available_qty=parse_num(S.CAT_AVAILABLE_QTY, int, 0),
            distributed_qty=parse_num(S.CAT_DISTRIBUTED_QTY, int, 0),
            reserved_qty=parse_num(S.CAT_RESERVED_QTY, int, 0),
            donor_name=str(row.get(S.CAT_DONOR_NAME, "")),
            donor_type=str(row.get(S.CAT_DONOR_TYPE, "Individual")),
            notes=str(row.get(S.CAT_NOTES, "")),
            row_index=row_idx,
        )

    def to_row(self) -> List[Any]:
        """Returns values in the EXACT order of SCHEMA.CATALOG.headers."""
        return [
            self.catalog_id, self.title, self.author, self.genre,
            self.target_class, self.language, self.cost_per_unit,
            self.total_qty, self.available_qty, self.distributed_qty,
            self.reserved_qty, self.donor_name, self.donor_type, self.notes
        ]

    # --- INVENTORY STATE LOGIC ---

    def add_stock(self, qty: int):
        if qty > 0:
            self.total_qty += qty
            self.available_qty += qty

    def reserve(self, qty: int) -> bool:
        if qty > 0 and self.available_qty >= qty:
            self.available_qty -= qty
            self.reserved_qty += qty
            return True
        return False

    def distribute(self, qty: int) -> bool:
        if qty > 0 and self.reserved_qty >= qty:
            self.reserved_qty -= qty
            self.distributed_qty += qty
            return True
        return False

    def return_to_stock(self, qty: int):
        if qty > 0:
            actual = min(qty, self.reserved_qty)
            self.reserved_qty -= actual
            self.available_qty += actual
