

import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy


import json
from flask import render_template
from markupsafe import Markup


app = Flask(__name__)

# Set a secret key for the application
app.secret_key = os.environ.get('SECRET_KEY') or '1337454554'



# Database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///solar_plants.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['GOOGLE_MAPS_API_KEY'] = os.environ.get('GOOGLE_MAPS_API_KEY', 'your_fallback_api_key_here')


db = SQLAlchemy(app)

class GridSubList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

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
    grid_substation_id = db.Column(db.Integer, db.ForeignKey('grid_sub_list.id'), nullable=False)
    grid_substation = db.relationship('GridSubList', backref=db.backref('solar_plants', lazy=True))
    connected_feeder = db.Column(db.String(100), nullable=False)





@app.route('/map')
def map_view():
    plants = SolarPlant.query.all()
    plants_data = [{
        'id': plant.id,
        'name': plant.name,
        'latitude': plant.latitude,
        'longitude': plant.longitude,
        'size': plant.size,
        'angle': plant.angle,
        'max_power': plant.max_power,
        'owner_name': plant.owner_name,
        'grid_substation': plant.grid_substation.name if plant.grid_substation else '',
        'connected_feeder': plant.connected_feeder
    } for plant in plants]
    
    plants_json = json.dumps(plants_data)
    return render_template('map.html', plants_json=Markup(plants_json))





@app.route('/manage_substations')
def manage_substations():
    substations = GridSubList.query.all()
    return render_template('manage_substations.html', substations=substations)

@app.route('/add_substation', methods=['POST'])
def add_substation():
    name = request.form['name']
    existing = GridSubList.query.filter_by(name=name).first()
    if existing:
        flash(f"Substation '{name}' already exists.", 'error')
    else:
        new_substation = GridSubList(name=name)
        db.session.add(new_substation)
        db.session.commit()
        flash(f"Substation '{name}' added successfully.", 'success')
    return redirect(url_for('manage_substations'))

@app.route('/remove_substation/<int:id>', methods=['POST'])
def remove_substation(id):
    substation = GridSubList.query.get_or_404(id)
    if SolarPlant.query.filter_by(grid_substation_id=id).first():
        flash(f"Cannot remove substation '{substation.name}' as it is in use.", 'error')
    else:
        db.session.delete(substation)
        db.session.commit()
        flash(f"Substation '{substation.name}' removed successfully.", 'success')
    return redirect(url_for('manage_substations'))










@app.route('/')
def index():
    plants = SolarPlant.query.all()
    return render_template('index.html', plants=plants)

@app.route('/add', methods=['GET', 'POST'])
def add_plant():
    substations = GridSubList.query.all()
    if request.method == 'POST':
        substation = GridSubList.query.get(request.form['grid_substation'])
        new_plant = SolarPlant(
            name=request.form['name'],
            size=float(request.form['size']),
            latitude=float(request.form['latitude']),
            longitude=float(request.form['longitude']),
            angle=float(request.form['angle']),
            max_power=float(request.form['max_power']),
            owner_name=request.form['owner_name'],
            owner_account=request.form['owner_account'],
            grid_substation=substation,
            connected_feeder=request.form['connected_feeder']
        )
        db.session.add(new_plant)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_plant.html', substations=substations)

def create_tables():
    with app.app_context():
        db.create_all()
        
        # Add some example substations if the table is empty
        if not GridSubList.query.first():
            substations = ['Substation Aq', 'Substation qB', 'Substation ewC']
            for sub in substations:
                db.session.add(GridSubList(name=sub))
            db.session.commit()

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
