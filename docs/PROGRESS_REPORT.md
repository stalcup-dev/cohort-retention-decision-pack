# Progress Report — Cohort Retention v1.2 (Teaching Edition)

## Status
**Block 1 (pipeline + gates): DONE**  
**Block 2 (story notebook → HTML + decision memo): DONE**  
**Block 3 (Teaching Edition): NOT STARTED (this is the redo request)**

## What’s shipped (current)
- `exports/cohort_retention_story.html` (3 charts, code hidden)
- `docs/DECISION_MEMO_1PAGE.md`
- `docs/QA_CHECKLIST.md`
- `docs/DRIVER_COVERAGE_REPORT.md`
- `data_processed/` outputs + gate receipts (A/B/C)

## Evidence pack (numbers)
- order_lines.csv: 1,067,371
- products.csv: 5,131
- orders.csv: 53,628
- transactions.csv: 53,628
- customers.csv: 5,878
- customer_month_activity.csv: 41,146
- Gate A: 0.0000% non-positive net proxy; trigger NO
- Gate B: 79.70% gross mapped non-Other; 59.08% customers non-Other
- Gate C: material_sensitivity count 0 across 21 families

## Teaching Edition goal (redo request)
Make this project **learnable**:
- Every transformation explained (why, assumptions, pitfalls)
- Code heavily commented, not just “working”
- A teaching notebook that walks step-by-step and prints intermediate checkpoints

## Next work blocks (90-minute chunks)
1) **Docs:** write `docs/TEACHING_GUIDE.md` (concepts + pipeline map + definitions + gates)  
2) **Notebook:** create `notebooks/cohort_retention_teaching.ipynb` (visible code + commentary + checkpoints)  
3) **Exports:** export teaching notebook to HTML with code visible; keep story HTML code-hidden
