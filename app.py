from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pymongo
from bson import ObjectId
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
app.secret_key = "super_secret_mini_gofood_key"
bcrypt = Bcrypt(app)

# --- DATABASE CONNECTION ---
# Replace with your actual string
MONGO_URI = "mongodb+srv://replicantxq_db_user:KLb5ZRn9MVh0MYGG@dinocluster.am5rctu.mongodb.net/?appName=DinoCluster"
client = pymongo.MongoClient(MONGO_URI)
db = client['MiniFood']

# --- TRACKING SIMULATOR ---
# Removed background threading for Vercel (serverless doesn't support long-running threads)
def simulate_orders():
    pass

# --- ROUTES ---

@app.route('/')
def index():
    # Fetch top restaurants and drivers
    restaurants = list(db.restaurants.find().limit(6))
    drivers = list(db.drivers.find())
    
    # Initial load: Filter orders by user if logged in
    query = {"user_id": session['user_id']} if 'user_id' in session else {}
    orders = list(db.orders.find(query).sort("_id", -1).limit(10)) 
    return render_template('index.html', restaurants=restaurants, drivers=drivers, orders=orders)

@app.route('/restaurants')
def list_restaurants():
    all_restaurants = list(db.restaurants.find())
    return render_template('restaurants.html', restaurants=all_restaurants)

@app.route('/restaurant/<id>')
def view_menu(id):
    restaurant = db.restaurants.find_one({"_id": ObjectId(id)})
    if not restaurant:
        return "Restaurant not found", 404
    return render_template('menu.html', restaurant=restaurant)

# --- AUTH ROUTES ---

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        role = request.form.get('role', 'customer')
        
        # Check if user exists
        if db.users.find_one({"email": email}):
            return render_template('signup.html', error="Email already registered")
        
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        db.users.insert_one({
            "name": name,
            "email": email,
            "password": hashed_pw,
            "role": role
        })
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = db.users.find_one({"email": email})
        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['user_name'] = user['name']
            
            # Detect role from database
            role = user.get('role', 'customer')
            session['role'] = role
            
            if role == 'driver':
                driver = db.drivers.find_one()
                session['driver_name'] = driver['name'] if driver else user['name']
                return redirect(url_for('driver_dashboard'))
            elif role == 'restaurant':
                res = db.restaurants.find_one()
                session['res_name'] = res['name'] if res else "Bellissimo Pizza"
                return redirect(url_for('restaurant_dashboard'))
                
            return redirect(url_for('index'))
        return render_template('login.html', error="Invalid email or password")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- DRIVER DASHBOARD ---

@app.route('/driver')
def driver_dashboard():
    # Demo hack: default to the first driver if not 'logged in' as driver
    if 'driver_name' not in session:
        driver = db.drivers.find_one()
        session['driver_name'] = driver['name'] if driver else "Agus Kurir"
    
    current_driver = session['driver_name']
    available_drivers = list(db.drivers.find())
    return render_template('driver_dashboard.html', driver_name=current_driver, all_drivers=available_drivers)

@app.route('/driver/switch/<name>')
def switch_driver(name):
    session['driver_name'] = name
    return redirect(url_for('driver_dashboard'))

# --- RESTAURANT DASHBOARD ---

@app.route('/restaurant/dashboard')
def restaurant_dashboard():
    # Demo hack: default to the first restaurant if not "logged in" as restaurant
    if 'res_name' not in session:
        res = db.restaurants.find_one()
        session['res_name'] = res['name'] if res else "Bellissimo Pizza"
        
    current_res = session['res_name']
    available_res = list(db.restaurants.find())
    return render_template('restaurant_dashboard.html', res_name=current_res, all_restaurants=available_res)

@app.route('/restaurant/switch-res/<name>')
def switch_restaurant(name):
    session['res_name'] = name
    return redirect(url_for('restaurant_dashboard'))

@app.route('/api/restaurant/orders')
def restaurant_orders_api():
    res_name = session.get('res_name', 'Bellissimo Pizza')
    orders = list(db.orders.find({"restaurant": res_name}).sort("_id", -1))
    
    for o in orders:
        o['_id'] = str(o['_id'])
    return jsonify(orders)

