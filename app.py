from flask import Flask, render_template, request, jsonify, redirect, send_from_directory
from googleapiclient.discovery import build
import random
import os
import time
import json
import requests
import smtplib
import pandas as pd
from geopy.geocoders import Nominatim
import PyPDF2
import re
import os, pickle
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaInMemoryUpload
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from flask import redirect, session
from googleapiclient.discovery import build
import gspread
from google.oauth2 import service_account
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'




geolocator = Nominatim(user_agent="aam_ayush_app")
from email.mime.text import MIMEText
sender_email = os.getenv("EMAIL_USER")
app_password = os.getenv("EMAIL_PASS")


# 🔹 ADD THESE
import gspread
from flask import session
from google.auth.transport.requests import Request

 

app = Flask(__name__)


app.secret_key = "supersecret123"
app.config['SESSION_PERMANENT'] = True
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets"
]

SCOPES_SHEET = [

    "https://www.googleapis.com/auth/spreadsheets",

    "https://www.googleapis.com/auth/drive"
]

creds = service_account.Credentials.from_service_account_file(
    "credentials.json",
    scopes=SCOPES_SHEET
)

client = gspread.authorize(creds)


# =====================================
# GLOBAL CACHE
# =====================================

cached_df = None

last_load_time = 0

CACHE_DURATION = 300   # 5 minutes


# =====================================
# LOAD SHEET WITH CACHE
# =====================================

def load_sheet_cached():

    global cached_df
    global last_load_time

    current_time = time.time()

    # =====================================
    # USE CACHE
    # =====================================

    if (

        cached_df is not None

        and

        (current_time - last_load_time)
        < CACHE_DURATION
    ):

        print("⚡ USING CACHED DATA")

        return cached_df

    # =====================================
    # LOAD FROM GOOGLE SHEET
    # =====================================

    print("🔥 LOADING FROM GOOGLE SHEET")

    sheet = client.open_by_key(
        "1FmXqroQN2IYzGbwEKj2V01oJAFjhilYzvpiXuLODqPU"
    ).worksheet("AAM_AYUSH")

    data = sheet.get_all_records()

    df = pd.DataFrame(data)

    # =====================================
    # SAVE CACHE
    # =====================================

    cached_df = df

    last_load_time = current_time

    print("✅ CACHE UPDATED")

    return df

        
        
CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ['https://www.googleapis.com/auth/drive.file']

@app.route('/login')
def login():


    flow = Flow.from_client_secrets_file(
        "client_secret.json",
        scopes=['https://www.googleapis.com/auth/drive.file'],
        redirect_uri='https://website-three-nu-85.vercel.app/oauth2callback'
    )
    auth_url, state = flow.authorization_url(prompt='consent')

    # 🔥 SAVE EVERYTHING
    session['state'] = state
    session['flow'] = flow.oauth2session._client.code_verifier   # IMPORTANT

    return redirect(auth_url)
    
@app.route('/oauth2callback')
def oauth2callback():

    flow = Flow.from_client_secrets_file(
        "client_secret.json",
        scopes=['https://www.googleapis.com/auth/drive.file'],
        state=session['state'],
        redirect_uri='https://website-three-nu-85.vercel.app/oauth2callback'
    )

    # 🔥 RESTORE verifier
    flow.oauth2session._client.code_verifier = session.get('flow')

    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials

    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

    return "LOGIN SUCCESS"
    
def get_drive_service():

    creds = Credentials(**session['credentials'])

    return build('drive', 'v3', credentials=creds)

def clean_col(col):
    return col.strip().lower().replace("_", "").replace(" ", "")

def get_val(row_dict, key):
    key_clean = str(key).strip().lower().replace(" ", "").replace("_", "")
    
    for k in row_dict:
        k_clean = str(k).strip().lower().replace(" ", "").replace("_", "")
        
        if k_clean == key_clean:
            return row_dict[k]
    
    return ""


def safe(val):
    try:
        if val in (None, "", "-", " "):
            return 0
        return float(val)
    except:
        return 0
    
def send_email_otp(to_email, otp):

    sender_email = "yogitadelhi01@gmail.com"
    app_password = "vqvf bbrj ucrd cuhm"

    subject = "Your OTP for Login"
    body = f"Your OTP is: {otp}"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to_email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, app_password)
        server.send_message(msg)    
    


def upload_to_drive(service, file_path, file_name):
    try:
        file_metadata = {
            'name': file_name,
            'parents': ['1lx6ltoWBK6AFLPWQZrSJYZdPme23BJiC']
        }

        media = MediaFileUpload(file_path, resumable=True)

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id',
            supportsAllDrives=True
        ).execute()

        file_id = file.get('id')

        # 🔥 MAKE FILE PUBLIC
        service.permissions().create(
            fileId=file_id,
            body={'role': 'reader', 'type': 'anyone'}
        ).execute()

        # 🔥 SHAREABLE LINK
        file_link = f"https://drive.google.com/file/d/{file_id}/view"

        print("✅ Uploaded to Drive:", file_link)

        return file_link   # 🔥 direct link return

    except Exception as e:
        print("🔥 Drive Upload Error:", e)
        return None
  
def save_to_sheet(sheet, data_rows):

    # 🔥 Check karo sheet empty hai ya nahi
    existing_data = sheet.get_all_values()

    if not existing_data:
        headers = [
            "state",
            "month",
            "type",
            "section",
            "indicator",
            "previous",
            "current",
            "prevFY",
            "ytdCurrent",
            "ytdPrev",
            "percent"
        ]

        sheet.append_row(headers)  # 👈 header add

    # 🔥 ab data add karo
    for row in data_rows:
        sheet.append_row([
            row["state"],
            row["month"],
            row["type"],
            row["section"],
            row["indicator"],
            row.get("previous", ""),
            row.get("current", ""),
            row.get("prevFY", ""),
            row.get("ytdCurrent", ""),
            row.get("ytdPrev", ""),
            row.get("percent", "")
        ])
  
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
# home
@app.route('/')
def home():
    return render_template("index.html")   # pehle login page
#FORM


@app.route('/form')
def form_page():

    role = request.args.get('role')  # central / state

    state = request.args.get('state')
    if role == "central":
        # Central user → state select karega
        return render_template("form.html", role="central", selected_state=None)

    else:
        # State user → fixed state
        state = session.get('state')
        return render_template("form.html", role="state", selected_state=state)


@app.route('/submit', methods=['POST'])
def submit():

    try:
        if 'user' not in session:
            return redirect('/')

        data = request.form.to_dict(flat=True)

        data['state'] = request.form.get('state_hidden')
        data['year'] = request.form.get('year')
        data['month'] = request.form.get('month')

        # 🔍 DUPLICATE CHECK
        existing = sheet.get_all_records()

        for r in existing:
            if str(r.get('state')).strip().lower() == data['state'].lower() and \
               str(r.get('year')).strip() == str(data['year']) and \
               str(r.get('month')).strip().lower() == str(data['month']).lower():
                return "⚠️ Already submitted"

        # 📁 FILE SAVE
        file = request.files.get('signed_copy')

        if file and file.filename:
            os.makedirs("uploads", exist_ok=True)

            path = os.path.join("uploads", file.filename)
            file.save(path)

            data['file_path'] = path

        # 📊 SHEET SAVE
        
        headers = main_sheet.row_values(1)
       
        new_headers = [k for k in data if k not in headers]
        if new_headers:
            sheet.update('A1', [headers + new_headers])
            headers += new_headers

        row = [data.get(h, "") for h in headers]
        main_sheet.append_row(row)


        return redirect('/form?success=1')

    except Exception as e:
        print("🔥 ERROR:", e)
        return str(e)
        
