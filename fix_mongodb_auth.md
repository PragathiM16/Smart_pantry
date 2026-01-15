# Fix MongoDB Authentication Error

## Your Error:
```
❌ MongoDB connection failed: bad auth : authentication failed
```

## Quick Fix Steps:

### Step 1: Create New Database User in Atlas
1. Go to https://cloud.mongodb.com
2. Click "Database Access" (left sidebar)
3. Click "Add New Database User"
4. Fill in:
   - **Username**: `smartpantry_admin`
   - **Password**: `SmartPantry2024!` (or generate secure password)
   - **Database User Privileges**: "Read and write to any database"
5. Click "Add User"

### Step 2: Get Your Cluster Address
1. Go to "Database" (left sidebar)
2. Click "Connect" on your cluster
3. Choose "Connect your application"
4. Copy the connection string
5. It looks like: `mongodb+srv://smartpantry_admin:<password>@cluster-name.xxxxx.mongodb.net/?retryWrites=true&w=majority`

### Step 3: Build Your Connection String
Replace the placeholders:
```
mongodb+srv://smartpantry_admin:SmartPantry2024!@YOUR-CLUSTER-ADDRESS/smart_pantry?retryWrites=true&w=majority
```

**Example**:
```
mongodb+srv://smartpantry_admin:SmartPantry2024!@smart-pantry-cluster.abc12.mongodb.net/smart_pantry?retryWrites=true&w=majority
```

### Step 4: Update Render Environment Variable
1. Go to https://dashboard.render.com
2. Click your smart-pantry service
3. Click "Environment" tab
4. Find `MONGO_URI` and click "Edit"
5. Replace with your new connection string
6. Click "Save Changes"

### Step 5: Wait for Redeploy
- Render will automatically redeploy (5 minutes)
- Check logs for "✅ Connected to MongoDB successfully!"

## Common Issues:

### Special Characters in Password
If your password has special characters, URL-encode them:
- `@` becomes `%40`
- `#` becomes `%23`
- `$` becomes `%24`
- `!` becomes `%21`

### Wrong Cluster Address
Make sure you're using the correct cluster address from Atlas, not a generic one.

### User Doesn't Exist
Make sure the database user actually exists in Atlas under "Database Access".

## Test Your Connection:
After updating, visit: `https://your-app.onrender.com/debug/connection`