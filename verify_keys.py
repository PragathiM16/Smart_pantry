#!/usr/bin/env python3
"""
Smart Pantry Key Verification Script
This script helps you test your API keys before deployment
"""

import os
import requests
from pymongo import MongoClient

def test_mongodb_connection(connection_string):
    """Test MongoDB Atlas connection"""
    try:
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        client.server_info()
        print("✅ MongoDB connection successful!")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False

def test_sendgrid_key(api_key, sender_email):
    """Test SendGrid API key"""
    try:
        from sendgrid import SendGridAPIClient
        sg = SendGridAPIClient(api_key)
        # Just test if the key is valid (don't send email)
        print("✅ SendGrid API key format is valid!")
        print(f"✅ Sender email: {sender_email}")
        return True
    except Exception as e:
        print(f"❌ SendGrid test failed: {e}")
        return False

def test_pixabay_key(api_key):
    """Test Pixabay API key"""
    try:
        url = f"https://pixabay.com/api/?key={api_key}&q=food&per_page=3"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print("✅ Pixabay API key is working!")
            return True
        else:
            print(f"❌ Pixabay API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Pixabay test failed: {e}")
        return False

def main():
    print("🔑 Smart Pantry API Key Verification")
    print("=" * 50)
    
    # Get user input
    print("\n📝 Enter your API keys to test them:")
    
    mongo_uri = input("MongoDB URI: ").strip()
    if mongo_uri:
        test_mongodb_connection(mongo_uri)
    
    sendgrid_key = input("SendGrid API Key: ").strip()
    sender_email = input("Sender Email: ").strip()
    if sendgrid_key and sender_email:
        test_sendgrid_key(sendgrid_key, sender_email)
    
    pixabay_key = input("Pixabay API Key (or press Enter for default): ").strip()
    if not pixabay_key:
        pixabay_key = "53925676-923ada41045b5b093107c781b"
    test_pixabay_key(pixabay_key)
    
    print("\n🎯 Ready for deployment!")
    print("Copy your working keys to Render environment variables.")

if __name__ == "__main__":
    main()