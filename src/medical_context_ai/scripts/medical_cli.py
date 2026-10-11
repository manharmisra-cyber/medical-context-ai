
from medical_context_ai.scripts.disease_lookup import run_disease_lookup
from medical_context_ai.scripts.symptom_lookup import run_symptom_lookup


def main():
    while True:
        print("\n" + "=" * 45)
        print("         MEDICAL CONTEXT AI")
        print("              STAGE 2.5")
        print("=" * 45)

        print("1. Disease to symptoms and information")
        print("2. Symptoms/information to diseases")
        print("0. Exit")

        choice = input("\nSelect option: ").strip()

        if choice == "1":
            run_disease_lookup()

        elif choice == "2":
            run_symptom_lookup()

        elif choice == "0":
            print("\nExiting Medical Context AI.")
            break

        else:
            print("\nInvalid option. Enter 0, 1, or 2.")


if __name__ == "__main__":
    main()
