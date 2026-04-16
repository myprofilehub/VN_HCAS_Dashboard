# AEBAS Attendance Dashboard — Setup Guide

## 1. Install dependencies
```bash
pip install -r requirements.txt
```

## 2. Place your Excel file next to the script
```
aebas_dashboard.py
requirements.txt
Copy_of_AEBAS_Attendance_Report.xlsx   ← same folder
```

If your Excel file has a different name, open `aebas_dashboard.py` and update line 13:
```python
EXCEL_FILE = "your_file_name.xlsx"
```

## 3. Run the dashboard
```bash
streamlit run aebas_dashboard.py
```

This opens the dashboard at http://localhost:8501 in your browser.

## 4. Auto-update behaviour
- The dashboard **checks for file changes every 30 seconds**.
- Simply save your Excel file → the dashboard refreshes automatically with new data.
- You can also click the **🔄 Refresh** button at the top right anytime.
- To change the refresh interval, edit line 14:
  ```python
  REFRESH_SECONDS = 30  # change to e.g. 10 for faster refresh
  ```

## Features
| Feature | Description |
|---|---|
| 📊 KPI cards | Total students, class days, avg attendance, good/low counts |
| 📅 Daily bar chart | Present vs Absent per date |
| 🍩 Distribution donut | Good / Average / Low breakdown |
| 🔍 Filters | Search by name, filter by attendance band, sort options |
| 🟢 Colour-coded table | Green/amber/red rows by attendance status |
| 🌡️ Heatmap | Expandable daily attendance grid per student |
| ⬇️ CSV export | Download filtered data |
| 🔄 Auto-refresh | Picks up Excel saves within 30 seconds |

## Excel format expected
- Sheet names: any (each becomes a tab)
- Columns: `S.No`, `Name`, `Registration ID`, `Mbl Number`, then **date columns** (Excel date format), then `No of days present`, `No of days Absent`, `Total Number of Class Days`, `Attendance Percentage`
- Cell values in date columns: `P` or `p` = Present, `A` or `a` = Absent, `-` = N/A
