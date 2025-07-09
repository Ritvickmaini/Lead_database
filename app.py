import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

# --- Google Sheets Setup ---
SHEET_NAME = "Expo-Sales-Management"
SHEET_TAB = "speakers-2"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
CREDS_FILE = "/etc/secrets/service_account.json"

# --- Start the automation loop ---
while True:
    try:
        creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
        gc = gspread.authorize(creds)
        sheet = gc.open(SHEET_NAME).worksheet(SHEET_TAB)

        # --- Step 1: Get existing emails from column M (13th column) ---
        existing_emails = set(email.strip().lower() for email in sheet.col_values(13)[1:])  # Skip header

        # --- Step 2: Fetch data from protected API ---
        url = "https://b2bgrowthexpo.com/wp-json/custom-api/v1/protected/fetch-form-data"
        headers = {
            "Authorization": "Bearer e3e6836eb425245556aebc1e0a9e5bfbb41ee9c81ec5db1bc121debc5907fd85"
        }

        response = requests.get(url, headers=headers)
        form_data = response.json()
        entries = form_data.get("data", [])

        new_rows = []

        for item in entries:
            form_entry = item.get("Form_Entry", {})
            email = form_entry.get("Email", "").strip().lower()
            if not email or email in existing_emails:
                continue

            first_name = form_entry.get("First Name", "").strip()
            last_name = form_entry.get("Last Name", "").strip()

            # ✅ Skip if name contains "test"
            if "test" in first_name.lower() or "test" in last_name.lower():
                continue

            # Parse form_date
            form_date_raw = item.get("form_date", "")
            form_date = ""
            parsed_form_date = None
            if form_date_raw:
                try:
                    parsed_form_date = datetime.strptime(form_date_raw, "%Y-%m-%d %H:%M:%S")
                    if parsed_form_date < datetime(2025, 7, 8):
                        continue  # Skip older entries
                    form_date = parsed_form_date.strftime("%d-%m-%Y")
                except:
                    continue  # Skip invalid date

            # Prepare row
            row = [
                form_date,
                "Website",
                first_name,
                last_name,
                "",
                "",
                form_entry.get("Business Name", ""),
                "",
                "Speaker",
                "",
                "",
                form_entry.get("Mobile Number", ""),
                email,
                form_entry.get("Select Location Of Interest", "")
            ]

            new_rows.append(row)
            existing_emails.add(email)

        # --- Step 4: Append rows to Google Sheet ---
        if new_rows:
            sheet.append_rows(new_rows, value_input_option="USER_ENTERED")
            print(f"[{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}] ✅ Added {len(new_rows)} new entries.")
        else:
            print(f"[{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}] 🔁 No new unique entries to add.")

    except Exception as e:
        print(f"[{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}] ❌ Error: {e}")

    # --- Wait 2 hours before running again ---
    time.sleep(7200)
