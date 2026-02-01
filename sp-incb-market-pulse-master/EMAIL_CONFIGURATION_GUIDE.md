# 📧 Email Configuration Guide

## Overview
The Market Pulse system can automatically send email reports after each processing run. All configuration is managed through a simple JSON file - you only need to add your SMTP credentials.

---

## Quick Setup

### 1. Configure Email Settings

Edit the file: `sp-incb-market-pulse-master/data/email_config.json`

```json
{
  "smtp_config": {
    "host": "smtp.gmail.com",          // Your SMTP server
    "port": 587,                        // SMTP port (usually 587 for TLS)
    "use_tls": true,                    // Use TLS encryption
    "username": "your-email@gmail.com", // ⚠️ ADD YOUR EMAIL HERE
    "password": "your-app-password",    // ⚠️ ADD YOUR APP PASSWORD HERE
    "from_email": "your-email@gmail.com",
    "from_name": "Market Pulse System"
  },
  "recipients": {
    "to_emails": [
      "recipient1@example.com",         // ⚠️ ADD RECIPIENT EMAILS HERE
      "recipient2@example.com"
    ],
    "cc_emails": [],                    // Optional CC recipients
    "bcc_emails": []                    // Optional BCC recipients
  },
  "templates": {
    "subject": "Market Pulse Report - {{date}}",
    "body_html": "...",                 // Email HTML body (pre-configured)
    "body_text": "..."                  // Email plain text (pre-configured)
  },
  "settings": {
    "is_active": true,                  // ⚠️ SET TO true TO ENABLE EMAILS
    "send_on_automation": true,         // Send email after cron automation runs
    "send_on_manual_upload": false,     // Send email after manual uploads
    "attach_output_file": true,         // Attach the processed Excel file
    "attach_excluded_file": false       // Attach excluded rows file (optional)
  }
}
```

### 2. Required Configuration

**You only need to configure these 3 things:**

1. **SMTP Credentials**
   - `username`: Your email address
   - `password`: Your email app password (see below)

2. **Recipient Emails**
   - `to_emails`: List of email addresses to receive reports

3. **Enable Email**
   - `is_active`: Set to `true` to enable email functionality

---

## Gmail Setup (Recommended)

### Step 1: Generate App Password

1. Go to your Google Account: https://myaccount.google.com/
2. Navigate to **Security**
3. Enable **2-Step Verification** (required for app passwords)
4. Go to **App passwords**
5. Select app: **Mail**
6. Select device: **Other (Custom name)**
7. Name it: "Market Pulse System"
8. Click **Generate**
9. Copy the 16-character password

### Step 2: Update Configuration

```json
{
  "smtp_config": {
    "host": "smtp.gmail.com",
    "port": 587,
    "username": "yourname@gmail.com",
    "password": "xxxx xxxx xxxx xxxx",  // Paste the 16-character app password here
    "from_email": "yourname@gmail.com"
  }
}
```

---

## Other Email Providers

### Microsoft Outlook / Office 365

```json
{
  "smtp_config": {
    "host": "smtp.office365.com",
    "port": 587,
    "username": "yourname@outlook.com",
    "password": "your-password"
  }
}
```

### Yahoo Mail

```json
{
  "smtp_config": {
    "host": "smtp.mail.yahoo.com",
    "port": 587,
    "username": "yourname@yahoo.com",
    "password": "your-app-password"  // Yahoo also requires app password
  }
}
```

### Custom SMTP Server

```json
{
  "smtp_config": {
    "host": "mail.yourcompany.com",
    "port": 587,
    "username": "yourname@yourcompany.com",
    "password": "your-password"
  }
}
```

---

## Email Templates

The system includes pre-configured email templates with the following variables:

### Available Variables

You can use these placeholders in `subject`, `body_html`, and `body_text`:

- `{{date}}` - Processing date (YYYY-MM-DD)
- `{{time}}` - Processing time (HH:MM:SS)
- `{{total_processed}}` - Number of rows processed
- `{{total_excluded}}` - Number of rows excluded by rules
- `{{rules_applied}}` - Number of active rules applied
- `{{duration}}` - Processing duration
- `{{manual_files_processed}}` - Number of manual files processed

### Example Custom Subject

```json
{
  "templates": {
    "subject": "Daily Market Pulse Report - {{date}} - {{total_processed}} colors processed"
  }
}
```

---

## API Endpoints

### Test Email Configuration
```http
POST /api/email/test
```

Tests the SMTP connection without sending a report.

**Response:**
```json
{
  "success": true,
  "message": "SMTP connection successful"
}
```

### Send Manual Email
```http
POST /api/email/send
Content-Type: application/json

{
  "to_emails": ["recipient@example.com"],
  "subject": "Test Report",
  "body": "<h1>Test Email</h1>",
  "attach_output_file": true
}
```

### Get Email Configuration
```http
GET /api/email/config
```

Returns current email configuration (password is masked).

