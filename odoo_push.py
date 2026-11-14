"""Post a camera count to an Odoo transfer (receipt or delivery) for a person to check.

It does NOT validate the transfer or change stock. It writes a note in the
transfer's chatter comparing expected and counted quantities, and attaches a
photo. A storekeeper then confirms.

Connection settings come from environment variables:
  ODOO_URL=http://localhost:8069  ODOO_DB=wh_lab  ODOO_USER=admin  ODOO_PASSWORD=...
Use a test database first, never the live one, until the owner approves.
"""
import base64
import os
import xmlrpc.client


def connect():
    url = os.environ["ODOO_URL"]
    db = os.environ["ODOO_DB"]
    user = os.environ["ODOO_USER"]
    password = os.environ["ODOO_PASSWORD"]
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, user, password, {})
    if not uid:
        raise SystemExit("Odoo login failed: check ODOO_* settings")
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    return models, db, uid, password


def compare(expected, counted, tolerance_pct=2.0):
    """Return a status word and the difference."""
    diff = counted - expected
    if expected == 0:
        return ("NO EXPECTED QUANTITY", diff)
    pct = abs(diff) / expected * 100
    if pct <= tolerance_pct:
        return ("OK", diff)
    return ("SHORT" if diff < 0 else "EXCESS", diff)


def post_count_to_picking(picking_name, counted, image_path=None):
    models, db, uid, pwd = connect()
    ids = models.execute_kw(db, uid, pwd, "stock.picking", "search",
                            [[["name", "=", picking_name]]], {"limit": 1})
    if not ids:
        raise SystemExit(f"Transfer {picking_name} not found")
    picking_id = ids[0]

    moves = models.execute_kw(db, uid, pwd, "stock.move", "search_read",
                              [[["picking_id", "=", picking_id]]],
                              {"fields": ["product_id", "product_uom_qty"]})
    expected = sum(m["product_uom_qty"] for m in moves)
    status, diff = compare(expected, counted)

    body = (f"<p><b>Camera count: {status}</b><br/>"
            f"Expected: {expected:g} &nbsp; Counted: {counted} &nbsp; Difference: {diff:+g}</p>"
            f"<p>Please check before validating.</p>")
    models.execute_kw(db, uid, pwd, "stock.picking", "message_post",
                      [[picking_id]], {"body": body})

    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        models.execute_kw(db, uid, pwd, "ir.attachment", "create", [{
            "name": os.path.basename(image_path),
            "datas": data,
            "res_model": "stock.picking",
            "res_id": picking_id,
        }])
    print(f"Posted to {picking_name}: {status} (expected {expected:g}, counted {counted})")
    return status, diff
