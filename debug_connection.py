#!/usr/bin/env python3
"""
Debug MongoDB Atlas Connection Issues
"""

import os
from pymongo import MongoClient
from urllib.parse import quote_plus

def test_connection():
    print("🔍 MongoDB Atlas Connection Debugger")
    print("=" * 50)
    
    # Get environment variable
    mongo_uri = os.getenv("MONGO_URI", "not_set")
    
    print(f"\n📋 Current MONGO_URI: {mongo_uri[:50]}..." if len(mongo_uri) > 50 else f"\n📋 Current MONGO_URI: {mongo_uri}")
    
    if mongo_uri == "not_set" or mongo_uri == "mongodb://localhost:27017/":
        print("\n❌ PROBLEM FOUND: MONGO_URI not set properly in Render")
        print("\n🔧 SOLUTION:")
        print("1. Go to https://dashboard.render.com")
        print("2. Click your smart-pantry service")
        print("3. Go to Environment tab")
        print("4. Add MONGO_URI with your Atlas connection string")
        return False
    
    if not mongo_uri.startswith("mongodb+srv://"):
        print("\n❌ PROBLEM FOUND: Invalid connection string format")
        print("✅ Should start with: mongodb+srv://")
        print(f"❌ Your string starts with: {mongo_uri[:20]}...")
        return False
    
    # Test connection
    try:
        print("\n🔄 Testing connection...")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
        client.server_info()
        print("✅ SUCCESS: Connected to MongoDB Atlas!")
        
        # Test database operations
        db = client.smart_pantry
        test_collection = db.test
        test_doc = {"test": "connection", "timestamp": "now"}
        result = test_collection.insert_one(test_doc)
        test_collection.delete_one({"_id": result.inserted_id})
        print("✅ SUCCESS: Database operations working!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ CONNECTION FAILED: {str(e)}")
        
        if "authentication failed" in str(e).lower():
            print("\n🔧 AUTHENTICATION ERROR - Check:")
            print("• Username and password in connection string")
            print("• Database user exists in Atlas")
            print("• Password is URL-encoded (no special characters)")
            
        elif "network" in str(e).lower() or "timeout" in str(e).lower():
            print("\n🔧 NETWORK ERROR - Check:")
            print("• Network Access allows 0.0.0.0/0 in Atlas")
            print("• Cluster is running (not paused)")
            print("• Internet connection is working")
            
        elif "dns" in str(e).lower():
            print("\n🔧 DNS ERROR - Check:")
            print("• Connection string is correct")
            print("• Cluster name is correct")
            
        return False

def generate_sample_connection_string():
    print("\n📝 SAMPLE CONNECTION STRING FORMAT:")
    print("mongodb+srv://username:password@cluster-name.xxxxx.mongodb.net/smart_pantry?retryWrites=true&w=majority")
    print("\n🔧 REPLACE:")
    print("• username: Your Atlas database username")
    print("• password: Your Atlas database password (URL-encoded)")
    print("• cluster-name.xxxxx: Your actual cluster address")
    
    print("\n⚠️ SPECIAL CHARACTERS IN PASSWORD:")
    print("If your password has special characters, URL-encode them:")
    print("• @ becomes %40")
    print("• # becomes %23")
    print("• $ becomes %24")
    print("• % becomes %25")
    print("• & becomes %26")

if __name__ == "__main__":
    success = test_connection()
    if not success:
        generate_sample_connection_string()