def make_file_public(service, file_id):
    service.permissions().create(
        fileId=file_id,
        body={'role': 'reader', 'type': 'anyone'}
    ).execute()
  
    

main_sheet = client.open_by_key("1FmXqroQN2IYzGbwEKj2V01oJAFjhilYzvpiXuLODqPU").sheet1
supp_sheet = client.open_by_key("1FmXqroQN2IYzGbwEKj2V01oJAFjhilYzvpiXuLODqPU").worksheet("Supplementary")
draft_sheet = client.open_by_key("1FmXqroQN2IYzGbwEKj2V01oJAFjhilYzvpiXuLODqPU").worksheet("draft_int")
int_form_sheet = client.open_by_key(
    "1FmXqroQN2IYzGbwEKj2V01oJAFjhilYzvpiXuLODqPU"
).worksheet("Int_form")

# 🔹 FETCH SHEET (data wali)
sheet_release = client.open_by_key("1FmXqroQN2IYzGbwEKj2V01oJAFjhilYzvpiXuLODqPU").worksheet("Overall Release")
sheet_released_total = client.open_by_key("1FmXqroQN2IYzGbwEKj2V01oJAFjhilYzvpiXuLODqPU").worksheet("Released_total") 
# 🔹 RESOURCE POOL SHEET (data wali)
sheet_resource = client.open_by_key("1FmXqroQN2IYzGbwEKj2V01oJAFjhilYzvpiXuLODqPU").worksheet("Resource_Pool") 
#   SAAP SHEET (data wali)
sheet_saap = client.open_by_key("1FmXqroQN2IYzGbwEKj2V01oJAFjhilYzvpiXuLODqPU").worksheet("SAAP")
#   MISSION DIRECTOR SHEET (data wali)
sheet_MD = client.open_by_key("1FmXqroQN2IYzGbwEKj2V01oJAFjhilYzvpiXuLODqPU").worksheet("Mission_Director")
login_sheet = client.open_by_key("1FmXqroQN2IYzGbwEKj2V01oJAFjhilYzvpiXuLODqPU").worksheet("Login_Data")
aeiup_sheet = client.open_by_key("1FmXqroQN2IYzGbwEKj2V01oJAFjhilYzvpiXuLODqPU").worksheet("AEI_UP")

# 🔹 draft

@app.route('/check_draft')
def check_draft():
    state = request.args.get('state')
    year = request.args.get('year')

    filename = f"draft_{state}_{year}.json"

    service = get_drive_service()

    results = service.files().list(
        q=f"name='{filename}'",
        fields="files(id, name)"
    ).execute()

    files = results.get('files', [])

    return jsonify({"exists": len(files) > 0})
    
    
    
@app.route('/save_draft', methods=['POST'])
def save_draft():
    try:
        data = request.json   # 🔥 IMPORTANT CHANGE

        state = data.get("state")
        month = data.get("month")

        sectionA = data.get("sectionA", [])
        sectionB = data.get("sectionB", [])
        sectionC = data.get("sectionC", [])

        # 🔥 FIXED HEADER (same as Int_form)
        headers = [
            "State",
            "Month",
            "Type",
            "Section",
            "Indicator",
            "Previous",
            "Current",
            "Prev FY",
            "YTD Current",
            "YTD Prev",
            "% Change",
            "Extra"
        ]

        rows = draft_sheet.get_all_values()

        # ✅ header create if empty
        if not rows:
            draft_sheet.clear()
            draft_sheet.append_row(headers)

        else:
            existing_headers = rows[0]

            # 🔥 अगर header mismatch है → fix कर दो
            if existing_headers != headers:
                draft_sheet.clear()
                draft_sheet.append_row(headers)

        # ===============================
        # 🔥 STEP 1: OLD DRAFT DELETE
        # ===============================
        rows = draft_sheet.get_all_values()

        if len(rows) > 1:
            for i in range(len(rows)-1, 0, -1):
                r = rows[i]

                if str(r[0]).strip() == state and str(r[1]).strip() == month:
                    draft_sheet.delete_rows(i+1)

        # ===============================
        # 🔥 STEP 2: SAVE NEW DATA
        # ===============================

        # 🔵 SECTION A
        for row in sectionA:
            draft_sheet.append_row([
                state,
                month,
                "draft",
                "A",
                row.get("indicator"),
                row.get("previous"),
                row.get("current"),
                row.get("prevFY"),
                row.get("ytdCurrent"),
                row.get("ytdPrev"),
                row.get("percent"),
                ""
            ])

        # 🟢 SECTION B
        for row in sectionB:
            draft_sheet.append_row([
                state,
                month,
                "draft",
                "B",
                row.get("indicator"),
                "",
                "",
                "",
                "",
                "",
                "",
                row.get("current")
            ])


        # 🟡 SECTION C (FIXED)
        for row in sectionC:
            draft_sheet.append_row([
                state,
                month,
                "draft",
                "C",
                row.get("indicator"),

                row.get("prevYear"),   # ✅ FIX
                row.get("currYear"),   # ✅ FIX

                "",                    # prevFY
                "",                    # ytdCurrent
                "",                    # ytdPrev

                row.get("percent"),    # ✅ FIX
                row.get("current")     # monthly
            ])

        return jsonify({"status": "saved"})

    except Exception as e:
        print("❌ ERROR:", e)
        return jsonify({"status": "error"})

        
@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")

@app.route('/test')
def test():
    return "WORKING OK"

# 🔹 BACKEND
@app.route('/get_draft')
def get_draft():
    state = request.args.get('state')
    year = request.args.get('year')

    filename = f"draft_{state}_{year}.json"

    service = get_drive_service()

    results = service.files().list(
        q=f"name='{filename}'",
        fields="files(id, name)"
    ).execute()

    files = results.get('files', [])

    if not files:
        return jsonify({})

    file_id = files[0]['id']

    request_drive = service.files().get_media(fileId=file_id)
    file_data = request_drive.execute()

    data = json.loads(file_data.decode('utf-8'))
    
    return jsonify(data)
# OTP
@app.route('/send_otp', methods=['POST'])
def send_otp():

    email = request.form.get('email')
    mobile = request.form.get('mobile')
    state = request.form.get('state')

    otp = str(random.randint(100000, 999999))

    # ✅ Session save
    session['otp'] = otp
    session['email'] = email
    session['state'] = state

    print("OTP:", otp)
    print("STATE SAVED:", state)

    # 🔹 SAVE TO SHEET
    try:
        login_sheet.append_row([email, mobile, state])
        print("✅ LOGIN SAVED IN SHEET")
    except Exception as e:
        print("❌ ERROR:", e)
        print("❌ LOGIN SAVE ERROR:", e)

    # 🔹 SEND EMAIL (separate)
    try:
        send_email_otp(email, otp)
        return jsonify({"status": "sent"})
    except Exception as e:
        print("❌ EMAIL ERROR:", e)
        return jsonify({
            "status": "error",
            "msg": "OTP send failed (email issue)"
        })
    
