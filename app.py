from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import requests, urllib.parse, os
import threading
import time
import schedule
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "SmartPantry")

# -------- CONFIG --------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "smartpantry28@gmail.com")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "53925676-923ada41045b5b093107c781b")
FLASK_ENV = os.getenv("FLASK_ENV", "development")

# -------- DB --------
print(f"🔍 Attempting to connect to MongoDB...")
print(f"📋 MONGO_URI: {MONGO_URI[:50]}..." if len(MONGO_URI) > 50 else f"📋 MONGO_URI: {MONGO_URI}")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
    # Test the connection
    client.server_info()
    db = client.smart_pantry
    users = db.users
    items = db.items
    print("✅ Connected to MongoDB successfully!")
    print(f"📊 Database: {db.name}")
    DB_CONNECTED = True
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    print(f"🔍 Error type: {type(e).__name__}")
    
    # Provide specific troubleshooting based on error type
    error_str = str(e).lower()
    if "authentication failed" in error_str:
        print("🔧 AUTHENTICATION ERROR: Check username/password in connection string")
    elif "network" in error_str or "timeout" in error_str:
        print("🔧 NETWORK ERROR: Check Network Access settings in MongoDB Atlas")
    elif "dns" in error_str:
        print("🔧 DNS ERROR: Check connection string format and cluster address")
    elif "localhost" in MONGO_URI:
        print("🔧 LOCALHOST ERROR: Update MONGO_URI environment variable in Render")
    
    print("⚠️ Running in demo mode - data will not persist")
    # Create enhanced mock database objects for demo
    class MockCollection:
        def __init__(self):
            self.data = {}
            self.counter = 1
        
        def find_one(self, query):
            return None
        
        def find(self, query):
            return []
        
        def insert_one(self, doc):
            doc_id = f"demo_{self.counter}"
            self.counter += 1
            self.data[doc_id] = doc
            return type('obj', (object,), {'inserted_id': doc_id})
        
        def update_one(self, query, update, **kwargs):
            return None
        
        def delete_one(self, query):
            return None
        
        def count_documents(self, query):
            return 0
    
    class MockDB:
        def __init__(self):
            self.users = MockCollection()
            self.items = MockCollection()
            self.saved_recipes = MockCollection()
            self.hidden_recipes = MockCollection()
            self.meal_plans = MockCollection()
    
    client = None
    db = MockDB()
    users = db.users
    items = db.items
    DB_CONNECTED = False

# -------- EMAIL --------
def send_email(to, subject, content):
    """Send email using SendGrid"""
    if not SENDGRID_API_KEY:
        print(f"SendGrid API key not configured. Would send email to {to}: {subject}")
        return False
    
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=to,
            subject=subject,
            html_content=content
        )
        response = sg.send(message)
        print(f"Email sent successfully to {to}")
        return True
    except Exception as e:
        print(f"Error sending email to {to}: {e}")
        return False

def send_welcome_email(email, username):
    """Send welcome email to new users"""
    subject = "Welcome to Smart Pantry! 🥗"
    content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #986533, #7a3e2f); padding: 30px; border-radius: 10px; text-align: center; color: white;">
            <h1 style="margin: 0; font-size: 28px;">🥗 Welcome to Smart Pantry!</h1>
        </div>
        
        <div style="padding: 30px; background: #f6f1eb; border-radius: 10px; margin-top: 20px;">
            <h2 style="color: #7a3e2f;">Hello {username}!</h2>
            
            <p style="font-size: 16px; line-height: 1.6; color: #333;">
                Thank you for joining Smart Pantry! We're excited to help you manage your kitchen inventory and reduce food waste.
            </p>
            
            <h3 style="color: #986533;">What you can do with Smart Pantry:</h3>
            <ul style="font-size: 14px; line-height: 1.8; color: #333;">
                <li>📊 Track your pantry items and expiry dates</li>
                <li>🍳 Discover recipes based on available ingredients</li>
                <li>📅 Plan your weekly meals efficiently</li>
                <li>⏰ Get notifications before items expire</li>
                <li>♻️ Reduce food waste and save money</li>
            </ul>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="http://127.0.0.1:5000/pantry" 
                   style="background: #986533; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold;">
                   Start Managing Your Pantry
                </a>
            </div>
            
            <p style="font-size: 14px; color: #666; text-align: center;">
                Happy cooking!<br>
                The Smart Pantry Team
            </p>
        </div>
    </body>
    </html>
    """
    return send_email(email, subject, content)

def send_expiry_notification(email, username, expiring_items):
    """Send expiry notification email"""
    if not expiring_items:
        return
    
    subject = f"⚠️ {len(expiring_items)} items expiring soon in your pantry"
    
    items_html = ""
    for item in expiring_items:
        days_left = item['days_left']
        urgency_color = "#e74c3c" if days_left <= 1 else "#f39c12" if days_left <= 2 else "#ff9800"
        
        items_html += f"""
        <div style="background: white; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid {urgency_color};">
            <h4 style="margin: 0; color: #333;">{item['name']}</h4>
            <p style="margin: 5px 0; color: {urgency_color}; font-weight: bold;">
                {'Expires today!' if days_left == 0 else f'Expires in {days_left} day{"s" if days_left > 1 else ""}'}
            </p>
            <p style="margin: 5px 0; color: #666; font-size: 14px;">Category: {item.get('category', 'Unknown')}</p>
        </div>
        """
    
    content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #f39c12, #e74c3c); padding: 30px; border-radius: 10px; text-align: center; color: white;">
            <h1 style="margin: 0; font-size: 24px;">⚠️ Items Expiring Soon!</h1>
        </div>
        
        <div style="padding: 30px; background: #f6f1eb; border-radius: 10px; margin-top: 20px;">
            <h2 style="color: #7a3e2f;">Hello {username}!</h2>
            
            <p style="font-size: 16px; line-height: 1.6; color: #333;">
                You have <strong>{len(expiring_items)} item{"s" if len(expiring_items) > 1 else ""}</strong> in your pantry that will expire soon. 
                Take action now to avoid food waste!
            </p>
            
            <h3 style="color: #986533;">Items requiring attention:</h3>
            {items_html}
            
            <div style="background: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h4 style="color: #856404; margin-top: 0;">💡 Suggestions:</h4>
                <ul style="color: #856404; margin: 0;">
                    <li>Check our recipe suggestions for these items</li>
                    <li>Plan meals using these ingredients</li>
                    <li>Consider preserving or freezing if possible</li>
                    <li>Share with friends or neighbors</li>
                </ul>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="http://127.0.0.1:5000/pantry" 
                   style="background: #986533; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold;">
                   View Your Pantry
                </a>
                <a href="http://127.0.0.1:5000/recipes/all" 
                   style="background: #27ae60; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin-left: 10px;">
                   Find Recipes
                </a>
            </div>
            
            <p style="font-size: 14px; color: #666; text-align: center;">
                Let's reduce food waste together!<br>
                The Smart Pantry Team
            </p>
        </div>
    </body>
    </html>
    """
    return send_email(email, subject, content)

