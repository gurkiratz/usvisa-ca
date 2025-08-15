# 🚀 Pushover Setup Guide

This guide will help you set up instant Pushover notifications for your US Visa appointment finder.

## 📱 What You'll Get

- **Instant notifications** (< 1 second delivery) when slots are found
- **Emergency priority** notifications that bypass Do Not Disturb
- **Custom sounds** for different notification types
- **Email backup** notifications still work as before

## 🔧 Setup Steps

### 1. Create Pushover Account & App

1. **Download Pushover app** on your iPhone from the App Store
2. **Create account** at https://pushover.net/
3. **Create an application** at https://pushover.net/apps/build
   - Name: "US Visa Appointment Finder" (or any name you prefer)
   - Description: "Notifications for visa appointment slots"
   - URL: (leave blank)
   - Icon: (optional)

### 2. Get Your Credentials

After creating the app, you'll need two keys:

1. **App Token**: Found on your app's page after creation (starts with `a`)
2. **User Key**: Found on your Pushover dashboard (starts with `u`)

### 3. Configure Your Environment

Add these to your environment variables or settings:

```bash
# Add to your local_env.sh or cloud environment
export PUSHOVER_APP_TOKEN="your_app_token_here"
export PUSHOVER_USER_KEY="your_user_key_here"
export PUSHOVER_ENABLED="true"
```

### 4. Test Your Setup

Run the test script to verify everything works:

```bash
# Edit test_pushover.py with your actual credentials first
python test_pushover.py
```

You should receive 3 test notifications on your iPhone.

## 🔊 Notification Types

### 🎯 Slot Found (Emergency Priority)

- **Sound**: Siren
- **Priority**: Emergency (bypasses Do Not Disturb)
- **Retries**: Every 30 seconds for 1 hour until acknowledged

### ✅ Booking Success (High Priority)

- **Sound**: Magic
- **Priority**: High (important but not emergency)

### ❌ Booking Failed (High Priority)

- **Sound**: Falling
- **Priority**: High (you should know, but not emergency)

## 🛠️ How It Works

The system now sends **both** Pushover and email notifications:

1. **Pushover first** (instant, synchronous) - for immediate alerts
2. **Email second** (async, background) - for record keeping

This gives you the best of both worlds: instant notifications AND email records.

## 🚨 Emergency Priority Features

When a slot is found, the notification uses **Emergency Priority** which:

- ✅ Bypasses Do Not Disturb mode
- ✅ Repeats every 30 seconds until you acknowledge it
- ✅ Shows as a banner even when phone is locked
- ✅ Plays loud siren sound

Perfect for when you're sleeping but don't want to miss a slot!

## 📋 Configuration Options

In your settings, you can customize:

```python
# Disable Pushover (keeps email only)
PUSHOVER_ENABLED = False

# Different app token for testing vs production
PUSHOVER_APP_TOKEN = "your_production_token"
```

## 🔍 Troubleshooting

### No notifications received?

1. Check your credentials are correct
2. Ensure Pushover app is installed and logged in
3. Check internet connectivity
4. Run the test script to verify

### Notifications delayed?

- Pushover notifications should be instant (< 1 second)
- If delayed, check your internet connection
- Emergency priority notifications retry automatically

### Want different sounds?

Edit the `sound` parameter in the notification functions:

- Available sounds: pushover, bike, bugle, cashregister, classical, cosmic, falling, gamelan, incoming, intermission, magic, mechanical, pianobar, siren, spacealarm, tugboat, alien, climb, persistent, echo, updown, none

## 🎉 You're All Set!

Once configured, your visa appointment finder will send instant Pushover notifications to your iPhone whenever:

- 🎯 A slot is found
- ✅ Booking succeeds
- ❌ Booking fails

The Gmail notifications continue to work as backup, so you have redundant notification channels for maximum reliability.

Good luck with your visa appointment search! 🍀
