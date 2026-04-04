from flask import Flask, render_template, request, redirect, session
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import cloudinary
import cloudinary.uploader
from datetime import datetime
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials as SACredentials
from datetime import timedelta
from PIL import Image
import io
import os
import json
import pytz
import psycopg2
from datetime import datetime

def parse_timestamp(ts):
    try:
        return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
    except:
        return datetime.min

# 🔥 sort by timestamp


def merge_images(images):

    if not images or images[0].filename == "":
        return None

    img_list = []

    # Open images (original size)
    for img in images:
        image = Image.open(img).convert("RGBA")
        img_list.append(image)

    # 🔥 Final height = max height
    max_height = max(img.height for img in img_list)

    # Total width = sum of all widths (original)
    total_width = sum(img.width for img in img_list)

    # Create black background
    final_img = Image.new("RGB", (total_width, max_height), (0, 0, 0))

    # Paste images (center vertically)
    x_offset = 0
    for img in img_list:
        y_offset = (max_height - img.height) // 2   # 🔥 center vertically
        final_img.paste(img, (x_offset, y_offset))
        x_offset += img.width

    return final_img


app = Flask(__name__)
app.secret_key = "heavy-secret"
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.permanent_session_lifetime = timedelta(days=1500)


from flask import Response

@app.route("/sitemap.xml", methods=["GET"])
def sitemap():

    base_url = "https://www.shopkarodeals.in"

    pages = []

    # 🔹 Static Pages
    static_urls = [
        "/",
        "/Customer_Login",
        "/Customer_Ragistration",
        "/Mediator_Login",
        "/orderform",
        "/directrefundform",
        "/customer/deals",
        "/Scanner",
        "/pay"
    ]

    for url in static_urls:
        pages.append(base_url + url)

    # 🔹 Dynamic Pages (Brands)
    try:
        conn = db()
        cur = conn.cursor()
        cur.execute(f"SELECT Seller FROM {NAME}_Sellers")
        brands = cur.fetchall()
        cur.close()
        conn.close()

        for b in brands:
            brand_name = b[0]
            pages.append(f"{base_url}/Customer_Portal/Dashboard?brand={brand_name}")

    except:
        pass

    # 🔹 XML Generate
    sitemap_xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap_xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    for page in pages:
        sitemap_xml.append("<url>")
        sitemap_xml.append(f"<loc>{page}</loc>")
        sitemap_xml.append("</url>")

    sitemap_xml.append("</urlset>")

    return Response("\n".join(sitemap_xml), mimetype="application/xml")

cloudinary.config(
    cloud_name="dajnnvznf",
    api_key="949949375829316",
    api_secret="BQ1CJTtlscFnilZ1OnU-MBgZ6vA"
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file"
]

creds = ServiceAccountCredentials.from_json_keyfile_name('/etc/secrets/credentials.json', SCOPES)
client = gspread.authorize(creds)


# ----------send email for password --------------

# ---------- DB CONNECTION ----------
def db():
    s=psycopg2.connect("postgresql://neondb_owner:npg_tYsv8cD9MVAu@ep-rough-grass-a1bedl2d-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")
    return s



NAME="ShopKaro"
MainSheet = client.open_by_key("1P4ES2eTEUTD0qTyfFyLVmJXvMmxrzgY4fVFEZ7JcbcA").sheet1
    
paymant=True
@app.before_request
def force_custom_domain():
    if paymant:
        if "onrender.com" in request.host:
            return redirect("https://www.shopkarodeals.in", code=301)
    else :
        return render_template("suspend.html")


import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_verification_email(to_email, code):
    try:
        sender_email = "heavydeals07@gmail.com"
        app_password = "YOUR_APP_PASSWORD"

        msg = MIMEMultipart()
        msg["Subject"] = "Heavy Deals | Password Reset Code"
        msg["From"] = sender_email
        msg["To"] = to_email

        html = f"""
        <h3>Heavy Deals – Password Reset</h3>
        <p>Your verification code is:</p>
        <h2>{code}</h2>
        """

        msg.attach(MIMEText(html, "html"))

        # 🔥 timeout add kiya
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
        server.starttls()
        server.login(sender_email, app_password)
        server.send_message(msg)
        server.quit()

        print("✅ Email sent")

    except Exception as e:
        print("❌ ERROR:", e)

@app.route('/ping')
def Ping():
    return "OK"

# ---------- HOME ----------
@app.route('/')
def Home():

    # 🔹 Customer already logged in?
    if session.get('Cust num'):
        return redirect('/Customer_Portal/Dashboard')

    # 🔹 Mediator already logged in?
    if session.get('Med Username'):
        return redirect('/Mediator_Portal/Dashboard')

    # 🔹 Otherwise show home page
    return render_template("Home.html", NAME=NAME)

# ---------- CUSTOMER REGISTRATION ----------
@app.route('/Customer_Ragistration', methods=['GET','POST'])
def Customer_Ragistration():
    msg = ""
    if request.method == 'POST':
        name = request.form['N']
        num = request.form['Num']
        passw = None
        email = request.form['E']
        upi = request.form['upi']
        conn = db()
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {NAME}_Customers WHERE Number=%s", (num,))
        if cur.fetchone():
            msg = "This mobile number is already registered"
        else:
            cur.execute(
                f"INSERT INTO {NAME}_Customers (Name, Number, passw, email,upi) VALUES (%s,%s,%s,%s,%s)",
                (name, num, passw, email,upi)
            )
            conn.commit()
            cur.close()
            conn.close()

            CustomerSheet=client.open_by_key("1P4ES2eTEUTD0qTyfFyLVmJXvMmxrzgY4fVFEZ7JcbcA").get_worksheet(1)
            data = {"Name":name,"Whatsapp":num,"Email":email,"UPI ID":upi,"Password":passw}
            safe_append(CustomerSheet, data)

            session.permanent = True
            session['Cust name'] = name
            session['Cust num'] = num
            session['Cust passw'] = passw
            session['Cust email'] = email
            session['Cust upi']=upi
            return render_template("Registration_Success.html")
        cur.close()
        conn.close()
    return render_template("Customer_Ragistration.html", msg=msg, NAME=NAME)

