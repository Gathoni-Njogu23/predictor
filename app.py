# === FILE: app.py ===
from flask import Flask, request
import requests
import os
from dotenv import load_dotenv
from utils.session_manager import get_session_level, update_session_level

# Loading environment variables from .env
load_dotenv()

app = Flask(__name__)

# Loading FastAPI prediction endpoint from environment
PREDICTION_API_URL = os.getenv("PREDICTION_API_URL")

@app.route("/ussd", methods=["POST"])
def ussd_callback():# ussd in checking the user sessions,the user themselves and the text
    session_id = request.form.get("sessionId")
    phone_number = request.form.get("phoneNumber")
    text = request.form.get("text", "")

    inputs = text.strip().split("*") if text else []
    level = get_session_level(session_id)
#this is the levels that users follows during the ussd process
    if level == 0:
        response = "CON Welcome to MaliYaLeo\n1. Farmer (Wholesale)\n2. Consumer (Retail)"
        update_session_level(session_id, 1)

    elif level == 1:
        user_type = "farmer" if inputs[-1] == "1" else "consumer"
        update_session_level(session_id, 2, {"user_type": user_type})
        response = "CON Enter your county (e.g. Nairobi)"

    elif level == 2:
        update_session_level(session_id, 3, {"location": inputs[-1]})
        response = "CON Enter market (e.g. Wakulima)"

    elif level == 3:
        update_session_level(session_id, 4, {"market": inputs[-1]})
        response = "CON Enter commodity (e.g. maize)"

    elif level == 4:
        update_session_level(session_id, 5, {"commodity": inputs[-1]})
        response = "CON Choose forecast type:\n1. Daily\n2. Weekly\n3. Monthly"

    elif level == 5:
        forecast_map = {"1": "daily", "2": "weekly", "3": "monthly"}
        forecast_type = forecast_map.get(inputs[-1], "daily")
        update_session_level(session_id, 6, {"forecast_type": forecast_type})
        response = "CON Enter date (YYYY-MM-DD)"

    elif level == 6:
        date = inputs[-1]
        session_data = update_session_level(session_id, 7, {"date": date})

        # Preparing prediction payload that will be sent to the main.py to calculate the predictions
        payload = {
            "user_type": session_data["user_type"],
            "location": session_data["location"],
            "market": session_data["market"],
            "commodity": session_data["commodity"],
            "forecast_type": session_data["forecast_type"],
            "date": session_data["date"]
        }

        try:
            # Send request to prediction API
            prediction = requests.post(PREDICTION_API_URL, json=payload).json()
            price = prediction.get("predicted_price", "N/A")
            response = (
                f"END {payload['commodity'].capitalize()} price at "
                f"{payload['market']}, {payload['location']} on {payload['date']} "
                f"({payload['forecast_type']}) is Ksh {price}"
            )
        except Exception as e:
            response = "END Sorry, we could not get your prediction. Please try again."

    else:
        response = "END Invalid session"

    return response

if __name__ == "__main__":
    app.run(debug=True)
