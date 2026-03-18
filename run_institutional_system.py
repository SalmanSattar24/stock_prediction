"""CLI entrypoint for the institutional swing system."""

import argparse

from institutional_trader import InstitutionalSwingSystem


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

    ranked, validation = system.train_and_rank()

    if ranked.empty:
        print("No signals generated from current filters.")
        if not args.execute:
            system.generate_top_picks_report(
                ranked,
                top_n=args.top_picks,
                output_path=args.report_file,
            )
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
        print(f"\nAnalysis report written to: {args.report_file}")
        print(f"Picks generated: {len(picks)}")


if __name__ == "__main__":
    main()
