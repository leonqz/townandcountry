import pandas as pd
import streamlit as st
import altair as alt

# 1️⃣ Load data
promo_periods = pd.read_csv("data/promo_period.csv")

# Set page config
st.set_page_config(
    page_title="BetterBasket Promo Dashboard",
    page_icon="town-and-country-markets.webp",
    layout="wide"
)

# Title
st.image("town-and-country-markets.webp", width=600)
st.title("Town & Country Markets Promo Dashboard")


with st.sidebar:
    st.header("ℹ Key Terms")
    with st.expander("📈 Lift", expanded=True):
        st.write("""
        **Lift** measures the percentage increase in units sold during a promotional period compared to the closest preceding non-promotional period.
        
        Formula:
        `Lift = (Promo Units / Previous Units) - 1`
        Example: If units sold go from 100 → 125, Lift = **25%**
        """)
    with st.expander("💰 Profit Difference", expanded=True):
        st.write("""
        **Profit Difference** compares the total profit during a promo period versus the preceding regular price period.

        Formula:
        `Profit Difference = Promo Profit - Previous Profit`
        Example: If profit was $500 before promo and $700 during promo, Profit Difference = **$200**
        """)
    with st.expander("📊 ROI", expanded=True):
        st.write("""
        **ROI (Promo ROI)** measures the return on promotional spend.
        
        Formula:
        `ROI = (Incremental Profit / Promo Spend)`
        Example: If incremental profit is $200 and promo spend is $100, ROI = **2.0x**
        """)


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


# Quadrant labels
quadrant_labels = pd.DataFrame([
    {"x": x_max, "y": y_max, "label": "⭐ Star", "recommendation": "Maintain pricing & replicate success"},
    {"x": x_min, "y": y_min, "label": "⚠ Risk", "recommendation": "Review pricing or discontinue"},
    {"x": x_min, "y": y_max, "label": "High Lift but Inefficient", "recommendation": "Optimize cost or price"},
    {"x": x_max, "y": y_min, "label": "Efficient but Low Lift", "recommendation": "Consider targeted promotions"},
])

# Background boxes for labels
label_bg = alt.Chart(quadrant_labels).mark_rect(
    color="black",
    opacity=0.6
).encode(
    x=alt.X("x:Q", scale=alt.Scale(domain=[x_min, x_max])),
    y=alt.Y("y:Q", scale=alt.Scale(domain=[y_min, y_max])),
    x2=alt.X2("x:Q"),
    y2=alt.Y2("y:Q")
).properties(width=200, height=40)  # approximate size of background box

# Label text (on top of the background box)
label_text = alt.Chart(quadrant_labels).mark_text(
    align="left",
    baseline="bottom",
    fontSize=16,
    fontWeight="bold",
    color="white",
    dx=5,  # padding inside background box
    dy=-2
).encode(
    x="x:Q",
    y="y:Q",
    text="label:N"
)

# Recommendation text (below label text)
recommendation_text = alt.Chart(quadrant_labels).mark_text(
    align="left",
    baseline="top",
    fontSize=12,
    color="lightgray",
    dx=5,
    dy=14
).encode(
    x="x:Q",
    y="y:Q",
    text="recommendation:N"
)

# Crosshair lines
mid_x = (x_min + x_max) / 2
mid_y = (y_min + y_max) / 2

vertical_line = alt.Chart(pd.DataFrame({'x': [mid_x]})).mark_rule(color="gray", strokeDash=[5, 5], opacity=0.5).encode(x='x:Q')
horizontal_line = alt.Chart(pd.DataFrame({'y': [mid_y]})).mark_rule(color="gray", strokeDash=[5, 5], opacity=0.5).encode(y='y:Q')

# Final chart (set explicit width and height)
final_chart = (scatter + label_bg + label_text + recommendation_text + vertical_line + horizontal_line).properties(
    width="container",
    height=500  # <-- Explicit height fixes the squashed issue
)

st.altair_chart(final_chart, use_container_width=True)


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

# Required columns in order
required_columns = [
    "upc",
    "Long_Desc",
    "sale_period",
    "promo_start",
    "promo_end",
    "promo_length",
    "promo_revenue",
    "preceding_non_promo_revenue",
    "lift",
    "promo_profit",
    "preceding_non_promo_profit",
    "profit_difference"
]

if not item_promos.empty:
    # Filter and reorder
    item_promos_display = item_promos[[col for col in required_columns if col in item_promos.columns]].copy()

    # Format numeric columns (keep numeric for styling)
    currency_columns = [
        "promo_revenue",
        "preceding_non_promo_revenue",
        "promo_profit",
        "preceding_non_promo_profit",
        "profit_difference"
    ]

    for col in currency_columns:
        if col in item_promos_display.columns:
            item_promos_display[col] = item_promos_display[col].astype(float)

    if "lift" in item_promos_display.columns:
        item_promos_display["lift"] = item_promos_display["lift"].astype(float)

    # Define styling function for profit_difference
    def highlight_profit(val):
        color = "red" if val < 0 else "green"
        return f"color: {color}; font-weight: bold"

    # Apply styling
    styled_df = (
        item_promos_display.style
        .format({
            "promo_revenue": "${:,.2f}",
            "preceding_non_promo_revenue": "${:,.2f}",
            "promo_profit": "${:,.2f}",
            "preceding_non_promo_profit": "${:,.2f}",
            "profit_difference": "${:,.2f}",
            "lift": "{:.1f}x"
        })
        .applymap(highlight_profit, subset=["profit_difference"])
    )

    st.dataframe(styled_df)
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