# ---------- CUSTOMER LOGIN ----------
@app.route('/Customer_Login', methods=['GET','POST'])
def Customer_Login():
    msg = ""
    if request.method == 'POST':
        num = request.form['Num']
        conn = db()
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {NAME}_Customers WHERE Number=%s", (num,))
        row = cur.fetchone()
        if row is None:
            msg = "Mobile number not registered"
        else:
            cur.close()
            conn.close()
            session.permanent = True
            session['Cust name'] = row[1]
            session['Cust num'] = row[2]
            session['Cust passw'] = row[3]
            session['Cust email'] = row[4]
            session['Cust upi']=row[5]
            return redirect('/Customer_Portal/Dashboard')
        cur.close()
        conn.close()
    return render_template("Customer_Login.html", msg=msg)

# ---------- Logout ----------
@app.route('/Logout')
def Logout():
    session.clear()
    return redirect('/')

    # -------------Cost Forgot password---------------

# ---------- Password reset ----------
@app.route('/Forgot_Password', methods=['GET', 'POST'])
def Forgot_Password():
    msg = ""

    if request.method == 'POST':
        email = request.form['email']

        conn = db()
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {NAME}_Customers WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user is None:
            msg = "Email not registered"
        else:
            code = str(random.randint(100000, 999999))
            session['fp_email'] = email
            session['fp_code'] = code

            send_verification_email(email, code)
            return redirect('/Verify_Code')

    return render_template('Forgot_Password.html', msg=msg, NAME=NAME)
@app.route('/Verify_Code', methods=['GET', 'POST'])
def Verify_Code():
    msg = ""

    if request.method == 'POST':
        user_code = request.form['code']

        if user_code == session.get('fp_code'):
            return redirect('/Reset_Password')
        else:
            msg = "Invalid verification code"

    return render_template('Verify_Code.html', msg=msg, NAME=NAME)
@app.route('/Reset_Password', methods=['GET', 'POST'])
def Reset_Password():
    msg = ""

    if request.method == 'POST':
        p1 = request.form['p1']
        p2 = request.form['p2']

        if p1 != p2:
            msg = "Passwords do not match"
        else:
            email = session.get('fp_email')

            conn = db()
            cur = conn.cursor()
            cur.execute(
                f"UPDATE {NAME}_Customers SET passw=%s WHERE email=%s",
                (p1, email)
            )
            conn.commit()
            cur.close()
            conn.close()

            session.pop('fp_email', None)
            session.pop('fp_code', None)

            return redirect('/Password_Reset_Success')

    return render_template('Reset_Password.html', msg=msg, NAME=NAME)
@app.route('/Password_Reset_Success')
def Password_Reset_Success():
    return render_template('Password_Reset_Success.html', NAME=NAME)


# ---------- CUSTOMER PORTAL ----------
@app.route('/Customer_Portal/Dashboard')
def Customer_Portal_Dashboard():
    if session.get('Cust num') == None:
        return redirect('/')

    currentbrand = request.args.get('brand')
    sort = request.args.get("sort")
    rec = request.args.get("rec")
    name=session.get('Cust name')
    num=session.get('Cust num')
    passw=session.get('Cust passw')
    email=session.get('Cust email')
    
    
    
    conn=db()
    cur=conn.cursor()
    cur.execute(f"SELECT Seller FROM {NAME}_Sellers")
    brands = cur.fetchall()
    cur.close()
    conn.close()
    


    global MainSheet
    sheet = MainSheet
    all_values = sheet.get_all_values()
    headers = all_values[0]
    data_rows = all_values[1:]
    mobile_index = headers.index("Whatsapp")
    order_product_index = headers.index("Product Name")
    order_id_index = headers.index("Order ID")
    order_date_index = headers.index("Order Date")
    order_status_index = headers.index("Status")
    order_brand_index = headers.index("Brand Name")
    order_amount_index = headers.index("Order Amount")
    order_refundAmount_index = headers.index("Refund Amount")
    order_reviewer_index = headers.index("Profile Name")
    order_ss_index = headers.index("Order SS")
    timestamp_index= headers.index("TimeStamp")
    order_type_index= headers.index("Type")
    user_orders = []
    


    TO = 0
    for row in data_rows:
        if str(row[mobile_index]) == str(num):
            TO+=1
            user_orders.append((row[order_id_index], row[order_date_index], row[order_status_index], row[order_brand_index], row[order_refundAmount_index],row[order_reviewer_index], row[order_amount_index],row[order_ss_index],row[order_product_index], row[timestamp_index], row[order_type_index]))
    
    RO = 0
    Payout=0
    for i in user_orders:
        if i[2]=="Done":
            Payout+=int(i[4])
            RO+=1
    
    if sort == "oldFirst":
        user_orders = sorted(user_orders, key=lambda x: parse_timestamp(x[9]))
    else:
        user_orders = sorted(user_orders, key=lambda x: parse_timestamp(x[9]), reverse=True)
    

    send_orders=[]
    if rec=="Done":
        for i in user_orders:
            if i[2]=="Done":
                send_orders.append(i)
    elif rec=="Pending":
        for i in user_orders:
            if i[2]=="Pending":
                send_orders.append(i)
    else:
        send_orders=user_orders


    if currentbrand and currentbrand != "None":
        filtered_orders = []
        for order in send_orders:
            if order[3] == str(currentbrand):
                filtered_orders.append(order)
        send_orders=filtered_orders
    
    
    return render_template("Customer_Dashboard.html",brands=brands,brand=currentbrand,rec=rec,sort=sort,orders=send_orders, name=name, num=num, passw=passw, email=email,TO=TO,PO=TO-RO,CO=RO,R=Payout, NAME=NAME)

# ---------- MEDIATOR LOGIN ----------
@app.route('/Mediator_Login',methods=['GET','POST'])
def Mediator_Login():
    msg=""
    if request.method == 'POST':
        MUN=request.form['MUN']
        MP=request.form['MP']

        conn = db()
        cur=conn.cursor()

        cur.execute(f"SELECT * FROM {NAME}_mediator WHERE username=%s", (MUN,))
        row = cur.fetchone()

        if row is None:
            msg = "Username not found"
        elif row[4] != MP:
            msg = "Incorrect password"
        else:
            cur.close()
            conn.close()
            session.permanent = True
            session['Med Username'] = row[1]
            session['Med name'] = row[2]
            session['Med num'] = row[3]
            session['Med passw'] = row[4]
            return redirect('/Mediator_Portal/Dashboard')
        cur.close()
        conn.close()
    return render_template("Mediator_Login.html",msg=msg)

