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

# Function to classify items for highlight
def classify_item(lift, profit_diff):
    if lift >= 1.2 and profit_diff > 0:
        return "⭐ Star"
    elif lift < 1.2 and profit_diff < 0:
        return "⚠ Risk"
    elif lift >= 1.2 and profit_diff < 0:
        return "📉 High Lift but Inefficient"
    else:
        return "💡 Efficient but Low Lift"

# Create highlight items from filtered_df
highlight_items = []
if not filtered_df.empty:
    # Pick top 2 stars and top 2 risks (if available)
    stars = filtered_df[(filtered_df["avg_lift"] >= 1.2) & (filtered_df["avg_profit"] > 0)].nlargest(2, "avg_profit")
    risks = filtered_df[(filtered_df["avg_lift"] < 1.2) & (filtered_df["avg_profit"] < 0)].nsmallest(2, "avg_profit")

    highlight_items = pd.concat([stars, risks]).to_dict("records")

# Display highlight section
if highlight_items:
    st.markdown("### 🔍 Highlighted Items")
    for item in highlight_items:
        classification = classify_item(item["avg_lift"], item["avg_profit"])
        st.markdown(
            f"""
            <div style="
                background-color: #111;
                padding: 8px;
                border-radius: 6px;
                border: 1px solid #333;
                margin-bottom: 6px;
            ">
                <strong style="color: white;">{classification}</strong>
                <span style="color: #ccc;"> — {item['item_name']} | Lift: {item['avg_lift']:.1f}x | Profit Diff: ${item['avg_profit']:,.2f}</span>
            </div>
            """,
            unsafe_allow_html=True
        )








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



# Padding for inside alignment
padding_x = (x_max - x_min) * 0.05
padding_y = (y_max - y_min) * 0.05

quadrant_labels = pd.DataFrame([
    {"x": x_max - padding_x, "y": y_max - padding_y, "label": "⭐ Star", "recommendation": "Maintain pricing & replicate success"},
    {"x": x_min + padding_x, "y": y_min + padding_y, "label": "⚠ Risk", "recommendation": "Review pricing or discontinue"},
    {"x": x_min + padding_x, "y": y_max - padding_y, "label": "High Lift but Inefficient", "recommendation": "Optimize cost or price"},
    {"x": x_max - padding_x, "y": y_min + padding_y, "label": "Efficient but Low Lift", "recommendation": "Consider targeted promotions"},
])

# Label text
label_text = alt.Chart(quadrant_labels).mark_text(
    fontSize=16,
    fontWeight="bold",
    color="white",
    align="center"  # fixed alignment (you can change to 'left' or 'right' if needed)
).encode(
    x="x:Q",
    y="y:Q",
    text="label:N"
)

# Recommendation text
recommendation_text = alt.Chart(quadrant_labels).mark_text(
    fontSize=12,
    color="lightgray",
    dy=14,
    align="center"
).encode(
    x="x:Q",
    y="y:Q",
    text="recommendation:N"
)



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
st.title("Item level recommendations")

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





def classify_overall_recommendation(df):
    """Generate a single recommendation line for an item based on its most recent promo period."""
    if df.empty:
        return None, "No promotions found for this item."

    # Use the most recent promotion period
    latest_promo = df.sort_values("promo_start").iloc[-1]

    lift = latest_promo["lift"]
    profit_diff = latest_promo["profit_difference"]

    if lift >= 1.2 and profit_diff > 0:
        return "⭐ Star", f"This item shows strong performance with {lift:.1f}x lift and a profit gain of ${profit_diff:,.2f}. Keep promoting and consider increasing support."
    elif lift < 1.2 and profit_diff < 0:
        return "⚠ Risk", f"Low lift ({lift:.1f}x) and a profit loss of ${profit_diff:,.2f}. Consider discontinuing promotions."
    elif lift >= 1.2 and profit_diff < 0:
        return "📉 High Lift but Inefficient", f"{lift:.1f}x lift but costs ${profit_diff:,.2f} in profit. Consider reducing discount depth or adjusting price."
    else:
        return "💡 Efficient but Low Lift", f"${profit_diff:,.2f} profit gain but only {lift:.1f}x lift. Consider targeted campaigns to improve sales."


# --- Display Recommendation with Highlight ---
if not item_promos.empty:
    title, text = classify_overall_recommendation(item_promos)

    if title:
        st.markdown(
            f"""
            <div style="
                background-color: #222;
                padding: 15px;
                border-radius: 10px;
                border: 1px solid #444;
                margin-bottom: 15px;
            ">
                <h3 style="color: white; margin-bottom: 5px;">{title}</h3>
                <p style="color: #ccc; margin: 0;">{text}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Display table
    required_columns = [
        "upc", "Long_Desc", "sale_period", "promo_start", "promo_end", 
        "promo_length", "promo_revenue", "preceding_non_promo_revenue", 
        "lift", "promo_profit", "preceding_non_promo_profit", "profit_difference"
    ]

    item_promos_display = item_promos[required_columns].copy()

    currency_columns = [
        "promo_revenue",
        "preceding_non_promo_revenue",
        "promo_profit",
        "preceding_non_promo_profit",
        "profit_difference"
    ]
    for col in currency_columns:
        item_promos_display[col] = item_promos_display[col].astype(float)

    item_promos_display["lift"] = item_promos_display["lift"].astype(float)

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
