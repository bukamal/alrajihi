from decimal import Decimal

from test_phase34_restaurant_modifiers_recipes import _load_gateway


def _seed_item(conn, item_id, name, quantity="0", avg="0", purchase="0"):
    for ddl in (
        "ALTER TABLE items ADD COLUMN average_cost TEXT",
        "ALTER TABLE items ADD COLUMN purchase_price TEXT",
    ):
        try:
            conn.execute(ddl)
        except Exception:
            pass
    conn.execute(
        "INSERT INTO items(id, name, selling_price, quantity, average_cost, purchase_price) VALUES (?, ?, '0', ?, ?, ?)",
        (int(item_id), name, str(quantity), str(avg), str(purchase)),
    )


def test_phase291_restaurant_recipe_posts_inventory_movement_once(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    conn = gateway._conn()
    _seed_item(conn, 1, "Burger", "0")
    _seed_item(conn, 2, "Bun", "10", avg="0.25")
    conn.commit()

    session = gateway.open_table(gateway.list_tables()[0]["id"], guests=1)
    gateway.upsert_recipe(1, name="Burger recipe", yield_quantity="1", lines=[{"component_item_id": 2, "component_name": "Bun", "quantity": "1", "unit": "pc", "unit_cost": "0.25"}])
    gateway.add_order_line(session["id"], item_id=1, item_name="Burger", quantity="2", unit_price="8")
    gateway.send_to_kitchen(session["id"])

    first = gateway.consume_session_recipes(session["id"], invoice_id=99)
    second = gateway.consume_session_recipes(session["id"], invoice_id=99)

    qty = conn.execute("SELECT quantity FROM items WHERE id=2").fetchone()["quantity"]
    movement = conn.execute("SELECT * FROM inventory_movements WHERE item_id=2 AND movement_type='restaurant_consume'").fetchone()

    assert first["count"] == 1
    assert first["by_source"] == {"restaurant_recipe": 1}
    assert second["count"] == 0
    assert Decimal(str(qty)) == Decimal("8.0")
    assert movement is not None
    assert Decimal(str(movement["quantity"])) == Decimal("2")
    assert str(movement["reference_id"]) == "99"


def test_phase291_manufacturing_bom_fallback_consumes_components(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    conn = gateway._conn()
    _seed_item(conn, 10, "Combo Meal", "0")
    _seed_item(conn, 20, "Rice", "50", avg="1.50", purchase="1.40")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS bom (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            quantity TEXT DEFAULT '1',
            user_id TEXT NOT NULL,
            created_at TEXT,
            updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS bom_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bom_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            quantity TEXT NOT NULL,
            unit_id INTEGER,
            conversion_factor TEXT DEFAULT '1',
            base_qty TEXT DEFAULT '0',
            barcode_scope TEXT,
            matched_barcode TEXT,
            waste_percent TEXT DEFAULT '0'
        );
        """
    )
    cur = conn.execute("INSERT INTO bom(product_id, quantity, user_id) VALUES (10, '2', 'restaurant')")
    conn.execute("INSERT INTO bom_lines(bom_id, item_id, quantity, conversion_factor, waste_percent) VALUES (?, 20, '3', '1', '0.10')", (int(cur.lastrowid),))
    conn.commit()

    session = gateway.open_table(gateway.list_tables()[0]["id"], guests=1)
    gateway.add_order_line(session["id"], item_id=10, item_name="Combo Meal", quantity="4", unit_price="12")
    gateway.send_to_kitchen(session["id"])

    result = gateway.consume_session_recipes(session["id"], invoice_id=101)
    qty = conn.execute("SELECT quantity FROM items WHERE id=20").fetchone()["quantity"]
    movement = conn.execute("SELECT * FROM inventory_movements WHERE item_id=20 AND movement_type='restaurant_consume'").fetchone()

    assert result["count"] == 1
    assert result["by_source"] == {"manufacturing_bom": 1}
    assert Decimal(str(result["consumed"][0]["quantity"])) == Decimal("6.6")
    assert Decimal(str(qty)) == Decimal("43.4")
    assert movement is not None
    assert Decimal(str(movement["quantity"])) == Decimal("6.6")
