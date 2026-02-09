import asyncio
from camptrack.utils.geocode import geocode_place

async def ask_for_location():
    while True:
        query = input(">> Enter camp location name: ").strip()

        if not query:
            print("Camp location cannot be empty. Please try again.")
            continue

        results = await geocode_place(query)

        # Network or API failure
        if results is None:
            print("\n⚠️  Unable to reach geocoding service (no internet or API error).")
            print("Type 'm' to enter location manually, or 'r' to retry.")
            choice = input("Your choice: ").strip().lower()
            if choice == 'm':
                return {"name": query, "lat": None, "lon": None}
            else:
                continue  # retry search

        # Valid API call, but no results
        if not results:
            print("\nNo results found.")
            print("Type 's' to search again or 'm' to enter manually.")
            choice = input("Your choice: ").strip().lower()
            if choice == 'm':
                return {"name": query, "lat": None, "lon": None}
            else:
                continue  # search again

        # Show matches
        print("\nPossible matches:")
        for i, r in enumerate(results, start=1):
            print(f"{i}) {r['name']}")

        print("\nOptions:")
        print(" - Enter a number to select a location.")
        print(" - Type 's' to search again.")
        print(" - Type 'm' to enter location manually (skip coordinates).")

        choice = input("Your choice: ").strip().lower()

        if choice == 's':
            continue

        if choice == 'm':
            return {"name": query, "lat": None, "lon": None}

        # Selecting a location
        try:
            index = int(choice) - 1
            selected = results[index]
        except (ValueError, IndexError):
            print("Invalid choice. Try again.")
            continue

        print(f"\nYou selected: {selected['name']}")
        return selected
