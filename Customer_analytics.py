# %%



# %%
# IMPORT LIBRARIES

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# %%
# LOADING DATA

orders = pd.read_csv("olist_orders_dataset.csv")
items = pd.read_csv("olist_order_items_dataset.csv")
customers = pd.read_csv("olist_customers_dataset.csv")
payments = pd.read_csv("olist_order_payments_dataset.csv")
products = pd.read_csv("olist_products_dataset.csv")
categories = pd.read_csv("product_category_name_translation.csv")

# %% [markdown]
# # DATA UNDERSTANDING

# %%
# QUICK CHECK OF THE DATAFRAMES

for name, df in {
    "orders": orders,
    "items": items,
    "customers": customers,
    "payments": payments,
    "products": products,
    "categories": categories
}.items():
    print(f"{name}: {df.shape}")


print("\n")
print(orders.info(), "\n")
print(items.info(), "\n")
print(customers.info(), "\n")
print(payments.info(), "\n")
print(products.info(), "\n")
print(categories.info(), "\n")


# %% [markdown]
# # DATA CLEANING

# %%
# CONVERTING DATE COLUMNS TO DATETIME

orders["order_purchase_timestamp"] = pd.to_datetime(
    orders["order_purchase_timestamp"]
)

orders["order_delivered_customer_date"] = pd.to_datetime(
    orders["order_delivered_customer_date"]
)

orders["order_estimated_delivery_date"] = pd.to_datetime(
    orders["order_estimated_delivery_date"]
)

# %%
# FILTERING ONLY DELIVERED ORDERS

orders_delivered = orders[orders["order_status"] == "delivered"].copy()

# %%
# CHECKING FOR MISSING VALUES IN THE DELIVERED ORDERS DATAFRAME

orders_delivered.isna().sum()

# %%
# CHECKING FOR DUPLICATES IN THE DATAFRAMES

print("Duplicated orders:", orders_delivered.duplicated().sum())
print("Duplicated order items:", items.duplicated().sum())
print("Duplicated customers:", customers.duplicated().sum())

# %%
# CHECKING OULIERS IN THE PRICE COLUMN OF THE ITEMS DATAFRAME

print(items["price"].describe(), "\n")

items[items["price"] > items["price"].quantile(0.99)][
    ["order_id", "product_id", "price", "freight_value"]
].sort_values("price", ascending=False).head(10)

# %%
# CREATING ANALYTICAL DATASET

df = (
    orders_delivered
    .merge(customers, on="customer_id", how="left")
    .merge(items, on="order_id", how="left")
    .merge(products, on="product_id", how="left")
    .merge(categories, on="product_category_name", how="left")
)

df["order_month"] = df["order_purchase_timestamp"].dt.to_period("M").astype(str)
df["order_date"] = df["order_purchase_timestamp"].dt.date
df["revenue"] = df["price"]
df["freight"] = df["freight_value"]

df.head()
df.info()

# %% [markdown]
# # EDA

# %%
# MAIN KPIs

total_revenue = df["revenue"].sum()
total_orders = df["order_id"].nunique()
total_customers = df["customer_unique_id"].nunique()
avg_order_value = total_revenue / total_orders

print(f"Total Revenue: {total_revenue:,.2f}")
print(f"Total Orders: {total_orders:,}")
print(f"Total Customers: {total_customers:,}")
print(f"Average Order Value: {avg_order_value:,.2f}")

# %%
# MONTHLY REVENUE TRENDS

monthly_sales = (
    df.groupby("order_month")
    .agg(
        revenue=("revenue", "sum"),
        orders=("order_id", "nunique"),
        customers=("customer_unique_id", "nunique")
    )
    .reset_index()
)

monthly_sales.head()

# %%
# PLOTTING MONTHLY REVENUE TRENDS

plt.figure(figsize=(12, 5))
plt.plot(monthly_sales["order_month"], monthly_sales["revenue"], marker="o")
plt.title("Monthly Revenue Trend")
plt.xlabel("Month")
plt.ylabel("Revenue")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# %%
# TOP 10 PRODUCT CATEGORIES BY REVENUE

category_sales = (
    df.groupby("product_category_name_english")
    .agg(
        revenue=("revenue", "sum"),
        orders=("order_id", "nunique")
    )
    .reset_index()
    .sort_values("revenue", ascending=False)
)

category_sales.head(10)

# %%
# PLOTTING TOP 10 PRODUCT CATEGORIES BY REVENUE

top_categories = category_sales.head(10)

plt.figure(figsize=(10, 6))
plt.barh(
    top_categories["product_category_name_english"],
    top_categories["revenue"]
)
plt.title("Top 10 Product Categories by Revenue")
plt.xlabel("Revenue")
plt.ylabel("Category")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.show()

