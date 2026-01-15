#!/usr/bin/env python3
"""
Quick Database Setup for Smart Pantry
This script helps you set up MongoDB Atlas connection
"""

import os
import sys

def main():
    print("🚀 Smart Pantry - Database Setup Helper")
    print("=" * 50)
    
    print("\n📋 You need to:")
    print("1. Create MongoDB Atlas account (free)")
    print("2. Get your connection string")
    print("3. Add it to Render environment variables")
    
    print("\n🔗 Quick Links:")
    print("• MongoDB Atlas: https://mongodb.com/atlas")
    print("• Render Dashboard: https://dashboard.render.com")
    
    print("\n📝 Sample Connection String Format:")
    print("mongodb+srv://username:password@cluster.mongodb.net/smart_pantry?retryWrites=true&w=majority")
    
    print("\n⚙️ Environment Variables to Add in Render:")
    print("Key: MONGO_URI")
    print("Value: [your MongoDB Atlas connection string]")
    
    print("\n✅ After adding the environment variable:")
    print("• Your app will automatically redeploy")
    print("• Database connection will work")
    print("• You can add/remove items")
    print("• All features will be functional")
    
    print("\n🆘 Need help? Follow the detailed guide in:")
    print("mongodb_atlas_setup.md")

if __name__ == "__main__":
    main()