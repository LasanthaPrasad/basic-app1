from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_fallback_secret_key_here')
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///solar_plants.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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
    plants = SolarPlant.query.order_by(SolarPlant.id.desc()).limit(10).all()
    return render_template('index.html', plants=plants)

# CRUD for Solar Plants
@app.route('/plants')
def list_plants():
    plants = SolarPlant.query.all()
    return render_template('list_plants.html', plants=plants)

@app.route('/plant/add', methods=['GET', 'POST'])
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
        return redirect(url_for('list_plants'))
    substations = GridSubstation.query.all()
    return render_template('add_plant.html', substations=substations)

@app.route('/plant/edit/<int:id>', methods=['GET', 'POST'])
def edit_plant(id):
    plant = SolarPlant.query.get_or_404(id)
    if request.method == 'POST':
        plant.name = request.form['name']
        plant.size = float(request.form['size'])
        plant.latitude = float(request.form['latitude'])
        plant.longitude = float(request.form['longitude'])
        plant.angle = float(request.form['angle'])
        plant.max_power = float(request.form['max_power'])
        plant.owner_name = request.form['owner_name']
        plant.owner_account = request.form['owner_account']
        plant.grid_substation_id = int(request.form['grid_substation'])
        plant.connected_feeder = request.form['connected_feeder']
        db.session.commit()
        flash('Solar plant updated successfully!', 'success')
        return redirect(url_for('list_plants'))
    substations = GridSubstation.query.all()
    return render_template('edit_plant.html', plant=plant, substations=substations)

@app.route('/plant/delete/<int:id>', methods=['POST'])
def delete_plant(id):
    plant = SolarPlant.query.get_or_404(id)
    db.session.delete(plant)
    db.session.commit()
    flash('Solar plant deleted successfully!', 'success')
    return redirect(url_for('list_plants'))

# CRUD for Grid Substations
@app.route('/substations')
def list_substations():
    substations = GridSubstation.query.all()
    return render_template('list_substations.html', substations=substations)

@app.route('/substation/add', methods=['GET', 'POST'])
def add_substation():
    if request.method == 'POST':
        new_substation = GridSubstation(
            name=request.form['name'],
            code=request.form['code'],
            latitude=float(request.form['latitude']),
            longitude=float(request.form['longitude']),
            current_load=float(request.form['current_load'])
        )
        db.session.add(new_substation)
        db.session.commit()
        flash('New grid substation added successfully!', 'success')
        return redirect(url_for('list_substations'))
    return render_template('add_substation.html')

@app.route('/substation/edit/<int:id>', methods=['GET', 'POST'])
def edit_substation(id):
    substation = GridSubstation.query.get_or_404(id)
    if request.method == 'POST':
        substation.name = request.form['name']
        substation.code = request.form['code']
        substation.latitude = float(request.form['latitude'])
        substation.longitude = float(request.form['longitude'])
        substation.current_load = float(request.form['current_load'])
        db.session.commit()
        flash('Grid substation updated successfully!', 'success')
        return redirect(url_for('list_substations'))
    return render_template('edit_substation.html', substation=substation)

@app.route('/substation/delete/<int:id>', methods=['POST'])
def delete_substation(id):
    substation = GridSubstation.query.get_or_404(id)
    if SolarPlant.query.filter_by(grid_substation_id=id).first():
        flash('Cannot delete substation. It has associated solar plants.', 'error')
    else:
        db.session.delete(substation)
        db.session.commit()
        flash('Grid substation deleted successfully!', 'success')
    return redirect(url_for('list_substations'))

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

# Database creation
def create_tables():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)