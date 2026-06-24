"""物流查询服务"""

from db.pg_conn import get_pg_conn

LOGISTICS_STATUS_LABEL = {
    "pending_shipment": "待发货",
    "in_transit": "运输中",
    "out_for_delivery": "派送中",
    "delivered": "已签收",
    "exception": "异常",
}


def _row_to_logistics(row) -> dict:
    return {
        "order_no": row[0],
        "carrier": row[1],
        "tracking_no": row[2],
        "status": LOGISTICS_STATUS_LABEL.get(row[3], row[3]),
        "latest_event": row[4],
        "updated_at": row[5].strftime("%Y-%m-%d %H:%M"),
    }


def query_by_order_no(order_no: str) -> dict | None:
    conn = get_pg_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT order_no, carrier, tracking_no, status, latest_event, updated_at
                FROM ec_logistics WHERE order_no = %s
                """,
                (order_no,),
            )
            row = cur.fetchone()
            return _row_to_logistics(row) if row else None
    finally:
        conn.close()


def query_by_tracking_no(tracking_no: str) -> dict | None:
    conn = get_pg_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT order_no, carrier, tracking_no, status, latest_event, updated_at
                FROM ec_logistics WHERE tracking_no = %s
                """,
                (tracking_no,),
            )
            row = cur.fetchone()
            return _row_to_logistics(row) if row else None
    finally:
        conn.close()
