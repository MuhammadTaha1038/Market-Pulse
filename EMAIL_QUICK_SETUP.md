# 📧 Email Configuration - Quick Reference

## ⚡ 3-Step Setup

### Step 1: Edit Configuration File
```
File: sp-incb-market-pulse-master/data/email_config.json
```

### Step 2: Add These 3 Things
```json
{
  "smtp_config": {
    "username": "your-email@gmail.com",    ← ADD YOUR EMAIL
    "password": "xxxx xxxx xxxx xxxx"       ← ADD APP PASSWORD
  },
  "recipients": {
    "to_emails": ["recipient@example.com"]  ← ADD RECIPIENT
  },
  "settings": {
    "is_active": true                       ← ENABLE EMAILS
  }
}
```

### Step 3: Test It
```powershell
# Test SMTP connection
Invoke-WebRequest -Method POST -Uri "http://127.0.0.1:3334/api/email/test"

# Send test email
Invoke-WebRequest -Method POST -Uri "http://127.0.0.1:3334/api/email/send" `
  -ContentType "application/json" `
  -Body '{"subject":"Test","body":"<h1>Test</h1>"}'
```

---

## 🔑 Gmail App Password (Required)

1. Go to: https://myaccount.google.com/security
2. Enable **2-Step Verification** (if not already)
3. Click **App passwords**
4. Select: **Mail** → **Other (Custom name)**
5. Name: "Market Pulse"
6. Click **Generate**
7. **Copy the 16-character password**
8. Paste into `email_config.json` → `smtp_config.password`

---

## 📋 Common SMTP Settings

### Gmail
```json
{
  "host": "smtp.gmail.com",
  "port": 587,
  "username": "yourname@gmail.com",
  "password": "app-password-here"
}
```

### Outlook
```json
{
  "host": "smtp.office365.com",
  "port": 587,
  "username": "yourname@outlook.com",
  "password": "your-password"
}
```

### Yahoo
```json
{
  "host": "smtp.mail.yahoo.com",
  "port": 587,
  "username": "yourname@yahoo.com",
  "password": "app-password-here"
}
```

---

## 🧪 Quick Test Commands

```powershell
# Get current config
Invoke-WebRequest -Method GET -Uri "http://127.0.0.1:3334/api/email/config"

# Test SMTP
Invoke-WebRequest -Method POST -Uri "http://127.0.0.1:3334/api/email/test"

# Check email logs
Invoke-WebRequest -Method GET -Uri "http://127.0.0.1:3334/api/email/logs"

# Manual trigger cron (to test automation email)
Invoke-WebRequest -Method POST -Uri "http://127.0.0.1:3334/api/cron/jobs/1/trigger"
```

---

## 🎯 Enable Automation Emails

Edit `email_config.json`:
```json
{
  "settings": {
    "is_active": true,              ← Master enable
    "send_on_automation": true,     ← Email after cron runs
    "send_on_manual_upload": false, ← Email after manual uploads
    "attach_output_file": true      ← Attach Excel file
  }
}
```

---

## 🚨 Troubleshooting

### "SMTP authentication failed"
→ Use App Password (not regular password)
→ Enable 2-Step Verification for Gmail

### "SMTP configuration incomplete"
→ Check: host, username, password, from_email are filled

### "No recipient email addresses configured"
→ Add at least one email to recipients.to_emails

### Email not sending automatically
→ Check settings.is_active = true
→ Check settings.send_on_automation = true
→ Check cron logs: GET /api/cron/logs

---

## ✅ Verification Checklist

- [ ] Email credentials added to config
- [ ] Recipient emails added
- [ ] is_active set to true
- [ ] SMTP test returns success
- [ ] Test email sends successfully
- [ ] send_on_automation enabled (if wanted)
- [ ] Cron job triggered successfully
- [ ] Email received (check spam folder)

---

## 📖 Full Documentation

See: `EMAIL_CONFIGURATION_GUIDE.md` for complete details

---

**Quick Help:** All endpoints at http://127.0.0.1:3334/api/email/*
