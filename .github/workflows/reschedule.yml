name: US Visa Appointment Rescheduler

on:
  schedule:
    # Run at 2 AM UTC daily (adjust timezone as needed)
    - cron: '0 2 * * *'
  workflow_dispatch: # Allow manual trigger
    inputs:
      max_runtime_hours:
        description: 'Maximum runtime in hours (max 6 for free tier)'
        required: false
        default: '5'
        type: choice
        options:
          - '1'
          - '2'
          - '3'
          - '4'
          - '5'
          - '6'

jobs:
  reschedule:
    runs-on: ubuntu-latest
    timeout-minutes: 360 # 6 hours max for GitHub Actions

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Chrome
        uses: browser-actions/setup-chrome@latest
        with:
          chrome-version: stable

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt

      - name: Validate required secrets
        run: |
          echo "Validating required secrets..."

          # Check required account credentials
          if [ -z "${{ secrets.USER_EMAIL }}" ]; then
            echo "❌ ERROR: USER_EMAIL secret is required"
            exit 1
          fi

          if [ -z "${{ secrets.USER_PASSWORD }}" ]; then
            echo "❌ ERROR: USER_PASSWORD secret is required"
            exit 1
          fi

          # Check date preferences
          if [ -z "${{ secrets.EARLIEST_ACCEPTABLE_DATE }}" ]; then
            echo "❌ ERROR: EARLIEST_ACCEPTABLE_DATE secret is required"
            exit 1
          fi

          if [ -z "${{ secrets.LATEST_ACCEPTABLE_DATE }}" ]; then
            echo "❌ ERROR: LATEST_ACCEPTABLE_DATE secret is required"
            exit 1
          fi

          if [ -z "${{ secrets.USER_CONSULATE }}" ]; then
            echo "❌ ERROR: USER_CONSULATE secret is required"
            exit 1
          fi

          # Check Gmail notification settings
          if [ -z "${{ secrets.GMAIL_EMAIL }}" ]; then
            echo "❌ ERROR: GMAIL_EMAIL secret is required"
            exit 1
          fi

          if [ -z "${{ secrets.GMAIL_APPLICATION_PWD }}" ]; then
            echo "❌ ERROR: GMAIL_APPLICATION_PWD secret is required"
            exit 1
          fi

          if [ -z "${{ secrets.RECEIVER_EMAIL }}" ]; then
            echo "❌ ERROR: RECEIVER_EMAIL secret is required"
            exit 1
          fi

          echo "✅ All required secrets are present"

      - name: Run visa appointment rescheduler
        env:
          # Account credentials (set these in GitHub Secrets)
          USER_EMAIL: ${{ secrets.USER_EMAIL }}
          USER_PASSWORD: ${{ secrets.USER_PASSWORD }}
          NUM_PARTICIPANTS: ${{ secrets.NUM_PARTICIPANTS || '1' }}

          # Date preferences
          EARLIEST_ACCEPTABLE_DATE: ${{ secrets.EARLIEST_ACCEPTABLE_DATE }}
          LATEST_ACCEPTABLE_DATE: ${{ secrets.LATEST_ACCEPTABLE_DATE }}
          USER_CONSULATE: ${{ secrets.USER_CONSULATE }}

          # Gmail notification settings
          GMAIL_SENDER_NAME: ${{ secrets.GMAIL_SENDER_NAME || 'Visa Appointment Reminder' }}
          GMAIL_EMAIL: ${{ secrets.GMAIL_EMAIL }}
          GMAIL_APPLICATION_PWD: ${{ secrets.GMAIL_APPLICATION_PWD }}
          RECEIVER_NAME: ${{ secrets.RECEIVER_NAME || 'User' }}
          RECEIVER_EMAIL: ${{ secrets.RECEIVER_EMAIL }}

          # Runtime settings
          SHOW_GUI: false
          TEST_MODE: false
          MAX_RUNTIME_SECONDS: ${{ github.event.inputs.max_runtime_hours || '5' }}

        run: |
          # Convert hours to seconds
          MAX_RUNTIME_SECONDS_CALC=$((MAX_RUNTIME_SECONDS * 3600))
          export MAX_RUNTIME_SECONDS=$MAX_RUNTIME_SECONDS_CALC

          echo "Starting visa appointment rescheduler..."
          echo "Target dates: $EARLIEST_ACCEPTABLE_DATE to $LATEST_ACCEPTABLE_DATE"
          echo "Consulate: $USER_CONSULATE"
          echo "Max runtime: $MAX_RUNTIME_SECONDS seconds"
          python reschedule.py

      - name: Upload logs (if any)
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: reschedule-logs
          path: |
            *.log
            logs/
          retention-days: 7
