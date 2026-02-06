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

def run_script():
    print("🔧 Setting up Google Sheets access...", flush=True)
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sheet = gc.open(SHEET_NAME).worksheet(SHEET_TAB)

    # --- Step 1: Get existing emails from column M (13th column) ---
    print("📦 Fetching existing emails from sheet...", flush=True)
    existing_emails = set(email.strip().lower() for email in sheet.col_values(7)[1:])  # Skip header

    # --- Step 2: Fetch data from protected API ---
    print("🌐 Fetching leads from API...", flush=True)
    url = "https://b2bgrowthexpo.com/wp-json/custom-api/v1/protected/fetch-form-data"
    headers = {
        "Authorization": "Bearer e3e6836eb425245556aebc1e0a9e5bfbb41ee9c81ec5db1bc121debc5907fd85"
    }

    response = requests.get(url, headers=headers)
    form_data = response.json()
    entries = form_data.get("data", [])

    print(f"📥 Received {len(entries)} entries from API.", flush=True)

    new_leads = []

    for item in entries:

        if not isinstance(item, dict):
            print(f"⚠️ Skipping invalid item (not dict): {item}")
            continue
        
        form_entry = item.get("Form_Entry", {})
        
        if not isinstance(form_entry, dict):
            print(f"⚠️ Skipping invalid Form_Entry (not dict): {form_entry}")
            continue
            
        email = form_entry.get("Email", "")

        if not email or email in existing_emails:
            continue

        # Extract and format date
        form_date_raw = item.get("form_date", "")
        form_date = ""
        parsed_form_date = None
        if form_date_raw:
            try:
                parsed_form_date = datetime.strptime(form_date_raw, "%Y-%m-%d %H:%M:%S")
                if parsed_form_date < datetime(2025, 7, 8):
                    continue
                form_date = parsed_form_date.strftime("%d/%m/%Y")
            except:
                continue

        # Prepare row data
        row = [
            form_date,                          # Lead Date
            "Website",                          # Lead Source
            form_entry.get("First Name", ""),
            form_entry.get("Last Name", ""),
            form_entry.get("Business Name", ""), # Company Name (E)
            form_entry.get("Mobile Number", ""), # Mobile (F)
            form_entry.get("Email", ""),         # Email (G)
            form_entry.get("Select Location Of Interest", ""),  # Show (H)
            "",                                  # Next Followup (I)
            "",                                  # Call Attempt (J)
            "",                                  #Email-count
            "",                                  # WhatsApp msg count (K)
            "",                                  # Linkedin Msg Count (L)
            "",                                  #Meeting-Booked
            "",                                  # Comments (M)
            "",                                  # Pitch Deck URL (N)
            "Speaker_opportunity",               # Interested In? (O)
            "",                                  # Email Sent-Date (P)
            "",                                  # Reply Status (Q)
            "",                                  # Designation (R)
            "",                                  # Company Linkedin Page (S)
            ""                                   # Personal Linkedin Page (T)
        ]

        new_leads.append(row)
        existing_emails.add(email)

    print(f"🧾 Found {len(new_leads)} new unique leads to insert.", flush=True)

    if new_leads:
        sheet.insert_rows(new_leads[::-1],row=2,value_input_option="USER_ENTERED",inherit_from_before=False)
        print(f"✅ Inserted {len(new_leads)} leads at row 2 (below header).", flush=True)
    else:
        print("🔁 No new leads to add.", flush=True)

# --- Repeat every 2 hours ---
while True:
    try:
        print("\n🔄 Starting new sync run...", flush=True)
        run_script()
    except Exception as e:
        print(f"❌ Error during execution: {e}", flush=True)
    
    print("⏸ Sleeping for 2 hours (7200 seconds)...", flush=True)
    time.sleep(7200)
