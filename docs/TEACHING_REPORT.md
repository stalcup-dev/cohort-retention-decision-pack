# RevOps Teaching Edition — Shopify‑Style Cohort Retention (Online Retail II → Shopify‑shaped)

## Teaching Path
- Start at `docs/TEACHING_HUB.md`.
- Next read `docs/COHORT_DEFENSE_CARD.md` for frozen definitions and gate logic.
- Then use `docs/CHART_TALK_TRACKS.md` and `docs/TEACHING_ANSWER_KEY.md` for interview practice.
- Practice operational execution with `docs/EXPERIMENT_BRIEF_SAMPLE.md` and `docs/WEEK2_READOUT_TEMPLATE.md`.

## What this project is (in one sentence)
Turn messy retail transactions into **Shopify‑style exports**, compute **cohort retention + net‑revenue proxy**, and ship a **decision memo**: *which first product families to prioritize for retention tests*.

## The decision (the point of the work)
**Decision:** Which **first_product_family** buckets should we prioritize for retention experiments (replenishment nudges + returns mitigation) based on **M2 logo retention** and **net retention proxy**.

## What you should open (reviewer flow)
1) `exports/cohort_retention_story.html` — the story (exactly 3 charts, code hidden)  
2) `docs/DECISION_MEMO_1PAGE.md` — the recommendation (1 page)  
3) `docs/QA_CHECKLIST.md` + `docs/DRIVER_COVERAGE_REPORT.md` — evidence and coverage

---

## Part A — Walkthrough of the confusing “Definitions + Chart tables exist…” section

### Why you see “Chart tables exist…”
Your notebook doesn’t plot directly off raw data. It plots off **chart tables** built from `data_processed/customer_month_activity.csv`.

Those chart tables are small, stable “presentation-ready” datasets:
- `chart1_logo_retention_heatmap.csv` → heatmap table
- `chart2_net_proxy_curves.csv` → a few cohorts for line curves
- `chart3_m2_by_family.csv` → one row per family group for the bar chart

### Why the row counts matter
They are a sanity check that the chart tables match the design:

- **Chart 1 rows = 175** → that’s **25 cohorts × 7 months (0..6)**  
- **Chart 2 rows = 21** → that’s **3 cohorts × 7 months (0..6)**  
- **Chart 3 rows = 8** → that’s **8 family groups** (bars)

If those counts are off, something drifted (wrong horizon, missing full grid, extra cohorts, etc.).

### What the definitions mean (plain English)
- **cohort_month**: the month the customer made their *first valid purchase* (Month 0).  
- **months_since_first**: how many months after Month 0 (0..6).  
- **logo retention**: “did they buy again this month?” (binary 0/1).  
- **net_retention_proxy**: a refund-aware revenue proxy over time (directional, not accounting-grade).  
- **first_product_family**: the product family inferred from the customer’s first purchase lines (non‑merch excluded).

---

## Part B — What the pipeline is doing (mental model)

### Step 1) Ingest + preflight (prove we can read the file)
**Goal:** prevent Excel variants from derailing the run.
- Detect the correct sheet
- Map column aliases → canonical names
- Record row_count, null CustomerID rate, date range
- Write receipt: `data_processed/ingest_preflight.json`

### Step 2) Create Shopify‑shaped exports (so the analysis looks “real”)
Outputs under `data_processed/`:
- `order_lines.csv` — line items (SKU, qty, unit_price, gross/net proxy fields, product_family)  
- `products.csv` — sku → product_family mapping (rules-driven)  
- `orders.csv` — order-level aggregates (gross/net proxy, validity flags, is_credit_like)  
- `transactions.csv` — simplified “sale/credit” proxies aligned to orders  
- `customers.csv` — cohort assignment + first_product_family  
- `customer_month_activity.csv` — **full customer×month grid** for months 0..6

### Step 3) Gates (quality + defensibility)
- **Gate A (validity):** “are too many valid purchases net<=0?” → if yes, apply strict rules.  
- **Gate B (mapping coverage):** “how much gross revenue is mapped to a specific family vs Other?”  
- **Gate C (confound check):** compare All vs Retail-only M2 retention by family; flag “material” gaps.

### Step 4) Story artifact (exactly 3 charts)
From chart tables:
1) **Heatmap** — logo retention by cohort_month × months_since_first  
2) **Curves** — net retention proxy over months_since_first (3 cohorts)  
3) **Bars** — M2 logo retention by first_product_family group

### Step 5) Decision memo
Memo pulls:
- Gate receipts (A/B/C)
- Chart3 ranking (top families + spread)
- Directional recommendations + test plan language

---

## Part C — How to interpret the 3 charts (what to look for)

### Chart 1 — Cohort heatmap (logo retention)
**Use it to answer:** Are cohorts trending better/worse over time? Are there seasonality cliffs?
- Month 0 should be ~100% by definition (after exclusions)
- Look for fast decay vs slow decay patterns

### Chart 2 — Net retention proxy curves
**Use it to answer:** Do cohorts “pay back” after month 0, or does net proxy collapse?
- This is directional: returns/credits and cancellations can drag net proxy down
- Denominator is guarded (eligible cohorts only)

### Chart 3 — M2 retention by first family
**Use it to answer:** Which first purchase families are associated with higher repeat at Month 2?
- This is your “where to focus experiments first” chart
- It’s not causal; it’s a prioritization heuristic

---

## Part D — The two places people get lost (and the fix)

### 1) “Net retention proxy” isn’t profit
Fix: treat it as a **refund-aware directional signal**, not accounting truth.

### 2) “first_product_family” can be wrong if NonMerch wins
Fix: ensure NonMerch is excluded from first-family competition (already enforced in v1.2).

---

## Next upgrades (only if you have time)
- Add a short “Why these rules” explanation next to PRODUCT_FAMILY_RULES.csv
- Add a tiny table in the story notebook: top families with (M2 retention, n customers)
