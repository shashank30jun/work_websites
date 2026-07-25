"""
Master Catalog Data Model
One row per unique book title - tracks quantities at title level
"""

from dataclasses import dataclass


@dataclass
class MasterCatalogItem:
    """Represents a unique book title in the master catalog."""

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

    @property
    def is_in_stock(self) -> bool:
        return self.available_qty > 0

    @property
    def formatted_cost(self) -> str:
        return f"₹{self.cost_per_unit:,.2f}" if self.cost_per_unit > 0 else "Free"

    @property
    def display_title(self) -> str:
        return f"{self.title} ({self.target_class})"

    @property
    def stock_status(self) -> str:
        if self.available_qty == 0:
            return "Out of Stock"
        elif self.available_qty <= 5:
            return "Low Stock"
        return "In Stock"

    @classmethod
    def from_row(cls, row: dict) -> "MasterCatalogItem":
        return cls(
            catalog_id=str(row.get("Catalog_ID", "")),
            title=str(row.get("Title", "")),
            author=str(row.get("Author", "")),
            genre=str(row.get("Genre", "")),
            target_class=str(row.get("Class", "")),
            language=str(row.get("Language", "Hindi")),
            cost_per_unit=float(row.get("Cost_Per_Unit_INR", 0) or 0),
            total_qty=int(row.get("Total_Qty", 0) or 0),
            available_qty=int(row.get("Available_Qty", 0) or 0),
            distributed_qty=int(row.get("Distributed_Qty", 0) or 0),
            reserved_qty=int(row.get("Reserved_Qty", 0) or 0),
            donor_name=str(row.get("Donor_Name", "")),
            donor_type=str(row.get("Donor_Type", "Individual")),
            notes=str(row.get("Notes", "")),
        )

    def to_row(self) -> list:
        return [
            self.catalog_id, self.title, self.author, self.genre,
            self.target_class, self.language, self.cost_per_unit,
            self.total_qty, self.available_qty, self.distributed_qty,
            self.reserved_qty, self.donor_name, self.donor_type, self.notes
        ]

    def add_stock(self, qty: int):
        """Add new stock (e.g., from donation)."""
        self.total_qty += qty
        self.available_qty += qty

    def reserve(self, qty: int) -> bool:
        """Reserve stock for a request."""
        if self.available_qty >= qty:
            self.available_qty -= qty
            self.reserved_qty += qty
            return True
        return False

    def distribute(self, qty: int) -> bool:
        """Mark reserved stock as distributed."""
        if self.reserved_qty >= qty:
            self.reserved_qty -= qty
            self.distributed_qty += qty
            return True
        return False

    def return_to_stock(self, qty: int):
        """Return reserved stock to available."""
        qty = min(qty, self.reserved_qty)
        self.reserved_qty -= qty
        self.available_qty += qty
