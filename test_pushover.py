#!/usr/bin/env python3
"""
Test script for Pushover notifications
Run this to test your Pushover integration before using it with the main reschedule script.
"""

import os
import sys
from datetime import datetime

# Add current directory to path so we can import from reschedule.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up test environment variables (replace with your actual values)
os.environ["PUSHOVER_APP_TOKEN"] = ""
os.environ["PUSHOVER_USER_KEY"] = ""
os.environ["PUSHOVER_ENABLED"] = "true"

# Import our notification function
from reschedule import send_pushover_notification


def test_pushover_notifications():
    """Test different types of Pushover notifications"""

    print("🧪 Testing Pushover Notifications...")
    print("=" * 50)

    # Test 1: Slot Found Notification (Emergency Priority)
    print("\n1. Testing SLOT FOUND notification (Emergency Priority)...")
    success1 = send_pushover_notification(
        title="🎯 TEST: VISA SLOT FOUND",
        message="Test slot found at Toronto!\nThis is a test notification with emergency priority.",
        priority=2,  # Emergency
        sound="alien",
        url="https://ais.usvisa-info.com/en-ca/niv/schedule/60227641/appointment",
        url_title="Login to your account",
    )
    print(f"   Result: {'✅ Success' if success1 else '❌ Failed'}")

    # Wait a moment between notifications
    import time

    time.sleep(5)

    # Test 2: Success Notification (High Priority)
    print("\n2. Testing SUCCESS notification (High Priority)...")
    success2 = send_pushover_notification(
        title="✅ TEST: APPOINTMENT BOOKED",
        message="Test booking successful for 2024-06-15!\nThis is a test notification.",
        priority=1,  # High
        sound="magic",
    )
    print(f"   Result: {'✅ Success' if success2 else '❌ Failed'}")

    time.sleep(5)

    # Test 3: Failure Notification (Normal Priority)
    print("\n3. Testing FAILURE notification (Normal Priority)...")
    success3 = send_pushover_notification(
        title="❌ TEST: BOOKING FAILED",
        message="Test booking failed.\nReason: This is just a test.\nContinuing to search...",
        priority=1,  # High
        sound="falling",
    )
    print(f"   Result: {'✅ Success' if success3 else '❌ Failed'}")

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   Slot Found:  {'✅' if success1 else '❌'}")
    print(f"   Success:     {'✅' if success2 else '❌'}")
    print(f"   Failure:     {'✅' if success3 else '❌'}")

    total_success = sum([success1, success2, success3])
    print(f"\n   Overall: {total_success}/3 notifications sent successfully")

    if total_success == 3:
        print("\n🎉 All tests passed! Pushover integration is working correctly.")
        print("   You should have received 3 test notifications on your iPhone.")
    else:
        print("\n⚠️  Some tests failed. Please check:")
        print("   - Your PUSHOVER_APP_TOKEN is correct")
        print("   - Your PUSHOVER_USER_KEY is correct")
        print("   - You have internet connectivity")
        print("   - The Pushover app is installed on your iPhone")


if __name__ == "__main__":
    # Check if credentials are set
    if os.environ.get("PUSHOVER_APP_TOKEN") == "your_app_token_here":
        print("❌ Please edit this script and add your actual Pushover credentials!")
        print("\nTo get your credentials:")
        print("1. App Token: Go to https://pushover.net/apps/build")
        print("2. User Key: Go to https://pushover.net/ (shown on your dashboard)")
        print(
            "\nThen edit the PUSHOVER_APP_TOKEN and PUSHOVER_USER_KEY values in this script."
        )
        sys.exit(1)

    test_pushover_notifications()