#VERIFY
@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    otp = request.form.get('otp')

    if otp == session.get('otp'):

        state = session.get('state')

        email = session.get('email')
        state = session.get('state')

        session.clear()

        session['user'] = email
        session['role'] = "state"
        session['state'] = state

        return jsonify({
            "status": "verified",
            "state": state
        })
    
#LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# 🔹 SAVE DATA
@app.route('/get_data', methods=['POST'])
def get_data():

    try:
        state = request.form.get('state_hidden') or request.form.get('state') or session.get('state')
        year = request.form.get("year")
        month = request.form.get("month")   # ✅ ADD THIS

        def clean(x):
            return str(x).strip().lower()

        def clean_year(x):
            return str(x).strip().replace("–", "-").replace(" ", "")

        def get_val(row_dict, key):
            for k in row_dict:
                if k.strip().lower() == key.lower():
                    return row_dict[k]
            return ""

        draft_rows = draft_sheet.get_all_values()

        print("🔥 FUNCTION CALLED")
        print("STATE:", state)
        print("MONTH:", month)

        # 🔥 RESULT STRUCTURE
        result = {
            "sectionA": [],
            "sectionB": [],
            "sectionC": []
        }

        # ===============================
        # 🔷 STEP 1: Draft check
        # ===============================
        if draft_rows and len(draft_rows) > 1:
            headers = draft_rows[0]

            for row in draft_rows[1:]:

                row_dict = dict(zip(headers, row))

                if clean(get_val(row_dict, "State")) == clean(state) and \
                   clean(get_val(row_dict, "Month")) == clean(month):

                    section = get_val(row_dict, "Section")

                    # 🔵 SECTION A
                    if section == "A":
                        result["sectionA"].append({
                            "indicator": get_val(row_dict, "Indicator"),
                            "previous": get_val(row_dict, "Previous"),
                            "current": get_val(row_dict, "Current"),
                            "prevFY": get_val(row_dict, "Prev FY"),
                            "ytdCurrent": get_val(row_dict, "YTD Current"),
                            "ytdPrev": get_val(row_dict, "YTD Prev"),
                            "percent": get_val(row_dict, "% Change")
                        })

                    # 🟢 SECTION B
                    elif section == "B":
                        result["sectionB"].append({
                            "indicator": get_val(row_dict, "Indicator"),
                            "current": get_val(row_dict, "Extra")
                        })

                    # 🟡 SECTION C
                    elif section == "C":
                        result["sectionC"].append({
                            "indicator": get_val(row_dict, "Indicator"),
                            "prevYear": get_val(row_dict, "Previous"),
                            "currYear": get_val(row_dict, "Current"),
                            "percent": get_val(row_dict, "% Change"),
                            "current": get_val(row_dict, "Extra")
                        })

        # 🔥 AFTER LOOP (IMPORTANT)
        if result["sectionA"] or result["sectionB"] or result["sectionC"]:
            print("✅ Draft Found (FULL)")
            return jsonify(result)

        print("⚠ Draft not found → fallback")


        # fallback
        data = sheet_release.get_all_records()
        data_resource = sheet_resource.get_all_records()
        data_saap = sheet_saap.get_all_records()
        data_MD = sheet_MD.get_all_records()


        resource_row = next((r for r in data_resource if clean(r.get("State")) == clean(state) and clean_year(r.get("Year")) == clean_year(year)), {})
        saap_row = next((s for s in data_saap if clean(s.get("State")) == clean(state) and clean_year(s.get("Year")) == clean_year(year)), {})
        md_row = next((m for m in data_MD if clean(m.get("State")) == clean(state) and clean_year(m.get("Year")) == clean_year(year)), {})
        release_row = next((r for r in data if clean(r.get("State")) == clean(state) and clean_year(r.get("Year")) == clean_year(year)), {})

        return jsonify({
            "recurring_central": safe(get_val(release_row, "Recurring_Central")),
            "recurring_state": safe(get_val(release_row, "Recurring_State")),
            "nonrecurring_central": safe(get_val(release_row, "NonRecurring_Central")),
            "nonrecurring_state": safe(get_val(release_row, "NonRecurring_State")),

            "r1": safe(get_val(resource_row, "Ayush Services")),
            "r2": safe(get_val(resource_row, "Educational Institutions")),
            "r3": safe(get_val(resource_row, "Medicinal Plants")),
            "r4": safe(get_val(resource_row, "Quality Control of ASU & H Drugs")),
            "r5": safe(get_val(resource_row, "Flexi Pool")),
            "r6": safe(get_val(resource_row, "Admin Cost")),

            "saap_r1": safe(get_val(saap_row, "Ayush Services")),
            "saap_r2": safe(get_val(saap_row, "Educational Institutions")),
            "saap_r3": safe(get_val(saap_row, "Medicinal Plants")),
            "saap_r4": safe(get_val(saap_row, "Quality Control of ASU & H Drugs")),
            "saap_r5": safe(get_val(saap_row, "Flexi Pool")),
            "saap_r6": safe(get_val(saap_row, "Admin Cost")),

            "md_r1": safe(get_val(md_row, "Ayush Services")),
            "md_r2": safe(get_val(md_row, "Educational Institutions")),
            "md_r3": safe(get_val(md_row, "Medicinal Plants")),
            "md_r4": safe(get_val(md_row, "Quality Control of ASU & H Drugs")),
            "md_r5": safe(get_val(md_row, "Flexi Pool")),
            "md_r6": safe(get_val(md_row, "Admin Cost"))
        })

    except Exception as e:
        print("🔥 ERROR:", e)
        return jsonify({"error": str(e)}), 500

#REPORT
@app.route('/report_data')
def report_data():
    try:
        sheet = client.open_by_key("1FmXqroQN2IYzGbwEKj2V01oJAFjhilYzvpiXuLODqPU").sheet1
        rows = sheet.get_all_records()

        role = session.get("role")
        user_state = session.get("state")

        print("ROLE:", role)
        print("USER STATE:", user_state)

        # 🔥 MAIN FIX
        if role == "state":
            rows = [
                r for r in rows
                if str(r.get("state")).strip().lower() == str(user_state).strip().lower()
            ]

        result = {}

        for row in rows:
            state = row.get('state') or row.get('State')
            year = row.get('year') or row.get('Year')

            state = str(state).strip() if state else ""
            year = str(year).strip() if year else ""

            if not state:
                continue

            if state not in result:
                result[state] = {}

            if year not in result[state]:
                result[state][year] = {
                    "Ayush Services": 0,
                    "Educational Institutions": 0,
                    "Medicinal Plants": 0,
                    "Quality Control": 0,
                    "Flexi Pool": 0,
                    "Admin Cost": 0
                }

            def safe(x):
                try:
                    return float(x)
                except:
                    return 0

            result[state][year]["Ayush Services"] += safe(row.get("c1")) + safe(row.get("c2")) + safe(row.get("s1")) + safe(row.get("s2"))
            result[state][year]["Educational Institutions"] += safe(row.get("c11")) + safe(row.get("c12")) + safe(row.get("s11")) + safe(row.get("s12"))
            result[state][year]["Medicinal Plants"] += safe(row.get("c21")) + safe(row.get("c22")) + safe(row.get("s21")) + safe(row.get("s22"))
            result[state][year]["Quality Control"] += safe(row.get("c31")) + safe(row.get("c32")) + safe(row.get("s31")) + safe(row.get("s32"))
            result[state][year]["Flexi Pool"] += safe(row.get("c41")) + safe(row.get("c42")) + safe(row.get("s41")) + safe(row.get("s42"))
            result[state][year]["Admin Cost"] += safe(row.get("c51")) + safe(row.get("c52")) + safe(row.get("s51")) + safe(row.get("s52"))

        return jsonify(result)

    except Exception as e:
        print("❌ REPORT ERROR:", e)
        return jsonify({})

