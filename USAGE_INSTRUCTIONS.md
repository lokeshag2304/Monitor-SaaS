# 🚀 MoniFy-Ping - Complete Usage Instructions

## 📍 Application Access

**Server is running at:**
- **Frontend (Login):** http://127.0.0.1:5000/static/index.html
- **Dashboard:** http://127.0.0.1:5000/static/dashboard.html
- **API Documentation:** http://127.0.0.1:5000/docs
- **Health Check:** http://127.0.0.1:5000/health

---

## 🎯 Quick Start Guide

### Step 1: Access the Application
1. Open your web browser
2. Navigate to: **http://127.0.0.1:5000/static/index.html**

### Step 2: Create Your Account
1. Click **"Sign Up"** link on the login page
2. Fill in:
   - **Name:** Your full name
   - **Email:** Your email address
   - **Password:** Choose a secure password
3. Click **"Create Account"**
4. You'll be automatically logged in

### Step 3: Add Your First Monitor
1. Once logged in, you'll see the dashboard
2. Click the **"Create new"** button (top right)
3. Fill in the form:
   - **Display Name:** e.g., "Production Server"
   - **URL:** e.g., "google.com" or "https://example.com"
   - **Interval:** Check frequency in minutes (default: 5)
4. Click **"Create Monitor"**
5. Your website will start being monitored automatically!

---

## 📊 Dashboard Features

### Main Dashboard View
- **Statistics Cards:** Shows UP, DOWN, and PAUSED monitor counts
- **Monitor Table:** Lists all your monitored websites with:
  - Host name and URL
  - Current status (UP/DOWN/UNKNOWN)
  - Response time
  - Protocol type (HTTP/HTTPS)
  - Delete action

### Sidebar Navigation
- **Uptime:** Main dashboard (default view)
- **Pagespeed:** Check website speed (opens modal)
- **Infrastructure:** (Future feature)
- **Notifications:** View incidents and errors
- **Incidents:** View recent downtime incidents
- **Status pages:** (Future feature)
- **Maintenance:** (Future feature)

### Top Bar Actions
- **Theme Toggle:** Switch between light/dark mode (moon/sun icon)
- **Create new:** Add a new website monitor
- **Bulk Import:** (Admin only) Import multiple URLs at once

---

## 👤 User Settings

### Access Settings
1. Click the **Settings icon** (gear icon) in the bottom-left sidebar
2. View your profile information:
   - Name
   - Email
   - Role (Team Member or Super Admin)

### Admin Features (Super Admin Only)
If you're an admin, you'll see:
- **"SUPER ADMIN" badge** next to "Uptime" title
- **"Bulk Import" button** in the top bar
- **Admin panel** in Settings with:
  - **"Fetch All Logs"** button to view system logs
  - All users list
  - All monitoring check results

---

## 🔧 Key Features Explained

### 1. Website Monitoring
- **Automatic Checks:** Websites are checked every 5 minutes (or your custom interval)
- **Status Updates:** Real-time status updates on the dashboard
- **Email Alerts:** Receive email notifications when sites go DOWN or come back UP
- **Response Time:** Track how fast your websites respond

### 2. PageSpeed Check
1. Click **"Pagespeed"** in the sidebar
2. Enter a URL (e.g., "google.com")
3. Click **"Check Speed"**
4. View response time and status code

### 3. Bulk Import (Admin Only)
1. Click **"Bulk Import"** button (top right, admin only)
2. Enter multiple URLs, one per line or separated by commas:
   ```
   google.com
   github.com
   stackoverflow.com
   ```
3. Click **"Import"**
4. All websites will be added as monitors

### 4. Delete a Monitor
1. Find the website in the table
2. Click **"Delete"** button in the Actions column
3. Confirm deletion

### 5. Theme Toggle
- Click the **moon/sun icon** in the top bar
- Toggle between dark mode (default) and light mode
- Your preference is saved automatically

---

## 📧 Email Alerts Setup

### Configure Email Notifications
1. Create a `.env` file in the project root directory
2. Add your SMTP credentials:
   ```env
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your_email@gmail.com
   SMTP_PASSWORD=your_app_password
   ```
3. **For Gmail:**
   - Enable 2-Factor Authentication
   - Generate App Password: https://myaccount.google.com/apppasswords
   - Use the app password (not your regular password)
4. Restart the server
5. You'll receive emails when:
   - A website goes DOWN
   - A website comes back UP

**See `EMAIL_SETUP.md` for detailed instructions.**

---

## 🔐 Admin Access

### Making a User Admin
1. The first user you create is typically a regular user
2. To make a user admin, you need to update the database:
   - Open the database: `data/monitoring.db`
   - Update the `users` table
   - Set `role = 'admin'` for the desired user
   - Or use SQL: `UPDATE users SET role = 'admin' WHERE email = 'user@example.com'`

### Admin Capabilities
- View all users' websites (not just your own)
- Access admin logs and system information
- Use bulk import feature
- See "SUPER ADMIN" badge in UI

---

## 🛠️ Troubleshooting

### Server Not Starting?
- Check if port 5000 is already in use
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check for error messages in the terminal

### Can't Login?
- Make sure you've registered an account first
- Check that the server is running
- Verify email and password are correct
- Check browser console for errors

### Websites Not Updating?
- Monitoring checks run every 5 minutes
- Wait a few minutes for the first check
- Check server logs for monitoring errors
- Verify the URL is accessible

### Email Not Sending?
- Check `.env` file exists and has correct SMTP credentials
- Verify SMTP settings are correct
- Check server logs for email errors
- For Gmail, ensure you're using an App Password

### Dashboard Not Loading?
- Check browser console for JavaScript errors
- Verify you're logged in (check localStorage for token)
- Try refreshing the page
- Clear browser cache if needed

---

## 📱 Keyboard Shortcuts

- **Escape:** Close any open modal
- **Tab:** Navigate between form fields
- **Enter:** Submit forms

---

## 🔄 Real-time Updates

- Dashboard automatically refreshes every **5 seconds**
- Website status updates in real-time
- No need to manually refresh the page

---

## 📝 Tips & Best Practices

1. **Monitor Important URLs:** Add your production websites, APIs, and critical services
2. **Set Appropriate Intervals:** 
   - Critical sites: 1-2 minutes
   - Regular sites: 5 minutes
   - Less critical: 10-15 minutes
3. **Use Descriptive Names:** Give monitors clear, descriptive names
4. **Check Email Alerts:** Set up email alerts for critical websites
5. **Review Incidents:** Check the Notifications section regularly
6. **Admin Monitoring:** Admins can monitor all users' websites

---

## 🆘 Need Help?

- **API Documentation:** http://127.0.0.1:5000/docs
- **Server Logs:** Check the terminal where the server is running
- **Browser Console:** Press F12 to see JavaScript errors
- **Health Check:** http://127.0.0.1:5000/health

---

## 🎉 You're All Set!

Your MoniFy-Ping monitoring system is ready to use. Start by adding your first website monitor and watch it track your sites automatically!

**Happy Monitoring! 🚀**

