# Cloud Deployment Guide for US Visa Appointment Rescheduler

## 🚀 Quick Start Options

### Option 1: GitHub Actions (Recommended - Free)

1. **Push your code to GitHub**
2. **Set up secrets** in your GitHub repository:

   - Go to Settings → Secrets and variables → Actions
   - Add these secrets:
     ```
     USER_EMAIL=your_email@example.com
     USER_PASSWORD=your_password
     GMAIL_EMAIL=your_gmail@gmail.com
     GMAIL_APPLICATION_PWD=your_app_password
     RECEIVER_EMAIL=notification_email@example.com
     USER_CONSULATE=Toronto
     EARLIEST_ACCEPTABLE_DATE=2025-08-10
     LATEST_ACCEPTABLE_DATE=2026-05-10
     ```

3. **The workflow will run automatically** at 2 AM UTC daily
4. **Manual trigger**: Go to Actions tab → "US Visa Appointment Rescheduler" → "Run workflow"

### Option 2: Railway (Always-On)

1. **Create Railway account** at railway.app
2. **Connect your GitHub repo**
3. **Set environment variables** in Railway dashboard
4. **Deploy** - it will run continuously and restart automatically

### Option 3: Google Cloud Run + Scheduler

1. **Build and push Docker image**:

   ```bash
   docker build -t gcr.io/your-project/visa-rescheduler .
   docker push gcr.io/your-project/visa-rescheduler
   ```

2. **Deploy to Cloud Run**:

   ```bash
   gcloud run deploy visa-rescheduler \
     --image gcr.io/your-project/visa-rescheduler \
     --platform managed \
     --set-env-vars="USER_EMAIL=your_email,USER_PASSWORD=your_password"
   ```

3. **Set up Cloud Scheduler** to trigger daily

## 🔧 Environment Variables

Set these in your cloud platform:

| Variable                   | Description                 | Example                   |
| -------------------------- | --------------------------- | ------------------------- |
| `USER_EMAIL`               | Your visa account email     | `john@example.com`        |
| `USER_PASSWORD`            | Your visa account password  | `SecurePass123`           |
| `USER_CONSULATE`           | Consulate city              | `Toronto`                 |
| `EARLIEST_ACCEPTABLE_DATE` | Earliest date you want      | `2025-08-10`              |
| `LATEST_ACCEPTABLE_DATE`   | Latest acceptable date      | `2026-05-10`              |
| `GMAIL_EMAIL`              | Gmail for notifications     | `notifications@gmail.com` |
| `GMAIL_APPLICATION_PWD`    | Gmail app password          | `abcd efgh ijkl mnop`     |
| `RECEIVER_EMAIL`           | Where to send notifications | `your_phone@carrier.com`  |

## 📱 Getting Gmail App Password

1. Enable 2-factor authentication on Gmail
2. Go to Google Account settings → Security → App passwords
3. Generate password for "Mail"
4. Use this 16-character password (not your regular Gmail password)

## ⏰ Scheduling Options

### GitHub Actions Cron Examples:

```yaml
# Daily at 2 AM UTC
- cron: '0 2 * * *'

# Every 6 hours
- cron: '0 */6 * * *'

# Weekdays at 1 AM UTC
- cron: '0 1 * * 1-5'
```

### Railway Cron Jobs:

Railway runs continuously, but you can modify the script to add sleep intervals.

## 🔍 Monitoring

### GitHub Actions:

- Check the "Actions" tab in your GitHub repo
- View logs and download artifacts
- Get email notifications on failures

### Railway:

- Check the deployment logs in Railway dashboard
- Set up log alerts

### Cloud Run:

- Monitor in Google Cloud Console
- Set up Cloud Logging alerts

## 🚨 Troubleshooting

### Common Issues:

1. **Chrome crashes**:

   - Ensure `--no-sandbox` and `--disable-dev-shm-usage` flags are set
   - Use the cloud-optimized Chrome options

2. **Timeout errors**:

   - GitHub Actions has 6-hour limit
   - Adjust `MAX_RUNTIME_SECONDS` environment variable

3. **Authentication fails**:

   - Double-check credentials in secrets/environment variables
   - Ensure Gmail app password is correct

4. **Session disconnects**:
   - This is normal behavior - the script will retry automatically
   - Check if website has anti-bot measures

## 💡 Tips for Success

1. **Test locally first** with `reschedule_cloud.py`
2. **Start with short runs** to verify everything works
3. **Monitor the first few runs** closely
4. **Set up notifications** so you know when it finds appointments
5. **Keep credentials secure** - never commit them to code

## 🔒 Security Best Practices

1. **Never commit credentials** to your repository
2. **Use environment variables** for all sensitive data
3. **Regularly rotate passwords** and app passwords
4. **Monitor access logs** for unusual activity
5. **Use strong, unique passwords** for your visa account

## Support

If you encounter issues:

1. Check the deployment logs first
2. Verify all environment variables are set correctly
3. Test the local version to isolate cloud-specific issues
4. Check if the visa website has changed (may require code updates)
