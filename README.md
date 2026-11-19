# Capacity & Backlog Planner

A portfolio project by **Vikrant Thenge** for operations managers in shared services, customer support, fulfilment, and other teams that process incoming work.

## What decision does it support?

Weekly volume rises from 1,000 requests to 1,230. Can the team clear all work by Friday? What does each staffing option cost, and how much work waits during the week?

The app compares the current roster, moving regular hours to busier days, adding overtime, and moving regular hours with targeted overtime. Change daily demand, paid hours, productivity, hourly costs, or backlog targets to see the effects on completions and cost. The app identifies the lowest-cost plan that meets the selected targets among the four plans entered.

## Case study

| Entered plan | Requests completed | Peak closing backlog | Friday backlog | Weekly labour cost |
|---|---:|---:|---:|---:|
| Current staffing | 1,200 | 150 | 30 | ₹84,000 |
| Shift regular hours | 1,200 | 60 | 30 | ₹84,000 |
| Add 24 overtime hours | 1,230 | 30 | 0 | ₹96,600 |
| Shift regular hours + six Monday overtime hours | 1,230 | 30 | 0 | ₹87,150 |

**Recommendation.** Move regular hours to the busiest days and add six overtime hours on Monday, subject to staff availability and shift rules. In this simulation, the plan completes all 1,230 requests by Friday for ₹87,150, or ₹9,450 less than the 24-hour overtime option. It costs ₹3,150 more than the existing roster and clears the 30 requests that roster leaves open.

The inputs are synthetic and the savings are a comparison between modeled scenarios. The model carries unfinished work forward each day and assumes a single rate of five completions per paid hour by default. A real pilot would use historical arrivals, completions and staff hours to calibrate the rate and check staffing feasibility. Individual turnaround and SLA performance require request timestamps.

## Run locally

Extract the project and open a terminal in the folder containing `app.py`. Tested with Python 3.12.

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

On Windows, use `py` in place of `python` if needed. To publish on Streamlit Community Cloud, put the project files in a GitHub repository and select `app.py` as the entry point.

## Demo in three minutes

1. Open **Plan comparison**. Explain why two plans miss the Friday deadline even though moving hours reduces the midweek backlog.
2. Change Monday demand from **350 to 320**. Look at how the recommendation changes when the team has 30 fewer requests to process.
3. Restore **350** and set the daily closing backlog target to **20**. The current staffing options need further changes to reach that stricter target.

## Power BI handoff

The `sample_data` folder contains both CSV exports for the initial scenario. You can generate fresh CSVs from the app after editing inputs.

| Import | What each row represents | Suggested visual |
|---|---|---|
| `daily_plan_data.csv` | One workday under one staffing plan | Line chart with Day on the X-axis, Closing backlog on the Y-axis, and Plan as the legend. Sort Day by Day order. |
| `weekly_comparison.csv` | One staffing plan for the whole week | Table by Plan showing Completed, Friday backlog, Labour cost (INR), and Meets targets. |

Each plan represents an alternative for the same week. Compare plans side by side and filter to one plan for headline totals.

## Project files

- `app.py` contains the Streamlit inputs, scenario comparison, charts and downloads.
- `model.py` contains the backlog and cost calculations and the recommendation rule.
- `requirements.txt` lists the Python dependencies.
