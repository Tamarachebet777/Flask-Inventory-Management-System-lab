import requests

BASE = "http://127.0.0.1:5000"


def show_item(item):
    print(f"""
  [{item['id']}] {item['name']}
  Barcode  : {item.get('barcode') or 'N/A'}
  Category : {item.get('category') or 'N/A'}
  Qty      : {item['quantity']}
  Price    : ${item['price']}
  Desc     : {item.get('description') or 'N/A'}
""")


def view_all():
    search = input("Search by name (Enter to skip): ").strip()
    page = input("Page (default 1): ").strip() or '1'

    params = f"?page={page}"
    if search:
        params += f"&search={search}"

    data = requests.get(f"{BASE}/items{params}").json()
    print(f"\nPage {data['page']} of {data['pages']} — {data['total']} total items")
    for item in data['items']:
        show_item(item)


def view_one():
    id = input("Item ID: ").strip()
    res = requests.get(f"{BASE}/items/{id}")
    show_item(res.json()) if res.status_code == 200 else print("Not found.")


def add_item():
    print("\nTip: enter a barcode to auto-fill from OpenFoodFacts\n")
    barcode = input("Barcode (optional): ").strip()
    prefill = {}

    if barcode:
        res = requests.get(f"{BASE}/fetch/barcode/{barcode}")
        if res.status_code == 200:
            prefill = res.json()
            print(f"Found: {prefill.get('name')} ({prefill.get('category')})")
            if input("Auto-add this? (yes/no): ").strip().lower() == 'yes':
                price = input("Price: ").strip()
                qty = input("Quantity: ").strip()
                res = requests.post(f"{BASE}/fetch/add/{barcode}", json={
                    'price': float(price), 'quantity': int(qty)
                })
                print("Added!" if res.status_code == 201 else res.json())
                if res.status_code == 201:
                    show_item(res.json())
                return

    name = input(f"Name [{prefill.get('name', '')}]: ").strip() or prefill.get('name', '')
    price = input("Price: ").strip()
    qty = input("Quantity: ").strip()
    desc = input(f"Description [{prefill.get('description', '')}]: ").strip() or prefill.get('description', '')
    cat = input(f"Category [{prefill.get('category', '')}]: ").strip() or prefill.get('category', '')

    res = requests.post(f"{BASE}/items", json={
        'name': name, 'barcode': barcode or None,
        'price': float(price), 'quantity': int(qty),
        'description': desc, 'category': cat
    })

    print("Created!" if res.status_code == 201 else f"Error: {res.json()}")
    if res.status_code == 201:
        show_item(res.json())


def edit_item():
    id = input("Item ID to edit: ").strip()
    res = requests.get(f"{BASE}/items/{id}")
    if res.status_code == 404:
        print("Not found.")
        return

    show_item(res.json())
    print("Leave blank to keep current value\n")

    data = {}
    for field in ['name', 'price', 'quantity', 'description', 'category']:
        val = input(f"New {field}: ").strip()
        if val:
            data[field] = float(val) if field in ['price', 'quantity'] else val
            if field == 'quantity':
                data[field] = int(data[field])

    if not data:
        print("No changes.")
        return

    res = requests.patch(f"{BASE}/items/{id}", json=data)
    print("Updated!" if res.status_code == 200 else f"Error: {res.json()}")
    if res.status_code == 200:
        show_item(res.json())


def delete_item():
    id = input("Item ID to delete: ").strip()
    res = requests.get(f"{BASE}/items/{id}")
    if res.status_code == 404:
        print("Not found.")
        return

    show_item(res.json())
    if input("Delete this item? (yes/no): ").strip().lower() != 'yes':
        print("Cancelled.")
        return

    res = requests.delete(f"{BASE}/items/{id}")
    print(res.json().get('message'))


def search_openfoodfacts():
    name = input("Product name to search: ").strip()
    res = requests.get(f"{BASE}/fetch/search/{name}")
    if res.status_code == 404:
        print("Nothing found.")
        return

    results = res.json().get('results', [])
    for i, p in enumerate(results, 1):
        print(f"  {i}. {p['name']} | {p.get('barcode')} | {p.get('category')}")

    pick = input("\nNumber to add to inventory (Enter to skip): ").strip()
    if pick.isdigit() and 1 <= int(pick) <= len(results):
        p = results[int(pick) - 1]
        price = input("Price: ").strip()
        qty = input("Quantity: ").strip()
        res = requests.post(f"{BASE}/items", json={
            'name': p['name'], 'barcode': p.get('barcode'),
            'price': float(price), 'quantity': int(qty),
            'category': p.get('category')
        })
        print("Added!" if res.status_code == 201 else f"Error: {res.json()}")


def menu():
    options = {
        '1': ('View all items', view_all),
        '2': ('View item by ID', view_one),
        '3': ('Add new item', add_item),
        '4': ('Edit item', edit_item),
        '5': ('Delete item', delete_item),
        '6': ('Search OpenFoodFacts by name', search_openfoodfacts),
        '0': ('Exit', None)
    }

    while True:
        print("\n=== Inventory Manager ===")
        for key, (label, _) in options.items():
            print(f"  {key}. {label}")

        choice = input("\nChoose: ").strip()
        if choice == '0':
            print("Bye!")
            break
        elif choice in options:
            options[choice][1]()
        else:
            print("Invalid option.")


if __name__ == '__main__':
    menu()
