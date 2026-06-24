"""初始化电商业务表并插入演示数据。用法: python -m db.seed_ecommerce"""

import os
from datetime import datetime, timedelta

from db.pg_conn import get_pg_conn

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "ecommerce_schema.sql")
MOCK_DATA_PATH = os.path.join(os.path.dirname(__file__), "ecommerce_mock_data.sql")


def _read_schema() -> str:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _table_empty(cur, table: str) -> bool:
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    return cur.fetchone()[0] == 0


def init_schema(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(_read_schema())
    conn.commit()


def seed_data(conn) -> None:
    with conn.cursor() as cur:
        if not _table_empty(cur, "ec_users"):
            print("演示数据已存在，跳过插入")
            return

        cur.execute(
            """
            INSERT INTO ec_users (phone, name) VALUES
            ('13800138000', '张三'),
            ('13900139000', '李四'),
            ('13700137000', '王五')
            RETURNING id, phone, name
            """
        )
        users = {row[1]: row[0] for row in cur.fetchall()}

        cur.execute(
            """
            INSERT INTO ec_products (sku, name, category, price, stock, description, status) VALUES
            ('SKU-IPHONE15', 'iPhone 15 128GB', '手机', 5999.00, 120,
             'A16 芯片，6.1 英寸超视网膜 XDR 显示屏', 'on_sale'),
            ('SKU-MBP14', 'MacBook Pro 14 M3', '电脑', 14999.00, 45,
             'M3 芯片，18 小时续航，Liquid 视网膜 XDR 屏', 'on_sale'),
            ('SKU-AIRPODS', 'AirPods Pro 2', '耳机', 1899.00, 300,
             '主动降噪，自适应通透模式', 'on_sale'),
            ('SKU-IPAD', 'iPad Air 11', '平板', 4799.00, 80,
             'M2 芯片，11 英寸全面屏', 'on_sale'),
            ('SKU-WATCH', 'Apple Watch S9', '穿戴', 2999.00, 0,
             '健康监测，全天候视网膜显示屏', 'sold_out')
            RETURNING id, sku
            """
        )
        products = {row[1]: row[0] for row in cur.fetchall()}

        now = datetime.now()
        orders = [
            ("ORD20250620001", users["13800138000"], "shipped", 7898.00,
             "北京市朝阳区望京街道 1 号", now - timedelta(days=3)),
            ("ORD20250622002", users["13900139000"], "paid", 14999.00,
             "上海市浦东新区陆家嘴环路 88 号", now - timedelta(days=1)),
            ("ORD20250623003", users["13800138000"], "delivered", 4799.00,
             "北京市海淀区中关村大街 10 号", now - timedelta(days=7)),
        ]

        order_ids = {}
        for order_no, user_id, status, total, addr, created in orders:
            cur.execute(
                """
                INSERT INTO ec_orders (order_no, user_id, status, total_amount, shipping_address, created_at)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                """,
                (order_no, user_id, status, total, addr, created),
            )
            order_ids[order_no] = cur.fetchone()[0]

        order_items = [
            (order_ids["ORD20250620001"], products["SKU-IPHONE15"], "SKU-IPHONE15", "iPhone 15 128GB", 1, 5999.00),
            (order_ids["ORD20250620001"], products["SKU-AIRPODS"], "SKU-AIRPODS", "AirPods Pro 2", 1, 1899.00),
            (order_ids["ORD20250622002"], products["SKU-MBP14"], "SKU-MBP14", "MacBook Pro 14 M3", 1, 14999.00),
            (order_ids["ORD20250623003"], products["SKU-IPAD"], "SKU-IPAD", "iPad Air 11", 1, 4799.00),
        ]
        for item in order_items:
            cur.execute(
                """
                INSERT INTO ec_order_items (order_id, product_id, sku, product_name, quantity, unit_price)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                item,
            )

        logistics = [
            (order_ids["ORD20250620001"], "ORD20250620001", "顺丰速运", "SF1234567890",
             "in_transit", "包裹已到达北京转运中心，预计明日送达"),
            (order_ids["ORD20250622002"], "ORD20250622002", "京东物流", "JD9876543210",
             "pending_shipment", "商家已接单，等待仓库拣货"),
            (order_ids["ORD20250623003"], "ORD20250623003", "顺丰速运", "SF5555666677",
             "delivered", "已于 6 月 18 日签收，签收人：本人"),
        ]
        for row in logistics:
            cur.execute(
                """
                INSERT INTO ec_logistics (order_id, order_no, carrier, tracking_no, status, latest_event)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                row,
            )

        cur.execute(
            """
            INSERT INTO ec_refunds (refund_no, order_id, order_no, reason, amount, status, created_at)
            VALUES
            ('RF20250621001', %s, 'ORD20250623003', '商品屏幕有轻微划痕', 4799.00, 'approved',
             %s)
            """,
            (order_ids["ORD20250623003"], now - timedelta(days=2)),
        )

    conn.commit()
    print("电商基础演示数据初始化完成")


def seed_mock_data(conn) -> None:
    """加载补充模拟数据 SQL（可重复执行）"""
    with open(MOCK_DATA_PATH, "r", encoding="utf-8") as f:
        sql = f.read()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print("电商补充模拟数据加载完成")


def main() -> None:
    import sys

    extra_only = "--extra-only" in sys.argv
    conn = get_pg_conn()
    try:
        if not extra_only:
            init_schema(conn)
            seed_data(conn)
        seed_mock_data(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
