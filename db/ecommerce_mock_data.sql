-- 电商演示数据补充（可重复执行，冲突时跳过）
-- 用法: psql -h localhost -p 15432 -U postgres -d customer-aide -f db/ecommerce_mock_data.sql

-- ========== 用户 ==========
INSERT INTO ec_users (phone, name) VALUES
    ('13600136000', '赵六'),
    ('13500135000', '钱七'),
    ('13400134000', '孙八'),
    ('13300133000', '周九'),
    ('13200132000', '吴十')
ON CONFLICT (phone) DO NOTHING;

-- ========== 商品 ==========
INSERT INTO ec_products (sku, name, category, price, stock, description, status) VALUES
    ('SKU-MI14', '小米 14 16GB+512GB', '手机', 4299.00, 200,
     '骁龙 8 Gen3，徕卡光学镜头，120W 快充', 'on_sale'),
    ('SKU-MATE60', '华为 Mate 60 Pro', '手机', 6999.00, 35,
     '卫星通信，昆仑玻璃，鸿蒙系统', 'on_sale'),
    ('SKU-OPPO-FIND', 'OPPO Find X7 Ultra', '手机', 5999.00, 88,
     '双潜望长焦，哈苏影像，天玑 9300', 'on_sale'),
    ('SKU-SONY-XM5', '索尼 WH-1000XM5', '耳机', 2499.00, 150,
     '旗舰降噪耳机，30 小时续航', 'on_sale'),
    ('SKU-DYSON-V15', '戴森 V15 吸尘器', '家电', 4990.00, 22,
     '激光探测微尘，智能调速', 'on_sale'),
    ('SKU-NESCAFE', '雀巢胶囊咖啡机 Genio S', '家电', 899.00, 60,
     '一键萃取，兼容多种胶囊', 'on_sale'),
    ('SKU-LOGITECH-MX', '罗技 MX Master 3S', '配件', 699.00, 180,
     '人体工学办公鼠标，静音微动', 'on_sale'),
    ('SKU-KEYCHRON-K2', 'Keychron K2 机械键盘', '配件', 548.00, 95,
     '蓝牙双模，热插拔轴体', 'on_sale'),
    ('SKU-SAMSUNG-T7', '三星 T7 移动固态 1TB', '配件', 599.00, 0,
     'USB 3.2，读写 1050MB/s', 'sold_out'),
    ('SKU-OLD-IPHONE13', 'iPhone 13 128GB（清仓）', '手机', 3999.00, 5,
     '上一代机型清仓特价', 'off_shelf')
ON CONFLICT (sku) DO NOTHING;

-- ========== 订单 ==========
INSERT INTO ec_orders (order_no, user_id, status, total_amount, shipping_address, created_at)
SELECT 'ORD20250610004', id, 'pending_payment', 4299.00,
       '广州市天河区体育西路 188 号', '2025-06-10 09:15:00'
FROM ec_users WHERE phone = '13700137000'
ON CONFLICT (order_no) DO NOTHING;

INSERT INTO ec_orders (order_no, user_id, status, total_amount, shipping_address, created_at)
SELECT 'ORD20250615005', id, 'cancelled', 2499.00,
       '深圳市南山区科技园南路 66 号', '2025-06-15 20:42:00'
FROM ec_users WHERE phone = '13600136000'
ON CONFLICT (order_no) DO NOTHING;

INSERT INTO ec_orders (order_no, user_id, status, total_amount, shipping_address, created_at)
SELECT 'ORD20250618006', id, 'shipped', 1247.00,
       '杭州市西湖区文三路 100 号', '2025-06-18 11:30:00'
FROM ec_users WHERE phone = '13500135000'
ON CONFLICT (order_no) DO NOTHING;

INSERT INTO ec_orders (order_no, user_id, status, total_amount, shipping_address, created_at)
SELECT 'ORD20250619007', id, 'delivered', 6999.00,
       '成都市武侯区天府大道 999 号', '2025-06-19 08:00:00'
FROM ec_users WHERE phone = '13400134000'
ON CONFLICT (order_no) DO NOTHING;

INSERT INTO ec_orders (order_no, user_id, status, total_amount, shipping_address, created_at)
SELECT 'ORD20250621008', id, 'paid', 5688.00,
       '南京市鼓楼区中山路 1 号', '2025-06-21 16:55:00'
FROM ec_users WHERE phone = '13300133000'
ON CONFLICT (order_no) DO NOTHING;

INSERT INTO ec_orders (order_no, user_id, status, total_amount, shipping_address, created_at)
SELECT 'ORD20250624009', id, 'shipped', 1899.00,
       '武汉市江汉区解放大道 688 号', '2025-06-24 10:20:00'
