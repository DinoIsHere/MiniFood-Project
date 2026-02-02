from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pymongo
from bson import ObjectId
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
app.secret_key = "super_secret_mini_gofood_key"
bcrypt = Bcrypt(app)

# --- DATABASE CONNECTION ---
MONGO_URI = "mongodb+srv://replicantxq_db_user:KLb5ZRn9MVh0MYGG@dinocluster.am5rctu.mongodb.net/?appName=DinoCluster"
client = pymongo.MongoClient(MONGO_URI)
db = client['MiniFood']

# --- ROUTES ---

@app.route('/')
def index():
    restaurants = list(db.restaurants.find().limit(6))
    drivers = list(db.drivers.find())
    
    # FIX 1: Use .get() to avoid KeyError if 'user_id' is missing
    user_id = session.get('user_id')
    query = {"user_id": user_id} if user_id else {}
    
    orders = list(db.orders.find(query).sort("_id", -1).limit(10)) 
    return render_template('index.html', restaurants=restaurants, drivers=drivers, orders=orders)

# --- AUTH ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = db.users.find_one({"email": email})
        
        # FIX 2: Check if user exists before checking password hash
        if user and bcrypt.check_password_hash(user.get('password', ''), password):
            session['user_id'] = str(user['_id'])
            
            # FIX 3: Fallback logic for name/username mismatch
            session['user_name'] = user.get('name') or user.get('username') or "User"
            
            # FIX 4: Default role to 'customer' if field is missing
            role = user.get('role', 'customer')
            session['role'] = role
            
            if role == 'driver':
                driver = db.drivers.find_one()
                session['driver_name'] = driver['name'] if driver else session['user_name']
                return redirect(url_for('driver_dashboard'))
            elif role == 'restaurant':
                res = db.restaurants.find_one()
                session['res_name'] = res['name'] if res else "Bellissimo Pizza"
                return redirect(url_for('restaurant_dashboard'))
                
            return redirect(url_for('index'))
        return render_template('login.html', error="Invalid email or password")
    return render_template('login.html')

@app.route('/order', methods=['POST'])
def place_order():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # FIX 5: Ensure session values exist before creating order
    customer_name = session.get('user_name', 'Anonymous')
    restaurant_name = request.form.get('restaurant_name')
    cart_data_raw = request.form.get('cart_data')
    
    import json
    try:
        cart_items = json.loads(cart_data_raw) if cart_data_raw else []
    except:
        cart_items = []

    total_price = sum(item.get('price', 0) * item.get('qty', 0) for item in cart_items)
    
    # FIX 6: Safety check for driver assignment
    driver = db.drivers.find_one({"is_available": True})
    driver_name = driver['name'] if driver else "Searching for Driver..."

    order_doc = {
        "user_id": session['user_id'],
        "customer": customer_name,
        "restaurant": restaurant_name,
        "items": cart_items,
        "total_price": total_price, # Simplified for debugging
        "driver": driver_name,
        "status": "Preparing" if driver else "Finding Driver",
        "timestamp": "2026-01-15 06:33" 
    }
    inserted = db.orders.insert_one(order_doc)
    
    return redirect(url_for('order_receipt', order_id=str(inserted.inserted_id)))