#------------Med Forgot passeord--------------
@app.route('/Med_Forgot_Password', methods=['GET', 'POST'])
def MForgot_Password():
    msg = ""

    if request.method == 'POST':
        email = request.form['email']

        conn = db()
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {NAME}_mediator WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user is None:
            msg = "Email not registered"
        else:
            code = str(random.randint(100000, 999999))
            session['fp_email'] = email
            session['fp_code'] = code

            send_verification_email(email, code)
            return redirect('/Med_Verify_Code')

    return render_template('Med_Forgot_Password.html', msg=msg, NAME=NAME)
@app.route('/Med_Verify_Code', methods=['GET', 'POST'])
def MVerify_Code():
    msg = ""

    if request.method == 'POST':
        user_code = request.form['code']

        if user_code == session.get('fp_code'):
            return redirect('/Med_Reset_Password')
        else:
            msg = "Invalid verification code"

    return render_template('Med_Verify_Code.html', msg=msg, NAME=NAME)
@app.route('/Med_Reset_Password/', methods=['GET', 'POST'])
def MReset_Password():
    msg = ""

    if request.method == 'POST':
        p1 = request.form['p1']
        p2 = request.form['p2']

        if p1 != p2:
            msg = "Passwords do not match"
        else:
            email = session.get('fp_email')

            conn = db()
            cur = conn.cursor()
            cur.execute(
                f"UPDATE {NAME}_mediator SET password=%s WHERE email=%s",
                (p1, email)
            )
            conn.commit()
            cur.close()
            conn.close()

            session.pop('fp_email', None)
            session.pop('fp_code', None)

            return redirect('/Med_Password_Reset_Success')

    return render_template('Med_Reset_Password.html', msg=msg, NAME=NAME)
@app.route('/Med_Password_Reset_Success')
def MPassword_Reset_Success():
    return render_template('Med_Password_Reset_Success.html', NAME=NAME)


# ---------- MEDIATOR PORTAL ----------
@app.route('/Mediator_Portal/Dashboard')
def Mediator_Portal_Dashboard():
    if session.get('Med Username') == None:
        return redirect('/Mediator_Login')
    
    currentbrand = request.args.get('brand')
    sort = request.args.get("sort")
    rec = request.args.get("rec")
    MUN = session.get('Med Username')
    MN = session.get('Med name')
    MNUM = session.get('Med num')

    
    
    conn=db()
    cur=conn.cursor()
    cur.execute(f"SELECT Seller FROM {NAME}_Sellers")
    brands = cur.fetchall()
    cur.close()
    conn.close()


    global MainSheet
    sheet = MainSheet
    sheeturl=sheet.url
    all_values = sheet.get_all_values()
    headers = all_values[0]
    data_rows = all_values[1:]
    
    product_name_index = headers.index("Product Name")
    mobile_index = headers.index("Whatsapp")
    timestamp_index= headers.index("TimeStamp")
    order_id_index = headers.index("Order ID")
    order_date_index = headers.index("Order Date")
    order_status_index = headers.index("Status")
    order_brand_index = headers.index("Brand Name")
    order_amount_index = headers.index("Order Amount")
    order_refundAmount_index = headers.index("Refund Amount")
    order_reviewer_index = headers.index("Profile Name")
    order_ss_index = headers.index("Order SS")
    order_upi_index = headers.index("UPI ID")

    user_orders = []


    TO=0
    for row in data_rows:
        if row[order_status_index]:
            TO+=1
            user_orders.append((row[order_id_index], row[order_date_index], row[order_status_index], row[order_brand_index], row[order_refundAmount_index],row[order_reviewer_index], row[order_date_index], row[mobile_index],row[timestamp_index], row[order_ss_index], row[product_name_index], row[order_amount_index],row[order_upi_index]))

    
    CO=0
    Payout=0
    for i in user_orders:
        if i[2]=="Done":
            Payout+=int(i[4])
            CO+=1
    
    if sort == "oldFirst":
        user_orders = sorted(user_orders, key=lambda x: parse_timestamp(x[8]))
    else:
        user_orders = sorted(user_orders, key=lambda x: parse_timestamp(x[8]), reverse=True)

    send_orders=[]
    if rec=="Done":
        for i in user_orders:
            if i[2]=="Done":
                send_orders.append(i)
    elif rec=="Pending":
        for i in user_orders:
            if i[2]=="Pending":
                send_orders.append(i)
    else:
        send_orders=user_orders


    if currentbrand:
        filtered_orders = []
        for order in send_orders:
            if order[3] == str(currentbrand):
                filtered_orders.append(order)
        send_orders=filtered_orders
    

    return render_template('Mediator_Dashboard.html',brand=currentbrand,brands=brands,rec=rec,sort=sort,orders=send_orders, MUN=MUN, MN=MN, MNUM=MNUM, TO=TO, CO=CO,PF=(TO-CO), TP=Payout, url=sheeturl, NAME=NAME)



@app.route("/add_deal_code", methods=["POST"])
def add_deal_code():
    if session.get('Med Username') == None:
        return redirect('/Mediator_Login')
    Nmsg=""
    pmsg=""
    MUN = session.get('Med Username')
    MN = session.get('Med name')
    MNUM = session.get('Med num')
    if request.method=='POST':
        seller = request.form["deal_code"]
        conn = db()
        cur=conn.cursor()
        cur.execute(f"SELECT * FROM {NAME}_Sellers WHERE Seller=%s", (seller,))
        if cur.fetchone():
            Nmsg = "This Brand is already exist"
            cur.close()
            conn.close()
            return redirect(f'/Brands?Nmsg={Nmsg}')
            
        else:
            
            cur.close()
            conn.close()
            session['Brand'] = seller
            return redirect('/login')
        
    return redirect('/Brands')
@app.route("/login")
def login():

    username = session.get("Med Username")

    if not username:
        return redirect("/Mediator_Login")

    # Check token in DB
    conn = db()
    cur = conn.cursor()

    cur.execute(f"""
        SELECT token FROM {NAME}_mediator
        WHERE username=%s
    """, (username,))

    row = cur.fetchone()

    cur.close()
    conn.close()

    # If token already exists skip Google login
    if row and row[0]:
        return redirect("/create-sheet")

    flow = Flow.from_client_secrets_file(
        "/etc/secrets/client_secret.json",    
        scopes=SCOPES,
        redirect_uri="https://shopkarodeals.in/callback"
    )

    auth_url, state = flow.authorization_url(
        prompt="consent",
        access_type="offline",
       include_granted_scopes="true"
    )

    session["state"] = state
    session["code_verifier"] = flow.code_verifier

    return redirect(auth_url)

