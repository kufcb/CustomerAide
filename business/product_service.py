"""商品检索服务"""

from db.pg_conn import get_pg_conn

STATUS_LABEL = {
    "on_sale": "在售",
    "sold_out": "售罄",
    "off_shelf": "下架",
}


def search_products(keyword: str = "", category: str = "", limit: int = 5) -> list[dict]:
    conn = get_pg_conn()
    try:
        with conn.cursor() as cur:
            sql = """
                SELECT sku, name, category, price, stock, description, status
                FROM ec_products
                WHERE 1=1
            """
            params: list = []
            if keyword:
                sql += " AND (name ILIKE %s OR description ILIKE %s OR sku ILIKE %s)"
                pattern = f"%{keyword}%"
                params.extend([pattern, pattern, pattern])
            if category:
                sql += " AND category ILIKE %s"
                params.append(f"%{category}%")
            sql += " ORDER BY stock DESC, id LIMIT %s"
            params.append(limit)
            cur.execute(sql, params)
            rows = cur.fetchall()
    finally:
        conn.close()

    return [
        {
            "sku": r[0],
            "name": r[1],
            "category": r[2],
            "price": float(r[3]),
            "stock": r[4],
            "description": r[5],
            "status": STATUS_LABEL.get(r[6], r[6]),
        }
        for r in rows
    ]
