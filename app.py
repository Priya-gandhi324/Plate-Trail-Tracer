import os, cv2
from flask import Flask, redirect, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from anpr_main import anpr_processing
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///anpr.db'
app.secret_key = "PRIYA"

db = SQLAlchemy(app)
app.app_context().push()

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


class Organizations(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    org_name = db.Column(db.String, nullable=False)
    org_email = db.Column(db.String(120), unique=True, nullable=False)
    org_address = db.Column(db.String, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Organization %r>' % self.id
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class VehicleRegistration(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    vehicle_number_plate = db.Column(db.String, nullable=False)
    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    organization = db.relationship('Organizations', backref=db.backref('vehicle_registrations', lazy=True))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return '<VehicleRegistrated %r>' % self.id


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        vehicle_image = request.files.get('image', None)
        
        if vehicle_image is None:
            return render_template('index.html')
            
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], vehicle_image.filename)
        vehicle_image.save(image_path)
        
        image = cv2.imread(image_path)
        if image is None:
            return "Failed to read the image"
        
        vehicle = anpr_processing(image)
        vehicle_number_plate, converted_img_path, message = vehicle.get('text'), vehicle.get('converted_img_path'), vehicle.get('message')
        registrations = []
        if vehicle_number_plate:
            registrations = VehicleRegistration.query.filter_by(vehicle_number_plate=vehicle_number_plate).all()
        return render_template('index.html', registrations=registrations, converted_img_path=converted_img_path, message=message)
        
    else:
        return render_template('index.html')


@app.route('/register/', methods=['GET', 'POST'])
def register():
    message = None
    if request.method == "POST":
        org_name = request.form.get('org_name', None)
        org_email = request.form.get('org_email', None)
        org_address = request.form.get('org_address', None)
        password = request.form.get('password', None)
        confirm_password = request.form.get('confirm_password', None)
        
        if password == confirm_password:
            if org_name and org_address and org_email and password and confirm_password:
                new_org = Organizations(org_name=org_name, org_email=org_email, org_address=org_address)
                new_org.set_password(password=password)
                try:
                    db.session.add(new_org)
                    db.session.commit()
                    return render_template('login.html')
                except:
                    message = "Unable to register the organization"
            else:
                message = "Please fill all the fields"
        else:
            message = "Passwords don't match"

    return render_template('register.html', message=message)
    

@app.route('/login/', methods=['GET', 'POST'])
def login():
    message = None
    if request.method == "POST":
        org_email = request.form.get('org_email')
        password = request.form.get('password')
        org = Organizations.query.filter_by(org_email=org_email).first()
        
        if org_email and password and org and org.check_password(password):
            session['org_id'] = org.id
            return render_template('register_vehicle.html')
        else:
            message = "Invalid Credentials"
    
    return render_template('login.html', message=message)


@app.route('/register_vehicle/', methods=['GET', 'POST'])
def register_vehicle():
    
    if request.method == 'POST':
        success, message, converted_img_path = 0, None, None

        if 'org_id' in session:
            
            vehicle_image = request.files.get('image', None)
            if vehicle_image is None:
                return render_template('register_vehicle.html')
                
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], vehicle_image.filename)
            vehicle_image.save(image_path)
            
            image = cv2.imread(image_path)
            if image is None:
                message = "Failed to read the image"
            
            vehicle = anpr_processing(image)
            vehicle_number_plate, converted_img_path, message = vehicle.get('text'), vehicle.get('converted_img_path'), vehicle.get('message')
            
            if not vehicle_number_plate:
                message = "No vehicle number plate found"
            
            new_registration = VehicleRegistration(vehicle_number_plate=vehicle_number_plate, org_id=session['org_id'])
            try:
                db.session.add(new_registration)
                db.session.commit()
                message = 'Vehicle Registered successfully'
                success = 1
            except:
                message = "Error vehicle not registered"
        
        else:
            return redirect('/')

        return render_template('register_vehicle.html', message=message, success=success, converted_img_path=converted_img_path)
    
    else:
        return render_template('register_vehicle.html')


if __name__ == "__main__":
    app.run(debug=True)