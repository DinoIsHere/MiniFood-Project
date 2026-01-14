import pymongo

# 1. Connection - Use your Atlas string
MONGO_URI = "mongodb+srv://replicantxq_db_user:KLb5ZRn9MVh0MYGG@dinocluster.am5rctu.mongodb.net/?appName=DinoCluster"
client = pymongo.MongoClient(MONGO_URI)

# Match your exact DB name from the screenshot
db = client['MiniFood']
restaurants_col = db['restaurants']

# 2. Data to Insert
full_dataset = [
    {
        "name": "Ayam Geprek Juara",
        "category": "Indonesian Fast Food",
        "menu": [
            {"item": "Paket Geprek Original", "price": 15000},
            {"item": "Paket Geprek Keju", "price": 22000},
            {"item": "Paket Geprek Mozzarella", "price": 27000},
            {"item": "Ayam Geprek Sambal Matah", "price": 18000},
            {"item": "Nasi Daun Jeruk", "price": 8000},
            {"item": "Kol Goreng Crispy", "price": 5000},
            {"item": "Tahu/Tempe Goreng", "price": 3000},
            {"item": "Es Teh Manis Jumbo", "price": 6000},
            {"item": "Es Jeruk Peras", "price": 10000}
        ]
    },
    {
        "name": "Kopi Kenangan",
        "category": "Beverage & Snacks",
        "menu": [
            {"item": "Kopi Kenangan Mantan", "price": 18000},
            {"item": "Dua Shot Iced Shaken", "price": 24000},
            {"item": "Caramel Macchiato", "price": 30000},
            {"item": "Milo Dinosaur", "price": 22000},
            {"item": "Thai Tea", "price": 18000},
            {"item": "Earl Grey Milk Tea", "price": 24000},
            {"item": "Roti Kopi", "price": 12000},
            {"item": "Sultana Cookies", "price": 15000},
            {"item": "Pandan Latte", "price": 25000}
        ]
    },
    {
        "name": "Sushi Zen",
        "category": "Japanese",
        "menu": [
            {"item": "Salmon Mentai Roll", "price": 45000},
            {"item": "Dragon Roll", "price": 55000},
            {"item": "Spicy Tuna Maki", "price": 35000},
            {"item": "Chicken Teriyaki Don", "price": 40000},
            {"item": "Ebi Tempura (3pcs)", "price": 30000},
            {"item": "Miso Soup", "price": 15000},
            {"item": "Ocha (Free Refill)", "price": 5000},
            {"item": "Matcha Ice Cream", "price": 15000}
        ]
    },
    {
        "name": "Bakmi GM Clone",
        "category": "Chinese-Indonesian",
        "menu": [
            {"item": "Bakmi Ayam Special GM", "price": 32000},
            {"item": "Bakmi Goreng", "price": 38000},
            {"item": "Pangsit Goreng (5pcs)", "price": 20000},
            {"item": "Nasi Goreng Smoked Chicken", "price": 42000},
            {"item": "Ayam Mentega", "price": 45000},
            {"item": "Bakso Kuah", "price": 25000},
            {"item": "Es Liang Teh", "price": 12000}
        ]
    },
    {
        "name": "Pizza Mania",
        "category": "Western",
        "menu": [
            {"item": "Pepperoni Feast", "price": 85000},
            {"item": "Meat Lovers", "price": 95000},
            {"item": "Super Supreme", "price": 90000},
            {"item": "Cheesy Garlic Bread", "price": 25000},
            {"item": "Chicken Wings (6pcs)", "price": 35000},
            {"item": "Beef Lasagna", "price": 50000},
            {"item": "Spaghetti Carbonara", "price": 45000},
            {"item": "Coca-Cola 1.5L", "price": 20000}
        ]
    }
]

# 3. Execution: Wipe and Load
restaurants_col.delete_many({}) # Removes old entries
restaurants_col.insert_many(full_dataset)

print(f"Done! {len(full_dataset)} restaurants with full menus are now live in Atlas.")