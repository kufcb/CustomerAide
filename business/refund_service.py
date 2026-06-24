"""退款查询与申请服务"""

from datetime import datetime

from db.pg_conn import get_pg_conn

REFUND_STATUS_LABEL = {
    "pending": "审核中",
    "approved": "已通过",
    "rejected": "已拒绝",
    "completed": "已退款",
}


def _row_to_refund(row) -> dict:
    return {
        "refund_no": row[0],
        "order_no": row[1],
        "reason": row[2],
        "amount": float(row[3]),
        "status": REFUND_STATUS_LABEL.get(row[4], row[4]),
        "created_at": row[5].strftime("%Y-%m-%d %H:%M"),
    }


def query_by_order_no(order_no: str) -> list[dict]:
    conn = get_pg_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT refund_no, order_no, reason, amount, status, created_at
                FROM ec_refunds WHERE order_no = %s
                ORDER BY created_at DESC
                """,
                (order_no,),
            )
            return [_row_to_refund(r) for r in cur.fetchall()]
    finally:
        conn.close()


def query_by_refund_no(refund_no: str) -> dict | None:
    conn = get_pg_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT refund_no, order_no, reason, amount, status, created_at
                FROM ec_refunds WHERE refund_no = %s
                """,
                (refund_no,),
            )
            row = cur.fetchone()
            return _row_to_refund(row) if row else None
    finally:
        conn.close()


def create_refund(order_no: str, reason: str, amount: float | None = None) -> dict:
    conn = get_pg_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, total_amount, status FROM ec_orders WHERE order_no = %s",
                (order_no,),
            )
            order = cur.fetchone()
            if not order:
                return {"success": False, "message": f"订单 {order_no} 不存在"}

            order_id, total_amount, order_status = order
            if order_status in ("pending_payment", "cancelled"):
                return {"success": False, "message": f"订单当前状态为 {order_status}，无法申请退款"}

            cur.execute(
                "SELECT id FROM ec_refunds WHERE order_no = %s AND status IN ('pending', 'approved')",
                (order_no,),
            )
            if cur.fetchone():
                return {"success": False, "message": "该订单已有进行中的退款申请"}

            refund_amount = amount if amount is not None else float(total_amount)
            if refund_amount > float(total_amount):
                return {"success": False, "message": "退款金额不能超过订单总额"}

            refund_no = f"RF{datetime.now().strftime('%Y%m%d%H%M%S')}"
            cur.execute(
                """
                INSERT INTO ec_refunds (refund_no, order_id, order_no, reason, amount, status)
                VALUES (%s, %s, %s, %s, %s, 'pending')
                RETURNING refund_no, order_no, reason, amount, status, created_at
                """,
                (refund_no, order_id, order_no, reason, refund_amount),
            )
            row = cur.fetchone()
        conn.commit()
        refund = _row_to_refund(row)
        return {"success": True, "message": "退款申请已提交", "refund": refund}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": f"退款申请失败: {e}"}
    finally:
        conn.close()