#----------callback--------
@app.route("/callback")
def callback():

    state = session.get("state")

    flow = Flow.from_client_secrets_file(
        "/etc/secrets/client_secret.json",
        scopes=SCOPES,
        state=session["state"],
        redirect_uri="https://shopkarodeals.in/callback"
    )

    flow.code_verifier = session["code_verifier"]

    flow.fetch_token(authorization_response=request.url)

    creds = flow.credentials
    token_json = creds.to_json()

    username = session.get("Med Username")

    if not username:
        return redirect("/Mediator_Login")

    conn = db()
    cur = conn.cursor()

    cur.execute(
        f"UPDATE {NAME}_mediator SET token=%s WHERE username=%s",
        (token_json, username)
    )

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/create-sheet")

from google.oauth2.credentials import Credentials
import json
def get_mediator_creds(username):
    conn = db()
    cur = conn.cursor()
    cur.execute(f"""
        SELECT token FROM {NAME}_mediator
        WHERE username=%s
    """, (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row or not row[0]:
        return None
    
    token_data = json.loads(row[0])
    creds = Credentials.from_authorized_user_info(token_data)
    return creds
from google.auth.transport.requests import Request
def refresh_if_needed(creds, username):
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Save updated token
        conn = db()
        cur = conn.cursor()
        cur.execute(f"""
            UPDATE {NAME}_mediator
            SET token=%s
            WHERE username=%s
        """, (
            creds.to_json(),
            username
        ))
        conn.commit()
        cur.close()
        conn.close()
    return creds
# ---------------- CREATE SHEET ----------------
from google.auth.transport.requests import Request
@app.route("/create-sheet")
def create_sheet():

    username = session["Med Username"]

    creds = get_mediator_creds(username)

    if not creds:
        return redirect("/login")

    creds = refresh_if_needed(creds, username)

    sheets_service = build("sheets", "v4", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    # Continue sheet creation...

    # -------- Create Sheet --------
    Brand=session.get('Brand')
    spreadsheet = {
        "properties": {
            "title": Brand
        }
    }

    sheet = sheets_service.spreadsheets().create(
        body=spreadsheet,
        fields="spreadsheetId,spreadsheetUrl"
    ).execute()

    

    sheet_id = sheet["spreadsheetId"]
    sheet_url = sheet["spreadsheetUrl"]

    # -------- Add Header Row --------
    headers = [[
        "Brand Name",
        "Order Date",
        "Product Name",
        "Order ID",
        "Profile Name",
        "Order Amount",
        "Order SS",
        "Delivered SS",
        "Review SS",
        "Review Link",
        "Status",
        "Type"
    ]]

    body = {
        "values": headers
    }

    sheets_service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range="A1",
        valueInputOption="RAW",
        body=body
    ).execute()

    # -------- Share Sheet --------
    permission = {
        "type": "user",
        "role": "writer",
        "emailAddress": "hd-839@last-488313.iam.gserviceaccount.com"   # 👈 Change this
    }

    drive_service.permissions().create(
        fileId=sheet_id,
        body=permission
    ).execute()

    
# -------- Format Header Like Screenshot --------

    requests = [

        # Header Style
        {
            "repeatCell": {
                "range": {
                    "sheetId": 0,
                    "startRowIndex": 0,
                    "endRowIndex": 1
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {
                            "red": 1,
                            "green": 0.8,
                            "blue": 0.2
                        },
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE",
                        "textFormat": {
                            "fontSize": 18,
                            "bold": True,
                            "foregroundColor": {
                                "red": 0,
                                "green": 0,
                                "blue": 0
                            }
                        }
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
            }
        },

        # Freeze Header Row
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": 0,
                    "gridProperties": {
                        "frozenRowCount": 1
                    }
                },
                "fields": "gridProperties.frozenRowCount"
            }
        },

        # Set Row Height Bigger
        {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": 0,
                    "dimension": "ROWS",
                    "startIndex": 0,
                    "endIndex": 1
                },
                "properties": {
                    "pixelSize": 45
                },
                "fields": "pixelSize"
            }
        }
    ]

    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={"requests": requests}
    ).execute()

    Pmsg=f"Added :- {Brand}"
    conn = db()
    cur=conn.cursor()
    cur.execute(f"INSERT INTO {NAME}_Sellers (Seller,key,status) VALUES (%s,%s,%s)",(Brand,sheet_id,"Open"))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(f'/Brands?Pmsg={Pmsg}')


@app.route("/Scanner")
def Scanner():
    return render_template("scanner.html")

@app.route("/Brands")
def Brands():
    if session.get('Med Username') == None:
        return redirect('/Mediator_Login')
    
    Nmsg = request.args.get("Nmsg")
    Pmsg = request.args.get("Pmsg")
    MUN = session.get('Med Username')
    MN = session.get('Med name')
    MNUM = session.get('Med num')
    global MainSheet
    sheet=MainSheet
    mainurl=sheet.url
    brands = []

    conn = db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {NAME}_Sellers")
    db_brands = cursor.fetchall()
    cursor.close()
    conn.close()

    for b in db_brands:
        brandSheet = client.open_by_key(b[1]).sheet1
        url=brandSheet.url
        data = brandSheet.get_all_values()
        row = data[1:]
        brands.append((b[0], len(row), url, b[2]))

    return render_template("Brands.html", Nmsg=Nmsg,Pmsg=Pmsg, MUN=MUN, MN=MN, MNUM=MNUM, brands=brands,url=mainurl, NAME=NAME)

@app.route("/Brand_Hide/<BN>")
def BrandHide(BN):
    conn = db()
    cur = conn.cursor()
    cur.execute(f"UPDATE {NAME}_Sellers SET status=%s WHERE seller=%s", ("Hide",BN))
    conn.commit()
    cur.close()
    conn.close()

    return redirect("/Brands")

@app.route("/Brand_Open/<BN>")
def BrandOpen(BN):
    conn = db()
    cur = conn.cursor()
    cur.execute(f"UPDATE {NAME}_Sellers SET status=%s WHERE seller=%s", ("Open",BN))
    conn.commit()
    cur.close()
    conn.close()

    return redirect("/Brands")

