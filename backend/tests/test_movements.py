import pytest


def post_movement(client, product_id, movement_type, quantity, note=""):
    return client.post(
        f"/api/products/{product_id}/movements",
        json={"movement_type": movement_type, "quantity": quantity, "note": note},
    )


def test_receive_stock_increases_quantity(client, make_product):
    product = make_product(quantity=10)
    response = post_movement(client, product["id"], "RECEIVED", 15, "PO-7781")
    assert response.status_code == 201
    body = response.json()
    assert body["quantity_change"] == 15
    assert body["balance_after"] == 25
    assert body["product_sku"] == product["sku"]
    assert client.get(f"/api/products/{product['id']}").json()["quantity"] == 25


def test_ship_stock_decreases_quantity(client, make_product):
    product = make_product(quantity=10)
    body = post_movement(client, product["id"], "SHIPPED", 4).json()
    assert body["quantity_change"] == -4
    assert body["balance_after"] == 6


def test_shipping_more_than_on_hand_is_rejected(client, make_product):
    product = make_product(quantity=3)
    response = post_movement(client, product["id"], "SHIPPED", 5)
    assert response.status_code == 409
    assert "Insufficient stock" in response.json()["detail"]
    assert client.get(f"/api/products/{product['id']}").json()["quantity"] == 3


def test_adjustment_can_be_negative(client, make_product):
    product = make_product(quantity=10)
    body = post_movement(client, product["id"], "ADJUSTED", -2, "Damaged in transit").json()
    assert body["balance_after"] == 8


@pytest.mark.parametrize(
    ("movement_type", "quantity"),
    [("RECEIVED", 0), ("RECEIVED", -5), ("SHIPPED", -1), ("STOLEN", 1)],
)
def test_invalid_movements_are_rejected(client, make_product, movement_type, quantity):
    product = make_product()
    assert post_movement(client, product["id"], movement_type, quantity).status_code == 422


def test_movement_for_missing_product_returns_404(client):
    assert post_movement(client, 9999, "RECEIVED", 1).status_code == 404


def test_stock_status_transitions_with_movements(client, make_product):
    product = make_product(quantity=12, reorder_level=5)
    post_movement(client, product["id"], "SHIPPED", 8)
    assert client.get(f"/api/products/{product['id']}").json()["stock_status"] == "LOW_STOCK"
    post_movement(client, product["id"], "SHIPPED", 4)
    assert client.get(f"/api/products/{product['id']}").json()["stock_status"] == "OUT_OF_STOCK"


def test_recent_movements_newest_first_and_limited(client, make_product):
    product = make_product(quantity=0)
    for qty in (1, 2, 3):
        post_movement(client, product["id"], "RECEIVED", qty)
    movements = client.get("/api/movements?limit=2").json()
    assert [m["quantity_change"] for m in movements] == [3, 2]
