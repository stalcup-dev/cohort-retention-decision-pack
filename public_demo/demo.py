from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
DATA_PATH = ROOT / "demo_data.csv"
PLOT_PATH = ROOT / "demo_output.png"
SUMMARY_PATH = ROOT / "demo_summary.csv"


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    df["logo_retention"] = df["customers_active"] / df["customers_start"]
    df["net_retention_proxy"] = df["net_revenue_proxy_total"] / df["gross_m0"]

    m2 = (
        df[df["months_since_first"] == 2]
        .loc[:, ["cohort_month", "logo_retention", "net_retention_proxy"]]
        .rename(
            columns={
                "logo_retention": "m2_logo_retention",
                "net_retention_proxy": "m2_net_retention_proxy",
            }
        )
        .sort_values("cohort_month", kind="stable")
        .reset_index(drop=True)
    )
    m2.to_csv(SUMMARY_PATH, index=False)

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    for cohort, cohort_df in df.groupby("cohort_month"):
        cohort_df = cohort_df.sort_values("months_since_first", kind="stable")
        ax.plot(
            cohort_df["months_since_first"],
            cohort_df["logo_retention"],
            marker="o",
            label=str(cohort),
        )
    ax.set_title("Demo Cohort Logo Retention")
    ax.set_xlabel("months_since_first")
    ax.set_ylabel("logo_retention")
    ax.set_ylim(0.0, 1.05)
    ax.legend(title="cohort_month")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(PLOT_PATH, dpi=150)
    plt.close(fig)

    plot_rel = PLOT_PATH.relative_to(REPO_ROOT).as_posix()
    summary_rel = SUMMARY_PATH.relative_to(REPO_ROOT).as_posix()
    print(f"demo=PASS plot={plot_rel} summary={summary_rel}")


if __name__ == "__main__":
    main()
