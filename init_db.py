from app import app, db, SolarPlant, GridSubstation, SubstationForecast
from datetime import datetime, timedelta
import random
import math

def reset_database():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        print("Database reset complete. All tables dropped and recreated.")

def create_sample_data():
    with app.app_context():
        # Create sample grid substations
        substations = [
            {"name": "Kesbewa", "code": "KESBE_CO", "latitude": 6.795783, "longitude": 79.962302, "current_load": 10.2},
            {"name": "Sri Jayawardanapura", "code": "SJAPU_CO", "latitude": 6.890911, "longitude":79.924413, "current_load": 30},
            {"name": "Trincomalee", "code": "TRNCO_AN", "latitude": 8.591325, "longitude": 81.217654, "current_load": 15} 
        ]

        for sub_data in substations:
            substation = GridSubstation(**sub_data)
            db.session.add(substation)
        
        db.session.commit()
        print("Sample substations created.")

        # Create sample solar plants
        plants = [
            {"name": "Sunnyvale Solar Farm", "size": 50.0, "latitude": 6.819242, "longitude": 79.969933, "angle": 30, "max_power": 45.5, "owner_name": "Green Energy Co.", "owner_account": "GE001", "grid_substation_id": 1, "connected_feeder": "F001"},
            {"name": "Desert Sun Project", "size": 75.5, "latitude":  6.590911, "longitude": 79.924429, "angle": 35, "max_power": 70.0, "owner_name": "Solar Future Ltd.", "owner_account": "SF002", "grid_substation_id": 2, "connected_feeder": "F002"},
            {"name": "Coastal Breeze Array", "size": 40.0, "latitude": 8.561325, "longitude": 81.817654, "angle": 25, "max_power": 38.5, "owner_name": "Ocean Power Inc.", "owner_account": "OP003", "grid_substation_id": 3, "connected_feeder": "F003"}
        ]

        for plant_data in plants:
            plant = SolarPlant(**plant_data)
            db.session.add(plant)
        
        db.session.commit()
        print("Sample solar plants created.")

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
        print("Sample forecast data created.")

if __name__ == "__main__":
    reset_database()
    create_sample_data()
    print("Database initialization complete. Sample data has been added.")