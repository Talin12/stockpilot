from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, joinedload

from ..db import get_db
from ..models import Product, StockMovement
from ..schemas import CategorySummary, MovementOut, StatsOut
from ..services import movement_out

router = APIRouter(prefix="/api", tags=["inventory"])


@router.get("/movements", response_model=list[MovementOut])
def recent_movements(limit: int = Query(default=20, ge=1, le=200), db: Session = Depends(get_db)):
    movements = db.scalars(
        select(StockMovement)
        .options(joinedload(StockMovement.product))
        .order_by(StockMovement.created_at.desc(), StockMovement.id.desc())
        .limit(limit)
    ).all()
    return [movement_out(m) for m in movements]


@router.get("/stats", response_model=StatsOut)
def inventory_stats(db: Session = Depends(get_db)):
    value = Product.quantity * Product.unit_price
    totals = db.execute(
        select(
            func.count(Product.id),
            func.coalesce(func.sum(Product.quantity), 0),
            func.coalesce(func.sum(value), 0),
            func.coalesce(
                func.sum(
                    case(
                        (
                            (Product.quantity > 0) & (Product.quantity <= Product.reorder_level),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ),
            func.coalesce(func.sum(case((Product.quantity <= 0, 1), else_=0)), 0),
        )
    ).one()

    rows = db.execute(
        select(
            Product.category,
            func.count(Product.id),
            func.coalesce(func.sum(Product.quantity), 0),
            func.coalesce(func.sum(value), 0),
        )
        .group_by(Product.category)
        .order_by(func.sum(value).desc())
    ).all()

    return StatsOut(
        total_products=totals[0],
        total_units=int(totals[1]),
        inventory_value=round(float(totals[2]), 2),
        low_stock=int(totals[3]),
        out_of_stock=int(totals[4]),
        categories=[
            CategorySummary(category=c, products=n, units=int(u), value=round(float(v), 2))
            for c, n, u, v in rows
        ],
    )


@router.get("/categories", response_model=list[str])
def categories(db: Session = Depends(get_db)):
    return db.scalars(select(Product.category).distinct().order_by(Product.category)).all()