@app.route('/state_year_status')
def state_year_status():

    rows = sheet.get_all_records()
    user_state = session.get("state")

    all_years = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]

    filled_years = set()

    for row in rows:
        state = str(row.get("state")).strip().lower()
        year = str(row.get("year")).strip()

        if state == str(user_state).strip().lower():
            if year:
                filled_years.add(year)

    result = []

    for y in all_years:
        result.append({
            "year": y,
            "status": 1 if y in filled_years else 0
        })

    return jsonify(result)
    
@app.route('/dashboard1')
def dashboard1():
    return render_template("dashboard_new.html")

@app.route('/send_otp_login', methods=['POST'])
def send_otp_login():
    try:
        # 🔹 get data
        email = request.form.get('email')
        mobile = request.form.get('mobile')
        state = request.form.get('state')

        print("FORM DATA:", request.form)
        print("LOGIN:", email, mobile, state)

        # 🔴 validation
        if not email or not mobile or not state:
            return jsonify({"status": "error", "msg": "Missing fields"})

        # 🔥 data prepare
        data = {
            "email": email,
            "mobile": mobile,
            "state": state
        }

        # 🔥 normalize
        data = {k.strip().lower(): v for k, v in data.items()}

        # 🔥 header + row logic
        existing_headers = login_sheet.row_values(1)

        # ✅ first time header create
        if not existing_headers or all(h.strip() == "" for h in existing_headers):
            headers = list(data.keys())
            login_sheet.clear()
            login_sheet.insert_row(headers, 1)
            existing_headers = headers

        else:
            # 🔥 auto add new columns
            new_headers = [k for k in data.keys() if k not in existing_headers]

            if new_headers:
                updated_headers = existing_headers + new_headers
                login_sheet.update('A1', [updated_headers])
                existing_headers = updated_headers

        # ✅ row mapping
        row = [data.get(h, "") for h in existing_headers]

        login_sheet.append_row(row)

        return jsonify({"status": "sent"})

    except Exception as e:
        print("LOGIN ERROR:", e)
        return jsonify({"status": "error"})
    

