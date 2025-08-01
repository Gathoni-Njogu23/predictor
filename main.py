from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")

# Load models and encoders
xgb_wholesale = joblib.load("model/xgb_model_wholesale.pkl")
xgb_retail = joblib.load("model/xgb_model_retail.pkl")
ohe_encoder = joblib.load("model/ohe_encoder.pkl")
columns = joblib.load("model/columns.pkl")

class PredictionRequest(BaseModel):
    user_type: str
    location: str
    market: str
    commodity: str
    forecast_type: str
    date: str

@app.post("/predict")
def predict_price(request: PredictionRequest):
    try:
        # Create a dummy row with the provided inputs
        df_input = pd.DataFrame([{ 
            "County": request.location,
            "Market": request.market,
            "Commodity": request.commodity,
            "Month_name": pd.to_datetime(request.date).month_name(),
            "Day_Name": pd.to_datetime(request.date).day_name(),
            "Classification": request.user_type.capitalize()
        }])

        # One-hot encode using the saved encoder and align with training columns
        df_encoded = pd.get_dummies(df_input, columns=["County", "Market", "Commodity", "Month_name", "Day_Name", "Classification"])
        df_encoded = df_encoded.reindex(columns=columns, fill_value=0)

        if request.user_type.lower() == "farmer":
            final_pred = xgb_wholesale.predict(df_encoded)[0]
        else:
            final_pred = xgb_retail.predict(df_encoded)[0]

        # Save prediction to database
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO predictions_log (user_type, location, market, commodity, forecast_type, date, predicted_price)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (request.user_type, request.location, request.market, request.commodity, request.forecast_type, request.date, final_pred))
        conn.commit()
        cur.close()
        conn.close()

        return {"predicted_price": round(final_pred, 2)}

    except Exception as e:
        return {"error": str(e)}

