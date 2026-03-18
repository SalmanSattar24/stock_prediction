"""CLI entrypoint for the institutional swing system."""

import argparse

from institutional_trader import InstitutionalSwingSystem


def main():
    parser = argparse.ArgumentParser(description="Institutional-style free swing trading pipeline")
    parser.add_argument("--execute", action="store_true", help="Execute orders on Alpaca paper (default is dry run)")
    parser.add_argument("--universe-size", type=int, default=300, help="Number of tickers from universe to process")
    parser.add_argument("--min-prob", type=float, default=0.57, help="Minimum probability threshold for ranking")
    args = parser.parse_args()

    system = InstitutionalSwingSystem()
    system.config.universe_size = args.universe_size
    system.config.min_probability = args.min_prob

    ranked, validation = system.train_and_rank()

    if ranked.empty:
        print("No signals generated.")
        return

    print("Top ranked signals:")
    print(ranked.head(20).to_string(index=False))

    actions = system.execute_paper_trades(ranked, dry_run=not args.execute)
    print("\nExecution plan:")
    print(actions[:10])


if __name__ == "__main__":
    main()
