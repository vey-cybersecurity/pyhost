import json
from flask import Flask, render_template, request, redirect, url_for, make_response
from products import PRODUCTS, get_product_id

app = Flask(__name__)

def get_cart_data():
    cart_list = request.cookies.get('cart_list')
    try:
        cart_list = json.loads(cart_list) if cart_list else []
    except Exception:
        cart_list = []
    
    cart_items = []
    cart_total = 0.0
    for item in cart_list:
        product_data = {
            'id': item.get('id'),
            'title': item.get('title'),
            'price': float(item.get('price', 0)),
            'image': item.get('image'),
            'category': item.get('category'),
            'description': item.get('description')
        }
        quantity = int(item.get('qty', 1))
        cart_items.append({
            'product': product_data,
            'quantity': quantity
        })
        cart_total += product_data['price'] * quantity
        
    return cart_items, cart_total

@app.route('/')
def index():
    for item in PRODUCTS:
        print(item['title'])

    cart_items, _ = get_cart_data()
    return render_template('index.html', products=PRODUCTS, cart_items=cart_items)

@app.route('/products')
def products():
    cart_items, _ = get_cart_data()
    return render_template('products.html', products=PRODUCTS, cart_items=cart_items)

@app.route('/product/<product_name>')
def product_detail(product_name):
    from products import get_product_title, get_product_category
    product = get_product_title(product_name)
    if product is None:
        return "Product not found", 404
    related_products = get_product_category(product['category'])
    # Exclude current product from related products
    related_products = [p for p in related_products if p['id'] != product['id']]
    cart_items, _ = get_cart_data()
    return render_template('product_detail.html', product=product, related_products=related_products, cart_items=cart_items)

@app.route('/add_to_cart', methods=['POST', 'GET'])
def add_to_cart():
    product_id = request.args.get("product_id")
    qty = request.form.get("quantity", 1, type=int)
    if request.method == 'GET':
        qty = request.args.get("qty", 1, type=int)
        
    return redirect(url_for('cart', product_id=product_id, qty=qty))

@app.route('/cart')
def cart():
    product_id = request.args.get("product_id")
    qty = request.args.get("qty", 1, type=int)
    
    cart_list = request.cookies.get('cart_list')
    try:
        cart_list = json.loads(cart_list) if cart_list else []
    except Exception:
        cart_list = []
    
    if product_id:
        product = get_product_id(product_id)
        if product:
            found = False
            for item in cart_list:
                if str(item['id']) == str(product_id):
                    item['qty'] += qty
                    found = True
                    break
            
            cart_list = [item for item in cart_list if item['qty'] > 0]
            
            if not found and qty > 0:
                cart_list.append(
                    {
                        "id" : product['id'],
                        "title" : product['title'],
                        "qty" : qty,
                        "price" : product['price'],
                        "category" : product['category'],
                        "image" : product['image'],
                        "description" : product['description'],
                    }
                )

            resp = redirect(url_for('cart'))
            resp.set_cookie('cart_list', json.dumps(cart_list))
            return resp

    cart_items, cart_total = get_cart_data()
    return render_template("cart.html", cart_items=cart_items, cart_total=cart_total)

@app.route('/cart/remove')
def cart_remove():
    product_id = request.args.get("product_id")
    cart_list = request.cookies.get('cart_list')
    try:
        cart_list = json.loads(cart_list) if cart_list else []
    except Exception:
        cart_list = []
    
    if product_id:
        cart_list = [item for item in cart_list if str(item['id']) != str(product_id)]
        resp = redirect(url_for('cart'))
        resp.set_cookie('cart_list', json.dumps(cart_list))
        return resp
        
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart_list = request.cookies.get('cart_list')
    cart_list = json.loads(cart_list) if cart_list else []

    # telegram BOT
    if request.method == 'POST':
        # Telegram Bot Credentials - Replace these with your actual keys
        TELEGRAM_BOT_TOKEN = "8210831643:AAF7KbzQGGPJhBWYGdZXEF3h20Dyubjr4yI"
        TELEGRAM_CHAT_ID = "-1003588022931"

        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        address = request.form.get('address')
        city = request.form.get('city')
        zip_code = request.form.get('zip')

        if cart_list:
            subtotal = sum(item['price'] * item['qty'] for item in cart_list)
            shipping = 15.00 if subtotal > 0 else 0
            tax = subtotal * 0.08
            total = subtotal + shipping + tax

            msg = f"🛒 *New Order Received!*\n\n"
            msg += f"👤 *Customer:* {first_name} {last_name}\n"
            msg += f"📍 *Address:* {address}, {city}, {zip_code}\n\n"
            msg += f"🛍️ *Items:*\n"
            for item in cart_list:
                msg += f"- {item['title']} (x{item['qty']}): ${item['price'] * item['qty']:.2f}\n"
            
            msg += f"\n💰 *Subtotal:* ${subtotal:.2f}\n"
            msg += f"🚚 *Shipping:* ${shipping:.2f}\n"
            msg += f"🧾 *Tax:* ${tax:.2f}\n"
            msg += f"💳 *Total:* ${total:.2f}\n"

            if TELEGRAM_BOT_TOKEN != "YOUR_TELEGRAM_BOT_TOKEN" and TELEGRAM_CHAT_ID != "YOUR_TELEGRAM_CHAT_ID":
                import urllib.request
                import json as json_lib
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                payload = {
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": msg,
                    "parse_mode": "Markdown"
                }
                try:
                    req = urllib.request.Request(url, data=json_lib.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
                    urllib.request.urlopen(req)
                except Exception as e:
                    print(f"Error sending Telegram message: {e}")

        from flask import redirect, url_for
        resp = make_response(redirect(url_for('index')))
        resp.set_cookie('cart_list', '', expires=0)
        return resp

    return render_template('checkout.html', cart_list=cart_list)

@app.route('/login')
def login():
    cart_items, _ = get_cart_data()
    return render_template('login.html', cart_items=cart_items)

@app.route('/register')
def register():
    cart_items, _ = get_cart_data()
    return render_template('register.html', cart_items=cart_items)

if __name__ == '__main__':
    app.run(debug=True)