@app.route("/delete-brand/<brand>")
def delete_brand(brand):
    if session.get('Med Username') == None:
        return redirect('/Mediator_Login')

    conn = db()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {NAME}_Sellers WHERE Seller=%s", (brand,))
    brand_data = cur.fetchone()
    cur.close()
    conn.close()

    key=brand_data[1]


    username = session.get("Med Username")

    if not username:
        return redirect("/Mediator_Login")

    creds = get_mediator_creds(username)
    creds = refresh_if_needed(creds, username)

    drive_service = build("drive", "v3", credentials=creds)

    try:
        spreadsheet = client.open_by_key(key)
        sheet_id = spreadsheet.id

        # 🔥 Delete using mediator (Owner)
        drive_service.files().delete(fileId=sheet_id).execute()

    except Exception as e:
        print("Delete Error:", e)

    # 🔹 Remove brand from MySQL
    conn = db()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {NAME}_Sellers WHERE Seller=%s", (brand,))
    conn.commit()
    cur.close()
    conn.close()

    return redirect("/Brands")


def safe_append(sheet, data_dict):

    headers = sheet.row_values(1)

    row = []
    for header in headers:
        row.append(data_dict.get(header, ""))

    # find next empty row
    data = sheet.get_all_values()
    next_row = len(data) + 1

    sheet.insert_row(row, next_row)


def upload_compressed_image(file):

    if isinstance(file, Image.Image):
        img = file.convert("RGB")
    else:
        img = Image.open(file).convert("RGB")


    # resize large images
    img.thumbnail((1000, 1000))

    # compress image
    img_io = io.BytesIO()
    img.save(img_io, format="JPEG", quality=60, optimize=True)
    img_io.seek(0)

    # upload to cloudinary
    result = cloudinary.uploader.upload(img_io)

    return result["secure_url"]


@app.route("/orderform", methods=["GET", "POST"])
def orderform():
    if session.get('Cust num') == None:
        return redirect('/')
    conn = db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {NAME}_Sellers")
    brands = cursor.fetchall()
    cursor.close()
    conn.close()
    msg=""
    name = session.get('Cust name')
    num = session.get('Cust num')
    passw = session.get('Cust passw')
    email = session.get('Cust email')
    upi = session.get("Cust upi")
    if request.method == "POST":

        brand = request.form.get("brand")
        order_id = request.form.get("order_id").replace(" ", "")
        date_input = request.form.get("order_date")
        order_date = datetime.strptime(date_input, "%Y-%m-%d").strftime("%d-%m-%Y")
        reviewer_name = request.form.get("reviewer_name")
        Product_name = request.form.get("PN")
        Oamount = int(request.form.get("amount"))
        Ramount = int(request.form.get("refund_amount"))
        type = request.form.get("type")
        upi = request.form.get("upi")

        global MainSheet
        OSheet = MainSheet
        conn = db()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {NAME}_Sellers WHERE Seller=%s", (brand,))
        brand_data = cursor.fetchone()
        cursor.close()
        conn.close()
        
        BrandSheet = client.open_by_key(brand_data[1]).sheet1
        all_values = OSheet.get_all_values()
        headers = all_values[0]
        data_rows = all_values[1:]
        order_id_index = headers.index("Order ID")
        user_orders = []
        for row in data_rows:
            if row[order_id_index] == order_id:
                msg="This Order ID is already filled"
                return render_template("Customer_Order_Form.html",upi = upi,name=name,num=num,passw=passw,email=email,brands=brands,msg=msg,NAME=NAME)


        now = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")

        url = ""   # 🔥 important fix (avoid undefined error)

        Order_SS = request.files.get("screenshot")
        if Order_SS:
            url = upload_compressed_image(Order_SS)

        # 🔥 Header-based mapping
        data = {
            "TimeStamp": str(now),
            "Brand Name": brand,
            "Profile Name": reviewer_name,
            "Order Date": order_date,
            "Product Name": Product_name,
            "Order SS": url,
            "Order Amount": Oamount,
            "Order ID": order_id,
            "Email": email,
            "Whatsapp": int(num),
            "Status": "Pending",
            "UPI ID": upi,
            "Refund Amount": Ramount,
            "Mediator name": NAME,
            "Type" : type
        }

        safe_append(OSheet, data)
        safe_append(BrandSheet, data)

        return render_template("order_success.html")

    # -------- GET REQUEST PART --------
    

    return render_template(
        "Customer_Order_Form.html",
        upi = upi,
        name=name,
        num=num,
        passw=passw,
        email=email,
        brands=brands,
        msg=msg,
        NAME=NAME
    )

@app.route("/directrefundform", methods=["GET", "POST"])
def directrefundform():
    msg=""
    if request.method == "POST":
        ID = request.form.get("order_id")

        global MainSheet
        OrderSheet = MainSheet
        all_values = OrderSheet.get_all_values()
        headers = all_values[0]
        data_rows = all_values[1:]
        order_id_index = headers.index("Order ID")
        order_brand_index = headers.index("Brand Name")
        order_reviewer_index = headers.index("Profile Name")
        

        for row in data_rows:
            if str(row[order_id_index]) == str(ID):
               detail=(row[order_brand_index],row[order_id_index],row[order_reviewer_index]) 

        if detail:
            return redirect(f"/refundform?id={detail[1]}&DealCode={detail[0]}&ProfileName={detail[2]}&direct=1")
        else:
            msg="Order id is not Exist"
            return render_template("order_check.html",msg=msg)
        
    return render_template("order_check.html")

