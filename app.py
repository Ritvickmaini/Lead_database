import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

# --- Google Sheets Setup ---
SHEET_NAME = "Expo-Sales-Management"
SHEET_TAB = "speakers-2"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
CREDS_FILE = "/etc/secrets/service_account.json"

API_URL = "https://b2bgrowthexpo.com/wp-json/custom-api/v1/protected/speaker-form-data"
API_TOKEN = "Bearer e3e6836eb425245556aebc1e0a9e5bfbb41ee9c81ec5db1bc121debc5907fd85"

def run_script():
    print("🔧 Connecting to Google Sheets...", flush=True)
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sheet = gc.open(SHEET_NAME).worksheet(SHEET_TAB)

    # --- Existing emails (Column G) ---
    existing_emails = {
        e.strip().lower()
        for e in sheet.col_values(7)[1:]
        if e.strip()
    }

    print(f"📦 Existing emails: {len(existing_emails)}", flush=True)

    # --- Fetch API data ---
    headers = {"Authorization": API_TOKEN}
    response = requests.get(API_URL, headers=headers)
    response.raise_for_status()

    entries = response.json().get("data", [])
    print(f"📥 API entries received: {len(entries)}", flush=True)

    new_leads = []

    for item in entries:
        if not isinstance(item, dict):
            continue

        form_entry = item.get("Form_Entry", {})
        if not isinstance(form_entry, dict):
            continue

        email = form_entry.get("Email", "").strip().lower()
        if not email or email in existing_emails:
            continue

        # --- Parse date ---
        form_date = ""
        raw_date = item.get("form_date")
        try:
            parsed_date = datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S")
            form_date = parsed_date.strftime("%d/%m/%Y")
        except Exception:
            continue

        row = [
            form_date,                                        # A Lead Date
            "Website",                                        # B Lead Source
            form_entry.get("First Name", ""),                 # C
            form_entry.get("Last Name", ""),                  # D
            form_entry.get("Business Name", ""),              # E Company
            form_entry.get("Mobile Number", ""),              # F Mobile
            email,                                            # G Email
            form_entry.get("Select Location Of Interest", ""),# H Show
            "",                                               # I Next Followup
            "",                                               # J Call Attempt
            "",                                               # K Email Count
            "",                                               # L WhatsApp Count
            "",                                               # M LinkedIn Msg Count
            "",                                               # N Meeting Booked
            "",                                               # O Comments
            "",                                               # P Pitch Deck
            "Speaker_opportunity",                             # Q Interested In
            "",                                               # R Email Sent Date
            "",                                               # S Reply Status
            "",                                               # T Designation
            form_entry.get(
                "Business Linkedln Page Or Website", ""
            ),                                                # U Company LinkedIn
            form_entry.get("LinkedIn ProfileLink", "")        # V Personal LinkedIn
        ]

        new_leads.append(row)
        existing_emails.add(email)

    print(f"🧾 New leads to insert: {len(new_leads)}", flush=True)

    if new_leads:
        for row in reversed(new_leads):
            sheet.insert_row(
                row,
                index=2,
                value_input_option="USER_ENTERED",
                inherit_from_before=False
            )
        print("✅ Leads inserted successfully", flush=True)
    else:
        print("🔁 No new leads found", flush=True)

# --- Run every 2 hours ---
while True:
    try:
        print("\n🔄 Sync started...", flush=True)
        run_script()
    except Exception as e:
        print(f"❌ Error: {e}", flush=True)

    print("⏸ Sleeping for 2 hours...", flush=True)
    time.sleep(7200)
