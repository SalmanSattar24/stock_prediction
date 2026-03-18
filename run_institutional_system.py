"""CLI entrypoint for the institutional swing system."""

import argparse
from pathlib import Path

import pandas as pd

from institutional_trader import InstitutionalSwingSystem


def _write_minimal_report(output_path: str, reason: str) -> None:
    path = Path(output_path)
    content = (
        "TOP SWING STOCK PICKS (ANALYSIS ONLY)\n"
        + "=" * 90
        + "\n"
        + "Execution Mode: NO ORDERS PLACED (suggestions only)\n"
        + f"Status: {reason}\n"
        + "=" * 90
        + "\n\n"
        + "No qualifying picks found for current run.\n"
        + "Try rerunning with smaller --universe-size or lower --min-prob.\n"
    )
    path.write_text(content, encoding="utf-8")


def _ensure_non_empty_report(output_path: str, reason: str) -> None:
    path = Path(output_path)
    if not path.exists() or path.stat().st_size == 0:
        _write_minimal_report(output_path, reason)


def main():
    parser = argparse.ArgumentParser(description="Institutional-style free swing trading pipeline")
    parser.add_argument("--execute", action="store_true", help="Execute orders on Alpaca paper (default is dry run)")
    parser.add_argument("--universe-size", type=int, default=300, help="Number of tickers from universe to process")
    parser.add_argument("--min-prob", type=float, default=0.57, help="Minimum probability threshold for ranking")
    parser.add_argument("--top-picks", type=int, default=10, help="How many picks to include in text report (5-10)")
    parser.add_argument("--report-file", type=str, default="top_stock_picks.txt", help="Output text file for analysis suggestions")
    args = parser.parse_args()

    system = InstitutionalSwingSystem()
    system.config.universe_size = args.universe_size
    system.config.min_probability = args.min_prob

    try:
        ranked, validation = system.train_and_rank()

        if ranked.empty:
            print("No signals generated from current filters.")
            if not args.execute:
                system.generate_top_picks_report(
                    ranked,
                    top_n=args.top_picks,
                    output_path=args.report_file,
                )
                _ensure_non_empty_report(args.report_file, "No ranked signals generated")
                print(f"Analysis report written to: {args.report_file}")
            return

        print("Top ranked signals:")
        print(ranked.head(20).to_string(index=False))

        if args.execute:
            actions = system.execute_paper_trades(ranked, dry_run=False)
            print("\nExecution plan:")
            print(actions[:10])
        else:
            picks = system.generate_top_picks_report(
                ranked,
                top_n=args.top_picks,
                output_path=args.report_file,
            )
            _ensure_non_empty_report(args.report_file, "Report generated with no qualifying picks")
            print(f"\nAnalysis report written to: {args.report_file}")
            print(f"Picks generated: {len(picks)}")
    except KeyboardInterrupt:
        if not args.execute:
            try:
                system.generate_top_picks_report(
                    pd.DataFrame(),
                    top_n=args.top_picks,
                    output_path=args.report_file,
                )
            except Exception:
                _write_minimal_report(args.report_file, "Run interrupted by user")
            _ensure_non_empty_report(args.report_file, "Run interrupted by user")
            print(f"\nRun interrupted. Fallback report written to: {args.report_file}")
        else:
            print("\nRun interrupted.")
    except Exception as exc:
        if not args.execute:
            try:
                system.generate_top_picks_report(
                    pd.DataFrame(),
                    top_n=args.top_picks,
                    output_path=args.report_file,
                )
            except Exception:
                _write_minimal_report(args.report_file, f"Run failed: {type(exc).__name__}")
            _ensure_non_empty_report(args.report_file, f"Run failed: {type(exc).__name__}")
            print(f"\nRun failed ({type(exc).__name__}). Fallback report written to: {args.report_file}")
        else:
            raise


if __name__ == "__main__":
    main()