# %%
# RFM CUSTOMER SEGMENTATION

reference_date = df["order_purchase_timestamp"].max() + pd.Timedelta(days=1)

rfm = (
    df.groupby("customer_unique_id")
    .agg(
        last_order_date=("order_purchase_timestamp", "max"),
        frequency=("order_id", "nunique"),
        monetary=("revenue", "sum")
    )
    .reset_index()
)

rfm["recency"] = (
    reference_date - rfm["last_order_date"]
).dt.days

rfm = rfm[["customer_unique_id", "recency", "frequency", "monetary"]]

rfm.head()

# %%
# CALCULATING RFM SCORES (1-5 SCALE FOR EACH METRIC)

rfm["r_score"] = pd.qcut(
    rfm["recency"],
    5,
    labels=[5, 4, 3, 2, 1]
)

rfm["f_score"] = pd.qcut(
    rfm["frequency"].rank(method="first"),
    5,
    labels=[1, 2, 3, 4, 5]
)

rfm["m_score"] = pd.qcut(
    rfm["monetary"],
    5,
    labels=[1, 2, 3, 4, 5]
)

rfm["rfm_score"] = (
    rfm["r_score"].astype(str)
    + rfm["f_score"].astype(str)
    + rfm["m_score"].astype(str)
)

# %%
# BUSINESS SEGMENTS BASED ON RFM SCORES

def assign_segment(row):
    r = int(row["r_score"])
    f = int(row["f_score"])
    m = int(row["m_score"])

    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    elif r >= 4 and f <= 2:
        return "New / Recent Customers"
    elif r <= 2 and f >= 4:
        return "At Risk Loyal Customers"
    elif m >= 4 and f <= 2:
        return "Big Spenders - Low Frequency"
    elif r <= 2 and f <= 2:
        return "Lost Customers"
    else:
        return "Regular Customers"

rfm["customer_segment"] = rfm.apply(assign_segment, axis=1)

rfm.head()

# %%
# SUMMARIZING CUSTOMER SEGMENTS WITH KEY METRICS

segment_summary = (
    rfm.groupby("customer_segment")
    .agg(
        customers=("customer_unique_id", "count"),
        avg_recency=("recency", "mean"),
        avg_frequency=("frequency", "mean"),
        total_revenue=("monetary", "sum"),
        avg_monetary=("monetary", "mean")
    )
    .reset_index()
    .sort_values("total_revenue", ascending=False)
)

segment_summary

# %%
# PLOTTING REVENUE BY CUSTOMER SEGMENT

plt.figure(figsize=(10, 5))
plt.bar(segment_summary["customer_segment"], segment_summary["total_revenue"])
plt.title("Revenue by Customer Segment")
plt.xlabel("Customer Segment")
plt.ylabel("Revenue")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.show()

# %% [markdown]
# # Clustering KMeans

# %%
# PREPARING AND SCALING DATA FOR KMEANS CLUSTERING

cluster_data = rfm[["recency", "frequency", "monetary"]].copy()

scaler = StandardScaler()
cluster_scaled = scaler.fit_transform(cluster_data)

# %%
# USING ELBOW METHOD TO DETERMINE OPTIMAL NUMBER OF CLUSTERS

inertia = []

for k in range(1, 11):
    model = KMeans(n_clusters=k, random_state=42, n_init=10)
    model.fit(cluster_scaled)
    inertia.append(model.inertia_)

plt.figure(figsize=(8, 5))
plt.plot(range(1, 11), inertia, marker="o")
plt.title("Elbow Method for KMeans")
plt.xlabel("Number of Clusters")
plt.ylabel("Inertia")
plt.tight_layout()
plt.show()

# %%
# FITTING KMEANS MODEL WITH 4 CLUSTERS AND ASSIGNING CLUSTER LABELS

kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
rfm["cluster"] = kmeans.fit_predict(cluster_scaled)

# %%
# SUMMARIZING CLUSTER CHARACTERISTICS AND PERFORMANCE METRICS

cluster_summary = (
    rfm.groupby("cluster")
    .agg(
        customers=("customer_unique_id", "count"),
        avg_recency=("recency", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
        total_revenue=("monetary", "sum")
    )
    .reset_index()
    .sort_values("total_revenue", ascending=False)
)

cluster_summary

# %% [markdown]
# # Data export for dashboards

# %%
monthly_sales.to_csv("monthly_sales.csv", index=False)
category_sales.to_csv("category_sales.csv", index=False)
rfm.to_csv("rfm_customers.csv", index=False)
segment_summary.to_csv("segment_summary.csv", index=False)
cluster_summary.to_csv("cluster_summary.csv", index=False)

# %%