FROM ec_users WHERE phone = '13200132000'
ON CONFLICT (order_no) DO NOTHING;

INSERT INTO ec_orders (order_no, user_id, status, total_amount, shipping_address, created_at)
SELECT 'ORD20250624010', id, 'delivered', 10296.00,
       '北京市朝阳区望京街道 1 号', '2025-06-20 14:00:00'
FROM ec_users WHERE phone = '13800138000'
ON CONFLICT (order_no) DO NOTHING;

-- ========== 订单明细 ==========
INSERT INTO ec_order_items (order_id, product_id, sku, product_name, quantity, unit_price)
SELECT o.id, p.id, 'SKU-MI14', '小米 14 16GB+512GB', 1, 4299.00
FROM ec_orders o, ec_products p
WHERE o.order_no = 'ORD20250610004' AND p.sku = 'SKU-MI14'
  AND NOT EXISTS (SELECT 1 FROM ec_order_items i WHERE i.order_id = o.id);

INSERT INTO ec_order_items (order_id, product_id, sku, product_name, quantity, unit_price)
SELECT o.id, p.id, 'SKU-SONY-XM5', '索尼 WH-1000XM5', 1, 2499.00
FROM ec_orders o, ec_products p
WHERE o.order_no = 'ORD20250615005' AND p.sku = 'SKU-SONY-XM5'
  AND NOT EXISTS (SELECT 1 FROM ec_order_items i WHERE i.order_id = o.id);

INSERT INTO ec_order_items (order_id, product_id, sku, product_name, quantity, unit_price)
SELECT o.id, p.id, 'SKU-LOGITECH-MX', '罗技 MX Master 3S', 1, 699.00
FROM ec_orders o, ec_products p
WHERE o.order_no = 'ORD20250618006' AND p.sku = 'SKU-LOGITECH-MX'
  AND NOT EXISTS (SELECT 1 FROM ec_order_items i WHERE i.order_id = o.id);

INSERT INTO ec_order_items (order_id, product_id, sku, product_name, quantity, unit_price)
SELECT o.id, p.id, 'SKU-KEYCHRON-K2', 'Keychron K2 机械键盘', 1, 548.00
FROM ec_orders o, ec_products p
WHERE o.order_no = 'ORD20250618006' AND p.sku = 'SKU-KEYCHRON-K2'
  AND NOT EXISTS (
      SELECT 1 FROM ec_order_items i
      WHERE i.order_id = o.id AND i.sku = 'SKU-KEYCHRON-K2'
  );

INSERT INTO ec_order_items (order_id, product_id, sku, product_name, quantity, unit_price)
SELECT o.id, p.id, 'SKU-MATE60', '华为 Mate 60 Pro', 1, 6999.00
FROM ec_orders o, ec_products p
WHERE o.order_no = 'ORD20250619007' AND p.sku = 'SKU-MATE60'
  AND NOT EXISTS (SELECT 1 FROM ec_order_items i WHERE i.order_id = o.id);

INSERT INTO ec_order_items (order_id, product_id, sku, product_name, quantity, unit_price)
SELECT o.id, p.id, 'SKU-OPPO-FIND', 'OPPO Find X7 Ultra', 1, 5999.00
FROM ec_orders o, ec_products p
WHERE o.order_no = 'ORD20250621008' AND p.sku = 'SKU-OPPO-FIND'
  AND NOT EXISTS (SELECT 1 FROM ec_order_items i WHERE i.order_id = o.id);

INSERT INTO ec_order_items (order_id, product_id, sku, product_name, quantity, unit_price)
SELECT o.id, p.id, 'SKU-AIRPODS', 'AirPods Pro 2', 1, 1899.00
FROM ec_orders o, ec_products p
WHERE o.order_no = 'ORD20250624009' AND p.sku = 'SKU-AIRPODS'
  AND NOT EXISTS (SELECT 1 FROM ec_order_items i WHERE i.order_id = o.id);

INSERT INTO ec_order_items (order_id, product_id, sku, product_name, quantity, unit_price)
SELECT o.id, p.id, 'SKU-MBP14', 'MacBook Pro 14 M3', 1, 14999.00
FROM ec_orders o, ec_products p
WHERE o.order_no = 'ORD20250624010' AND p.sku = 'SKU-MBP14'
  AND NOT EXISTS (
      SELECT 1 FROM ec_order_items i
      WHERE i.order_id = o.id AND i.sku = 'SKU-MBP14'
  );