### Update Email Configuration
```http
PUT /api/email/config
Content-Type: application/json

{
  "smtp_config": {
    "username": "new-email@gmail.com",
    "password": "new-app-password"
  },
  "recipients": {
    "to_emails": ["recipient@example.com"]
  },
  "settings": {
    "is_active": true
  }
}
```

### Get Email Logs
```http
GET /api/email/logs?limit=50
```

Returns email send history.

---

## Troubleshooting

### Email Not Sending

1. **Check Configuration**
   ```json
   {
     "settings": {
       "is_active": true,
       "send_on_automation": true
     }
   }
   ```

2. **Test Connection**
   ```http
   POST /api/email/test
   ```

3. **Check Logs**
   ```http
   GET /api/email/logs
   ```

### Common Errors

**"SMTP authentication failed"**
- Verify username and password are correct
- For Gmail: Use App Password, not regular password
- Ensure 2-Step Verification is enabled (Gmail)

**"SMTP configuration incomplete"**
- Check that `host`, `username`, `password`, and `from_email` are filled
- Ensure no fields are empty strings

**"No recipient email addresses configured"**
- Add at least one email to `recipients.to_emails`

**"Connection failed"**
- Verify SMTP server address and port
- Check firewall/network settings
- Try port 465 with SSL instead of 587 with TLS

---

## Security Best Practices

1. **Use App Passwords**
   - Never use your main email password
   - Generate app-specific passwords

2. **Restrict Recipients**
   - Only add authorized recipients
   - Use BCC for privacy

3. **File Permissions**
   - Protect `email_config.json` file
   - Don't commit passwords to version control

4. **Encryption**
   - Always use TLS (`use_tls: true`)
   - Use secure SMTP ports (587 or 465)

---

## Example: Complete Setup

Here's a complete working example for Gmail:

```json
{
  "smtp_config": {
    "host": "smtp.gmail.com",
    "port": 587,
    "use_tls": true,
    "username": "marketpulse@gmail.com",
    "password": "abcd efgh ijkl mnop",
    "from_email": "marketpulse@gmail.com",
    "from_name": "Market Pulse Automated System"
  },
  "recipients": {
    "to_emails": [
      "admin@company.com",
      "team@company.com"
    ],
    "cc_emails": [
      "manager@company.com"
    ],
    "bcc_emails": []
  },
  "templates": {
    "subject": "Market Pulse Report - {{date}}",
    "body_html": "<html><body><h2>Market Pulse Processing Report</h2><p>Date: {{date}}</p><p>Time: {{time}}</p><p><strong>Processing Summary:</strong></p><ul><li>Total Rows Processed: {{total_processed}}</li><li>Rows Excluded: {{total_excluded}}</li><li>Rules Applied: {{rules_applied}}</li><li>Duration: {{duration}}</li></ul><p>Please find the processed data attached.</p><p>---<br>Market Pulse Automated System</p></body></html>",
    "body_text": "Market Pulse Processing Report\n\nDate: {{date}}\nTime: {{time}}\n\nProcessing Summary:\n- Total Rows Processed: {{total_processed}}\n- Rows Excluded: {{total_excluded}}\n- Rules Applied: {{rules_applied}}\n- Duration: {{duration}}\n\nPlease find the processed data attached.\n\n---\nMarket Pulse Automated System"
  },
  "settings": {
    "is_active": true,
    "send_on_automation": true,
    "send_on_manual_upload": false,
    "attach_output_file": true,
    "attach_excluded_file": false
  }
}
```

---

## Testing the Setup

### 1. Update Configuration
Edit `data/email_config.json` with your credentials

### 2. Test SMTP Connection
```bash
# Using curl
curl -X POST http://127.0.0.1:3334/api/email/test

# Or using PowerShell
Invoke-WebRequest -Method POST -Uri "http://127.0.0.1:3334/api/email/test"
```

### 3. Send Test Email
```bash
# Using curl
curl -X POST http://127.0.0.1:3334/api/email/send \
  -H "Content-Type: application/json" \
  -d '{"subject":"Test Report","body":"<h1>Test</h1>","attach_output_file":false}'

# Or using PowerShell
$body = @{
    subject = "Test Report"
    body = "<h1>Test Email</h1>"
    attach_output_file = $false
} | ConvertTo-Json

Invoke-WebRequest -Method POST -Uri "http://127.0.0.1:3334/api/email/send" `
    -ContentType "application/json" -Body $body
```

### 4. Trigger Automation
The email will be sent automatically after the next cron job runs:
```bash
# Manually trigger the cron job to test email
curl -X POST http://127.0.0.1:3334/api/cron/jobs/1/trigger
```

---

## Support

If you encounter issues:

1. Check email logs: `GET /api/email/logs`
2. Test SMTP connection: `POST /api/email/test`
3. Verify cron logs show `email_sent: true`: `GET /api/cron/logs`
4. Check backend console for email-related log messages

---

**Last Updated:** 2024
**Version:** 1.4.0