def check_expiring_items():
    """Check for expiring items and send notifications"""
    print("Checking for expiring items...")
    today = datetime.today().date()
    
    # Get all users
    all_users = list(users.find({}))
    
    for user in all_users:
        username = user.get('username')
        email = user.get('email')
        
        if not email:
            continue
        
        # Get user's items that expire in 3 days or less
        user_items = list(items.find({"user": username}))
        expiring_items = []
        
        for item in user_items:
            try:
                expiry_date = datetime.strptime(item["expiry"], "%Y-%m-%d").date()
                days_left = (expiry_date - today).days
                
                # Remove expired items
                if days_left < 0:
                    items.delete_one({"_id": item["_id"]})
                    continue
                
                # Add items expiring in 3 days or less
                if days_left <= 3:
                    item['days_left'] = days_left
                    expiring_items.append(item)
            except:
                continue
        
        # Send notification if there are expiring items
        if expiring_items:
            print(f"Sending expiry notification to {email} for {len(expiring_items)} items")
            send_expiry_notification(email, username, expiring_items)

def start_scheduler():
    """Start the background scheduler for daily email notifications"""
    schedule.every().day.at("09:00").do(check_expiring_items)  # Send at 9 AM daily
    
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("Email scheduler started - will check for expiring items daily at 9:00 AM")

