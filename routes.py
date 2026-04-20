from flask import Blueprint, request, jsonify
import requests
from models import db, Item

inventory_bp = Blueprint('inventory', __name__)



def get_product_by_barcode(barcode):
    try:
        res = requests.get(
            f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json",
            timeout=5
        )
        data = res.json()
        if data.get('status') == 1:
            p = data['product']
            return {
                'name': p.get('product_name'),
                'description': p.get('ingredients_text'),
                'category': p.get('categories'),
                'image_url': p.get('image_url')
            }
    except Exception:
        return None
    return None


# search openfoodfacts by product name
def search_products_by_name(name):
    try:
        res = requests.get(
            f"https://world.openfoodfacts.org/cgi/search.pl",
            params={'search_terms': name, 'json': 1, 'page_size': 5},
            timeout=5
        )
        products = res.json().get('products', [])
        return [
            {
                'name': p.get('product_name'),
                'barcode': p.get('code'),
                'category': p.get('categories'),
                'image_url': p.get('image_url')
            }
            for p in products if p.get('product_name')
        ]
    except Exception:
        return []


# get all items — supports search and pagination
@inventory_bp.route('/items', methods=['GET'])
def get_items():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '').strip()

    query = Item.query
    if search:
        query = query.filter(Item.name.ilike(f'%{search}%'))

    results = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'items': [item.to_dict() for item in results.items],
        'total': results.total,
        'pages': results.pages,
        'page': results.page
    }), 200


# get one item by id
@inventory_bp.route('/items/<int:id>', methods=['GET'])
def get_item(id):
    item = Item.query.get(id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    return jsonify(item.to_dict()), 200


# create a new item
@inventory_bp.route('/items', methods=['POST'])
def create_item():
    data = request.get_json()

    if not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400
    if data.get('price') is None:
        return jsonify({'error': 'Price is required'}), 400

    # try to fill in details from openfoodfacts if barcode is given
    extra = get_product_by_barcode(data['barcode']) if data.get('barcode') else None

    item = Item(
        name=data.get('name') or (extra and extra.get('name')),
        barcode=data.get('barcode'),
        quantity=data.get('quantity', 0),
        price=float(data['price']),
        description=data.get('description') or (extra and extra.get('description')),
        category=data.get('category') or (extra and extra.get('category')),
        image_url=data.get('image_url') or (extra and extra.get('image_url'))
    )

    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


# update an item — only change what's sent
@inventory_bp.route('/items/<int:id>', methods=['PATCH'])
def update_item(id):
    item = Item.query.get(id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404

    data = request.get_json()

    for field in ['name', 'quantity', 'price', 'description', 'category', 'image_url']:
        if field in data:
            setattr(item, field, data[field])

    db.session.commit()
    return jsonify(item.to_dict()), 200


# delete an item
@inventory_bp.route('/items/<int:id>', methods=['DELETE'])
def delete_item(id):
    item = Item.query.get(id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': f'{item.name} deleted'}), 200


# look up a barcode on openfoodfacts
@inventory_bp.route('/fetch/barcode/<barcode>', methods=['GET'])
def fetch_by_barcode(barcode):
    product = get_product_by_barcode(barcode)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify(product), 200


# search openfoodfacts by name
@inventory_bp.route('/fetch/search/<name>', methods=['GET'])
def fetch_by_name(name):
    results = search_products_by_name(name)
    if not results:
        return jsonify({'error': 'No products found'}), 404
    return jsonify({'results': results}), 200


# fetch from openfoodfacts and save straight to inventory
@inventory_bp.route('/fetch/add/<barcode>', methods=['POST'])
def fetch_and_add(barcode):
    if Item.query.filter_by(barcode=barcode).first():
        return jsonify({'error': 'Item with this barcode already exists'}), 409

    product = get_product_by_barcode(barcode)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    data = request.get_json() or {}

    item = Item(
        name=product.get('name', 'Unknown'),
        barcode=barcode,
        quantity=data.get('quantity', 0),
        price=float(data.get('price', 0.0)),
        description=product.get('description'),
        category=product.get('category'),
        image_url=product.get('image_url')
    )

    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201
