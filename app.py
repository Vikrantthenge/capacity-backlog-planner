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
