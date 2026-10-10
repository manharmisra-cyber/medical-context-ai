
from medical_context_ai.knowledge.icd_client import ICDClient


def main():
    print("MEDICAL CONTEXT AI - ICD-11 CONNECTION")
    print("=" * 45)

    client = ICDClient()

    print("Authenticating...")
    client.authenticate()
    print("Authentication successful!")

    print("\nSearching ICD-11 for influenza...")
    results = client.search("influenza")

    destinations = results.get("destinationEntities", [])

    print(f"Results returned: {len(destinations)}")

    for item in destinations[:5]:
        print(
            f"  {item.get('title', 'Unknown')}"
            f" | {item.get('id', 'No ID')}"
        )


if __name__ == "__main__":
    main()
