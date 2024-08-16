from app import app, db, SolarPlant, GridSubstation, SubstationForecast
from datetime import datetime, timedelta
import random
import math

def create_sample_data():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()

        # Create sample grid substations
        substations = [
            {"name": "North City Substation", "code": "NCS001", "latitude": 34.0522, "longitude": -118.2437, "current_load": 150.5},
            {"name": "East Valley Substation", "code": "EVS002", "latitude": 34.1478, "longitude": -118.1445, "current_load": 120.3},
            {"name": "South Bay Substation", "code": "SBS003", "latitude": 33.8822, "longitude": -118.4089, "current_load": 180.7}
        ]

        for sub_data in substations:
            substation = GridSubstation(**sub_data)
            db.session.add(substation)
        
        db.session.commit()

        # Create sample solar plants
        plants = [
            {"name": "Sunnyvale Solar Farm", "size": 50.0, "latitude": 34.0403, "longitude": -118.2696, "angle": 30, "max_power": 45.5, "owner_name": "Green Energy Co.", "owner_account": "GE001", "grid_substation_id": 1, "connected_feeder": "F001"},
            {"name": "Desert Sun Project", "size": 75.5, "latitude": 34.1850, "longitude": -118.3090, "angle": 35, "max_power": 70.0, "owner_name": "Solar Future Ltd.", "owner_account": "SF002", "grid_substation_id": 2, "connected_feeder": "F002"},
            {"name": "Coastal Breeze Array", "size": 40.0, "latitude": 33.9416, "longitude": -118.4085, "angle": 25, "max_power": 38.5, "owner_name": "Ocean Power Inc.", "owner_account": "OP003", "grid_substation_id": 3, "connected_feeder": "F003"}
        ]

        for plant_data in plants:
            plant = SolarPlant(**plant_data)
            db.session.add(plant)
        
        db.session.commit()

        # Create sample forecast data
        start_time = datetime.now().replace(minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=3)
        
        for substation in GridSubstation.query.all():
            current_time = start_time
            base_load = substation.current_load
            base_generation = base_load * 0.8  # Assume generation is about 80% of load on average

            while current_time < end_time:
                # Create some variation in the forecasts
                time_factor = 1 + 0.3 * math.sin(current_time.hour / 12 * math.pi)  # Daily cycle
                random_factor = random.uniform(0.9, 1.1)  # Random variation

                generation_forecast = base_generation * time_factor * random_factor
                load_forecast = base_load * time_factor * random_factor * 1.1  # Load slightly higher than generation

                forecast = SubstationForecast(
                    substation_id=substation.id,
                    timestamp=current_time,
                    generation_forecast=round(generation_forecast, 2),
                    load_forecast=round(load_forecast, 2)
                )
                db.session.add(forecast)

                current_time += timedelta(minutes=15)

        db.session.commit()
        print("Sample data created successfully!")

if __name__ == "__main__":
    create_sample_data()