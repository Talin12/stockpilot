from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from . import metrics
from .models import Product, StockMovement


def record_movement(
    db: Session, product: Product, movement_type: str, quantity: int, note: str = ""
) -> StockMovement:
    """Apply a stock change and append it to the ledger. Caller commits."""
    change = -quantity if movement_type == "SHIPPED" else quantity
    new_balance = product.quantity + change
    if new_balance < 0:
        metrics.REJECTED_SHIPMENTS.inc()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Insufficient stock: {product.quantity} on hand, {abs(change)} requested",
        )

    product.quantity = new_balance
    movement = StockMovement(
        product=product,
        movement_type=movement_type,
        quantity_change=change,
        balance_after=new_balance,
        note=note,
    )
    db.add(movement)

    metrics.STOCK_MOVEMENTS.labels(movement_type).inc()
    metrics.UNITS_MOVED.labels(movement_type).inc(abs(change))
    return movement


def movement_out(movement: StockMovement) -> dict:
    return {
        "id": movement.id,
        "product_id": movement.product_id,
        "product_sku": movement.product.sku,
        "product_name": movement.product.name,
        "movement_type": movement.movement_type,
        "quantity_change": movement.quantity_change,
        "balance_after": movement.balance_after,
        "note": movement.note,
        "created_at": movement.created_at,
    }