@app.route('/api/states')
def api_states():

    df = load_sheet_cached()

    # 🔥 column normalize
    df.columns = [c.strip().lower() for c in df.columns]

    # 🔥 state column detect
    state_col = None

    for col in df.columns:
        clean = col.strip().lower().replace(" ", "").replace("_", "")

        if clean in ["state", "statename", "state_name"]:
            state_col = col
            break

    if not state_col:
        return jsonify([])

    states = (
        df[state_col]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    states.sort()

    return jsonify(states)
    
@app.route('/api/hfi-data')
def api_hfi_data():

    state = request.args.get('state', '').strip()

    # =========================================
    # OPEN SPREADSHEET ONLY ONCE (FAST)
    # =========================================

    spreadsheet = client.open_by_key(
        "1FmXqroQN2IYzGbwEKj2V01oJAFjhilYzvpiXuLODqPU"
    )

    # =========================================
    # HELPER
    # =========================================

    def clean_cols(df):

        df.columns = [

            str(c)
            .strip()
            .lower()
            .replace("\n", " ")
            .replace("_", " ")

            for c in df.columns
        ]

        return df

    def find_col(df, names):

        for c in df.columns:

            cc = (
                str(c)
                .strip()
                .lower()
            )

            for n in names:

                nn = (
                    str(n)
                    .strip()
                    .lower()
                )

                if cc == nn or nn in cc:
                    return c

        return None

    def load_sheet(sheet_name, source_type):

        print(f"\n🔥 LOADING: {sheet_name}")

        ws = spreadsheet.worksheet(sheet_name)

        values = ws.get_all_values()

        if not values or len(values) < 2:
            return pd.DataFrame()

        headers = values[0]
        rows = values[1:]

        df = pd.DataFrame(rows, columns=headers)

        df = clean_cols(df)

        print(df.columns.tolist())

        # =====================================
        # FIND COLS
        # =====================================

        state_col = find_col(df, [

            "state",

            "state/ut",

            "state ut",

            "state name",

            "state_name"
        ])

        print("STATE COL:", state_col)

        district_col = find_col(df, [

            "district",
            "district name",
            "district_name"
        ])

        locality_col = find_col(df, [

            "locality",
            "locality name",
            "locality_name"
        ])

        block_col = find_col(df, [
            "block"
        ])

        hfi_col = None

        if sheet_name == "IAH List":

            hfi_col = "location"

        else:

            hfi_col = find_col(df, [

                "hfi name",

                "facility name",

                "name of the college",

                "college name",

                "hospital name",

                "iah name",

                "institution name",

                "institute name",

                "hospital/institute name",

                "name"
            ])

        lat_col = find_col(df, [

            "latitude",
            "lat"
        ])

        lng_col = find_col(df, [

            "longitude",
            "lng",
            "long"
        ])

        mobile_col = find_col(df, [

            "mobile",
            "mobile no.",
            "contact no."
        ])

        email_col = find_col(df, [

            "email",
            "email id"
        ])

        # =====================================
        # STANDARD COLS
        # =====================================

        final = pd.DataFrame()

        final["state"] = (
            df[state_col]
            if state_col else ""
        )

        final["district"] = (
            df[district_col]
            if district_col else ""
        )

        final["locality"] = (
            df[locality_col]
            if locality_col else ""
        )

        final["block"] = (
            df[block_col]
            if block_col else ""
        )

        final["hfi_name"] = (
            df[hfi_col]
            if hfi_col else ""
        )

        final["latitude"] = pd.to_numeric(

            df[lat_col]
            if lat_col else "",

            errors="coerce"
        )

        final["longitude"] = pd.to_numeric(

            df[lng_col]
            if lng_col else "",

            errors="coerce"
        )

        final["mobile"] = (
            df[mobile_col]
            if mobile_col else ""
        )

        final["email"] = (
            df[email_col]
            if email_col else ""
        )

        # =====================================
        # OPTIONAL
        # =====================================

        for col in [

            "pincode",
            "landmark",
            "incharge",
            "pharmacist",
            "asha",
            "anm",
            "remarks"
        ]:

            c = find_col(df, [col])

            final[col] = (
                df[c]
                if c else ""
            )

        # =====================================
        # TYPE
        # =====================================

        final["type"] = source_type

        # =====================================
        # CLEAN
        # =====================================

        for c in [

            "state",
            "district",
            "locality",
            "block",
            "hfi_name"
        ]:

            final[c] = (

                final[c]
                .astype(str)
                .str.strip()
            )

        # =====================================
        # REMOVE INVALID LAT LNG
        # =====================================

        final = final.dropna(

            subset=[
                "latitude",
                "longitude"
            ]
        )

        print("✅ ROWS:", len(final))

        return final

    # =========================================
    # LOAD ALL SHEETS
    # =========================================

    df1 = load_sheet(
        "AAM_AYUSH",
        "AAM"
    )

    df2 = load_sheet(
        "SPMU_DPMU Details",
        "SPMU_DPMU"
    )

    df3 = load_sheet(
        "List of Erstwhile AEI",
        "ERSTWHILE_AEI"
    )

    df4 = load_sheet(
        "IAH List",
        "IAH"
    )

    df5 = load_sheet(
        "Ayush_Facilities",
        "AYUSH_FACILITY"
    )

    df6 = load_sheet(
        "List of All Colleges",
        "COLLEGE"
    )

    # ✅ SAFE LOAD
    try:
        df7 = load_sheet(
            "AEI_NEW",
            "NEWCOLLEGE"
        )
    except:
        print("❌ AEI_NEW sheet not found")
        df7 = pd.DataFrame()

    # ✅ SAFE LOAD
    try:
        df8 = load_sheet(
            "AEI_UP",
            "UPGRADATION"
        )
    except:
        print("❌ AEI_UP sheet not found")
        df8 = pd.DataFrame()



    # =========================================
    # MERGE
    # =========================================

    final_df = pd.concat(

        [df1, df2, df3, df4, df5, df6, df7, df8],

        ignore_index=True,
        sort=False
    )

    
    # =========================================
    # REMOVE DUPLICATES
    # =========================================

    final_df = final_df.drop_duplicates(

        subset=[

            "hfi_name",
            "district",
            "latitude",
            "longitude",
            "type"

        ],

        keep="first"
    )

    print("✅ AFTER DUPLICATE REMOVE:", len(final_df))
    
    
    # =========================================
    # FILTER STATE
    # =========================================

    if state:

        s = (
            state
            .lower()
            .replace("&", "and")
            .replace("  ", " ")
            .strip()
        )

        final_df["state_clean"] = (

            final_df["state"]
            .astype(str)
            .str.lower()
            .str.replace("&", "and")
            .str.replace("  ", " ")
            .str.strip()
        )

        final_df = final_df[

            final_df["state_clean"] == s
        ]

    # =========================================
    # DEBUG
    # =========================================

    print("\n✅ FINAL DATA")

    print(
        final_df[[
            "state",
            "district",
            "hfi_name",
            "latitude",
            "longitude",
            "type"
        ]].head(20)
    )

    print("TOTAL:", len(final_df))

    # =========================================
    # RETURN
    # =========================================

    return jsonify(

        final_df
        .fillna("")
        .to_dict(orient="records")
    )
        
@app.route('/api/districts')
def get_districts():

    try:

        state = request.args.get('state')

        df = load_sheet_cached()

        # 🔥 normalize columns
        df.columns = [c.strip().lower() for c in df.columns]

        print("ALL COLUMNS:", df.columns.tolist())

        state_col = None
        district_col = None

        # 🔥 flexible detect
        for col in df.columns:

            clean = (
                col.strip()
                .lower()
                .replace(" ", "")
                .replace("_", "")
            )

            if clean in ["state", "statename"]:
                state_col = col

            if clean in ["district", "districtname"]:
                district_col = col

        print("STATE COL:", state_col)
        print("DISTRICT COL:", district_col)

        if not state_col or not district_col:
            return jsonify([])

        # 🔥 filter state
        filtered = df[
            df[state_col]
            .astype(str)
            .str.strip()
            .str.lower()
            == state.strip().lower()
        ]

        districts = (
            filtered[district_col]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )

        districts.sort()

        print("DISTRICTS:", districts)

        return jsonify(districts)

    except Exception as e:

        print("❌ DISTRICT ERROR:", e)

        return jsonify([])


@app.route('/api/save-aam', methods=['POST'])
def save_aam():
    try:
        data = request.json

        print("RECEIVED AAM DATA:", data)

        if not data or not isinstance(data, list):
            return jsonify({"status": "error", "msg": "Invalid data format"})

        aam_sheet = client.open_by_key(
            "1FmXqroQN2IYzGbwEKj2V01oJAFjhilYzvpiXuLODqPU"
        ).worksheet("AAM_AYUSH_SAVE")

        headers = aam_sheet.row_values(1)

        # 🔥 FIX 1: proper empty check
        if not headers or all(h.strip() == "" for h in headers):
            headers = list(data[0].keys())
            aam_sheet.clear()
            aam_sheet.append_row(headers)

        else:
            # 🔥 FIX 2: new keys auto add
            new_headers = []
            for row in data:
                for k in row.keys():
                    if k not in headers:
                        new_headers.append(k)

            if new_headers:
                headers += new_headers
                aam_sheet.update('A1', [headers])

        # 🔥 SAVE DATA
        for row in data:
            row_values = [row.get(h, "") for h in headers]
            aam_sheet.append_row(row_values)

        return jsonify({"status": "success"})

    except Exception as e:
        print("❌ ERROR:", e)
        return jsonify({"status": "error", "msg": str(e)})
      
@app.route('/set_central_session')
def set_central_session():
    session.clear()   # 🔥 ADD THIS (important)
    session['user'] = "central_user"
    session['role'] = "central"
    return "OK"

@app.route('/monthly_report')
def monthly_report():
    try:
        sheet = client.open_by_key("1FmXqroQN2IYzGbwEKj2V01oJAFjhilYzvpiXuLODqPU").worksheet("Int_form")
        rows = sheet.get_all_records(default_blank="")

        result = {}

        for row in rows:

            if str(row.get("Type")).strip().lower() != "final":
                continue

            state = str(row.get("State")).strip()
            month = str(row.get("Month")).strip()
            section = str(row.get("Section")).strip().upper()

            if not state or not month:
                continue

            if state not in result:
                result[state] = {}

            if month not in result[state]:
                result[state][month] = {
                    "sectionA": [],
                    "sectionB": [],
                    "sectionC": []
                }

            # ✅ SECTION A
            if section == "A":
                clean_row = {k.strip(): v for k, v in row.items()}


                result[state][month]["sectionA"].append({
                    "indicator": str(row.get("Indicator")).strip(),

                    "current": float(row.get("Current") or 0),
                    "prevFY": float(row.get("Prev FY") or 0),

                    "ytdCurrent": float(row.get("YTD Current") or 0),
                    "ytdPrev": float(row.get("YTD Prev") or 0),

                    "percent": float(row.get("% Change") or 0)
                })


            # ✅ SECTION B
            elif section == "B":
                result[state][month]["sectionB"].append({
                    "indicator": str(row.get("Indicator")).strip(),
                    "current": float(row.get("Extra") or 0)
                })

            # ✅ SECTION C
            elif section == "C":
                result[state][month]["sectionC"].append({
                    "indicator": str(row.get("Indicator")).strip(),

                    "prevYear": float(row.get("Previous") or 0),
                    "currYear": float(row.get("Current") or 0),

                    "percent": float(row.get("% Change") or 0),   # K column
                    "current": float(row.get("Extra") or 0)       # L column
                })
        return jsonify(result)

    except Exception as e:
        print("ERROR:", e)
        return jsonify({})


@app.route('/monthly_summary')
def monthly_summary():

    df = load_sheet_cached()   # 🔥 पहले df define करो

    result = df.groupby(["Indicator", "Section"]).sum().reset_index()

    return jsonify(result.to_dict(orient="records"))
      
@app.route('/api/save-ayush', methods=['POST'])
def save_ayush():
    try:
        data = request.json

        print("INTEGRATED DATA:", data)

        state = (session.get("state") or data.get("state") or "").strip()
        month = (data.get("month") or "").strip()

        if not state or not month:
            return jsonify({"status": "error", "msg": "State or Month missing"})

        sectionA = data.get("sectionA", [])
        sectionB = data.get("sectionB", [])
        sectionC = data.get("sectionC", [])

        sheet = client.open_by_key(
            "1FmXqroQN2IYzGbwEKj2V01oJAFjhilYzvpiXuLODqPU"
        ).worksheet("Int_form")

        # ===============================
        # 🔥 STEP 0: HEADER FIX (IMPORTANT)
        # ===============================
        headers = [
            "State",
            "Month",
            "Type",
            "Section",
            "Indicator",
            "Previous",
            "Current",
            "Prev FY",
            "YTD Current",
            "YTD Prev",
            "% Change",
            "Extra"
        ]

        rows = sheet.get_all_values()

        # 👉 अगर sheet empty है
        if not rows:
            sheet.append_row(headers)
            rows = [headers]

        else:
            existing_headers = rows[0]

            # 👉 अगर header गलत है
            if existing_headers != headers:
                sheet.clear()
                sheet.append_row(headers)
                rows = [headers]

        # ===============================
        # 🔥 STEP 1: DELETE OLD DATA
        # ===============================
        deleted_count = 0

        if len(rows) > 1:
            headers = rows[0]

            state_idx = headers.index("State")
            month_idx = headers.index("Month")

            rows_to_delete = []

            for i, r in enumerate(rows[1:], start=2):
                if str(r[state_idx]).strip() == state and \
                   str(r[month_idx]).strip() == month:
                    rows_to_delete.append(i)

            for i in reversed(rows_to_delete):
                sheet.delete_rows(i)
                deleted_count += 1

        print(f"🗑 Deleted old rows: {deleted_count}")

        # ===============================
        # 🔥 STEP 2: SAVE NEW DATA
        # ===============================


        # 🔥 SECTION A FINAL FIX
        for row in sectionA:

            current = float(row.get("current") or 0)
            prevFY = float(row.get("prevFY") or 0)

            # 🔥 IMPORTANT FIX (empty string handle)
            ytdCurrent = row.get("ytdCurrent")
            ytdPrev = row.get("ytdPrev")

            ytdCurrent = float(ytdCurrent) if str(ytdCurrent).strip() != "" else current
            ytdPrev = float(ytdPrev) if str(ytdPrev).strip() != "" else prevFY

            percent = ((ytdCurrent - ytdPrev) / ytdPrev * 100) if ytdPrev else 0

            sheet.append_row([
                state,
                month,
                "final",
                "A",
                row.get("indicator"),
                row.get("previous"),
                current,
                prevFY,
                ytdCurrent,
                ytdPrev,
                round(percent, 2),
                ""
            ])

        # 🟢 SECTION B
        for row in sectionB:
            sheet.append_row([
                state,
                month,
                "final",
                "B",
                row.get("indicator"),
                "",
                "",
                "",
                "",
                "",
                "",
                row.get("current")
            ])

        # 🟡 SECTION C (FINAL FIX)
        for row in sectionC:

            prev = row.get("prevYear") or ""
            curr = row.get("currYear") or ""
            percent = row.get("percent") or ""
            monthly = row.get("current") or ""

            # 🔥 CASE 1: Row with % (1st row)
            if prev or curr:
                sheet.append_row([
                    state,
                    month,
                    "final",
                    "C",
                    row.get("indicator"),

                    prev,       # Previous → col F
                    curr,       # Current → col G
                    "", "", "",

                    percent,    # % Change → col K ✅
                    ""          # Extra → empty
                ])

            # 🔥 CASE 2: Monthly rows (बाकी rows)
            else:
                sheet.append_row([
                    state,
                    month,
                    "final",
                    "C",
                    row.get("indicator"),

                    "", "", "", "", "",

                    "",         # % Change empty
                    monthly     # Extra → col L ✅
                ])

        return jsonify({"status": "success"})

    except Exception as e:
        print("❌ ERROR:", e)
        return jsonify({"status": "error", "msg": str(e)})     
     
     
@app.route('/api/final-submit', methods=['POST'])
def final_submit():

    data = request.json

    state = data.get("state")
    month = data.get("month")

    def clean(x):
        return str(x).strip().lower()

    rows = draft_sheet.get_all_values()

    to_save = []

    # 🔥 STEP 1: collect draft data
    for r in rows[1:]:

        if len(r) < 2:
            continue

        if clean(r[0]) == clean(state) and clean(r[1]) == clean(month):
            to_save.append(r)

    # 🔥 STEP 2: save to main sheet
    if to_save:
        int_form_sheet.append_rows(to_save)

    # 🔥 STEP 3: DELETE FROM DRAFT
    deleted = 0

    for i in range(len(rows)-1, 0, -1):

        r = rows[i]

        if len(r) < 2:
            continue

        if clean(r[0]) == clean(state) and clean(r[1]) == clean(month):

            draft_sheet.delete_rows(i+1)
            deleted += 1

    print(f"🗑 Deleted rows: {deleted}")

    return jsonify({"status": "success"})     
     

@app.route('/get_draft_data', methods=['POST'])
def get_draft_data():

    data = request.json
    state = data.get("state")
    month = data.get("month")

    def clean(x):
        return str(x).strip().lower()

    rows = draft_sheet.get_all_values()

    headers = rows[0]

    sectionA = []
    sectionB = []
    sectionC = []

    for row in rows[1:]:

        if len(row) < 4:
            continue

        if clean(row[0]) == clean(state) and clean(row[1]) == clean(month):

            section = row[3]

            if section == "A":
                sectionA.append({
                    "indicator": row[4],
                    "previous": row[5],
                    "current": row[6],
                    "prevFY": row[7],
                    "ytdCurrent": row[8],
                    "ytdPrev": row[9],
                    "percent": row[10]
                })

            elif section == "B":
                sectionB.append({
                    "indicator": row[4],
                    "current": row[11]
                })

            elif section == "C":
                sectionC.append({
                    "indicator": row[4],
                    "prevYear": row[5],
                    "currYear": row[6],
                    "percent": row[10],
                    "current": row[11]
                })

    return jsonify({
        "sectionA": sectionA,
        "sectionB": sectionB,
        "sectionC": sectionC
    })
     
     
@app.route('/api/aam-state-report')
def aam_state_report():
    try:
        df = load_sheet_cached()

        aam_sheet = client.open_by_key(
            "1FmXqroQN2IYzGbwEKj2V01oJAFjhilYzvpiXuLODqPU"
        ).worksheet("AAM_AYUSH")

        aam_rows = aam_sheet.get_all_records()

        result = {}

        # 🔵 PART 1: HFI DATA
        for _, row in df.iterrows():

            state = str(row.get("State_Name") or "").strip()

            if not state:
                continue

            if state not in result:
                result[state] = {
                    "total_hfi": 0,
                    "with_location": 0
                }

            result[state]["total_hfi"] += 1

            if pd.notna(row.get("latitude")) and pd.notna(row.get("longitude")):
                result[state]["with_location"] += 1

        # 🟢 PART 2: AAM DETAILS
        for row in aam_rows:

            state = str(row.get("State") or "").strip()

            if not state:
                continue

            if state not in result:
                result[state] = {}

            def safe(x):
                try:
                    return float(str(x).replace("+", "").strip())
                except:
                    return 0

            result[state].update({
                "dispensary": safe(row.get("Dispensary")),
                "sub_centre": safe(row.get("Sub Centre")),
                "units_approved": safe(row.get("Units Approved")),
                "units_functional": safe(row.get("Units Functional")),
                "assessment_done": safe(row.get("Assessment Done")),
                "certified": safe(row.get("Certified")),
                "aam_planned": row.get("AAM Planned"),

                "training_participants": safe(row.get("Training Participants")),
                "hospital_presence": row.get("Hospital Presence"),
                "status": row.get("Status"),
                "virtual_training": row.get("State Participated in Virtual Training"),
                "training_date": row.get("Date of Training"),
                "participants": safe(row.get("Participants")),
                "hospital_summary": row.get("Hospital Summary")
            })

        return jsonify(result)

    except Exception as e:
        print("❌ ERROR:", e)
        return jsonify({})
     
     
     
@app.route("/api/released-full-table")
def released_full_table():

    try:
        data = sheet_release.get_all_records()

        print("🔥 RELEASE DATA:", data[:2])  # debug

        result = []

        for row in data:
            clean_row = {}

            for k, v in row.items():
                try:
                    clean_row[k] = float(v) if str(v).strip() != "" else 0
                except:
                    clean_row[k] = v

            result.append(clean_row)

        return jsonify(result)

    except Exception as e:
        print("❌ ERROR:", e)
        return jsonify([])

@app.route("/api/released-total")
def released_total():

    try:
        data = sheet_released_total.get_all_records()
        return jsonify(data)

    except Exception as e:
        print("❌ ERROR:", e)
        return jsonify([])


@app.route('/api/overall-release')
def overall_release():

    data = sheet_overall_release.get_all_records()

    return jsonify(data)



def grammar_fix_advanced(text):
    return text


def clean_text(text):


    # remove headings (first line caps)
    text = re.sub(r'^[A-Z][^\n]+\n?', '', text)

    # remove "Will the ... state:"
    text = re.sub(r'Will the.*?state:', '', text, flags=re.IGNORECASE)

    # remove MP name + question no
    text = re.sub(r'\d+\s+Shri.*?:', '', text)

    # normalize spaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def split_clauses(text):

    # 1. (a)(b)(c) format
    matches = re.findall(
        r'\(\s*[a-zA-Z]\s*\)\s*(.*?)(?=\(\s*[a-zA-Z]\s*\)|$)',
        text,
        flags=re.DOTALL
    )

    if matches:
        return [m.strip() for m in matches if len(m.strip()) > 20]

    # 2. numbered (1)(2)(3)
    matches = re.findall(
        r'\d+\.\s*(.*?)(?=\d+\.|$)',
        text,
        flags=re.DOTALL
    )

    if matches:
        return [m.strip() for m in matches if len(m.strip()) > 20]

    # 3. fallback: sentence split
    sentences = re.split(r'\.|\;', text)

    return [s.strip() for s in sentences if len(s.strip()) > 30]



def build_thrust(parts):

    if len(parts) > 1:
        combined = "; ".join(parts[:-1]) + "; and " + parts[-1]
    else:
        combined = parts[0]

    prefix = "Hon’ble Members of Parliament desire to know whether the Government has "

    suffix = ", if so, the details thereof."

    return prefix + combined + suffix

def grammar_fix(text):

    # duplicate semicolon हटाओ
    text = re.sub(r';{2,}', ';', text)

    # गलत ;, ठीक करो
    text = re.sub(r';\s*,', ',', text)

    # गलत ", ;" हटाओ
    text = re.sub(r',\s*;', ',', text)

    # double and हटाओ
    text = re.sub(r'\band\s+and\b', 'and', text)

    # FDI fix
    text = re.sub(r'\bFDI\b', 'Foreign Direct Investment (FDI)', text)

    # spaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()

    return text



def generate_thrust_pro(text):

    parts = split_clauses(text)

    # clean
    cleaned = []
    for p in parts:
        p = clean_text(p)
        if len(p) > 25:
            p = re.sub(r'[;,.]+$', '', p)
            cleaned.append(p)

    parts = cleaned

    if not parts:
        return "Hon’ble Members of Parliament desire to know whether the Government has provided details regarding the subject matter, if so, the details thereof."

    # 🔥 verb detect (first clause)
    verb = detect_verb(parts[0])

    # 🔥 build body
    if len(parts) > 1:
        body = "; ".join(parts[:-1]) + "; and " + parts[-1]
    else:
        body = parts[0]

    body = grammar_fix(body)

    return f"Hon’ble Members of Parliament desire to know whether the Government has {verb} {body}, if so, the details thereof."

def detect_verb(text):

    text = text.lower()

    if "policy" in text or "initiative" in text:
        return "undertaken"

    if "status" in text:
        return "provided"

    if "incentive" in text or "proposal" in text:
        return "proposed"

    if "roadmap" in text or "plan" in text:
        return "formulated"

    return "provided"

def extract_points(text):
    matches = re.findall(
        r'\(\s*[a-zA-Z]\s*\)\s*(.*?)(?=\(\s*[a-zA-Z]\s*\)|$)',
        text,
        flags=re.DOTALL
    )

    return [m.strip() for m in matches if m.strip()] or ["No points extracted"]
    
    
latest_data = {}

# 🔥 Google Sheet fetch function
def fetch_sheet_data():

    SHEET_API = "https://script.google.com/macros/s/AKfycbwoQomuM8AmLf0ysRC5_fY-6lc-0F7Fc53g-fPIFzIPjJR3ON2ySlxOZwIQTCeLzkkO/exec"

    try:
        res = requests.get(SHEET_API, timeout=5)
        data = res.json()

        # expected format: {"points": ["Intro...", "Vision...", ...]}
        return data.get("points", [])

    except Exception as e:
        print("❌ Sheet fetch error:", e)
        return []


@app.route("/generate_thrust", methods=["POST"])
def generate_thrust():
    try:
        file = request.files.get("file")

        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        text = ""

        if file.filename.endswith(".txt"):
            text = file.read().decode("utf-8", errors="ignore")

        elif file.filename.endswith(".pdf"):
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                content = page.extract_text()
                if content:
                    text += content + "\n"

        text = text.strip()

        if not text:
            return jsonify({"error": "No readable content"}), 400

        # 🔥 REAL LOGIC
        thrust = generate_thrust_pro(text)
        thrust = grammar_fix(thrust)

        points = extract_points(text)

        if not isinstance(points, list):
            points = []

        return jsonify({
            "thrust": str(thrust),
            "points": points,
            "original": text[:2000]
        })

    except Exception as e:
        print("🔥 ERROR:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/get-supplementary")
def get_supplementary():
    global latest_data
    return jsonify(latest_data)

def create_pdf(data, filename="report.pdf"):
    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()

    content = []

    content.append(Paragraph("Note for Supplementary", styles['Title']))
    content.append(Paragraph(f"House: {data.get('house','')}", styles['Normal']))
    content.append(Paragraph(f"Question No: {data.get('qno','')}", styles['Normal']))
    content.append(Paragraph(f"Date: {data.get('date','')}", styles['Normal']))
    content.append(Paragraph(f"Subject: {data.get('subject','')}", styles['Normal']))

    content.append(Paragraph("<b>Members:</b>", styles['Heading3']))
    for mp in data.get("mps", []):
        content.append(Paragraph(mp, styles['Normal']))

    content.append(Paragraph("<b>Original Question:</b>", styles['Heading3']))
    content.append(Paragraph(data.get("original",""), styles['Normal']))

    content.append(Paragraph("<b>Thrust:</b>", styles['Heading3']))
    content.append(Paragraph(data.get("thrust",""), styles['Normal']))

    doc.build(content)

    return filename



@app.route("/get-by-qno/<qno>")
def get_by_qno(qno):
    try:
        filepath = f"data/Q{qno}.json"

        if not os.path.exists(filepath):
            return jsonify({"error": "Not found"}), 404

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
        



def save_doc_to_drive(service, content, file_name):

    file_metadata = {
        'name': file_name,
        'mimeType': 'application/vnd.google-apps.document',
        'parents': ['1lx6ltoWBK6AFLPWQZrSJYZdPme23BJiC']  # 🔥 YOUR FOLDER
    }

    media = MediaInMemoryUpload(
        content.encode('utf-8'),
        mimetype='text/plain',
        resumable=True
    )

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    return file.get('id')



@app.route('/save-supplementary', methods=['POST'])
def save_supplementary():
    try:
        import os, json

        # 🔹 BASIC FIELDS
        data = {
            "house": request.form.get("house"),
            "qno": request.form.get("qno"),
            "date": request.form.get("date"),
            "subject": request.form.get("subject"),
            "thrust": request.form.get("thrust"),
            "original": request.form.get("original"),
            "points": request.form.get("points")
        }

        # 🔹 MPs JSON
        mps = json.loads(request.form.get("mps", "[]"))

        service = get_drive_service()

        final_mps = []

        # =========================
        # 🔥 MP LOOP (PHOTO UPLOAD)
        # =========================
        for mp in mps:

            file = request.files.get(mp.get("photo_key"))
            photo_link = ""

            if file:
                filename = f"{mp.get('name','mp')}_{file.filename}"

                os.makedirs("uploads", exist_ok=True)
                path = os.path.join("uploads", filename)

                file.save(path)

                photo_link = upload_to_drive(service, path, filename)

            mp["photo"] = photo_link
            final_mps.append(mp)

        # 🔹 attach MP data
        data["mp_details"] = json.dumps(final_mps)

        # =========================
        # 🔥 SAVE JSON TO DRIVE
        # =========================
        file_id = save_doc_to_drive(
            service,
            json.dumps(data, indent=2),
            f"supp_{data['qno']}.json"
        )

        drive_link = f"https://drive.google.com/file/d/{file_id}/view"

        data["file_link"] = drive_link

        print("✅ DRIVE LINK:", drive_link)

        # =========================
        # 🔥 SAVE TO SHEET (AUTO HEADERS)
        # =========================
        headers = supp_sheet.row_values(1)

        if not headers or all(h.strip() == "" for h in headers):
            headers = list(data.keys())
            supp_sheet.clear()
            supp_sheet.append_row(headers)

        else:
            new_headers = [k for k in data if k not in headers]
            if new_headers:
                headers += new_headers
                supp_sheet.update('A1', [headers])

        row = [data.get(h, "") for h in headers]
        supp_sheet.append_row(row)

        print("✅ SAVED IN supplementry SHEET")

        return jsonify({
            "status": "success",
            "drive_link": drive_link
        })

    except Exception as e:
        print("🔥 ERROR:", e)
        return jsonify({
            "status": "error",
            "msg": str(e)
        })



@app.route('/api/phc')
def phc():
    data = sheet.get_all_records()
    return jsonify(data)


# 🔥 GLOBAL CACHE
cached_data = None


@app.route('/api/aei-up')
def aei_up():
    try:
        global cached_data

        state_param = request.args.get("state")
        year_param = request.args.get("year")

        # 🔥 CACHE USE
        if cached_data is None:
            print("🔥 FETCHING FROM GOOGLE SHEET")

            data = aeiup_sheet.get_all_values()

            if not data:
                return jsonify([])

            headers = data[0]
            rows = data[1:]

            cached_data = {
                "headers": headers,
                "rows": rows
            }

        else:
            print("⚡ USING CACHED DATA")

        headers = cached_data["headers"]
        rows = cached_data["rows"]

        # 🔥 column detect
        state_index = None
        year_index = None

        for i, h in enumerate(headers):
            h_clean = str(h).strip().lower()

            if "state" in h_clean:
                state_index = i

            if "year" in h_clean:
                year_index = i

        result = []

        for row in rows:

            row_state = row[state_index].strip() if state_index < len(row) else ""
            row_year = row[year_index].strip() if year_index < len(row) else ""

            # 🔥 CLEANING
            clean_row_state = row_state.strip().lower()
            clean_param_state = (state_param or "").strip().lower()

            clean_row_year = row_year.strip().replace(" ", "").replace("–", "-")
            clean_param_year = (year_param or "").strip().replace(" ", "").replace("–", "-")

            # 🔥 STATE FILTER
            if clean_param_state:
                if clean_row_state != clean_param_state:
                    continue

            # 🔥 YEAR FILTER
            if clean_param_year:
                if clean_row_year != clean_param_year:
                    continue

            # 🔥 OBJECT
            obj = {}
            for i in range(len(headers)):
                key = headers[i] if headers[i] else f"col_{i}"
                value = row[i] if i < len(row) else ""
                obj[key] = value

            result.append(obj)

        print("✅ ROWS RETURNED:", len(result))
        return jsonify(result)

    except Exception as e:
        print("❌ ERROR:", e)
        return jsonify([])

@app.route('/refresh-cache')
def refresh_cache():
    global cached_aeiup_data
    cached_aeiup_data = None
    return "Cache cleared"

@app.route('/api/localities')
def get_localities():

    try:

        state = request.args.get('state')
        district = request.args.get('district')

        df = load_sheet_cached()

        # normalize
        df.columns = [c.strip().lower() for c in df.columns]

        state_col = None
        district_col = None
        locality_col = None

        for col in df.columns:

            clean = (
                col.strip()
                .lower()
                .replace(" ", "")
                .replace("_", "")
            )

            if clean in ["state", "statename"]:
                state_col = col

            elif clean in ["district", "districtname"]:
                district_col = col

            elif clean in ["locality", "village", "area"]:
                locality_col = col

        if not locality_col:
            return jsonify([])

        # filter
        filtered = df.copy()

        if state and state_col:
            filtered = filtered[
                filtered[state_col]
                .astype(str)
                .str.strip()
                .str.lower()
                == state.strip().lower()
            ]

        if district and district_col:
            filtered = filtered[
                filtered[district_col]
                .astype(str)
                .str.strip()
                .str.lower()
                == district.strip().lower()
            ]

        localities = (
            filtered[locality_col]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )

        localities.sort()

        return jsonify(localities)

    except Exception as e:

        print("LOCALITY ERROR:", e)

        return jsonify([])


        

if __name__ == "__main__":
    app.run(debug=True)       
