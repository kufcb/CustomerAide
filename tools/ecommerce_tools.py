"""电商 Tool Calling 工具定义"""

import json

from langchain_core.tools import tool

from business.logistics_service import query_by_order_no as logistics_by_order
from business.logistics_service import query_by_tracking_no as logistics_by_tracking
from business.order_service import get_order_by_no, list_orders_by_phone
from business.product_service import search_products as search_products_svc
from business.refund_service import create_refund, query_by_order_no as refunds_by_order
from business.refund_service import query_by_refund_no


def _json(data) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


@tool
def search_products(keyword: str = "", category: str = "", limit: int = 5) -> str:
    """按关键词或品类检索在售商品，用于回答商品咨询、比价、库存等问题。

    Args:
        keyword: 商品名称或描述关键词，如「iPhone」「降噪耳机」
        category: 品类筛选，如「手机」「电脑」「耳机」
        limit: 返回条数上限，默认 5
    """
    products = search_products_svc(keyword=keyword, category=category, limit=limit)
    if not products:
        return "未找到匹配商品"
    return _json(products)


@tool
def get_order_detail(order_no: str = "", phone: str = "") -> str:
    """查询订单详情。必须提供订单号或手机号其一。

    Args:
        order_no: 订单号，如 ORD20250620001
        phone: 客户手机号，如 13800138000，将返回该用户最近订单列表
    """
    if order_no:
        order = get_order_by_no(order_no)
        if not order:
            return f"未找到订单号 {order_no}"
        return _json(order)
    if phone:
        orders = list_orders_by_phone(phone)
        if not orders:
            return f"未找到手机号 {phone} 的订单"
        return _json(orders)
    return "请提供订单号 order_no 或手机号 phone"


@tool
def query_logistics(order_no: str = "", tracking_no: str = "") -> str:
    """查询物流进度，支持按订单号或快递单号查询。

    Args:
        order_no: 订单号
        tracking_no: 快递运单号
    """
    if order_no:
        info = logistics_by_order(order_no)
        if not info:
            return f"未找到订单 {order_no} 的物流信息"
        return _json(info)
    if tracking_no:
        info = logistics_by_tracking(tracking_no)
        if not info:
            return f"未找到运单号 {tracking_no} 的物流信息"
        return _json(info)
    return "请提供订单号 order_no 或运单号 tracking_no"


@tool
def query_refund_status(order_no: str = "", refund_no: str = "") -> str:
    """查询退款申请状态。

    Args:
        order_no: 订单号
        refund_no: 退款单号
    """
    if refund_no:
        refund = query_by_refund_no(refund_no)
        if not refund:
            return f"未找到退款单 {refund_no}"
        return _json(refund)
    if order_no:
        refunds = refunds_by_order(order_no)
        if not refunds:
            return f"订单 {order_no} 暂无退款记录"
        return _json(refunds)
    return "请提供订单号 order_no 或退款单号 refund_no"


@tool
def apply_refund(order_no: str, reason: str, amount: float = 0) -> str:
    """为客户提交退款申请（可执行操作）。金额不传或为 0 时默认全额退款。

    Args:
        order_no: 需要退款的订单号
        reason: 退款原因
        amount: 退款金额，0 表示全额退款
    """
    refund_amount = amount if amount > 0 else None
    result = create_refund(order_no, reason, refund_amount)
    return _json(result)


ECOMMERCE_TOOLS = [
    search_products,
    get_order_detail,
    query_logistics,
    query_refund_status,
    apply_refund,
]
