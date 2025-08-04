import pandas as pd
import streamlit as st
import altair as alt

# 1️⃣ Load data
promo_periods = pd.read_csv("data/promo_period.csv")

# 2️⃣ Aggregate by UPC but keep an item name (take the first occurrence per UPC)
upc_summary = promo_periods.groupby('upc').agg(
    item_name=('Long_Desc', 'first'),     # or 'Item' if that's the column name
    avg_profit=('profit_difference', 'mean'),
    avg_lift=('lift', 'mean'),
    total_revenue=('promo_revenue', 'sum'),
    total_profit=('promo_profit', 'sum'),
    promo_count=('sale_period', 'count')
).reset_index()

# 3️⃣ Streamlit UI
st.title("Item Profit vs Lift Analysis")

# Filter: minimum promotions
min_promos = st.slider("Minimum # of Promotions", 1, int(upc_summary['promo_count'].max()), 1)
filtered_df = upc_summary[upc_summary['promo_count'] >= min_promos]

# Calculate axis domains
x_min, x_max = filtered_df['avg_profit'].min(), filtered_df['avg_profit'].max()
y_min, y_max = filtered_df['avg_lift'].min(), filtered_df['avg_lift'].max()

# 4️⃣ Altair Scatter Chart
scatter = alt.Chart(filtered_df).mark_circle(size=100, opacity=0.75).encode(
    x=alt.X("avg_profit:Q", title="Average Profit Difference", scale=alt.Scale(domain=[x_min, x_max])),
    y=alt.Y("avg_lift:Q", title="Average Lift", scale=alt.Scale(domain=[y_min, y_max])),
    size=alt.Size("total_revenue:Q", scale=alt.Scale(range=[30, 400]), title="Total Revenue"),
    color=alt.Color("total_profit:Q", scale=alt.Scale(scheme="redyellowgreen"), title="Profit"),
    tooltip=["item_name", "avg_profit", "avg_lift", "total_revenue", "total_profit", "promo_count"]
)

st.altair_chart(scatter, use_container_width=True)


sales_df = pd.read_csv("data/skinny_sales_data.csv")

# Convert date fields
sales_df['SaleDate'] = pd.to_datetime(sales_df['SaleDate'])
promo_periods['start_date'] = pd.to_datetime(promo_periods['promo_start'])
promo_periods['end_date'] = pd.to_datetime(promo_periods['promo_end'])

# 2️⃣ UI Title
st.title("Units Sold Over Time with Promotions")

# 3️⃣ Item selector
selected_item = st.selectbox("Select an item", sorted(sales_df['Long_Desc'].dropna().unique()))

# Filter sales data for item
item_sales = sales_df[sales_df['Long_Desc'] == selected_item].sort_values('SaleDate')

# Filter promo data for item
item_promos = promo_periods[promo_periods['Long_Desc'] == selected_item].copy()

# 4️⃣ Display promo table
st.subheader("Promotion Periods with Metrics")
if not item_promos.empty:
    st.dataframe(item_promos)
else:
    st.write("No promotions found for this item.")

# 5️⃣ Units sold chart
units_chart = alt.Chart(item_sales).mark_line(point=True).encode(
    x=alt.X("SaleDate:T", title="Date"),
    y=alt.Y("ItemsSold:Q", title="Units Sold"),
    tooltip=["SaleDate", "ItemsSold", "Curr_Price", "RegRetail"]
)

# 6️⃣ Add promo shading from promo_period file
if not item_promos.empty:
    promo_layer = alt.Chart(item_promos).mark_rect(opacity=0.2, color='red').encode(
        x='start_date:T',
        x2='end_date:T'
    )
    final_chart = units_chart + promo_layer
else:
    final_chart = units_chart

# 7️⃣ Show chart
st.write("### Units Sold Over Time")
st.altair_chart(final_chart, use_container_width=True)