@app.route("/refundform", methods=["GET", "POST"])
def refundform():
    msg=""
    id = request.args.get("id")
    DC = request.args.get("DealCode")
    RN = request.args.get("ProfileName")
    D = str(request.args.get("direct"))
    name=session.get('Cust name')
    num=session.get('Cust num')
    passw=session.get('Cust passw')
    email=session.get('Cust email')
    if request.method == "POST":
        
        global MainSheet
        OrderSheet = MainSheet
        
        if DC :
            deal_code=DC
        else:
            deal_code   = request.form.get("deal_code")
        
        if id :
            order_id=id.replace(" ","")
        else:
            order_id       = request.form.get("order_id_p").replace(" ","")

        
        reviewer_name  = request.form.get("reviewer_name")
        link           = request.form.get("link")

        all_values = OrderSheet.get_all_values()
        headers = all_values[0]
        data_rows = all_values[1:]
        order_id_index = headers.index("Order ID")
        order_mobile_index = headers.index("Whatsapp")
        status_col   = headers.index("Status")
        Dss_col      = headers.index("Delivered SS")
        Rss_col      = headers.index("Review SS")
        RL_col       = headers.index("Review Link")


        flag = 0
        for row in data_rows:
            if row[order_id_index] == order_id and row[order_mobile_index]==num:
                flag=1
                break
            
        if flag == 0:
            msg="Invalid Order-ID"
            if id != 'undefined' :
                return render_template("Customer_Refund_Form.html",D=D,RN=RN,DC=DC,msg=msg,id=id, name=name, num=num, passw=passw, email=email, NAME=NAME)
            else :
                return render_template("Customer_Refund_Form.html",D=D,RN=RN,DC=DC,msg=msg, name=name, num=num, passw=passw, email=email,NAME=NAME)

        else:
            Review_SS = request.files.getlist("Review-screenshot")
            if Review_SS:
                Murged_Review_SS = merge_images(Review_SS)
                Review_url = upload_compressed_image(Murged_Review_SS)

            D_SS = request.files.getlist("D-screenshot")
            if D_SS:
                Murged_D_SS = merge_images(D_SS)
                D_url = upload_compressed_image(Murged_D_SS)


            for i, row in enumerate(data_rows, start=2):
                if row[order_id_index] == order_id:
                    OrderSheet.update_cell(i, status_col + 1, "Done")
                    OrderSheet.update_cell(i, Dss_col + 1, D_url)
                    OrderSheet.update_cell(i, Rss_col + 1, Review_url)
                    OrderSheet.update_cell(i, RL_col + 1, link)
                    break

            conn = db()
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {NAME}_Sellers WHERE Seller=%s", (deal_code,))
            brand_data = cursor.fetchone()
            cursor.close()
            conn.close()

            BrandSheet= client.open_by_key(brand_data[1]).sheet1
            Call_values = BrandSheet.get_all_values()
            Cheaders = Call_values[0]
            Cdata_rows = Call_values[1:]
            Corder_id_index = Cheaders.index("Order ID")
            Cstatus_col   = Cheaders.index("Status")
            CDss_col      = Cheaders.index("Delivered SS")
            CRss_col      = Cheaders.index("Review SS")
            CRL_col       = Cheaders.index("Review Link")
            for i, row in enumerate(Cdata_rows, start=2):
                if row[Corder_id_index] == order_id:
                    BrandSheet.update_cell(i, Cstatus_col + 1, "Done")
                    BrandSheet.update_cell(i, CDss_col + 1, D_url)
                    BrandSheet.update_cell(i, CRss_col + 1, Review_url)
                    BrandSheet.update_cell(i, CRL_col + 1, link)
                    break

            return render_template("order_success.html")
    
    if id != 'undefined' :
        return render_template("Customer_Refund_Form.html",D=D,RN=RN,DC=DC,id=id,msg=msg, name=name, num=num, passw=passw, email=email, NAME=NAME)
    else :
        return render_template("Customer_Refund_Form.html",D=D,RN=RN,DC=DC, name=name,msg=msg, num=num, passw=passw, email=email, NAME=NAME)


# ---------------- Delete row ----------------
@app.route("/delete_order/<order_id>/<brand>")
def delete_order(order_id,brand):
    global MainSheet
    sheet = MainSheet
    data = sheet.get_all_values()

    headers = data[0]
    order_id_index = headers.index("Order ID")

    for i, row in enumerate(data):
        if row[order_id_index] == order_id:
            sheet.delete_rows(i+1)
            break

    # ----- Brand Sheet -----
    conn = db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {NAME}_Sellers WHERE Seller=%s", (brand,))
    brand_data = cursor.fetchone()
    cursor.close()
    conn.close()
    
    brand = client.open_by_key(brand_data[1]).sheet1
    data = brand.get_all_values()

    headers = data[0]
    order_id_index = headers.index("Order ID")

    for i, row in enumerate(data):
        if row[order_id_index] == order_id:
            brand.delete_rows(i+1)
            break
            
    return redirect("/Mediator_Portal/Dashboard")

@app.route("/customer/deals")
def customer_deals():
    if session.get('Cust num') == None:
        return redirect('/')
    name=session.get('Cust name')
    num=session.get('Cust num')
    passw=session.get('Cust passw')
    email=session.get('Cust email')
    

    sheet = client.open_by_key("1P4ES2eTEUTD0qTyfFyLVmJXvMmxrzgY4fVFEZ7JcbcA").worksheet("Deals")
    sheeturl=sheet.url

    deals = sheet.get_all_values()[1:]
    deals = deals[::-1]  # Show latest deals first

    return render_template(
        "Customer_All_Deal.html",
        deals=deals,
        NAME=NAME,
        name=name,
        num=num,
        passw=passw,
        email=email,
        url=sheeturl
    )

ALL_DEALS = []
@app.route("/mediator/deals")
def mediator_deals():
    if session.get('Med Username') == None:
        return redirect('/Mediator_Login')
    MUN = session.get('Med Username')
    MN = session.get('Med name')
    MNUM = session.get('Med num')

    sheet = client.open_by_key("1P4ES2eTEUTD0qTyfFyLVmJXvMmxrzgY4fVFEZ7JcbcA").worksheet("Deals")
    sheeturl=sheet.url

    deals = sheet.get_all_values()[1:]
    global ALL_DEALS
    ALL_DEALS = deals[::-1]  # Show latest deals first

    return render_template(
        "mediator_deals.html",
        deals=ALL_DEALS,
        NAME=NAME,
        MN=MN,
        MUN=MUN,
        MNUM=MNUM,
        url=sheeturl
    )



@app.route("/add_deal", methods=["POST"])
def add_deal():

    if session.get('Med Username') == None:
        return redirect('/Mediator_Login')

    sheet = client.open_by_key("1P4ES2eTEUTD0qTyfFyLVmJXvMmxrzgY4fVFEZ7JcbcA").worksheet("Deals")

    product_code = request.form.get("product_code")
    platform = request.form.get("platform")
    deal_type = request.form.get("deal_type")
    order_price = request.form.get("order_price")
    refund_amount = request.form.get("refund_amount")

    image_file = request.files.get("image")

    image_url = ""

    if image_file and image_file.filename != "":
        image_url = upload_compressed_image(image_file)

    

    data={
        "Image URL": image_url,
        "Product Code": product_code,
        "Platform": platform,
        "Deal Type": deal_type,
        "Order Price": order_price,
        "Refund Amount": refund_amount
    }

    safe_append(sheet, data)
    

    return redirect("/mediator/deals")

