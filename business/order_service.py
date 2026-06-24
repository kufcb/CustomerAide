"""订单查询服务"""

from db.pg_conn import get_pg_conn

ORDER_STATUS_LABEL = {
    "pending_payment": "待付款",
    "paid": "已付款",
    "shipped": "已发货",
    "delivered": "已签收",
    "cancelled": "已取消",
}


def _fetch_order_items(cur, order_id: int) -> list[dict]:
    cur.execute(
        """
        SELECT sku, product_name, quantity, unit_price
        FROM ec_order_items WHERE order_id = %s
        """,
        (order_id,),
    )
    return [
        {
            "sku": r[0],
            "product_name": r[1],
            "quantity": r[2],
            "unit_price": float(r[3]),
        }
        for r in cur.fetchall()
    ]


def _row_to_order(row, items: list[dict]) -> dict:
    return {
        "order_no": row[0],
        "status": ORDER_STATUS_LABEL.get(row[1], row[1]),
        "total_amount": float(row[2]),
        "shipping_address": row[3],
        "created_at": row[4].strftime("%Y-%m-%d %H:%M"),
        "customer_name": row[5],
        "customer_phone": row[6],
        "items": items,
    }


def get_order_by_no(order_no: str) -> dict | None:
    conn = get_pg_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT o.order_no, o.status, o.total_amount, o.shipping_address,
                       o.created_at, u.name, u.phone, o.id
                FROM ec_orders o
                JOIN ec_users u ON o.user_id = u.id
                WHERE o.order_no = %s
                """,
                (order_no,),
            )
            row = cur.fetchone()
            if not row:
                return None
            items = _fetch_order_items(cur, row[7])
            return _row_to_order(row, items)
    finally:
        conn.close()


def list_orders_by_phone(phone: str, limit: int = 5) -> list[dict]:
    conn = get_pg_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT o.order_no, o.status, o.total_amount, o.shipping_address,
                       o.created_at, u.name, u.phone, o.id
                FROM ec_orders o
                JOIN ec_users u ON o.user_id = u.id
                WHERE u.phone = %s
                ORDER BY o.created_at DESC
                LIMIT %s
                """,
                (phone, limit),
            )
            rows = cur.fetchall()
            orders = []
            for row in rows:
                items = _fetch_order_items(cur, row[7])
                orders.append(_row_to_order(row, items))
            return orders
    finally:
        conn.close()
