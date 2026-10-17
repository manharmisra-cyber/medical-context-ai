"""Manual MONDO name matching; requires downloaded MONDO and SapBERT model."""
import argparse
from pathlib import Path
from medical_context_ai.scripts.medical_data import get_medical_data
from medical_context_ai.terminology.mondo_matcher import MondoDiseaseMatcher


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cores", type=int, default=None, help="CPU threads, default leaves two logical cores free")
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()
    graph, _, _, _ = get_medical_data()
    root = Path(__file__).resolve().parents[3]
    matcher = MondoDiseaseMatcher(graph, cache_dir=root / "data" / "cache", batch_size=args.batch_size, cpu_cores=args.cores)
    print("\nEnter disease names to search (blank to exit).")
    while True:
        query = input("Disease name: ").strip()
        if not query:
            break
        for n, item in enumerate(matcher.search(query), 1):
            print(f"{n}. {item['name']} [{item['mondo_id']}]  similarity={item['similarity']:.3f}")
            print(f"   Matched: {item['matched_phrase']} | {item['status']}")


if __name__ == "__main__":
    main()
