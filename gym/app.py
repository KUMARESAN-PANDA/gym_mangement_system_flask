from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

# Define the timezone for India
india_timezone = pytz.timezone('Asia/Kolkata')

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessary for flashing messages

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gym.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create a SQLAlchemy instance
db = SQLAlchemy(app)

# Define a model for GymMember registration
class GymMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    height = db.Column(db.String(50), nullable=False)
    weight = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    address = db.Column(db.Text, nullable=False)
    date_of_joining = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"<GymMember {self.first_name} {self.last_name}>"

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('gym_member.id'), nullable=False)
    check_in_time = db.Column(db.DateTime, default=datetime.utcnow)
    check_out_time = db.Column(db.DateTime, nullable=True)
    total_time = db.Column(db.String, nullable=True)

    def __repr__(self):
        return f"<Attendance {self.member_id} - {self.check_in_time}>"

# Route for the home page
@app.route("/", methods=["POST", "GET"])
def root():
    attendances = Attendance.query.order_by(Attendance.check_in_time.desc()).all()

    if request.method == 'POST':
        mem_id = request.form['id']
        now = datetime.now(india_timezone)

        attendance_entry = Attendance.query.filter_by(member_id=mem_id, check_out_time=None).first()

        if attendance_entry:
            if attendance_entry.check_in_time.tzinfo is None:
                attendance_entry.check_in_time = india_timezone.localize(attendance_entry.check_in_time)

            attendance_entry.check_out_time = now
            duration = attendance_entry.check_out_time - attendance_entry.check_in_time
            total_seconds = int(duration.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, _ = divmod(remainder, 60)

            attendance_entry.total_time = f"{hours} hours {minutes} minutes"

            db.session.commit()
            flash(f"Checked out successfully. Total time: {attendance_entry.total_time}", 'success')
        else:
            india_time = datetime.now(india_timezone)
            attendance_entry = Attendance(member_id=mem_id, check_in_time=india_time)
            db.session.add(attendance_entry)
            db.session.commit()
            flash("Checked in successfully.", 'success')

    return render_template("base.html", attendances=attendances)

# Step 2: Admin Login Page
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Hardcoded admin credentials
        if username == 'admin' and password == 'admin@123':
            session['admin_logged_in'] = True  # Set admin logged in status
            flash('Login successful', 'success')
            return redirect(url_for('show_members'))
        else:
            flash('Invalid credentials', 'danger')

    return render_template('admin_login.html')

# Step 3: Admin Logout
@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_logged_in', None)  # Remove admin session
    flash('You have been logged out', 'success')
    return redirect(url_for('admin_login'))

# Step 4: Admin-only route to display all members
@app.route('/members')
def show_members():
    if not session.get('admin_logged_in'):
        flash('You must be logged in as admin to view this page.', 'danger')
        return redirect(url_for('admin_login'))

    members = GymMember.query.all()
    return render_template('members.html', members=members)

# Route for registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            height = request.form['height']
            weight = request.form['weight']
            phone = request.form['phone']
            email = request.form['email']
            gender = request.form['gender']
            address = request.form['address']
            date_of_joining = request.form['date_of_joining']
            user_id = request.form['id']

            if date_of_joining:
                date_of_joining = datetime.strptime(date_of_joining, '%Y-%m-%d').date()

            new_member = GymMember(
                first_name=first_name,
                last_name=last_name,
                height=height,
                weight=weight,
                phone=phone,
                email=email,
                gender=gender,
                address=address,
                date_of_joining=date_of_joining,
                user_id=user_id
            )
            db.session.add(new_member)
            db.session.commit()

            flash("Registration successful!", 'success')
            return redirect(url_for('root'))

        except Exception as e:
            print(f"Error during registration: {e}")
            flash("An error occurred during registration. Please try again.", 'danger')

    return render_template('register.html')

@app.route('/attendance')
def attendance():
    attendances = Attendance.query.order_by(Attendance.check_in_time.desc()).all()


    return render_template('attendance.html',attendances=attendances)

# Start the Flask app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
