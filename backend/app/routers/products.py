from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import metrics
from ..db import get_db
from ..models import Product, StockMovement
from ..schemas import (
    MovementCreate,
    MovementOut,
    ProductCreate,
    ProductOut,
    ProductUpdate,
    StockStatus,
)
from ..services import movement_out, record_movement

router = APIRouter(prefix="/api/products", tags=["products"])


def get_product_or_404(product_id: int, db: Session) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def sku_conflict(sku: str) -> HTTPException:
    return HTTPException(status_code=409, detail=f"SKU '{sku}' already exists")


@router.get("", response_model=list[ProductOut])
def list_products(
    search: str | None = Query(default=None, max_length=100, description="Match name, SKU or supplier"),
    category: str | None = Query(default=None, max_length=80),
    stock_status: StockStatus | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = select(Product).order_by(Product.name)
    if search:
        pattern = f"%{search.lower()}%"
        query = query.where(
            or_(
                func.lower(Product.name).like(pattern),
                func.lower(Product.sku).like(pattern),
                func.lower(Product.supplier).like(pattern),
            )
        )
    if category:
        query = query.where(Product.category == category)
    if stock_status == "OUT_OF_STOCK":
        query = query.where(Product.quantity <= 0)
    elif stock_status == "LOW_STOCK":
        query = query.where(Product.quantity > 0, Product.quantity <= Product.reorder_level)
    elif stock_status == "IN_STOCK":
        query = query.where(Product.quantity > Product.reorder_level)
    return db.scalars(query).all()


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return get_product_or_404(product_id, db)


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    if db.scalar(select(Product.id).where(Product.sku == payload.sku)) is not None:
        raise sku_conflict(payload.sku)

    product = Product(**payload.model_dump(exclude={"quantity"}), quantity=0)
    db.add(product)
    if payload.quantity > 0:
        record_movement(db, product, "RECEIVED", payload.quantity, "Opening stock")
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise sku_conflict(payload.sku) from None
    db.refresh(product)
    metrics.PRODUCTS_CREATED.inc()
    return product


@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    product = get_product_or_404(product_id, db)
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    new_sku = changes.get("sku")
    if new_sku and new_sku != product.sku:
        taken = db.scalar(select(Product.id).where(Product.sku == new_sku))
        if taken is not None:
            raise sku_conflict(new_sku)
    for field, value in changes.items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = get_product_or_404(product_id, db)
    db.delete(product)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{product_id}/movements", response_model=list[MovementOut])
def list_product_movements(product_id: int, db: Session = Depends(get_db)):
    product = get_product_or_404(product_id, db)
    movements = db.scalars(
        select(StockMovement)
        .where(StockMovement.product_id == product.id)
        .order_by(StockMovement.created_at.desc(), StockMovement.id.desc())
    ).all()
    return [movement_out(m) for m in movements]


@router.post(
    "/{product_id}/movements",
    response_model=MovementOut,
    status_code=status.HTTP_201_CREATED,
)
def create_movement(product_id: int, payload: MovementCreate, db: Session = Depends(get_db)):
    product = get_product_or_404(product_id, db)
    movement = record_movement(db, product, payload.movement_type, payload.quantity, payload.note)
    db.commit()
    db.refresh(movement)
    return movement_out(movement)
