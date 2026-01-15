#!/usr/bin/env python3
"""
Smart Pantry Deployment Setup Script
This script helps you prepare for deployment to Render with MongoDB Atlas
"""

import os
import secrets
import string

def generate_secret_key(length=50):
    """Generate a secure secret key"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def main():
    print("🥗 Smart Pantry Deployment Setup")
    print("=" * 40)
    
    # Generate secret key
    secret_key = generate_secret_key()
    print(f"✅ Generated SECRET_KEY: {secret_key}")
    
    print("\n📋 Environment Variables for Render:")
    print("-" * 40)
    print(f"SECRET_KEY={secret_key}")
    print("FLASK_ENV=production")
    print("MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/smart_pantry")
    print("SENDER_EMAIL=your_email@example.com")
    print("SENDGRID_API_KEY=SG.your_sendgrid_key")
    print("PIXABAY_API_KEY=your_pixabay_key")
    
    print("\n📝 Next Steps:")
    print("1. Set up MongoDB Atlas (see DEPLOYMENT_GUIDE.md)")
    print("2. Get SendGrid API key")
    print("3. Push code to GitHub")
    print("4. Deploy to Render")
    print("5. Add environment variables in Render dashboard")
    
    print("\n🔗 Useful Links:")
    print("- MongoDB Atlas: https://mongodb.com/atlas")
    print("- Render: https://render.com")
    print("- SendGrid: https://sendgrid.com")
    print("- Deployment Guide: ./DEPLOYMENT_GUIDE.md")

if __name__ == "__main__":
    main()