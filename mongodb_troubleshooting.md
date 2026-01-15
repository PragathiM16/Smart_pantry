# MongoDB Atlas Connection Troubleshooting

## Most Common Issues & Solutions:

### 1. Environment Variable Not Set in Render
**Problem**: MONGO_URI still pointing to localhost
**Solution**:
1. Go to https://dashboard.render.com
2. Click your smart-pantry service
3. Click "Environment" tab
4. Add new environment variable:
   - Key: `MONGO_URI`
   - Value: Your Atlas connection string
5. Click "Save Changes"

### 2. Wrong Connection String Format
**Problem**: Using wrong connection string
**Correct Format**:
```
mongodb+srv://username:password@cluster.mongodb.net/smart_pantry?retryWrites=true&w=majority
```

**Common Mistakes**:
- ❌ `mongodb://` (should be `mongodb+srv://`)
- ❌ Missing database name `/smart_pantry`
- ❌ Wrong cluster address

### 3. Authentication Failed
**Problem**: Wrong username/password
**Solutions**:
- Check username and password are correct
- Ensure database user exists in Atlas
- URL-encode special characters in password

### 4. Network Access Issues
**Problem**: IP not whitelisted
**Solution**:
1. Go to MongoDB Atlas → Network Access
2. Click "Add IP Address"
3. Choose "Allow Access from Anywhere" (0.0.0.0/0)
4. Click "Confirm"

### 5. Special Characters in Password
**Problem**: Password has special characters
**Solution**: URL-encode them:
- `@` → `%40`
- `#` → `%23`
- `$` → `%24`
- `%` → `%25`
- `&` → `%26`

## Quick Fix Steps:

### Step 1: Get Correct Connection String
1. Go to MongoDB Atlas
2. Click "Database" → "Connect"
3. Choose "Connect your application"
4. Copy the connection string
5. Replace `<password>` with your actual password
6. Add `/smart_pantry` before the `?`

### Step 2: Add to Render
1. Go to Render dashboard
2. Environment tab
3. Add MONGO_URI variable
4. Save changes
5. Wait for redeploy

### Step 3: Test
- Check Render logs for connection success
- Try adding items in your app

## Example Working Connection String:
```
mongodb+srv://smartpantry_user:mypassword123@smart-pantry-cluster.abc12.mongodb.net/smart_pantry?retryWrites=true&w=majority
```

## Still Having Issues?
1. Check Render logs for specific error messages
2. Verify cluster is not paused in Atlas
3. Try creating a new database user
4. Ensure cluster region matches your location