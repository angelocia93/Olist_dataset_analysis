SELECT
    c.customer_unique_id,
    c.customer_city,
    c.customer_state,
    ROUND(SUM(oi.price), 2) AS total_spent,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(AVG(oi.price), 2) AS avg_item_price
FROM orders o
JOIN order_items oi
    ON o.order_id = oi.order_id
JOIN customers c
    ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered'
GROUP BY
    c.customer_unique_id,
    c.customer_city,
    c.customer_state
ORDER BY total_spent DESC
LIMIT 20;