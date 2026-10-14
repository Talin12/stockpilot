"""Business metrics exposed on /metrics alongside the HTTP metrics from the instrumentator."""

from prometheus_client import Counter

STOCK_MOVEMENTS = Counter(
    "stockpilot_stock_movements_total",
    "Number of stock movements recorded",
    ["movement_type"],
)
UNITS_MOVED = Counter(
    "stockpilot_units_moved_total",
    "Absolute number of units moved",
    ["movement_type"],
)
PRODUCTS_CREATED = Counter(
    "stockpilot_products_created_total",
    "Number of products created",
)
REJECTED_SHIPMENTS = Counter(
    "stockpilot_rejected_shipments_total",
    "Shipments rejected because on-hand stock was insufficient",
)
