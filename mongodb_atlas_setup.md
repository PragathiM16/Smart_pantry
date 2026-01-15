# MongoDB Atlas Setup - Quick Guide

## 1. Create MongoDB Atlas Account
1. Go to: https://mongodb.com/atlas
2. Click "Try Free"
3. Sign up with your email
4. Verify your email

## 2. Create Database Cluster
1. Click "Build a Database"
2. Choose "M0 Sandbox" (FREE)
3. Choose any cloud provider (AWS recommended)
4. Choose region closest to you
5. Cluster Name: "smart-pantry-cluster"
6. Click "Create Cluster" (takes 3-5 minutes)

## 3. Create Database User
1. Click "Database Access" (left sidebar)
2. Click "Add New Database User"
3. Authentication Method: "Password"
4. Username: smartpantry_user
5. Password: Generate a secure password (SAVE THIS!)
6. Database User Privileges: "Read and write to any database"
7. Click "Add User"

## 4. Set Network Access
1. Click "Network Access" (left sidebar)
2. Click "Add IP Address"
3. Click "Allow Access from Anywhere" (0.0.0.0/0)
4. Click "Confirm"

## 5. Get Connection String
1. Go back to "Database" (left sidebar)
2. Click "Connect" button on your cluster
3. Choose "Connect your application"
4. Driver: Python, Version: 3.6 or later
5. Copy the connection string (looks like this):

mongodb+srv://smartpantry_user:<password>@smart-pantry-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority

6. Replace <password> with your actual password
7. Add database name at the end: /smart_pantry

FINAL CONNECTION STRING EXAMPLE:
mongodb+srv://smartpantry_user:yourpassword@smart-pantry-cluster.xxxxx.mongodb.net/smart_pantry?retryWrites=true&w=majority

## 6. Add to Render Environment Variables
1. Go to: https://dashboard.render.com
2. Click on your smart-pantry service
3. Click "Environment" tab
4. Add new environment variable:
   - Key: MONGO_URI
   - Value: [your connection string from step 5]
5. Click "Save Changes"

Your app will automatically redeploy and connect to the real database!