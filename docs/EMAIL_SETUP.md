# Email Alerting Setup Guide

MoniFy-Ping automatically sends email alerts when your monitored websites go DOWN or come back UP.

## Quick Setup

1. **Create a `.env` file** in the project root directory (same level as `backend/` and `frontend/`)

2. **Add your SMTP credentials** to the `.env` file:

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

3. **Restart your FastAPI server** to load the new configuration

## Gmail Setup (Recommended)

1. **Enable 2-Factor Authentication** on your Google Account
   - Go to: https://myaccount.google.com/security

2. **Generate an App Password**
   - Visit: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Enter "MoniFy-Ping" as the name
   - Copy the generated 16-character password

3. **Add to `.env` file**:
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
```

## Other Email Providers

### Outlook/Hotmail
```env
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=your_email@outlook.com
SMTP_PASSWORD=your_password
```

### Custom SMTP Server
```env
SMTP_SERVER=smtp.yourdomain.com
SMTP_PORT=587
SMTP_USER=noreply@yourdomain.com
SMTP_PASSWORD=your_password
```

## How It Works

- **Automatic Alerts**: Emails are sent automatically when:
  - A website goes from UP → DOWN
  - A website goes from DOWN → UP (recovery notification)

- **Email Content**:
  - **DOWN Alert**: Includes website URL, status, and error details
  - **UP Alert**: Confirmation that the website is back online

- **Recipient**: Emails are sent to the website owner's registered email address

## Testing

1. Add a test website to monitor
2. Stop the website (or use a non-existent URL)
3. Wait for the monitoring check (runs every 5 minutes by default)
4. Check your email inbox for the alert

## Troubleshooting

- **Email not sending?** Check the server console logs for error messages
- **"SMTP not configured" message?** Make sure your `.env` file is in the project root and contains valid credentials
- **Gmail authentication failed?** Make sure you're using an App Password, not your regular password
- **Still not working?** Check that `python-dotenv` is installed: `pip install python-dotenv`

## Security Note

⚠️ **Never commit your `.env` file to version control!** It contains sensitive credentials.

Make sure `.env` is in your `.gitignore` file.

