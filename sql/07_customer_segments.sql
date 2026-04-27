WITH customer_orders AS (
    SELECT
        c.customer_unique_id,
        MAX(o.order_purchase_timestamp) AS last_order_date,
        COUNT(DISTINCT o.order_id) AS frequency,
        SUM(oi.price) AS monetary
    FROM orders o
    JOIN order_items oi
        ON o.order_id = oi.order_id
    JOIN customers c
        ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),

rfm AS (
    SELECT
        customer_unique_id,
        CAST(
            julianday('2018-09-01') - julianday(last_order_date)
            AS INTEGER
        ) AS recency_days,
        frequency,
        ROUND(monetary, 2) AS monetary
    FROM customer_orders
),

rfm_scores AS (
    SELECT
        customer_unique_id,
        recency_days,
        frequency,
        monetary,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS recency_score,
        NTILE(5) OVER (ORDER BY frequency ASC) AS frequency_score,
        NTILE(5) OVER (ORDER BY monetary ASC) AS monetary_score
    FROM rfm
)

SELECT
    customer_unique_id,
    recency_days,
    frequency,
    monetary,
    recency_score,
    frequency_score,
    monetary_score,
    CASE
        WHEN recency_score >= 4 AND frequency_score >= 4 AND monetary_score >= 4
            THEN 'Champions'
        WHEN recency_score >= 4 AND frequency_score <= 2
            THEN 'New / Recent Customers'
        WHEN recency_score <= 2 AND frequency_score >= 4
            THEN 'At Risk Loyal Customers'
        WHEN monetary_score >= 4 AND frequency_score <= 2
            THEN 'Big Spenders - Low Frequency'
        WHEN recency_score <= 2 AND frequency_score <= 2
            THEN 'Lost Customers'
        ELSE 'Regular Customers'
    END AS customer_segment
FROM rfm_scores
ORDER BY monetary DESC;