@app.route('/api/driver/orders')
def driver_orders_api():
    driver_name = session.get('driver_name', 'Agus Kurir')
    # Show orders assigned to this driver OR unassigned orders
    orders = list(db.orders.find({
        "$or": [
            {"driver": driver_name},
            {"status": "Finding Driver"}
        ]
    }).sort("_id", -1))
    
    for o in orders:
        o['_id'] = str(o['_id'])
    return jsonify(orders)

@app.route('/api/driver/order/<order_id>/status', methods=['POST'])
def update_order_status(order_id):
    new_status = request.json.get('status')
    driver_name = session.get('driver_name')
    
    # Update status and ensure driver is assigned if they accepted it
    db.orders.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"status": new_status, "driver": driver_name}}
    )
    return jsonify({"success": True})

# --- TRACKING API ---

@app.route('/api/my-orders')
def my_orders_api():
    if 'user_id' not in session:
        return jsonify([])
    
    orders = list(db.orders.find({"user_id": session['user_id']}).sort("_id", -1))
    for o in orders:
        o['_id'] = str(o['_id'])
    return jsonify(orders)

@app.route('/checkout', methods=['POST'])
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    restaurant_name = request.form.get('restaurant_name')
    cart_data_raw = request.form.get('cart_data')
    
    import json
    try:
        cart_items = json.loads(cart_data_raw) if cart_data_raw else []
    except:
        cart_items = []
        
    total_price = sum(item['price'] * item['qty'] for item in cart_items)
    
    return render_template('checkout.html', 
                          restaurant_name=restaurant_name, 
                          cart_items=cart_items, 
                          total_price=total_price,
                          cart_data_raw=cart_data_raw)

@app.route('/order', methods=['POST'])
def place_order():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    customer_name = session['user_name']
    restaurant_name = request.form.get('restaurant_name')
    cart_data_raw = request.form.get('cart_data')
    
    # New fields from checkout
    address = request.form.get('address', 'Standard Address')
    payment_method = request.form.get('payment_method', 'Cash')
    delivery_type = request.form.get('delivery_type', 'Standard')
    promo_code = request.form.get('promo_code', '')
    
    import json
    try:
        cart_items = json.loads(cart_data_raw) if cart_data_raw else []
    except:
        cart_items = []

    # Calculate total price
    total_price = sum(item['price'] * item['qty'] for item in cart_items)
    
    # Calculate discount (simple demo logic)
    discount = 0
    if promo_code.upper() == 'GOFOOD50':
        discount = total_price * 0.5
    elif promo_code.upper() == 'LUCKY10':
        discount = total_price * 0.1
        
    # Add delivery fee
    delivery_fee = 15000 if delivery_type == 'Priority' else 5000
    
    final_total = total_price - discount + delivery_fee

    # Pick the first available driver
    driver = db.drivers.find_one({"is_available": True})
    driver_name = driver['name'] if driver else "Searching for Driver..."

    # Create Order
    order_doc = {
        "user_id": session['user_id'],
        "customer": customer_name,
        "restaurant": restaurant_name,
        "items": cart_items,
        "total_items_price": total_price,
        "discount": discount,
        "delivery_fee": delivery_fee,
        "total_price": final_total,
        "address": address,
        "payment_method": payment_method,
        "delivery_type": delivery_type,
        "driver": driver_name,
        "status": "Preparing" if driver else "Finding Driver",
        "timestamp": os.getenv('CURRENT_TIME', '2026-01-15 06:33') # Optional: Tracking time
    }
    inserted = db.orders.insert_one(order_doc)

    if driver:
        # Set driver to busy
        db.drivers.update_one({"_id": driver["_id"]}, {"$set": {"is_available": False}})
    
    return redirect(url_for('order_receipt', order_id=str(inserted.inserted_id)))

@app.route('/order/receipt/<order_id>')
def order_receipt(order_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    order = db.orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        return "Order not found", 404
        
    # Security check: ensure the order belongs to the user
    if order['user_id'] != session['user_id']:
        return "Unauthorized", 403
        
    return render_template('receipt.html', order=order)

if __name__ == '__main__':
    app.run(debug=True)