@app.route("/delete_deal/<code>")
def delete_deal(code):

    sheet = client.open_by_key("1P4ES2eTEUTD0qTyfFyLVmJXvMmxrzgY4fVFEZ7JcbcA").worksheet("Deals")
    data = sheet.get_all_values()

    for i,row in enumerate(data):
        if row[1] == code:
            sheet.delete_rows(i+1)
            break

    return redirect("/mediator/deals")



def get_deal_by_code(code):
    code = code.lower().replace("-", " ").strip()

    for d in ALL_DEALS:
        name = d[1].lower().strip()

        if name == code:
            return d

    return None

import urllib.parse

@app.route("/share/<code>")
def share_deal(code):


    print("URL CODE:", code)

    deal = get_deal_by_code(code)

    print("FOUND DEAL:", deal)

    if not deal:
        return "Deal not found", 404

    return render_template("share_deal.html", deal=deal)


@app.route("/subMediators")
def subMediators():
    if session.get('Med Username') == None:
        return redirect('/Mediator_Login')
    MUN = session.get('Med Username')
    MN = session.get('Med name')
    MNUM = session.get('Med num')

    conn = db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {NAME}_sub_mediator")
    mediators_data = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("subMediator.html",NAME=NAME,MN=MN,MUN=MUN,MNUM=MNUM,mediators=mediators_data)
    
@app.route("/add_med", methods=["POST"] )
def add_med():
    if session.get('Med Username') == None:
        return redirect('/Mediator_Login')

    mNAME = request.form.get("med_Name")
    mEMAIL = request.form.get("med_Email")
    mPHONE = request.form.get("med_Num")

    return redirect(f"/create-med-sheet/{mNAME}/{mEMAIL}/{mPHONE}")

    
@app.route("/create-med-sheet/<medName>/<medEmail>/<number>")
def create_med_sheet(medName,medEmail,number):

    creds = get_mediator_creds("admin")

    creds = refresh_if_needed(creds, "admin")

    sheets_service = build("sheets", "v4", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    # Continue sheet creation...

    # -------- Create Sheet --------
    
    spreadsheet = {
        "properties": {
            "title": medName+" By ShopKaro"
        }
    }

    sheet = sheets_service.spreadsheets().create(
        body=spreadsheet,
        fields="spreadsheetId,spreadsheetUrl"
    ).execute()

    

    sheet_id = sheet["spreadsheetId"]
    sheet_url = sheet["spreadsheetUrl"]

    # -------- Add Header Row --------
    headers = [[
        "TimeStamp",
        "Brand Name",
        "Profile Name",
        "Order Date",
        "Product Name",
        "Order ID",
        "Order SS",
        "Order Amount",
        "Refund Amount",
        "Status",
        "Delivered SS",
        "Review SS",
        "Review Link",
        "Whatsapp",
        "UPI ID"
    ]]

    body = {
        "values": headers
    }

    sheets_service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range="A1",
        valueInputOption="RAW",
        body=body
    ).execute()

    # -------- Share Sheet --------
    permission = {
        "type": "user",
        "role": "writer",
        "emailAddress": "hd-839@last-488313.iam.gserviceaccount.com"   # 👈 Change this
    }

    drive_service.permissions().create(
        fileId=sheet_id,
        body=permission
    ).execute()

    permission = {
        "type": "user",
        "role": "writer",
        "emailAddress": medEmail   # 👈 Change this
    }

    drive_service.permissions().create(
        fileId=sheet_id,
        body=permission
    ).execute()

    
# -------- Format Header Like Screenshot --------

    requests = [

        # Header Style
        {
            "repeatCell": {
                "range": {
                    "sheetId": 0,
                    "startRowIndex": 0,
                    "endRowIndex": 1
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {
                            "red": 1,
                            "green": 0.8,
                            "blue": 0.2
                        },
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE",
                        "textFormat": {
                            "fontSize": 18,
                            "bold": True,
                            "foregroundColor": {
                                "red": 0,
                                "green": 0,
                                "blue": 0
                            }
                        }
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
            }
        },

        # Freeze Header Row
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": 0,
                    "gridProperties": {
                        "frozenRowCount": 1
                    }
                },
                "fields": "gridProperties.frozenRowCount"
            }
        },

        # Set Row Height Bigger
        {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": 0,
                    "dimension": "ROWS",
                    "startIndex": 0,
                    "endIndex": 1
                },
                "properties": {
                    "pixelSize": 45
                },
                "fields": "pixelSize"
            }
        }
    ]

    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={"requests": requests}
    ).execute()

    
    conn = db()
    cur=conn.cursor()
    cur.execute(f"INSERT INTO {NAME}_sub_mediator (med_name,sheet_id,email,number,sheet_url) VALUES (%s,%s,%s,%s,%s)",(medName,sheet_id,medEmail,number,sheet_url))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/subMediators")

@app.route('/gfd7dhgf6gjhs')
def cust():
    return render_template("cust.html")

@app.route("/Normal_orderform", methods=["GET", "POST"])
def Normal_orderform():
    conn = db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT Seller FROM {NAME}_Sellers")
    brands = cursor.fetchall()
    cursor.close()
    conn.close()

    conn = db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {NAME}_sub_mediator")
    mediators = cursor.fetchall()
    cursor.close()
    conn.close()
    
    msg=""
    
    if request.method == "POST":

        brand = request.form.get("brand")
        order_id = request.form.get("order_id").replace(" ", "")
        date_input = request.form.get("order_date")
        order_date = datetime.strptime(date_input, "%Y-%m-%d").strftime("%d-%m-%Y")
        reviewer_name = request.form.get("reviewer_name")
        Product_name = request.form.get("PN")
        Oamount = int(request.form.get("amount"))
        Ramount = int(request.form.get("refund_amount"))
        med = request.form.get("mediator")
        upi = request.form.get("upi")
        whatsapp = request.form.get("W")

        global MainSheet
        OSheet = MainSheet
        all_values = OSheet.get_all_values()
        headers = all_values[0]
        data_rows = all_values[1:]
        order_id_index = headers.index("Order ID")
        for row in data_rows:
            if row[order_id_index] == order_id:
                msg="This Order ID is already filled"
                return render_template("OrderForm.html",brands=brands,msg=msg,NAME=NAME,mediators=mediators)
            

        conn = db()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {NAME}_Sellers WHERE Seller=%s", (brand,))
        brand_data = cursor.fetchone()
        cursor.close()
        conn.close()
        BrandSheet = client.open_by_key(brand_data[1]).sheet1

        conn = db()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {NAME}_sub_mediator where med_name=%s", (med,))
        mediator_data = cursor.fetchone()
        cursor.close()
        conn.close()
        MedSheet=client.open_by_key(mediator_data[2]).sheet1
    


        now = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")

        url = ""   # 🔥 important fix (avoid undefined error)

        Order_SS = request.files.get("screenshot")
        if Order_SS:
            url = upload_compressed_image(Order_SS)

        # 🔥 Header-based mapping
        data = {
            "TimeStamp": str(now),
            "Brand Name": brand,
            "Profile Name": reviewer_name,
            "Order Date": order_date,
            "Product Name": Product_name,
            "Order SS": url,
            "Order Amount": Oamount,
            "Order ID": order_id,
            "Email": mediator_data[3],
            "Whatsapp": mediator_data[4],
            "Status": "Pending",
            "UPI ID": "as per mediator",
            "Refund Amount": 0,
            "Mediator name": mediator_data[1]
        }
        safe_append(OSheet, data)
        safe_append(BrandSheet, data)

        med_data = {
            "TimeStamp": str(now),
            "Brand Name": brand,
            "Profile Name": reviewer_name,
            "Order Date": order_date,
            "Product Name": Product_name,
            "Order SS": url,
            "Order Amount": Oamount,
            "Order ID": order_id,
            "Whatsapp": whatsapp,
            "Status": "Pending",
            "UPI ID": upi,
            "Refund Amount": Ramount,
            "Mediator name": NAME
        }
        safe_append(MedSheet, med_data)

        

        return render_template("NOrder_Success.html")
    
    return render_template(
        "OrderForm.html",
        
        brands=brands,
        mediators=mediators,
        msg=msg,
        NAME=NAME
    )

