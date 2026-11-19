"""Streamlit interface for comparing shared-services staffing plans."""

import pandas as pd
import plotly.express as px
import streamlit as st

from model import DAYS, DEFAULT_PLANS, StaffingPlan, meets_targets, recommend, simulate


st.set_page_config(page_title="Capacity & Backlog Planner", layout="wide")
st.title("Capacity & Backlog Planner")
st.markdown("Compare staffing plans to see what it costs to meet your backlog targets.")
st.caption("Five-day planning model. The initial values are simulated.")

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
