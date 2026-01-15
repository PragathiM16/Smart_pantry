# Smart Pantry Deployment Guide - Render + MongoDB Atlas

## Step 1: Set up MongoDB Atlas

### 1.1 Create MongoDB Atlas Account
1. Go to [mongodb.com/atlas](https://mongodb.com/atlas)
2. Sign up for a free account
3. Create a new project called "Smart Pantry"

### 1.2 Create a Cluster
1. Click "Build a Database"
2. Choose "M0 Sandbox" (Free tier)
3. Select your preferred cloud provider and region
4. Name your cluster "smart-pantry-cluster"
5. Click "Create Cluster"

### 1.3 Create Database User
1. Go to "Database Access" in the left sidebar
2. Click "Add New Database User"
3. Choose "Password" authentication
4. Username: `smartpantry_user`
5. Generate a secure password (save it!)
6. Database User Privileges: "Read and write to any database"
7. Click "Add User"

### 1.4 Configure Network Access
1. Go to "Network Access" in the left sidebar
2. Click "Add IP Address"
3. Choose "Allow Access from Anywhere" (0.0.0.0/0)
4. Click "Confirm"

### 1.5 Get Connection String
1. Go to "Database" in the left sidebar
2. Click "Connect" on your cluster
3. Choose "Connect your application"
4. Select "Python" and version "3.6 or later"
5. Copy the connection string (looks like):
   ```
   mongodb+srv://smartpantry_user:<password>@smart-pantry-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
6. Replace `<password>` with your actual password
7. Add database name at the end: `/smart_pantry`

**Final connection string example:**
```
mongodb+srv://smartpantry_user:yourpassword@smart-pantry-cluster.xxxxx.mongodb.net/smart_pantry?retryWrites=true&w=majority
```

## Step 2: Set up MongoDB Compass (Optional)

### 2.1 Download MongoDB Compass
1. Go to [mongodb.com/products/compass](https://mongodb.com/products/compass)
2. Download and install MongoDB Compass

### 2.2 Connect to Your Atlas Database
1. Open MongoDB Compass
2. Use the same connection string from Step 1.5
3. Click "Connect"
4. You can now view and manage your database visually

## Step 3: Deploy to Render

### 3.1 Prepare Your Code
1. Make sure all files are in your project directory
2. Push your code to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initial commit for Smart Pantry"
   git remote add origin https://github.com/yourusername/smart-pantry.git
   git push -u origin main
   ```

### 3.2 Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with your GitHub account
3. Authorize Render to access your repositories

### 3.3 Deploy Web Service
1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Select "smart-pantry" repository
4. Configure the service:
   - **Name**: `smart-pantry`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Plan**: `Free`

### 3.4 Add Environment Variables
In the Render dashboard, add these environment variables:

```
MONGO_URI=mongodb+srv://smartpantry_user:yourpassword@smart-pantry-cluster.xxxxx.mongodb.net/smart_pantry?retryWrites=true&w=majority
SECRET_KEY=your_super_secret_random_key_here_make_it_long_and_random
FLASK_ENV=production
SENDER_EMAIL=your_email@gmail.com
SENDGRID_API_KEY=SG.your_sendgrid_api_key_here
PIXABAY_API_KEY=your_pixabay_api_key_here
```

### 3.5 Deploy
1. Click "Create Web Service"
2. Render will automatically build and deploy your app
3. Wait for the build to complete (5-10 minutes)
4. Your app will be available at: `https://smart-pantry.onrender.com`

## Step 4: Set up SendGrid (Email Service)

### 4.1 Create SendGrid Account
1. Go to [sendgrid.com](https://sendgrid.com)
2. Sign up for free account (100 emails/day free)
3. Verify your email address

### 4.2 Create API Key
1. Go to Settings → API Keys
2. Click "Create API Key"
3. Choose "Restricted Access"
4. Give it "Mail Send" permissions
5. Copy the API key (starts with "SG.")
6. Add it to your Render environment variables

### 4.3 Verify Sender Identity
1. Go to Settings → Sender Authentication
2. Verify your sender email address
3. Use this email in the `SENDER_EMAIL` environment variable

## Step 5: Set up Pixabay (Optional - for food images)

### 5.1 Create Pixabay Account
1. Go to [pixabay.com](https://pixabay.com)
2. Sign up for free account
3. Go to [pixabay.com/api/docs/](https://pixabay.com/api/docs/)
4. Get your API key
5. Add it to Render environment variables

## Step 6: Test Your Deployment

### 6.1 Basic Functionality Test
1. Visit your Render URL
2. Test user registration
3. Test login
4. Add pantry items
5. Check recipe generation
6. Test meal planning

### 6.2 Database Verification
1. Open MongoDB Compass
2. Connect to your Atlas database
3. Check if collections are created:
   - `users`
   - `items`
   - `meal_plans`
   - `saved_recipes`
   - `hidden_recipes`

### 6.3 Email Testing
1. Register a new account
2. Check if welcome email is received
3. Add items with short expiry dates
4. Check if expiry notifications work

## Troubleshooting

### Common Issues:

1. **Build Fails**: Check requirements.txt and Python version
2. **Database Connection Error**: Verify MongoDB connection string and network access
3. **Email Not Sending**: Check SendGrid API key and sender verification
4. **App Crashes**: Check Render logs in the dashboard

### Render Logs:
- Go to your service dashboard
- Click "Logs" tab to see real-time logs
- Look for error messages

### MongoDB Atlas Monitoring:
- Go to your Atlas dashboard
- Check "Metrics" tab for connection issues
- Use "Real Time" tab to see live database activity

## Your App URLs:
- **Live App**: `https://your-app-name.onrender.com`
- **MongoDB Atlas**: `https://cloud.mongodb.com`
- **Render Dashboard**: `https://dashboard.render.com`

## Security Notes:
- Never commit API keys to GitHub
- Use strong passwords for MongoDB
- Regularly rotate API keys
- Monitor usage in all services

## Support:
- Render: [render.com/docs](https://render.com/docs)
- MongoDB Atlas: [docs.atlas.mongodb.com](https://docs.atlas.mongodb.com)
- SendGrid: [docs.sendgrid.com](https://docs.sendgrid.com)