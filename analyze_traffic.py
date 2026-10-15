"""Summarize synthetic assessment traffic; do not infer causes."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from validate_data import CATEGORIES, DEFAULT_INPUT, load_traffic

DEFAULT_OUTPUT = Path(__file__).resolve().parent / "outputs" / "synthetic_traffic"


def summarize_traffic(data):
    """Calculate monthly totals and category summaries from validated data."""
    monthly = data.copy()
    monthly["total_traffic"] = monthly[CATEGORIES].sum(axis=1)
    previous = monthly["total_traffic"].shift(1).replace(0, float("nan"))
    monthly["traffic_mom_pct"] = (monthly["total_traffic"] / previous - 1) * 100
    totals = monthly[CATEGORIES].sum()
    start = monthly[CATEGORIES].iloc[0].replace(0, float("nan"))
    growth = (monthly[CATEGORIES].iloc[-1] / start - 1) * 100
    overall = totals.sum()
    categories = pd.DataFrame({
        "total_traffic": totals,
        "share_pct": totals / (overall if overall else float("nan")) * 100,
        "first_to_last_pct": growth,
    }).rename_axis("category").reset_index()
    return monthly, categories.sort_values("total_traffic", ascending=False)


def save_outputs(monthly, categories, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    monthly.to_csv(output_dir / "monthly_summary.csv", index=False, float_format="%.2f")
    categories.to_csv(output_dir / "category_summary.csv", index=False, float_format="%.2f")

    fig, axes = plt.subplots(3, 2, figsize=(11, 9), sharex=True)
    for ax, category in zip(axes.flat, CATEGORIES):
        ax.plot(monthly.month, monthly[category], color='black', marker='o', linewidth=1.5)
        ax.set(title=category, ylabel='Reported sessions')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(axis='y', color='0.85', linewidth=0.5)
    fig.suptitle('Synthetic assessment: reported sessions by section (individual y scales)')
    fig.tight_layout()
    fig.savefig(output_dir / 'traffic_by_month.png', dpi=150)
    plt.close(fig)

    peak = monthly.loc[monthly["total_traffic"].idxmax()]
    summary = [
        "Synthetic assessment traffic: descriptive summary",
        f"Period: {monthly.month.iloc[0]} to {monthly.month.iloc[-1]} ({len(monthly)} months)",
        f"Total category traffic: {monthly.total_traffic.sum():,.0f}",
        f"Total newsletter signups (separate): {monthly.newsletter_signups.sum():,.0f}",
        f"Highest traffic month: {peak['month']} ({peak['total_traffic']:,.0f})",
        "Category changes from first to last month:",
    ]
    for row in categories.itertuples(index=False):
        change = "undefined (zero starting count)" if pd.isna(row.first_to_last_pct) else f"{row.first_to_last_pct:+.2f}%"
        summary.append(f"  {row.category}: {change}")
    summary += [
        "", "These are synthetic counts, not verified website visitors.",
        "Category totals assume categories are additive. Signups are excluded.",
        "Monthly changes describe patterns; they do not establish causes.",
        "No public article records are joined to these data.",
    ]
    (output_dir / "summary.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")


def main():
    from investigate_traffic import run, DEFAULT_OUTPUT as INVESTIGATION_OUTPUT, DEFAULT_ARTICLES
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--investigation-dir", type=Path, default=INVESTIGATION_OUTPUT)
    parser.add_argument("--articles", type=Path, default=DEFAULT_ARTICLES)
    args = parser.parse_args()
    try:
        monthly, categories = summarize_traffic(load_traffic(args.input))
        save_outputs(monthly, categories, args.output_dir)
        run(args.input, args.investigation_dir, args.articles)
    except (OSError, ValueError, pd.errors.ParserError) as error:
        parser.exit(1, f"Analysis failed: {error}\n")
    print(f"Saved traffic summaries and charts to {args.output_dir}")


if __name__ == "__main__":
    main()
