from app import app
from models import db, Item
from faker import Faker

fake = Faker()

with app.app_context():
    db.drop_all()
    db.create_all()

    categories = ['Dairy', 'Bakery', 'Beverages', 'Snacks', 'Frozen', 'Produce']

    # a few real items to start with
    starters = [
        Item(name='Whole Milk', barcode='0041303002742', quantity=50,
             price=2.99, description='Fresh whole milk', category='Dairy'),
        Item(name='White Bread', barcode='0041220576707', quantity=30,
             price=1.49, description='Soft white bread', category='Bakery'),
        Item(name='Orange Juice', barcode='0045114119419', quantity=40,
             price=3.49, description='Freshly squeezed', category='Beverages'),
    ]

    # pad with fake data
    fakes = [
        Item(
            name=f"{fake.word().capitalize()} {fake.word().capitalize()}",
            barcode=fake.ean13(),
            quantity=fake.random_int(min=5, max=100),
            price=round(fake.random_number(digits=2) / 10 + 1.0, 2),
            description=fake.sentence(),
            category=fake.random_element(categories)
        )
        for _ in range(7)
    ]

    db.session.add_all(starters + fakes)
    db.session.commit()
    print(f"Done — seeded {len(starters) + len(fakes)} items")