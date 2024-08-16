import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import json

app = Flask(__name__)

# Set a secret key for the application
app.secret_key = os.environ.get('SECRET_KEY') or 'your_fallback_secret_key_here'

# Database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///solar_plants.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Google Maps API key
app.config['GOOGLE_MAPS_API_KEY'] = os.environ.get('GOOGLE_MAPS_API_KEY', 'your_fallback_api_key_here')

db = SQLAlchemy(app)

# Models
class GridSubstation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    current_load = db.Column(db.Float)
    solar_plants = db.relationship('SolarPlant', backref='grid_substation', lazy=True)

class SubstationForecast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    substation_id = db.Column(db.Integer, db.ForeignKey('grid_substation.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    generation_forecast = db.Column(db.Float)
    load_forecast = db.Column(db.Float)

    substation = db.relationship('GridSubstation', backref=db.backref('forecasts', lazy=True))

class SolarPlant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    size = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    angle = db.Column(db.Float, nullable=False)
    max_power = db.Column(db.Float, nullable=False)
    owner_name = db.Column(db.String(100), nullable=False)
    owner_account = db.Column(db.String(50), nullable=False)
    grid_substation_id = db.Column(db.Integer, db.ForeignKey('grid_substation.id'), nullable=False)
    connected_feeder = db.Column(db.String(100), nullable=False)

# Routes
@app.route('/')
def index():
    plants = SolarPlant.query.all()
    return render_template('index.html', plants=plants)

@app.route('/add', methods=['GET', 'POST'])
def add_plant():
    if request.method == 'POST':
        new_plant = SolarPlant(
            name=request.form['name'],
            size=float(request.form['size']),
            latitude=float(request.form['latitude']),
            longitude=float(request.form['longitude']),
            angle=float(request.form['angle']),
            max_power=float(request.form['max_power']),
            owner_name=request.form['owner_name'],
            owner_account=request.form['owner_account'],
            grid_substation_id=int(request.form['grid_substation']),
            connected_feeder=request.form['connected_feeder']
        )
        db.session.add(new_plant)
        db.session.commit()
        flash('New solar plant added successfully!', 'success')
        return redirect(url_for('index'))
    substations = GridSubstation.query.all()
    return render_template('add_plant.html', substations=substations)

@app.route('/map')
def map_view():
    plants = SolarPlant.query.all()
    substations = GridSubstation.query.all()
    
    current_time = datetime.utcnow()
    forecast_end = current_time + timedelta(days=3)
    
    plants_data = [{
        'id': plant.id,
        'name': plant.name,
        'latitude': plant.latitude,
        'longitude': plant.longitude,
        'size': plant.size,
        'angle': plant.angle,
        'max_power': plant.max_power,
        'owner_name': plant.owner_name,
        'grid_substation': plant.grid_substation.name,
        'connected_feeder': plant.connected_feeder
    } for plant in plants]

    substations_data = [{
        'id': sub.id,
        'name': sub.name,
        'code': sub.code,
        'latitude': sub.latitude,
        'longitude': sub.longitude,
        'current_load': sub.current_load,
        'forecasts': [{
            'timestamp': f.timestamp.isoformat(),
            'generation_forecast': f.generation_forecast,
            'load_forecast': f.load_forecast
        } for f in SubstationForecast.query.filter(
            SubstationForecast.substation_id == sub.id,
            SubstationForecast.timestamp.between(current_time, forecast_end)
        ).order_by(SubstationForecast.timestamp).all()]
    } for sub in substations]

    return render_template('map.html', 
                           plants_json=json.dumps(plants_data),
                           substations_json=json.dumps(substations_data))

@app.route('/manage_substations')
def manage_substations():
    substations = GridSubstation.query.all()
    return render_template('manage_substations.html', substations=substations)


@app.route('/add_substation', methods=['POST'])
def add_substation():
    name = request.form['name']
    code = request.form['code']
    latitude = float(request.form['latitude'])
    longitude = float(request.form['longitude'])
    current_load = float(request.form['current_load'])

    new_substation = GridSubstation(name=name, code=code, latitude=latitude, longitude=longitude, current_load=current_load)
    db.session.add(new_substation)
    db.session.commit()
    flash(f"Substation '{name}' added successfully.", 'success')
    return redirect(url_for('manage_substations'))



@app.route('/remove_substation/<int:id>', methods=['POST'])
def remove_substation(id):
    substation = GridSubstation.query.get_or_404(id)
    if SolarPlant.query.filter_by(grid_substation_id=id).first():
        flash(f"Cannot remove substation '{substation.name}' as it is in use.", 'error')
    else:
        db.session.delete(substation)
        db.session.commit()
        flash(f"Substation '{substation.name}' removed successfully.", 'success')
    return redirect(url_for('manage_substations'))

# Database creation
def create_tables():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)