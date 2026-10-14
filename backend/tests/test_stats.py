def test_stats_on_empty_inventory(client):
    body = client.get("/api/stats").json()
    assert body == {
        "total_products": 0,
        "total_units": 0,
        "inventory_value": 0,
        "low_stock": 0,
        "out_of_stock": 0,
        "categories": [],
    }


def test_stats_aggregate_value_and_alerts(client, make_product):
    make_product(sku="SKU-A", category="Tools", quantity=10, reorder_level=2, unit_price=5)  # 50
    make_product(sku="SKU-B", category="Tools", quantity=1, reorder_level=5, unit_price=100)  # 100, low
    make_product(sku="SKU-C", category="Paint", quantity=0, unit_price=30)  # 0, out

    body = client.get("/api/stats").json()
    assert body["total_products"] == 3
    assert body["total_units"] == 11
    assert body["inventory_value"] == 150
    assert body["low_stock"] == 1
    assert body["out_of_stock"] == 1
    assert body["categories"][0] == {"category": "Tools", "products": 2, "units": 11, "value": 150}


def test_categories_are_distinct_and_sorted(client, make_product):
    make_product(sku="CAT-1", category="Zeta")
    make_product(sku="CAT-2", category="Alpha")
    make_product(sku="CAT-3", category="Zeta")
    assert client.get("/api/categories").json() == ["Alpha", "Zeta"]


def test_seed_demo_data_is_idempotent(db_session):
    from app.seed import DEMO_PRODUCTS, seed_demo_data

    assert seed_demo_data(db_session) == len(DEMO_PRODUCTS)
    assert seed_demo_data(db_session) == 0
