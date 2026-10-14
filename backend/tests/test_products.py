def test_create_product_returns_201_with_stock_status(client, make_product):
    product = make_product(quantity=20, reorder_level=5)
    assert product["id"] > 0
    assert product["quantity"] == 20
    assert product["stock_status"] == "IN_STOCK"


def test_create_product_records_opening_stock_movement(client, make_product):
    product = make_product(quantity=12)
    movements = client.get(f"/api/products/{product['id']}/movements").json()
    assert len(movements) == 1
    assert movements[0]["movement_type"] == "RECEIVED"
    assert movements[0]["quantity_change"] == 12
    assert movements[0]["note"] == "Opening stock"


def test_create_product_rejects_duplicate_sku(client, make_product):
    make_product(sku="DUP-1")
    response = client.post("/api/products", json={"sku": "DUP-1", "name": "Other", "category": "X"})
    assert response.status_code == 409


def test_create_product_validates_payload(client):
    response = client.post(
        "/api/products",
        json={"sku": "BAD SKU!", "name": "", "category": "X", "unit_price": -1},
    )
    assert response.status_code == 422
    fields = {err["loc"][-1] for err in response.json()["detail"]}
    assert {"sku", "name", "unit_price"} <= fields


def test_list_products_sorted_by_name(client, make_product):
    make_product(sku="B-1", name="Bravo")
    make_product(sku="A-1", name="Alpha")
    names = [p["name"] for p in client.get("/api/products").json()]
    assert names == ["Alpha", "Bravo"]


def test_list_products_search_matches_name_sku_and_supplier(client, make_product):
    make_product(sku="CAB-1", name="HDMI Cable", supplier="Cablez")
    make_product(sku="MUG-1", name="Coffee Mug", supplier="Kitchenly")
    assert [p["sku"] for p in client.get("/api/products?search=hdmi").json()] == ["CAB-1"]
    assert [p["sku"] for p in client.get("/api/products?search=mug-").json()] == ["MUG-1"]
    assert [p["sku"] for p in client.get("/api/products?search=kitchen").json()] == ["MUG-1"]


def test_list_products_filters_by_category_and_stock_status(client, make_product):
    make_product(sku="IN-1", category="Tools", quantity=50, reorder_level=10)
    make_product(sku="LOW-1", category="Tools", quantity=3, reorder_level=10)
    make_product(sku="OUT-1", category="Paint", quantity=0)

    def skus(query):
        return sorted(p["sku"] for p in client.get(f"/api/products?{query}").json())

    assert skus("category=Tools") == ["IN-1", "LOW-1"]
    assert skus("stock_status=IN_STOCK") == ["IN-1"]
    assert skus("stock_status=LOW_STOCK") == ["LOW-1"]
    assert skus("stock_status=OUT_OF_STOCK") == ["OUT-1"]


def test_get_product_by_id(client, make_product):
    created = make_product()
    response = client.get(f"/api/products/{created['id']}")
    assert response.status_code == 200
    assert response.json()["sku"] == created["sku"]


def test_get_missing_product_returns_404(client):
    assert client.get("/api/products/9999").status_code == 404


def test_update_product_changes_only_sent_fields(client, make_product):
    created = make_product(name="Old name", unit_price=10)
    response = client.put(f"/api/products/{created['id']}", json={"name": "New name"})
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "New name"
    assert body["unit_price"] == 10
    assert body["quantity"] == created["quantity"]


def test_update_product_ignores_quantity_field(client, make_product):
    created = make_product(quantity=5)
    response = client.put(f"/api/products/{created['id']}", json={"quantity": 999})
    assert response.status_code == 200
    assert response.json()["quantity"] == 5


def test_update_product_rejects_sku_taken_by_another_product(client, make_product):
    make_product(sku="KEEP-1")
    other = make_product(sku="MOVE-1")
    response = client.put(f"/api/products/{other['id']}", json={"sku": "KEEP-1"})
    assert response.status_code == 409


def test_update_missing_product_returns_404(client):
    assert client.put("/api/products/9999", json={"name": "x"}).status_code == 404


def test_delete_product_removes_it_and_its_movements(client, make_product):
    created = make_product()
    assert client.delete(f"/api/products/{created['id']}").status_code == 204
    assert client.get(f"/api/products/{created['id']}").status_code == 404
    assert client.get("/api/movements").json() == []


def test_delete_missing_product_returns_404(client):
    assert client.delete("/api/products/9999").status_code == 404
