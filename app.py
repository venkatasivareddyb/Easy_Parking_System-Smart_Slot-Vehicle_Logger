from flask import Flask, render_template, redirect, url_for, flash, request, session 
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, date
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from collections import defaultdict
import os
import qrcode
import cv2
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_vehicle_number(image_path):
    try:
        img = cv2.imread(image_path)

        # Resize to improve clarity
        img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

        # Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Denoise
        gray = cv2.bilateralFilter(gray, 11, 17, 17)

        # Edge Detection (optional)
        # edged = cv2.Canny(gray, 30, 200)

        # Thresholding
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

        # OCR
        custom_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        text = pytesseract.image_to_string(thresh, config=custom_config)

        # Clean up
        number = ''.join(filter(str.isalnum, text))
        return number.upper() if number else "UNKNOWN"
    except Exception as e:
        print("OCR error:", e)
        return "UNKNOWN"


app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/plates'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True)   # NEW - for login                                  # Optional: full name
    password = db.Column(db.String(100), nullable=False)
    company_name = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)
    address = db.Column(db.String(255))
    mobile_no = db.Column(db.String(20))
    car_slots = db.Column(db.Integer, default=0)
    bike_slots = db.Column(db.Integer, default=0)
    car_cost = db.Column(db.Integer, default=0)
    bike_cost = db.Column(db.Integer, default=0)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)

class Slot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100))
    #slot_id = db.Column(db.String(20))
    type = db.Column(db.String(10))
    status = db.Column(db.String(10), default="Available")

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cid = db.Column(db.Integer)
    user_email = db.Column(db.String(100))
    company_name = db.Column(db.String(100))
    vehicle_type = db.Column(db.String(10))
    vehicle_number = db.Column(db.String(20))
    plate_photo = db.Column(db.String(100))
    entry_time = db.Column(db.DateTime)
    exit_time = db.Column(db.DateTime, nullable=True)
    duration = db.Column(db.Float, nullable=True)
    amount = db.Column(db.Float, nullable=True)

@login_manager.user_loader
def load_user(company_id):
    return db.session.get(User, int(company_id))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']  # Changed from 'email'
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()  # Match by username

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))

        flash("Invalid credentials", "danger")

    return render_template('login.html')

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    new_username = request.form.get('new_username')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not new_username and not new_password:
        flash("No changes submitted", "warning")
        return redirect(url_for('dashboard'))
        
    # Update username
    if new_username:
        if User.query.filter_by(username=new_username).first():
            flash("Username already exists. Choose another.", "danger")
            return redirect(url_for('dashboard'))
        current_user.username = new_username
        current_user.email = f"{new_username}@{current_user.company_name.lower().replace(' ', '')}.com"

    # Update password
    if new_password:
        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('dashboard'))
        current_user.password = generate_password_hash(new_password)

    db.session.commit()
    flash("Profile updated successfully", "success")
    return redirect(url_for('dashboard'))
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "info")
    return redirect(url_for('home'))

