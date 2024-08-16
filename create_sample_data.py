from app import app, db, GridSubstation, SubstationForecast
from datetime import datetime, timedelta
import random
import math

def create_sample_data():
    with app.app_context():
        # First, let's create some sample substations if they don't exist
        substations = [
            {"name": "Kesbewa", "code": "KESBE_CO", "latitude": 6.795783, "longitude": 79.962302, "current_load": 10.2},
            {"name": "Sri Jayawardanapura", "code": "SJAPU_CO", "latitude": 6.890911, "longitude":79.924413, "current_load": 30},
            {"name": "Trincomalee", "code": "TRNCO_AN", "latitude": 8.591325, "longitude": 81.217654, "current_load": 15}
        ]

        for sub_data in substations:
            substation = GridSubstation.query.filter_by(code=sub_data["code"]).first()
            if not substation:
                substation = GridSubstation(**sub_data)
                db.session.add(substation)
        
        db.session.commit()

        # Now, let's create forecast data for each substation
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