@app.route("/Check_Order_for_refund", methods=["GET", "POST"])
def check_order():
    msg=""
    if request.method == "POST":
        ID = request.form.get("order_id")

        global MainSheet
        OrderSheet = MainSheet
        all_values = OrderSheet.get_all_values()
        headers = all_values[0]
        data_rows = all_values[1:]
        order_id_index = headers.index("Order ID")
        order_brand_index = headers.index("Brand Name")
        order_reviewer_index = headers.index("Profile Name")
        order_med_index = headers.index("Mediator name")

        for row in data_rows:
            if str(row[order_id_index]) == str(ID):
               detail=(row[order_brand_index],row[order_id_index],row[order_reviewer_index],row[order_med_index]) 

        if detail:
            return redirect(f"/Normal_refundform/{detail[1]}/{detail[0]}/{detail[2]}/{detail[3]}")
        else:
            msg="Order id is not Exist"
            return render_template("order_check.html",msg=msg)
        
    return render_template("order_check.html")


@app.route("/Normal_refundform/<ID>/<Brand>/<PN>/<MED>", methods=["GET", "POST"])
def Normal_refundform(ID,Brand,PN,MED):

    msg=""
    
    
    
    if request.method == "POST":

        link           = request.form.get("link")

        global MainSheet
        OrderSheet = MainSheet
        all_values = OrderSheet.get_all_values()
        headers = all_values[0]
        data_rows = all_values[1:]
        order_id_index = headers.index("Order ID")
        status_col   = headers.index("Status")
        Dss_col      = headers.index("Delivered SS")
        Rss_col      = headers.index("Review SS")
        RL_col       = headers.index("Review Link")

        conn = db()
        cursor = conn.cursor()
        cursor.execute(f"SELECT key FROM {NAME}_Sellers WHERE Seller=%s",(Brand,))
        brand_key = cursor.fetchone()
        cursor.close()
        conn.close()

        BrandSheet= client.open_by_key(brand_key[0]).sheet1
        Call_values = BrandSheet.get_all_values()
        Cheaders = Call_values[0]
        Cdata_rows = Call_values[1:]
        Corder_id_index = Cheaders.index("Order ID")
        Cstatus_col   = Cheaders.index("Status")
        CDss_col      = Cheaders.index("Delivered SS")
        CRss_col      = Cheaders.index("Review SS")
        CRL_col       = Cheaders.index("Review Link")

        conn = db()
        cursor = conn.cursor()
        cursor.execute(f"SELECT sheet_id FROM {NAME}_sub_mediator WHERE med_name=%s",(MED,))
        med_key = cursor.fetchone()
        cursor.close()
        conn.close()

        MEDSheet= client.open_by_key(med_key[0]).sheet1
        Mall_values = MEDSheet.get_all_values()
        Mheaders = Mall_values[0]
        Mdata_rows = Mall_values[1:]
        Morder_id_index = Mheaders.index("Order ID")
        Mstatus_col   = Mheaders.index("Status")
        MDss_col      = Mheaders.index("Delivered SS")
        MRss_col      = Mheaders.index("Review SS")
        MRL_col       = Mheaders.index("Review Link")


        Review_SS = request.files.get("Review-screenshot")
        if Review_SS:
            Review_url = upload_compressed_image(Review_SS)
        D_SS = request.files.get("D-screenshot")
        if D_SS:
            D_url = upload_compressed_image(D_SS)


        for i, row in enumerate(data_rows, start=2):
            if row[order_id_index] == ID:
                OrderSheet.update_cell(i, status_col + 1, "Done")
                OrderSheet.update_cell(i, Dss_col + 1, D_url)
                OrderSheet.update_cell(i, Rss_col + 1, Review_url)
                OrderSheet.update_cell(i, RL_col + 1, link)
                break
        
        
        for i, row in enumerate(Cdata_rows, start=2):
            if row[Corder_id_index] == ID:
                BrandSheet.update_cell(i, Cstatus_col + 1, "Done")
                BrandSheet.update_cell(i, CDss_col + 1, D_url)
                BrandSheet.update_cell(i, CRss_col + 1, Review_url)
                BrandSheet.update_cell(i, CRL_col + 1, link)
                break

        for i, row in enumerate(Mdata_rows, start=2):
            if row[Morder_id_index] == ID:
                BrandSheet.update_cell(i, Mstatus_col + 1, "Done")
                BrandSheet.update_cell(i, MDss_col + 1, D_url)
                BrandSheet.update_cell(i, MRss_col + 1, Review_url)
                BrandSheet.update_cell(i, MRL_col + 1, link)
                break

        return render_template("NOrder_Success.html")
    
    
    return render_template("RefundForm.html",MED=MED,RN=PN,DC=Brand,id=ID)


@app.route("/pay")
def pay():
    return render_template("PAY.HTML")
# ---------- RUN ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT",8080))
    app.run(host="0.0.0.0", port=port)





