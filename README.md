# US Visa Appointment Rescheduler

Automatically monitors and reschedules US visa appointments to earlier available dates.

## 🚀 Quick Start

### Cloud Deployment (Recommended)

1. **Fork/Clone this repository**
2. **Set GitHub Secrets** in your repo → Settings → Secrets and variables → Actions:
   ```
   USER_EMAIL=your_visa_account@example.com
   USER_PASSWORD=your_visa_password
   EARLIEST_ACCEPTABLE_DATE=2025-08-10
   LATEST_ACCEPTABLE_DATE=2026-05-10
   USER_CONSULATE=Toronto
   GMAIL_EMAIL=your_gmail@gmail.com
   GMAIL_APPLICATION_PWD=your_16_char_app_password
   RECEIVER_EMAIL=notifications@example.com
   ```
3. **Push to GitHub** - The workflow runs automatically at 2 AM UTC daily!

### Local Development

1. **Set up environment variables**:

   ```bash
   cp local_env.example.sh local_env.sh
   # Edit local_env.sh with your credentials
   source local_env.sh
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the script**:
   ```bash
   python reschedule.py
   ```

## 🔧 Configuration

All configuration is done via environment variables:

### Required Variables

- `USER_EMAIL` - Your visa account email
- `USER_PASSWORD` - Your visa account password
- `EARLIEST_ACCEPTABLE_DATE` - Earliest date you want (YYYY-MM-DD)
- `LATEST_ACCEPTABLE_DATE` - Latest acceptable date (YYYY-MM-DD)
- `USER_CONSULATE` - Consulate city (Toronto, Vancouver, etc.)
- `GMAIL_EMAIL` - Gmail for sending notifications
- `GMAIL_APPLICATION_PWD` - Gmail app password (16 characters)
- `RECEIVER_EMAIL` - Where to send notifications

### Optional Variables

- `NUM_PARTICIPANTS` - Number of applicants (default: 1)
- `SHOW_GUI` - Show browser window (default: false)
- `TEST_MODE` - Test mode without actual rescheduling (default: false)

## 📧 Gmail Setup

1. Enable 2-factor authentication on Gmail
2. Go to Google Account → Security → App passwords
3. Generate password for "Mail"
4. Use this 16-character password (not your regular Gmail password)

## 🕐 Scheduling

The GitHub Actions workflow runs automatically at **2 AM UTC daily**.

To change the schedule, edit `.github/workflows/reschedule.yml`:

```yaml
# Daily at different time
- cron: '0 1 * * *' # 1 AM UTC

# Every 6 hours
- cron: '0 */6 * * *'

# Weekdays only
- cron: '0 2 * * 1-5' # 2 AM UTC, Monday-Friday
```

## 🔍 Monitoring

- Check **GitHub Actions** tab for run logs
- **Email notifications** when appointments are found/rescheduled
- **Manual trigger** available in GitHub Actions

## 🏗️ Architecture

- **reschedule.py** - Main script with cloud-native configuration
- **legacy_rescheduler.py** - Handles the actual rescheduling logic
- **.github/workflows/reschedule.yml** - GitHub Actions automation
- **console_utils.py** - Pretty console output and logging

## 🚨 Troubleshooting

### Common Issues

1. **Missing environment variables**: The script will fail with clear error messages
2. **Chrome crashes**: Cloud-optimized Chrome options are included
3. **Session timeouts**: Automatic retry logic handles disconnections
4. **Gmail authentication**: Use app passwords, not regular passwords

### Logs

- GitHub Actions: Check the Actions tab in your repository
- Local: Console output shows detailed progress and errors

## 🔒 Security

- **No credentials in code**: Everything uses environment variables
- **GitHub Secrets**: Encrypted storage for sensitive data
- **App passwords**: Use Gmail app passwords for better security

## 📞 Support

If you encounter issues:

1. Check the GitHub Actions logs
2. Verify all environment variables are set correctly
3. Test Gmail credentials separately
4. Ensure the visa website hasn't changed

## 🎯 How It Works

1. **Logs into** your visa account
2. **Navigates to** appointment scheduling page
3. **Checks for** available dates earlier than your current appointment
4. **Automatically reschedules** if better dates are found
5. **Sends email** notifications on success/failure
6. **Runs continuously** until successful or timeout

Built with ❤️ for visa applicants worldwide.
