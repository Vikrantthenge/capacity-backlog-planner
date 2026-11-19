# Capacity & Backlog Planner

An interactive staffing simulator for operations teams that need to clear a backlog by Friday while managing labour costs. Adjust demand, staffing hours, and backlog targets to compare four plans in Streamlit.

[View the Power BI report (PDF)](Capacity_Backlog_Planner.pdf) · [Download the Power BI file (.pbix)](https://raw.githubusercontent.com/Vikrantthenge/capacity-backlog-planner/main/Capacity_Backlog_Planner.pbix)

## Case study

A shared-services team expects **1,230 requests over five working days** and wants to finish Friday with **zero open requests**. The app compares the current roster with three alternatives.

| Staffing plan | Requests completed | Peak end-of-day backlog | Friday backlog | Weekly labour cost |
|---|---:|---:|---:|---:|
| Current staffing | 1,200 | 150 | 30 | ₹84,000 |
| Move regular hours to busier days | 1,200 | 60 | 30 | ₹84,000 |
| Add 24 hours of overtime | 1,230 | 30 | 0 | ₹96,600 |
| **Move regular hours and add 6 hours of Monday overtime** | **1,230** | **30** | **0** | **₹87,150** |

**Recommendation.** Move regular hours to busier days and add six overtime hours on Monday. It was the lowest-cost option that met the Friday target among the four plans tested. It cost **₹9,450 less** than the 24-hour overtime option and **₹3,150 more** than the current roster, while clearing the 30 requests the current roster would leave open.

The figures come from simulated inputs. A real staffing decision would require historical demand and productivity data, plus a check that the proposed hours fit staff availability and shift rules.

## Try the simulator

1. Open **Plan comparison** and compare the Friday backlog and weekly cost for each plan.
2. Change Monday demand from **350 to 320**. The plan that shifts regular hours now clears the Friday backlog for **₹84,000**.
3. Restore Monday demand to **350**, enable the daily closing backlog limit, and set it to **20**. None of the four entered plans meets both backlog targets.

The app also lets you change regular and overtime hours, hourly labour costs, requests completed per paid hour, and the work carried into Monday. Use **Daily detail** to see when the backlog builds and export the daily or weekly comparison as a CSV.

## How the model works

- **Available work** equals the opening backlog plus new requests. Unfinished requests carry into the next day.
- **Daily capacity** equals paid hours multiplied by requests completed per paid hour, rounded down. The app uses a single productivity rate across plans and days.
- **Labour cost** equals regular hours multiplied by the regular rate plus overtime hours multiplied by the overtime rate.
- **Recommendation** selects the lowest-cost entered plan that meets the backlog targets. If no plan qualifies, the app shows that result so the user can adjust the inputs.

The model works with daily totals. Measuring request-level turnaround or service-level compliance requires timestamps for individual requests.

## Run locally

Clone or download the repository, then open a terminal in the folder containing `app.py`. The app was tested with Python 3.12.

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Project files

| File | Purpose |
|---|---|
| [`app.py`](app.py) | Streamlit interface and Plotly backlog chart |
| [`model.py`](model.py) | Capacity, backlog, cost, and plan selection logic |
| [`daily_plan_data.csv`](sample_data/daily_plan_data.csv) | Daily results for each plan |
| [`weekly_comparison.csv`](sample_data/weekly_comparison.csv) | Weekly results for the four plans |

The Power BI report shows the original simulated week. The Streamlit app recalculates the comparison when you change the inputs.

Developed by **[Vikrant Thenge](https://www.linkedin.com/in/vthenge/)**.