INSERT INTO ec_order_items (order_id, product_id, sku, product_name, quantity, unit_price)
SELECT o.id, p.id, 'SKU-DYSON-V15', '戴森 V15 吸尘器', 1, 4990.00
FROM ec_orders o, ec_products p
WHERE o.order_no = 'ORD20250624010' AND p.sku = 'SKU-DYSON-V15'
  AND NOT EXISTS (
      SELECT 1 FROM ec_order_items i
      WHERE i.order_id = o.id AND i.sku = 'SKU-DYSON-V15'
  );

-- ========== 物流 ==========
INSERT INTO ec_logistics (order_id, order_no, carrier, tracking_no, status, latest_event, updated_at)
SELECT o.id, o.order_no, '中通快递', 'ZT7788990011', 'out_for_delivery',
       '快递员正在派送，预计今日 18:00 前送达', '2025-06-24 08:30:00'
FROM ec_orders o WHERE o.order_no = 'ORD20250618006'
  AND NOT EXISTS (SELECT 1 FROM ec_logistics l WHERE l.order_no = o.order_no);

INSERT INTO ec_logistics (order_id, order_no, carrier, tracking_no, status, latest_event, updated_at)
SELECT o.id, o.order_no, '圆通速递', 'YT6655443322', 'delivered',
       '已于 6 月 22 日 15:20 签收，签收人：门卫', '2025-06-22 15:20:00'
FROM ec_orders o WHERE o.order_no = 'ORD20250619007'
  AND NOT EXISTS (SELECT 1 FROM ec_logistics l WHERE l.order_no = o.order_no);

INSERT INTO ec_logistics (order_id, order_no, carrier, tracking_no, status, latest_event, updated_at)
SELECT o.id, o.order_no, '韵达快递', 'YD1122334455', 'pending_shipment',
       '订单已支付，仓库排队出库中', '2025-06-21 17:00:00'
FROM ec_orders o WHERE o.order_no = 'ORD20250621008'
  AND NOT EXISTS (SELECT 1 FROM ec_logistics l WHERE l.order_no = o.order_no);

INSERT INTO ec_logistics (order_id, order_no, carrier, tracking_no, status, latest_event, updated_at)
SELECT o.id, o.order_no, '顺丰速运', 'SF9988776655', 'in_transit',
       '快件已离开武汉集散中心，发往江汉区', '2025-06-24 12:10:00'
FROM ec_orders o WHERE o.order_no = 'ORD20250624009'
  AND NOT EXISTS (SELECT 1 FROM ec_logistics l WHERE l.order_no = o.order_no);

INSERT INTO ec_logistics (order_id, order_no, carrier, tracking_no, status, latest_event, updated_at)
SELECT o.id, o.order_no, '德邦快递', 'DB5566778899', 'delivered',
       '已于 6 月 23 日签收，签收人：张三', '2025-06-23 11:45:00'
FROM ec_orders o WHERE o.order_no = 'ORD20250624010'
  AND NOT EXISTS (SELECT 1 FROM ec_logistics l WHERE l.order_no = o.order_no);

-- ========== 退款 ==========
INSERT INTO ec_refunds (refund_no, order_id, order_no, reason, amount, status, created_at)
SELECT 'RF20250616001', o.id, o.order_no, '下单后未付款，超时自动取消申请退款', 2499.00, 'completed',
       '2025-06-16 10:00:00'
FROM ec_orders o WHERE o.order_no = 'ORD20250615005'
ON CONFLICT (refund_no) DO NOTHING;

INSERT INTO ec_refunds (refund_no, order_id, order_no, reason, amount, status, created_at)
SELECT 'RF20250620002', o.id, o.order_no, '收到商品与描述不符，申请七天无理由退货', 6999.00, 'pending',
       '2025-06-20 09:30:00'
FROM ec_orders o WHERE o.order_no = 'ORD20250619007'
ON CONFLICT (refund_no) DO NOTHING;

INSERT INTO ec_refunds (refund_no, order_id, order_no, reason, amount, status, created_at)
SELECT 'RF20250622003', o.id, o.order_no, '商品质量问题，耳机右耳杂音', 1899.00, 'rejected',
       '2025-06-22 14:15:00'
FROM ec_orders o WHERE o.order_no = 'ORD20250624009'
ON CONFLICT (refund_no) DO NOTHING;

INSERT INTO ec_refunds (refund_no, order_id, order_no, reason, amount, status, created_at)
SELECT 'RF20250623004', o.id, o.order_no, '吸尘器吸力不足，申请部分退款', 1500.00, 'approved',
       '2025-06-23 16:40:00'
FROM ec_orders o WHERE o.order_no = 'ORD20250624010'
ON CONFLICT (refund_no) DO NOTHING;