@app.route('/user_dashboard')
@login_required
def user_dashboard():
    print(f"Current user: {current_user}")  # Check terminal
    print(f"Email: {current_user.email}, Name: {current_user.username}, Company: {current_user.company_name}")
    return render_template('user_dashboard.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        current_date = date.today().strftime('%Y-%m-%d')
        companies = User.query.filter_by(is_admin=False).all()
        company_slots = defaultdict(lambda: {'car': 0, 'bike': 0})
        slots = Slot.query.filter(Slot.company_name.ilike(current_user.company_name.strip())).all()
        for slot in slots:
            if slot.type == 'Car':
                company_slots[slot.company_name]['car'] += 1
            elif slot.type == 'Bike':
                company_slots[slot.company_name]['bike'] += 1
        return render_template('admin_dashboard.html', current_date=current_date, companies=companies, company_slots=company_slots)
    else:
        slots = Slot.query.filter_by(company_name=current_user.company_name).all()
        logs = Log.query.filter_by(user_email=current_user.email).order_by(Log.entry_time.desc()).all()
        slot_summary = {'Car': {'available': 0, 'occupied': 0}, 'Bike': {'available': 0, 'occupied': 0}}
        
        # ✅ Compute counts per slot type
        for slot in slots:
            if slot.status == 'Available':
                slot_summary[slot.type]['available'] += 1
            else:
                slot_summary[slot.type]['occupied'] += 1
        car_cost = current_user.car_cost
        bike_cost = current_user.bike_cost
        cost_summary = {'Car': car_cost, 'Bike': bike_cost}

        # 🚀 Process logs with duration & amount
        updated_logs = []
        for log in logs:
            duration_hrs = ''
            amount = ''
            qr_path = ''
            if log.exit_time:
                duration = log.exit_time - log.entry_time
                duration_hrs = round(duration.total_seconds() / 3600, 2)  # hours
                rate = car_cost if log.vehicle_type.lower() == 'car' else bike_cost
                amount = round(duration_hrs * rate, 2)
                upi_url = f"upi://pay?pa=yourupi@bank&pn=EasyParking&am={amount}&cu=INR&tn=Parking+Payment+for+LogID:{log.id}"
                qr_path = f'static/qrcodes/payment_qr_{log.id}.png'
                os.makedirs(os.path.dirname(qr_path), exist_ok=True)
                if not os.path.exists(qr_path):
                    qr = qrcode.make(upi_url)
                    qr.save(qr_path)
            updated_logs.append({
                'id': log.id,
                'cid': log.cid,
                'vehicle_type': log.vehicle_type,
                'vehicle_number': log.vehicle_number,
                'entry_time': log.entry_time,
                'exit_time': log.exit_time,
                'duration': duration_hrs if duration_hrs != '' else '--',
                'amount': amount if amount != '' else '--',
                'qr_path': qr_path if log.exit_time else None
          })
        return render_template('user_dashboard.html', slots=slots, logs=updated_logs, slot_summary=slot_summary,cost_summary=cost_summary)

@app.route('/manage_company', methods=['GET', 'POST'])
@login_required
def manage_company():
    if not current_user.is_admin:
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            company_name = request.form.get('company_name')
            address = request.form.get('address')
            car_slots = int(request.form.get('car_slots', 0))
            bike_slots = int(request.form.get('bike_slots', 0))
            date = request.form.get('date')
            username = request.form.get('username')
            password = request.form.get('password')
            mobile_no = request.form.get('mobile_no')
            car_cost_raw = request.form.get('car_cost', '').strip()
            bike_cost_raw = request.form.get('bike_cost', '').strip()
            company_id = request.form.get('id')
            # ✅ Use company_name for safe email
            safe_company = company_name.lower().replace(" ", "") if company_name else ""
            email = f"{username}@{safe_company}.com" if username else None

            # ✅ Validate cost fields
            if not car_cost_raw.isdigit():
                flash("Invalid Car Cost. Must be a non-negative number.", "danger")
                return redirect(url_for('manage_company'))
            if not bike_cost_raw.isdigit():
                flash("Invalid Bike Cost. Must be a non-negative number.", "danger")
                return redirect(url_for('manage_company'))

            car_cost = int(car_cost_raw)
            bike_cost = int(bike_cost_raw)

            if not username:
                flash("Username is required to create a user account.", "danger")
                return redirect(url_for('manage_company'))

            # ✅ Default password = username if not provided
            if not password:
                password = username

            hashed_password = generate_password_hash(password)

            # ✅ Handle date or fallback
            try:
                created_date = datetime.strptime(date, '%Y-%m-%d') if date else datetime.now()
            except ValueError:
                flash("Invalid date format. Use YYYY-MM-DD.", "danger")
                return redirect(url_for('manage_company'))

            if company_id:  # Update existing user
                existing_user = db.session.get(User, int(company_id))
                if not existing_user:
                    flash("Company not found.", "danger")
                    return redirect(url_for('manage_company'))

                # Prevent duplicates
                duplicate_email = User.query.filter(User.email == email, User.id != existing_user.id).first()
                if duplicate_email:
                    flash("Email already in use by another user.", "danger")
                    return redirect(url_for('manage_company'))

                duplicate_username = User.query.filter(User.username == username, User.id != existing_user.id).first()
                if duplicate_username:
                    flash("Username already in use by another user.", "danger")
                    return redirect(url_for('manage_company'))

                # Update fields
                existing_user.username = username
                existing_user.email = email
                existing_user.password = hashed_password
                existing_user.company_name = company_name
                existing_user.address = address
                existing_user.mobile_no = mobile_no
                existing_user.car_slots = car_slots
                existing_user.bike_slots = bike_slots
                existing_user.car_cost = car_cost
                existing_user.bike_cost = bike_cost
                existing_user.created_on = created_date

                db.session.commit()
                flash("Company details updated successfully.", "success")

            else:  # Add new company
                new_user = User(
                    username=username,
                    email=email,
                    password=hashed_password,
                    company_name=company_name,
                    is_admin=False,
                    address=address,
                    mobile_no=mobile_no,
                    car_slots=car_slots,
                    bike_slots=bike_slots,
                    car_cost=car_cost,
                    bike_cost=bike_cost,
                    created_on=created_date
                )

                db.session.add(new_user)

                for _ in range(car_slots):
                    db.session.add(Slot(company_name=company_name, type='Car', status='Available'))

                for _ in range(bike_slots):
                    db.session.add(Slot(company_name=company_name, type='Bike', status='Available'))

                db.session.commit()
                flash("Company and user account added successfully.", "success")

                return redirect(url_for('manage_company'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error adding/updating company: {str(e)}", "danger")
            return redirect(url_for('manage_company'))

    companies = User.query.filter_by(is_admin=False).all()
    return render_template('admin_dashboard.html', companies=companies)



@app.route('/entry', methods=['POST'])
@login_required
def entry():
    vehicle_type = request.form['vehicle_type']
    plate_image = request.files['plate_image']
    filename = secure_filename(plate_image.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    plate_image.save(filepath)
    vehicle_number = extract_vehicle_number(filepath)
    available_slot = Slot.query.filter_by(company_name=current_user.company_name, type=vehicle_type.capitalize(), status='Available').first()
    if not available_slot:
        flash(f"No available {vehicle_type} slots", "danger")
        return redirect(url_for('dashboard'))
    available_slot.status = 'Occupied'
    log = Log(cid=current_user.id, user_email=current_user.email, company_name=current_user.company_name, vehicle_type=vehicle_type, vehicle_number=vehicle_number, plate_photo=filepath, entry_time=datetime.now())
    db.session.add(log)
    db.session.commit()
    flash("Entry recorded successfully", "success")
    return redirect(url_for('dashboard'))

@app.route('/exit', methods=['POST'])
@login_required
def exit_vehicle():
    log = Log.query.filter_by(user_email=current_user.email, exit_time=None).order_by(Log.entry_time.desc()).first()
    if log:
        log.exit_time = datetime.now()
        slot = Slot.query.filter_by(type=log.vehicle_type, company_name=current_user.company_name, status='Occupied').first()
        if slot:
            slot.status = 'Available'
        
        # ✅ Calculate duration and amount
        duration = log.exit_time - log.entry_time
        duration_hrs = round(duration.total_seconds() / 3600, 2)

        admin_user = User.query.filter_by(company_name=current_user.company_name, is_admin=True).first()
        car_cost = admin_user.car_cost if admin_user else 0
        bike_cost = admin_user.bike_cost if admin_user else 0
        rate = car_cost if log.vehicle_type.lower() == 'car' else bike_cost

        log.duration = duration_hrs
        log.amount = round(duration_hrs * rate, 2)

        db.session.commit()
        flash("Exit recorded", "success")
    else:
        flash("No active parking log found", "danger")
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(username='admin@system').first():
            hashed_password = generate_password_hash("admin123")
            admin = User(
                username='admin@system',  # Changed from 'email' to 'username'
                password=hashed_password,
                company_name='admin',
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)