# -------- RECIPE GENERATION --------
def get_recipes_for_item(item_name):
    """Generate diverse Indian recipes based on the specific food item"""
    item_lower = item_name.lower()
    
    # Comprehensive Indian recipe database with unique recipes and authentic images
    recipe_database = {
        # Vegetables
        'tomato': [
            {'name': 'Tomato Rasam', 'type': 'South Indian', 'time': '25 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=400&h=300&fit=crop', 'description': 'Tangy South Indian soup with tomatoes, tamarind, and aromatic spices'},
            {'name': 'Tamatar Bharta', 'type': 'North Indian', 'time': '30 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', 'description': 'Smoky roasted tomato curry with onions and traditional spices'},
            {'name': 'Tomato Pulao', 'type': 'Indian', 'time': '35 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop', 'description': 'Fragrant rice dish cooked with fresh tomatoes and whole spices'},
            {'name': 'Tomato Pachadi', 'type': 'South Indian', 'time': '20 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400&h=300&fit=crop', 'description': 'Traditional South Indian tomato chutney with curry leaves and mustard seeds'},
            {'name': 'Tomato Shorba', 'type': 'Mughlai', 'time': '40 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1547592166-23ac45744acd?w=400&h=300&fit=crop', 'description': 'Rich and creamy tomato soup with aromatic Mughlai spices'}
        ],
        'potato': [
            {'name': 'Aloo Jeera', 'type': 'North Indian', 'time': '25 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400&h=300&fit=crop', 'description': 'Simple yet flavorful potatoes cooked with cumin seeds and turmeric'},
            {'name': 'Dum Aloo Kashmiri', 'type': 'Kashmiri', 'time': '45 mins', 'difficulty': 'Hard', 'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', 'description': 'Baby potatoes in rich yogurt-based gravy with Kashmiri spices'},
            {'name': 'Aloo Posto', 'type': 'Bengali', 'time': '30 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop', 'description': 'Bengali potato curry cooked with poppy seed paste'},
            {'name': 'Batata Vada', 'type': 'Maharashtrian', 'time': '35 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=300&fit=crop', 'description': 'Crispy potato fritters served with spicy chutneys'},
            {'name': 'Aloo Bhujia', 'type': 'Rajasthani', 'time': '20 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=400&h=300&fit=crop', 'description': 'Dry potato curry with onions and Rajasthani spices'}
        ],
        'onion': [
            {'name': 'Pyaz Kachori', 'type': 'Rajasthani', 'time': '50 mins', 'difficulty': 'Hard', 'image': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=300&fit=crop', 'description': 'Crispy pastry filled with spiced onion mixture'},
            {'name': 'Vengaya Sambar', 'type': 'South Indian', 'time': '40 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop', 'description': 'Tangy lentil curry with small onions and tamarind'},
            {'name': 'Onion Bhaji', 'type': 'Maharashtrian', 'time': '25 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', 'description': 'Crispy onion fritters perfect for monsoon evenings'},
            {'name': 'Pyaz Ka Halwa', 'type': 'Mughlai', 'time': '60 mins', 'difficulty': 'Hard', 'image': 'https://images.unsplash.com/photo-1551024506-0bccd828d307?w=400&h=300&fit=crop', 'description': 'Sweet onion dessert cooked in ghee and milk'},
            {'name': 'Onion Thokku', 'type': 'South Indian', 'time': '35 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400&h=300&fit=crop', 'description': 'Spicy onion pickle-style curry from Tamil Nadu'}
        ],
        'carrot': [
            {'name': 'Gajar Ka Achaar', 'type': 'Punjabi', 'time': '30 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400&h=300&fit=crop', 'description': 'Tangy carrot pickle with mustard oil and spices'},
            {'name': 'Carrot Kosambari', 'type': 'South Indian', 'time': '15 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&h=300&fit=crop', 'description': 'Fresh carrot salad with lentils and coconut'},
            {'name': 'Gajar Methi Sabzi', 'type': 'Gujarati', 'time': '25 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop', 'description': 'Carrots cooked with fresh fenugreek leaves'},
            {'name': 'Carrot Payasam', 'type': 'South Indian', 'time': '45 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1551024506-0bccd828d307?w=400&h=300&fit=crop', 'description': 'Sweet carrot pudding with coconut milk and jaggery'},
            {'name': 'Gajar Matar Ki Sabzi', 'type': 'North Indian', 'time': '30 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', 'description': 'Carrots and green peas cooked in aromatic spices'}
        ],
        'broccoli': [
            {'name': 'Broccoli Thoran', 'type': 'Kerala', 'time': '20 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400&h=300&fit=crop', 'description': 'Kerala-style broccoli stir-fry with coconut and curry leaves'},
            {'name': 'Broccoli Masala', 'type': 'Indian Fusion', 'time': '25 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop', 'description': 'Broccoli cooked in rich tomato and onion gravy'},
            {'name': 'Broccoli Tikki', 'type': 'North Indian', 'time': '35 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=300&fit=crop', 'description': 'Crispy broccoli patties served with mint chutney'},
            {'name': 'Broccoli Sambar', 'type': 'South Indian', 'time': '40 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', 'description': 'Tangy lentil curry with broccoli and tamarind'},
            {'name': 'Broccoli Bhel', 'type': 'Street Food', 'time': '15 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&h=300&fit=crop', 'description': 'Healthy twist on bhel puri with steamed broccoli'}
        ],
        'spinach': [
            {'name': 'Palak Kofta', 'type': 'North Indian', 'time': '45 mins', 'difficulty': 'Hard', 'image': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop', 'description': 'Spinach dumplings in rich tomato-based gravy'},
            {'name': 'Palak Pakoda', 'type': 'North Indian', 'time': '25 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=300&fit=crop', 'description': 'Crispy spinach fritters perfect for tea time'},
            {'name': 'Keerai Masiyal', 'type': 'Tamil', 'time': '20 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400&h=300&fit=crop', 'description': 'Tamil-style mashed spinach with lentils and coconut'},
            {'name': 'Palak Khichdi', 'type': 'Gujarati', 'time': '35 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', 'description': 'Nutritious rice and lentil dish with spinach'},
            {'name': 'Spinach Uttapam', 'type': 'South Indian', 'time': '30 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop', 'description': 'Fermented rice pancake topped with spinach and spices'}
        ],
        # Proteins
        'chicken': [
            {'name': 'Chicken Chettinad', 'type': 'Tamil', 'time': '50 mins', 'difficulty': 'Hard', 'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', 'description': 'Spicy Tamil chicken curry with roasted spices and coconut'},
            {'name': 'Murgh Musallam', 'type': 'Mughlai', 'time': '90 mins', 'difficulty': 'Hard', 'image': 'https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=400&h=300&fit=crop', 'description': 'Whole chicken cooked in rich Mughlai gravy with nuts'},
            {'name': 'Chicken Koliwada', 'type': 'Maharashtrian', 'time': '35 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=300&fit=crop', 'description': 'Crispy fried chicken pieces with coastal spices'},
            {'name': 'Kozhi Curry', 'type': 'Kerala', 'time': '45 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400&h=300&fit=crop', 'description': 'Kerala-style chicken curry with coconut milk and curry leaves'},
            {'name': 'Chicken Xacuti', 'type': 'Goan', 'time': '60 mins', 'difficulty': 'Hard', 'image': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop', 'description': 'Goan chicken curry with roasted coconut and poppy seeds'}
        ],
        'mutton': [
            {'name': 'Mutton Rara', 'type': 'Punjabi', 'time': '75 mins', 'difficulty': 'Hard', 'image': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop', 'description': 'Rich mutton curry with minced meat and whole spices'},
            {'name': 'Kosha Mangsho', 'type': 'Bengali', 'time': '90 mins', 'difficulty': 'Hard', 'image': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400&h=300&fit=crop', 'description': 'Bengali slow-cooked mutton with caramelized onions'},
            {'name': 'Mutton Sukka', 'type': 'South Indian', 'time': '60 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', 'description': 'Dry mutton curry with coconut and South Indian spices'},
            {'name': 'Laal Maas', 'type': 'Rajasthani', 'time': '80 mins', 'difficulty': 'Hard', 'image': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop', 'description': 'Fiery red mutton curry with Mathania chilies'},
            {'name': 'Mutton Pepper Fry', 'type': 'Kerala', 'time': '55 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400&h=300&fit=crop', 'description': 'Kerala-style mutton with black pepper and curry leaves'}
        ],
        # Grains & Starches
        'rice': [
            {'name': 'Bisi Bele Bath', 'type': 'Karnataka', 'time': '50 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop', 'description': 'Karnataka-style rice dish with lentils and vegetables'},
            {'name': 'Coconut Rice', 'type': 'South Indian', 'time': '25 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400&h=300&fit=crop', 'description': 'Fragrant rice cooked with fresh coconut and curry leaves'},
            {'name': 'Tamarind Rice', 'type': 'South Indian', 'time': '30 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', 'description': 'Tangy rice dish with tamarind and South Indian spices'},
            {'name': 'Ghee Rice', 'type': 'Kerala', 'time': '35 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop', 'description': 'Aromatic rice cooked in ghee with whole spices'},
            {'name': 'Pongal', 'type': 'Tamil', 'time': '40 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400&h=300&fit=crop', 'description': 'Comforting rice and lentil dish with black pepper and ghee'}
        ],
        'wheat': [
            {'name': 'Makki Ki Roti', 'type': 'Punjabi', 'time': '40 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400&h=300&fit=crop', 'description': 'Corn flour flatbread served with sarson ka saag'},
            {'name': 'Bhakri', 'type': 'Maharashtrian', 'time': '30 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop', 'description': 'Thick flatbread made from jowar or bajra flour'},
            {'name': 'Thepla', 'type': 'Gujarati', 'time': '35 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', 'description': 'Spiced flatbread with fenugreek leaves and spices'},
            {'name': 'Rumali Roti', 'type': 'Mughlai', 'time': '45 mins', 'difficulty': 'Hard', 'image': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400&h=300&fit=crop', 'description': 'Paper-thin handkerchief bread cooked on inverted tawa'},
            {'name': 'Lachha Paratha', 'type': 'North Indian', 'time': '50 mins', 'difficulty': 'Hard', 'image': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop', 'description': 'Multi-layered flaky paratha with ghee'}
        ],
        # Lentils
        'lentils': [
            {'name': 'Gujarati Dal', 'type': 'Gujarati', 'time': '35 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400&h=300&fit=crop', 'description': 'Sweet and tangy lentil curry with jaggery and tamarind'},
            {'name': 'Panchmel Dal', 'type': 'Rajasthani', 'time': '45 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop', 'description': 'Five-lentil curry with ghee and aromatic spices'},
            {'name': 'Moong Dal Halwa', 'type': 'North Indian', 'time': '60 mins', 'difficulty': 'Hard', 'image': 'https://images.unsplash.com/photo-1551024506-0bccd828d307?w=400&h=300&fit=crop', 'description': 'Rich dessert made from yellow lentils, ghee, and milk'},
            {'name': 'Paruppu Usili', 'type': 'Tamil', 'time': '30 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', 'description': 'Steamed and crumbled lentils mixed with vegetables'},
            {'name': 'Khatta Moong', 'type': 'Rajasthani', 'time': '25 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400&h=300&fit=crop', 'description': 'Tangy moong dal curry with dried mango powder'}
        ],
        # Additional common items
        'paneer': [
            {'name': 'Paneer Lababdar', 'type': 'Punjabi', 'time': '40 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=400&h=300&fit=crop', 'description': 'Rich paneer curry with tomatoes, cashews, and cream'},
            {'name': 'Paneer Bhurji', 'type': 'North Indian', 'time': '20 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400&h=300&fit=crop', 'description': 'Scrambled paneer with onions, tomatoes, and spices'},
            {'name': 'Paneer Kofta', 'type': 'Mughlai', 'time': '50 mins', 'difficulty': 'Hard', 'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', 'description': 'Paneer dumplings in rich tomato and cashew gravy'},
            {'name': 'Paneer Tikka', 'type': 'Punjabi', 'time': '35 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=300&fit=crop', 'description': 'Grilled paneer cubes marinated in yogurt and spices'},
            {'name': 'Paneer Paratha', 'type': 'North Indian', 'time': '45 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop', 'description': 'Stuffed flatbread with spiced paneer filling'}
        ],
        'cauliflower': [
            {'name': 'Gobi Manchurian', 'type': 'Indo-Chinese', 'time': '35 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=300&fit=crop', 'description': 'Crispy cauliflower in tangy Indo-Chinese sauce'},
            {'name': 'Gobi Paratha', 'type': 'Punjabi', 'time': '40 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop', 'description': 'Stuffed flatbread with spiced cauliflower filling'},
            {'name': 'Cauliflower Pickle', 'type': 'North Indian', 'time': '25 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400&h=300&fit=crop', 'description': 'Tangy cauliflower pickle with mustard oil and spices'},
            {'name': 'Gobi 65', 'type': 'South Indian', 'time': '30 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', 'description': 'Spicy fried cauliflower appetizer with curry leaves'},
            {'name': 'Gobi Masala', 'type': 'North Indian', 'time': '35 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=400&h=300&fit=crop', 'description': 'Cauliflower curry in rich tomato and onion gravy'}
        ],
        'okra': [
            {'name': 'Bhindi Masala', 'type': 'North Indian', 'time': '30 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400&h=300&fit=crop', 'description': 'Spiced okra curry with onions and tomatoes'},
            {'name': 'Bhindi Fry', 'type': 'South Indian', 'time': '25 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop', 'description': 'Crispy fried okra with South Indian spices'},
            {'name': 'Stuffed Bhindi', 'type': 'Rajasthani', 'time': '40 mins', 'difficulty': 'Hard', 'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', 'description': 'Okra stuffed with spice mixture and slow cooked'},
            {'name': 'Bhindi Sambar', 'type': 'South Indian', 'time': '35 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=400&h=300&fit=crop', 'description': 'Tangy lentil curry with okra and tamarind'},
            {'name': 'Bhindi Raita', 'type': 'North Indian', 'time': '15 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&h=300&fit=crop', 'description': 'Cooling yogurt-based side dish with fried okra'}
        ],
        'eggplant': [
            {'name': 'Baingan Bharta', 'type': 'Punjabi', 'time': '45 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400&h=300&fit=crop', 'description': 'Smoky roasted eggplant mash with spices'},
            {'name': 'Stuffed Baingan', 'type': 'Maharashtrian', 'time': '50 mins', 'difficulty': 'Hard', 'image': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop', 'description': 'Baby eggplants stuffed with spice paste'},
            {'name': 'Baingan Curry', 'type': 'South Indian', 'time': '35 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', 'description': 'Eggplant curry in coconut and tamarind gravy'},
            {'name': 'Baingan Pakoda', 'type': 'North Indian', 'time': '25 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=300&fit=crop', 'description': 'Crispy eggplant fritters with gram flour batter'},
            {'name': 'Vangi Bath', 'type': 'Karnataka', 'time': '40 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=400&h=300&fit=crop', 'description': 'Spiced rice dish with eggplant and special masala'}
        ],
        'green beans': [
            {'name': 'Green Bean Poriyal', 'type': 'South Indian', 'time': '20 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400&h=300&fit=crop', 'description': 'South Indian stir-fry with coconut and curry leaves'},
            {'name': 'Bean Sabzi', 'type': 'North Indian', 'time': '25 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop', 'description': 'Simple green bean curry with basic spices'},
            {'name': 'Bean Aloo', 'type': 'Punjabi', 'time': '30 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', 'description': 'Green beans and potatoes cooked together'},
            {'name': 'Bean Pickle', 'type': 'Indian', 'time': '35 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400&h=300&fit=crop', 'description': 'Tangy green bean pickle with oil and spices'},
            {'name': 'Bean Sambar', 'type': 'Tamil', 'time': '40 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=400&h=300&fit=crop', 'description': 'Lentil curry with green beans and tamarind'}
        ]
    }
    
    # Check for exact matches first
    if item_lower in recipe_database:
        return recipe_database[item_lower]
    
    # Check for partial matches
    for key, recipes in recipe_database.items():
        if key in item_lower or item_lower in key:
            return recipes
    
    # Generate generic Indian recipes if no specific match found
    return [
        {'name': f'{item_name} Curry', 'type': 'Indian', 'time': '30 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400&h=300&fit=crop', 'description': f'Traditional Indian curry with {item_name} and aromatic spices'},
        {'name': f'{item_name} Sabzi', 'type': 'North Indian', 'time': '25 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop', 'description': f'Simple dry curry with {item_name} and basic spices'},
        {'name': f'{item_name} Paratha', 'type': 'Punjabi', 'time': '40 mins', 'difficulty': 'Medium', 'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop', 'description': f'Stuffed flatbread with spiced {item_name} filling'},
        {'name': f'{item_name} Pickle', 'type': 'Indian', 'time': '20 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400&h=300&fit=crop', 'description': f'Tangy {item_name} pickle with mustard oil and spices'},
        {'name': f'{item_name} Raita', 'type': 'North Indian', 'time': '10 mins', 'difficulty': 'Easy', 'image': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&h=300&fit=crop', 'description': f'Cooling yogurt-based side dish with {item_name}'}
    ]

def get_recipe_image(recipe_name, recipe_type):
    """Get appropriate image for recipe based on type and name - now handled in recipe database"""
    # This function is now mainly for fallback, as images are defined in the recipe database
    recipe_images = {
        'Italian': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop',
        'Indian': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400&h=300&fit=crop',
        'Asian': 'https://images.unsplash.com/photo-1512058564366-18510be2db19?w=400&h=300&fit=crop',
        'French': 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=400&h=300&fit=crop',
        'American': 'https://images.unsplash.com/photo-1571091718767-18b5b1457add?w=400&h=300&fit=crop',
        'Mexican': 'https://images.unsplash.com/photo-1565299585323-38174c4a6c7b?w=400&h=300&fit=crop',
        'Soup': 'https://images.unsplash.com/photo-1547592166-23ac45744acd?w=400&h=300&fit=crop',
        'Dessert': 'https://images.unsplash.com/photo-1551024506-0bccd828d307?w=400&h=300&fit=crop',
        'Salad': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&h=300&fit=crop',
        'Healthy': 'https://images.unsplash.com/photo-1459411621453-7b03977f4bfc?w=400&h=300&fit=crop'
    }
    
    return recipe_images.get(recipe_type, 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&h=300&fit=crop')

# -------- IMAGE --------
def get_food_image(name):
    """Get specific food images based on the item name"""
    name_lower = name.lower()
    
    # Specific food item images
    food_images = {
        # Vegetables
        'tomato': 'https://images.unsplash.com/photo-1546470427-e5ac89c8ba3a?w=400&h=300&fit=crop',
        'potato': 'https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=400&h=300&fit=crop',
        'onion': 'https://images.unsplash.com/photo-1508747703725-719777637510?w=400&h=300&fit=crop',
        'carrot': 'https://images.unsplash.com/photo-1445282768818-728615cc910a?w=400&h=300&fit=crop',
        'broccoli': 'https://images.unsplash.com/photo-1459411621453-7b03977f4bfc?w=400&h=300&fit=crop',
        'spinach': 'https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=400&h=300&fit=crop',
        'cauliflower': 'https://images.unsplash.com/photo-1568584711271-946d4d46b7d8?w=400&h=300&fit=crop',
        'cabbage': 'https://images.unsplash.com/photo-1594282486552-05b4d80fbb9f?w=400&h=300&fit=crop',
        'bell pepper': 'https://images.unsplash.com/photo-1563565375-f3fdfdbefa83?w=400&h=300&fit=crop',
        'cucumber': 'https://images.unsplash.com/photo-1449300079323-02e209d9d3a6?w=400&h=300&fit=crop',
        'okra': 'https://images.unsplash.com/photo-1583663848850-46af132dc08e?w=400&h=300&fit=crop',
        'eggplant': 'https://images.unsplash.com/photo-1659261200833-ec8761558af7?w=400&h=300&fit=crop',
        'green beans': 'https://images.unsplash.com/photo-1553395572-6ac2b2b4d0a1?w=400&h=300&fit=crop',
        'peas': 'https://images.unsplash.com/photo-1587735243615-c03f25aaff15?w=400&h=300&fit=crop',
        'corn': 'https://images.unsplash.com/photo-1551754655-cd27e38d2076?w=400&h=300&fit=crop',
        
        # Fruits
        'apple': 'https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=400&h=300&fit=crop',
        'banana': 'https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=400&h=300&fit=crop',
        'orange': 'https://images.unsplash.com/photo-1547514701-42782101795e?w=400&h=300&fit=crop',
        'mango': 'https://images.unsplash.com/photo-1553279768-865429fa0078?w=400&h=300&fit=crop',
        'grapes': 'https://images.unsplash.com/photo-1537640538966-79f369143f8f?w=400&h=300&fit=crop',
        'strawberry': 'https://images.unsplash.com/photo-1464965911861-746a04b4bca6?w=400&h=300&fit=crop',
        
        # Proteins
        'chicken': 'https://images.unsplash.com/photo-1604503468506-a8da13d82791?w=400&h=300&fit=crop',
        'mutton': 'https://images.unsplash.com/photo-1588347818133-38c4106c8f4b?w=400&h=300&fit=crop',
        'fish': 'https://images.unsplash.com/photo-1544943910-4c1dc44aab44?w=400&h=300&fit=crop',
        'eggs': 'https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=400&h=300&fit=crop',
        'paneer': 'https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=400&h=300&fit=crop',
        
        # Grains & Starches
        'rice': 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=400&h=300&fit=crop',
        'wheat': 'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=400&h=300&fit=crop',
        'bread': 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400&h=300&fit=crop',
        'pasta': 'https://images.unsplash.com/photo-1551892374-ecf8754cf8b0?w=400&h=300&fit=crop',
        
        # Lentils & Legumes
        'lentils': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop',
        'chickpeas': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop',
        'kidney beans': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop',
        
        # Dairy
        'milk': 'https://images.unsplash.com/photo-1550583724-b2692b85b150?w=400&h=300&fit=crop',
        'yogurt': 'https://images.unsplash.com/photo-1571212515416-fef01fc43637?w=400&h=300&fit=crop',
        'cheese': 'https://images.unsplash.com/photo-1486297678162-eb2a19b0a32d?w=400&h=300&fit=crop',
        'butter': 'https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?w=400&h=300&fit=crop',
        
        # Spices & Herbs
        'ginger': 'https://images.unsplash.com/photo-1599639832862-bd92c6e10b5b?w=400&h=300&fit=crop',
        'garlic': 'https://images.unsplash.com/photo-1553978297-833d09932d31?w=400&h=300&fit=crop',
        'turmeric': 'https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=400&h=300&fit=crop',
        'coriander': 'https://images.unsplash.com/photo-1618375569909-3c8616cf7733?w=400&h=300&fit=crop'
    }
    
    # Check for exact matches first
    if name_lower in food_images:
        return food_images[name_lower]
    
    # Check for partial matches
    for key, image_url in food_images.items():
        if key in name_lower or name_lower in key:
            return food_images[key]
    
    # Try Pixabay API as fallback
    try:
        url = "https://pixabay.com/api/"
        params = {
            "key": PIXABAY_API_KEY,
            "q": urllib.parse.quote(f"{name} food fresh"),
            "image_type": "photo",
            "category": "food",
            "min_width": 400,
            "min_height": 300,
            "per_page": 3
        }
        res = requests.get(url, params=params, timeout=5).json()
        if res.get("hits") and len(res["hits"]) > 0:
            return res["hits"][0]["webformatURL"]
    except Exception as e:
        print(f"Pixabay API error: {e}")
    
    # Final fallback to generic food image
    return f"https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=400&h=300&fit=crop&crop=center"

# -------- ROUTES --------
@app.route("/debug/clear-database")
def clear_database():
    """Debug endpoint to completely clear all collections"""
    if not DB_CONNECTED:
        return "Database not connected"
    
    try:
        # Clear all collections
        users.delete_many({})
        items.delete_many({})
        db.saved_recipes.delete_many({})
        db.hidden_recipes.delete_many({})
        db.meal_plans.delete_many({})
        
        # Count remaining documents
        user_count = users.count_documents({})
        item_count = items.count_documents({})
        
        return f"""
        <html>
        <head><title>Database Cleared</title></head>
        <body style="font-family: monospace; padding: 20px;">
            <h2>🗑️ Database Cleared Successfully!</h2>
            <p>✅ Users collection: {user_count} documents remaining</p>
            <p>✅ Items collection: {item_count} documents remaining</p>
            <p>✅ Saved recipes cleared</p>
            <p>✅ Hidden recipes cleared</p>
            <p>✅ Meal plans cleared</p>
            
            <h3>Next Steps:</h3>
            <ol>
                <li><a href="/signup">Create a new account</a></li>
                <li><a href="/login">Login with new account</a></li>
                <li><a href="/pantry">Start using the app</a></li>
            </ol>
            
            <p><strong>Note:</strong> This endpoint will be removed in production.</p>
        </body>
        </html>
        """
        
    except Exception as e:
        return f"Error clearing database: {e}"

@app.route("/debug/connection")
def debug_connection():
    """Debug endpoint to check MongoDB connection status"""
    debug_info = {
        "mongo_uri_set": "MONGO_URI" in os.environ,
        "mongo_uri_preview": MONGO_URI[:50] + "..." if len(MONGO_URI) > 50 else MONGO_URI,
        "db_connected": DB_CONNECTED,
        "flask_env": FLASK_ENV
    }
    
    connection_test = "❌ Failed"
    error_message = "No error"
    
    if DB_CONNECTED:
        connection_test = "✅ Success"
        try:
            # Test a simple operation
            test_count = users.count_documents({})
            debug_info["user_count"] = test_count
        except Exception as e:
            error_message = str(e)
    else:
        error_message = "Database not connected - check environment variables"
    
    debug_info["connection_test"] = connection_test
    debug_info["error_message"] = error_message
    
    return f"""
    <html>
    <head><title>MongoDB Connection Debug</title></head>
    <body style="font-family: monospace; padding: 20px;">
        <h2>🔍 MongoDB Connection Debug</h2>
        <pre>{chr(10).join([f"{k}: {v}" for k, v in debug_info.items()])}</pre>
        
        <h3>📋 Troubleshooting Steps:</h3>
        <ol>
            <li>Check if MONGO_URI is set in Render environment variables</li>
            <li>Verify connection string format: mongodb+srv://...</li>
            <li>Check Network Access in MongoDB Atlas (allow 0.0.0.0/0)</li>
            <li>Verify database user credentials</li>
        </ol>
        
        <p><a href="/pantry">← Back to Pantry</a></p>
    </body>
    </html>
    """

@app.route("/health")
def health_check():
    """Health check endpoint for Render"""
    try:
        if DB_CONNECTED and client:
            client.server_info()
            return {"status": "healthy", "database": "connected"}, 200
        else:
            return {"status": "healthy", "database": "demo_mode"}, 200
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 500

@app.route("/")
def welcome():
    return render_template("welcome.html")

@app.route("/index")
def index():
    return render_template("index.html")

@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        try:
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")
            
            if not username or not email or not password:
                return render_template("signup.html", error="Please fill in all fields", db_connected=DB_CONNECTED)
            
            # In demo mode, just create session
            if not DB_CONNECTED:
                session["user"] = username
                return render_template("signup.html", success="Account created successfully! You can now login.", db_connected=DB_CONNECTED)
            
            # Check if user already exists (more detailed checking)
            existing_user = users.find_one({"username": username})
            if existing_user:
                return render_template("signup.html", error=f"Username '{username}' already exists. Try a different username.", db_connected=DB_CONNECTED)
            
            existing_email = users.find_one({"email": email})
            if existing_email:
                return render_template("signup.html", error=f"Email '{email}' is already registered. Try a different email.", db_connected=DB_CONNECTED)
            
            # Create new user
            user_doc = {
                "username": username,
                "email": email,
                "password": generate_password_hash(password),
                "created_at": datetime.now()
            }
            
            result = users.insert_one(user_doc)
            print(f"✅ Created user: {username} with ID: {result.inserted_id}")
            
            # Send welcome email immediately in a separate thread
            def send_welcome_async():
                try:
                    send_welcome_email(email, username)
                    print(f"Welcome email sent successfully to {email}")
                except Exception as e:
                    print(f"Failed to send welcome email to {email}: {e}")
            
            # Start email sending in background
            email_thread = threading.Thread(target=send_welcome_async)
            email_thread.daemon = True
            email_thread.start()
            
            return render_template("signup.html", success=f"Account created successfully for '{username}'! Welcome email has been sent. You can now login.", db_connected=DB_CONNECTED)
            
        except Exception as e:
            print(f"Signup error: {e}")
            return render_template("signup.html", error=f"Signup failed: {str(e)}. Please try again.", db_connected=DB_CONNECTED)
    
    return render_template("signup.html", db_connected=DB_CONNECTED)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        try:
            username = request.form.get("username")
            password = request.form.get("password")
            
            if not username or not password:
                return render_template("login.html", error="Please enter both username and password")
            
            # In demo mode, show error message directing to database setup
            if not DB_CONNECTED:
                return render_template("login.html", error="Database not connected. Please set up MongoDB Atlas connection string in Render environment variables.")
            
            # Real database login
            user = users.find_one({"username": username})
            if not user or not check_password_hash(user["password"], password):
                return render_template("login.html", error="Invalid username or password")
            
            session["user"] = user["username"]
            return redirect("/pantry")
            
        except Exception as e:
            print(f"Login error: {e}")
            return render_template("login.html", error="Login failed. Please try again.")
    
    return render_template("login.html")

@app.route("/pantry")
def pantry():
    if "user" not in session:
        return redirect("/login")

    # Show database connection status
    db_status = "Connected to MongoDB" if DB_CONNECTED else "Demo Mode - Set up MongoDB Atlas for full functionality"
    
    today = datetime.today().date()
    user_items = list(items.find({"user": session["user"]}))

    stats = {"total":0,"soon":0,"safe":0,"expired":0}
    updated = []
    expired_items = []

    for i in user_items:
        try:
            expiry = datetime.strptime(i["expiry"], "%Y-%m-%d").date()
            days_left = (expiry - today).days

            if "image" not in i:
                i["image"] = get_food_image(i["name"])
                if DB_CONNECTED:
                    items.update_one({"_id": i["_id"]}, {"$set":{"image":i["image"]}})

            i["_id"] = str(i["_id"])
            i["days_left"] = days_left
            
            # Add default quantity and unit if not present (for existing items)
            if "quantity" not in i:
                i["quantity"] = 1
            if "unit" not in i:
                i["unit"] = "pieces"

            if days_left < 0:
                # Add to expired items list
                stats["expired"] += 1
                expired_items.append(i)
            else:
                # Add to current items
                stats["total"] += 1
                stats["soon" if days_left <= 3 else "safe"] += 1
                updated.append(i)
        except Exception as e:
            print(f"Error processing item {i.get('name', 'unknown')}: {e}")
            continue

    return render_template("pantry.html", 
                         items=updated, 
                         expired_items=expired_items, 
                         stats=stats,
                         db_status=db_status,
                         db_connected=DB_CONNECTED)

@app.route("/add", methods=["POST"])
def add():
    if "user" not in session:
        return redirect("/login")
    
    try:
        # Get form data
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "")
        quantity = request.form.get("quantity", "1")
        unit = request.form.get("unit", "")
        expiry = request.form.get("expiry", "")
        
        # Validate required fields
        if not all([name, category, quantity, unit, expiry]):
            return redirect("/pantry?error=Please fill all fields")
        
        # Create item document
        item_doc = {
            "user": session["user"],
            "name": name,
            "category": category,
            "quantity": int(quantity),
            "unit": unit,
            "expiry": expiry,
            "image": get_food_image(name),
            "added_at": datetime.now()
        }
        
        # Insert into database
        result = items.insert_one(item_doc)
        print(f"✅ Added item: {name} for user: {session['user']}")
        
    except Exception as e:
        print(f"❌ Error adding item: {e}")
        return redirect("/pantry?error=Failed to add item")
    
    return redirect("/pantry")

@app.route("/delete/<id>")
def delete(id):
    if "user" not in session:
        return redirect("/login")
    
    try:
        # Delete item by ID and ensure it belongs to the current user
        result = items.delete_one({
            "_id": ObjectId(id),
            "user": session["user"]
        })
        
        if result.deleted_count > 0:
            print(f"✅ Deleted item: {id} for user: {session['user']}")
        else:
            print(f"⚠️ Item not found or doesn't belong to user: {id}")
            
    except Exception as e:
        print(f"❌ Error deleting item: {e}")
    
    return redirect("/pantry")

@app.route("/clear_expired")
def clear_expired():
    """Remove all expired items from database"""
    if "user" not in session:
        return redirect("/login")
    
    today = datetime.today().date()
    user_items = list(items.find({"user": session["user"]}))
    
    for item in user_items:
        expiry = datetime.strptime(item["expiry"], "%Y-%m-%d").date()
        days_left = (expiry - today).days
        
        if days_left < 0:
            items.delete_one({"_id": item["_id"]})
    
    return redirect("/pantry")

@app.route("/recipes")
def recipes():
    item = request.args.get("item")
    if item:
        # Get specific recipes for this item
        recipes_data = get_recipes_for_item(item)
        
        # Get hidden recipes for this user
        hidden_recipes = []
        if "user" in session:
            hidden = db.hidden_recipes.find({"user": session["user"], "ingredient": item})
            hidden_recipes = [h["recipe_name"] for h in hidden]
        
        # Format recipes with images and additional info, filter out hidden ones
        recipes_list = []
        for recipe in recipes_data:
            if recipe['name'] not in hidden_recipes:
                recipes_list.append({
                    "name": recipe['name'],
                    "type": recipe['type'],
                    "time": recipe['time'],
                    "difficulty": recipe['difficulty'],
                    "image": recipe.get('image', get_recipe_image(recipe['name'], recipe['type'])),
                    "description": recipe.get('description', f"{recipe['difficulty']} • {recipe['time']} • {recipe['type']} cuisine"),
                    "ingredient": item
                })
    else:
        recipes_list = []
    
    return render_template("recipe.html", item=item, recipes=recipes_list)

@app.route("/recipes/all")
def all_recipes():
    """Get recipes based on all available pantry items"""
    if "user" not in session:
        return redirect("/login")
    
    user_items = list(items.find({"user": session["user"]}))
    all_recipes = []
    
    # Get hidden recipes for this user
    hidden_recipes = []
    hidden = db.hidden_recipes.find({"user": session["user"]})
    for h in hidden:
        hidden_recipes.append(f"{h['recipe_name']}_{h['ingredient']}")
    
    # Get recipes for each pantry item
    for item in user_items[:6]:  # Limit to first 6 items to avoid too many recipes
        item_recipes = get_recipes_for_item(item["name"])
        # Take first 2 recipes for each item, filter out hidden ones
        for recipe in item_recipes[:2]:
            recipe_key = f"{recipe['name']}_{item['name']}"
            if recipe_key not in hidden_recipes:
                all_recipes.append({
                    "name": recipe['name'],
                    "type": recipe['type'],
                    "time": recipe['time'],
                    "difficulty": recipe['difficulty'],
                    "image": recipe.get('image', get_recipe_image(recipe['name'], recipe['type'])),
                    "description": recipe.get('description', f"{recipe['difficulty']} • {recipe['time']} • {recipe['type']} cuisine"),
                    "ingredient": item["name"]
                })
    
    return render_template("recipe.html", item="your pantry items", recipes=all_recipes)

@app.route("/recipes/save", methods=["POST"])
def save_recipe():
    """Save a recipe to user's saved recipes"""
    if "user" not in session:
        return redirect("/login")
    
    recipe_data = {
        "user": session["user"],
        "name": request.form.get("recipe_name"),
        "type": request.form.get("recipe_type"),
        "time": request.form.get("recipe_time"),
        "difficulty": request.form.get("recipe_difficulty"),
        "image": request.form.get("recipe_image"),
        "description": request.form.get("recipe_description"),
        "ingredient": request.form.get("ingredient"),
        "saved_at": datetime.now()
    }
    
    # Check if recipe already saved
    existing = db.saved_recipes.find_one({
        "user": session["user"],
        "name": recipe_data["name"]
    })
    
    if not existing:
        db.saved_recipes.insert_one(recipe_data)
    
    return redirect(request.referrer or "/recipes")

@app.route("/recipes/remove/<recipe_id>")
def remove_recipe(recipe_id):
    """Remove a saved recipe"""
    if "user" not in session:
        return redirect("/login")
    
    db.saved_recipes.delete_one({
        "_id": ObjectId(recipe_id),
        "user": session["user"]
    })
    
    return redirect("/recipes/saved")

@app.route("/recipes/hide", methods=["POST"])
def hide_recipe():
    """Hide a recipe from suggestions"""
    if "user" not in session:
        return redirect("/login")
    
    recipe_data = {
        "user": session["user"],
        "recipe_name": request.form.get("recipe_name"),
        "ingredient": request.form.get("ingredient"),
        "hidden_at": datetime.now()
    }
    
    # Check if recipe already hidden
    existing = db.hidden_recipes.find_one({
        "user": session["user"],
        "recipe_name": recipe_data["recipe_name"],
        "ingredient": recipe_data["ingredient"]
    })
    
    if not existing:
        db.hidden_recipes.insert_one(recipe_data)
    
    return redirect(request.referrer or "/recipes")

@app.route("/recipes/saved")
def saved_recipes():
    """View user's saved recipes"""
    if "user" not in session:
        return redirect("/login")
    
    saved = list(db.saved_recipes.find({"user": session["user"]}))
    
    # Format saved recipes
    recipes_list = []
    for recipe in saved:
        recipes_list.append({
            "id": str(recipe["_id"]),
            "name": recipe["name"],
            "type": recipe["type"],
            "time": recipe["time"],
            "difficulty": recipe["difficulty"],
            "image": recipe["image"],
            "description": recipe["description"],
            "ingredient": recipe.get("ingredient", ""),
            "saved_at": recipe["saved_at"].strftime("%B %d, %Y")
        })
    
    return render_template("saved_recipes.html", recipes=recipes_list)

@app.route("/planner", methods=["GET", "POST"])
def planner():
    if "user" not in session:
        return redirect("/login")
    
    if request.method == "POST":
        # Handle meal plan updates
        day = request.form.get("day")
        meal = request.form.get("meal")
        meal_type = request.form.get("meal_type", "lunch")
        
        # Store meal plan in database
        db.meal_plans.update_one(
            {"user": session["user"], "day": day},
            {"$set": {meal_type: meal}},
            upsert=True
        )
        return redirect("/planner")
    
    # Get user's pantry items (only non-expired)
    today = datetime.today().date()
    user_items_raw = list(items.find({"user": session["user"]}))
    user_items = []
    
    for item in user_items_raw:
        expiry = datetime.strptime(item["expiry"], "%Y-%m-%d").date()
        days_left = (expiry - today).days
        
        # Only include non-expired items
        if days_left >= 0:
            item["days_left"] = days_left
            user_items.append(item)
        else:
            # Remove expired items
            items.delete_one({"_id": item["_id"]})
    
    # Get existing meal plans
    meal_plans = {}
    plans = db.meal_plans.find({"user": session["user"]})
    for plan in plans:
        meal_plans[plan["day"]] = plan
    
    # Generate smart suggestions based on expiry dates
    suggestions = []
    for item in user_items:
        days_left = item["days_left"]
        if days_left <= 7:  # Items expiring within a week
            suggestions.append({
                "name": item["name"],
                "days_left": days_left,
                "priority": "high" if days_left <= 3 else "medium"
            })
    
    suggestions.sort(key=lambda x: x["days_left"])
    
    return render_template("planner.html", items=user_items, meal_plans=meal_plans, suggestions=suggestions)

@app.route("/clear_meal/<day>/<meal_type>")
def clear_meal(day, meal_type):
    if "user" not in session:
        return redirect("/login")
    
    db.meal_plans.update_one(
        {"user": session["user"], "day": day},
        {"$unset": {meal_type: ""}}
    )
    return redirect("/planner")

@app.route("/test-expiry-email")
def test_expiry_email():
    """Test endpoint to manually trigger expiry email check (for development)"""
    if "user" not in session:
        return redirect("/login")
    
    check_expiring_items()
    return "Expiry email check triggered! Check your email if you have items expiring in 3 days or less."

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    # Start the email scheduler only in development
    if FLASK_ENV == "development":
        start_scheduler()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=(FLASK_ENV == "development"))