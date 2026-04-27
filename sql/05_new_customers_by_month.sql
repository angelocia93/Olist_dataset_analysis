WITH first_purchase AS (
    SELECT
        c.customer_unique_id,
        MIN(o.order_purchase_timestamp) AS first_order_date
    FROM orders o
    JOIN customers c
        ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
)

SELECT
    strftime('%Y-%m', first_order_date) AS first_purchase_month,
    COUNT(customer_unique_id) AS new_customers
FROM first_purchase
GROUP BY first_purchase_month
ORDER BY first_purchase_month;
