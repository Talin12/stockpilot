"""Demo catalogue so a fresh environment has something to show."""

import logging

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import Product
from .services import record_movement

logger = logging.getLogger("stockpilot.seed")

DEMO_PRODUCTS = [
    # sku, name, category, qty, reorder, price, supplier, location
    ("ELEC-1001", "Wireless Barcode Scanner", "Electronics", 42, 10, 3499.00, "ScanTech India", "A1-03"),
    ("ELEC-1002", "Thermal Label Printer", "Electronics", 6, 8, 12999.00, "PrintWorks", "A1-07"),
    ("ELEC-1003", "USB-C Charging Hub", "Electronics", 0, 15, 1899.00, "VoltEdge", "A2-01"),
    ("PACK-2001", "Corrugated Box 12x10x8", "Packaging", 850, 200, 28.50, "BoxCraft", "C3-11"),
    ("PACK-2002", "Bubble Wrap Roll 50m", "Packaging", 34, 40, 640.00, "BoxCraft", "C3-14"),
    ("PACK-2003", "Packing Tape 48mm", "Packaging", 310, 100, 55.00, "AdhesivePro", "C3-02"),
    ("OFFC-3001", "A4 Copier Paper (500)", "Office Supplies", 120, 50, 289.00, "PaperMill Co", "B2-05"),
    ("OFFC-3002", "Gel Pen Blue (Box of 10)", "Office Supplies", 18, 25, 120.00, "Inkwell", "B2-09"),
    ("SAFE-4001", "Safety Gloves (Pair)", "Safety", 260, 100, 95.00, "SafeHands", "D1-01"),
    ("SAFE-4002", "Hi-Vis Vest", "Safety", 9, 20, 349.00, "SafeHands", "D1-04"),
    ("FURN-5001", "Steel Shelving Unit", "Warehouse Equipment", 14, 4, 8750.00, "RackMasters", "E1-01"),
    ("FURN-5002", "Hand Pallet Truck", "Warehouse Equipment", 3, 2, 21500.00, "LiftLine", "E1-02"),
]


def seed_demo_data(db: Session) -> int:
    if db.scalar(select(func.count(Product.id))):
        return 0
    for sku, name, category, qty, reorder, price, supplier, location in DEMO_PRODUCTS:
        product = Product(
            sku=sku,
            name=name,
            category=category,
            quantity=0,
            reorder_level=reorder,
            unit_price=price,
            supplier=supplier,
            location=location,
        )
        db.add(product)
        if qty:
            record_movement(db, product, "RECEIVED", qty, "Opening stock")
    try:
        db.commit()
    except IntegrityError:
        # Another replica seeded concurrently; SKU uniqueness keeps this idempotent.
        db.rollback()
        return 0
    logger.info("seeded %d demo products", len(DEMO_PRODUCTS))
    return len(DEMO_PRODUCTS)
