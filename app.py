"""Streamlit interface for comparing shared-services staffing plans."""

import pandas as pd
import plotly.express as px
import streamlit as st

from model import DAYS, DEFAULT_PLANS, StaffingPlan, meets_targets, recommend, simulate


PROJECT_URL = "https://github.com/Vikrantthenge/capacity-backlog-planner"
POWER_BI_PDF_URL = f"{PROJECT_URL}/blob/main/Capacity_Backlog_Planner.pdf"
POWER_BI_PBIX_URL = (
    "https://raw.githubusercontent.com/Vikrantthenge/capacity-backlog-planner/main/Capacity_Backlog_Planner.pbix"
)


st.set_page_config(page_title="Capacity & Backlog Planner", layout="wide")
st.markdown(
    """
    <style>
    .capacity-hero {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 1.25rem 2rem;
        padding: clamp(1.25rem, 3vw, 2.5rem);
        border: 1px solid #356681;
        border-radius: 18px;
        background:
            radial-gradient(ellipse at top right, #2d6177 0%, transparent 55%),
            linear-gradient(120deg, #112039 12%, #163b54 100%);
        box-shadow: 0 10px 30px rgba(13, 33, 55, 0.16);
    }
    .capacity-hero__intro {
        flex: 1 1 28rem;
        min-width: 0;
    }
    .capacity-hero h1 {
        margin: 0;
        padding: 0;
        color: #ffffff;
        font-size: clamp(1.85rem, 3.5vw, 3.15rem);
        font-weight: 750;
        line-height: 1.12;
        letter-spacing: -0.035em;
    }
    .capacity-hero__intro p {
        max-width: 37rem;
        margin: 0.8rem 0 0;
        color: #d7e7f0;
        font-size: 1.02rem;
        line-height: 1.55;
    }
    .capacity-hero__horizon {
        flex: 0 1 auto;
        padding: 0.9rem 1.1rem;
        border: 1px solid #7093a7;
        border-left: 3px solid #7fe2ce;
        border-radius: 10px;
        background: #102a40;
    }
    .capacity-hero__horizon span,
    .capacity-hero__horizon strong {
        display: block;
    }
    .capacity-hero__label {
        color: #9ce9d9;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }
    .capacity-hero__horizon strong {
        margin: 0.25rem 0 0.15rem;
        color: #ffffff;
        font-size: 1.12rem;
    }
    .capacity-hero__note {
        color: #d7e7f0;
        font-size: 0.82rem;
    }
    </style>
    <section class="capacity-hero" aria-labelledby="capacity-hero-title">
        <div class="capacity-hero__intro">
            <h1 id="capacity-hero-title">Capacity &amp; Backlog Planner</h1>
            <p>Compare staffing and overtime plans to see which meets your backlog targets at the lowest cost.</p>
        </div>
        <div class="capacity-hero__horizon">
            <span class="capacity-hero__label">Planning horizon</span>
            <strong>Monday–Friday</strong>
            <span class="capacity-hero__note">Simulated starting inputs</span>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Planning assumptions")
    productivity = st.number_input("Requests per paid hour", min_value=0.0, value=5.0, step=0.25)
    regular_rate = st.number_input("Regular hourly cost (₹)", min_value=0.0, value=350.0, step=10.0)
    overtime_rate = st.number_input("Overtime hourly cost (₹)", min_value=0.0, value=525.0, step=10.0)
    opening_backlog = st.number_input("Requests carried into Monday", min_value=0, value=0, step=1)
    st.header("Backlog targets")
    friday_limit = st.number_input("Maximum open requests on Friday evening", min_value=0, value=0, step=1)
    cap_daily = st.checkbox("Set a maximum daily closing backlog")
    peak_limit = None
    if cap_daily:
        peak_limit = st.number_input("Maximum open requests at any day end", min_value=0, value=30, step=1)

st.subheader("Daily demand")
demand = []
for column, day, sample in zip(st.columns(5), DAYS, (350, 280, 230, 195, 175)):
    with column:
        demand.append(st.number_input(day, min_value=0, value=sample, step=5, key=f"demand_{day}"))

with st.expander("Edit staffing hours by plan"):
    st.caption("Enter total team hours for each day. For example, six staff working eight hours each equals 48 team hours.")
    staffing = pd.DataFrame(
        {
            "Plan": plan.name,
            "Day": day,
            "Regular hours": float(plan.regular_hours[index]),
            "Overtime hours": float(plan.overtime_hours[index]),
        }
        for plan in DEFAULT_PLANS
        for index, day in enumerate(DAYS)
    )
    edited = st.data_editor(
        staffing,
        key="staffing_hours",
        hide_index=True,
        disabled=["Plan", "Day"],
        column_config={
            "Regular hours": st.column_config.NumberColumn(min_value=0, required=True, step=0.5),
            "Overtime hours": st.column_config.NumberColumn(min_value=0, required=True, step=0.5),
        },
    )

if edited[["Regular hours", "Overtime hours"]].isna().any().any():
    st.error("Enter regular and overtime hours for every day. Enter 0 when no hours are planned.")
    st.stop()

plans = []
for default in DEFAULT_PLANS:
    schedule = edited.loc[edited["Plan"] == default.name].set_index("Day").loc[list(DAYS)]
    plans.append(StaffingPlan(default.name, schedule["Regular hours"].tolist(), schedule["Overtime hours"].tolist()))

try:
    daily, weekly = simulate(demand, plans, productivity, regular_rate, overtime_rate, opening_backlog)
except ValueError as error:
    st.error(str(error))
    st.stop()

detail = pd.DataFrame(daily)
summary = pd.DataFrame(weekly)
best = recommend(weekly, friday_limit, peak_limit)
current = weekly[0]

st.divider()
st.subheader("Staffing decision")
st.caption(f"{sum(demand):,} incoming requests this week · {opening_backlog:,} carried forward")

if best is None:
    st.warning("None of the entered plans reaches the backlog targets. Adjust staffing hours or review the targets.")
else:
    st.markdown(f"**Lowest-cost plan that meets the targets** · {best['Plan']}")
    cost_change = best["Labour cost (INR)"] - current["Labour cost (INR)"]
    if cost_change:
        direction = "above" if cost_change > 0 else "below"
        st.caption(f"₹{abs(cost_change):,.0f} {direction} current staffing for the week.")
    cards = st.columns(4)
    cards[0].metric("Completed", f"{best['Completed']:,}")
    cards[1].metric("Friday backlog", f"{best['Friday backlog']:,}")
    cards[2].metric("Peak closing backlog", f"{best['Peak backlog']:,}")
    cards[3].metric("Weekly labour cost", f"₹{best['Labour cost (INR)']:,.0f}")

compare_tab, detail_tab, method_tab = st.tabs(["Plan comparison", "Daily detail", "Model assumptions"])

with compare_tab:
    comparison = summary.assign(
        **{"Meets targets": [
            "Yes" if meets_targets(row, friday_limit, peak_limit) else "No"
            for row in weekly
        ]}
    )
    st.dataframe(
        comparison[[
            "Plan", "Completed", "Peak backlog", "Friday backlog", "Overtime hours",
            "Labour cost (INR)", "Cost per completed request (INR)", "Meets targets",
        ]],
        hide_index=True,
        column_config={
            "Labour cost (INR)": st.column_config.NumberColumn("Weekly cost (₹)", format="₹ %.0f"),
            "Cost per completed request (INR)": st.column_config.NumberColumn("Cost / completion (₹)", format="₹ %.2f"),
        },
    )
    chart = px.line(
        detail, x="Day", y="Closing backlog", color="Plan", markers=True,
        category_orders={"Day": list(DAYS)},
        title="Requests still open at the end of each day",
        labels={"Closing backlog": "Open requests", "Day": ""},
        color_discrete_sequence=["#536B83", "#167D7F", "#8F5310", "#4264D0"],
    )
    chart.update_layout(legend_title_text="", hovermode="x unified")
    chart.update_yaxes(rangemode="tozero")
    st.plotly_chart(chart, config={"displayModeBar": False})
    st.download_button("Download weekly comparison", comparison.to_csv(index=False), "weekly_comparison.csv", "text/csv")

with detail_tab:
    chosen = st.selectbox("Staffing plan", [plan.name for plan in plans])
    st.dataframe(detail.loc[detail["Plan"] == chosen].drop(columns=["Plan", "Day order"]), hide_index=True)
    st.download_button("Download daily data for all plans", detail.to_csv(index=False), "daily_plan_data.csv", "text/csv")

with method_tab:
    st.markdown(
        """
        - **Work available** is opening backlog plus new requests. Unfinished work carries into the next day.
        - **Daily capacity** is total team hours × requests per paid hour, rounded down to whole requests. Completions are limited by work available.
        - **Labour cost** is regular hours × regular rate plus overtime hours × overtime rate.
        - **Plan selection** uses the lowest labour cost among the entered plans that meet the backlog targets. Ties favour a lower Friday backlog, then a lower peak daily backlog.
        - **Scope** covers daily totals at one productivity rate. Request-level SLA reporting needs timestamps. Validate staffing feasibility, skill coverage and shift rules before changing a real roster.
        """
    )

st.divider()
st.subheader("Power BI report")
st.caption("The report shows the original simulated week and compares all four staffing plans.")
pdf_column, pbix_column = st.columns(2)
with pdf_column:
    st.link_button("View Power BI report (PDF)", POWER_BI_PDF_URL)
with pbix_column:
    st.link_button("Download Power BI file (.pbix)", POWER_BI_PBIX_URL)

st.divider()
st.markdown(
    """
    <footer aria-label="Developer and contact links" style="text-align:center; padding:0.4rem 0 1.25rem;">
      <p style="margin:0 0 0.7rem;"><strong>Developed by Vikrant Thenge</strong></p>
      <div style="display:flex; flex-wrap:wrap; justify-content:center; gap:0.55rem;">
        <a href="mailto:vikrantthenge@outlook.com"
           style="background:#0066B3; color:white; text-decoration:none; border-radius:6px; padding:0.35rem 0.8rem;">Email</a>
        <a href="https://github.com/Vikrantthenge" target="_blank" rel="noopener noreferrer"
           style="background:#24292F; color:white; text-decoration:none; border-radius:6px; padding:0.35rem 0.8rem;">GitHub</a>
        <a href="https://www.linkedin.com/in/vthenge/" target="_blank" rel="noopener noreferrer"
           style="background:#0A66C2; color:white; text-decoration:none; border-radius:6px; padding:0.35rem 0.8rem;">LinkedIn</a>
      </div>
    </footer>
    """,
    unsafe_allow_html=True,
)
