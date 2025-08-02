from flask import Flask, request
from datetime import datetime, timedelta
import os
import requests
from dotenv import load_dotenv
import logging

# Load .env variables
load_dotenv()

# Logging
logging.basicConfig(level=logging.INFO)

# Flask app
app = Flask(__name__)

# ML Prediction API
PREDICTION_API_URL = os.getenv("PREDICTION_API_URL", "").rstrip("/")

# In-memory sessions (dictionary instead of DB)
sessions = {}

@app.route('/ussd', methods=['POST'])
def ussd():
    session_id = request.values.get("sessionId")
    phone = request.values.get("phoneNumber")
    text = request.values.get("text", "")

    user_input = text.split("*")
    step = len(user_input)

    # Use in-memory session
    if session_id not in sessions:
        sessions[session_id] = {"phone": phone}

    session = sessions[session_id]

    if step == 0 or text == "":
        return (
            "CON Welcome to Price Prediction Assistant\n"
            "Are you a:\n1. Farmer (Wholesale)\n2. Consumer (Retail)"
        )

    elif step == 1:
        choice = user_input[0]
        if choice == "1":
            session["user_type"] = "wholesale"
        elif choice == "2":
            session["user_type"] = "retail"
        else:
            return "END Invalid selection. Try again."
        return "CON Enter your COUNTY:"

    elif step == 2:
        session["county"] = user_input[1].strip()

        try:
            res = requests.get(f"{PREDICTION_API_URL}/markets?county={session['county']}")
            if res.status_code == 200:
                markets = res.json().get("markets", [])
                if not markets:
                    return "END No markets found for this county."

                session["markets"] = markets
                market_list = "\n".join(f"{i+1}. {m}" for i, m in enumerate(markets))
                return f"CON Select a market:\n{market_list}"
            else:
                return "END Failed to load market list."
        except Exception as e:
            app.logger.error(f"Market error: {e}")
            return "END Error connecting to prediction service."

    elif step == 3:
        try:
            market_index = int(user_input[2]) - 1
            markets = session.get("markets", [])

            if 0 <= market_index < len(markets):
                session["market"] = markets[market_index]
                return "CON Enter forecast date (YYYY-MM-DD):"
            else:
                return "END Invalid market selection."
        except Exception as e:
            app.logger.error(f"Market select error: {e}")
            return "END Error retrieving market."

    elif step == 4:
        try:
            date_str = user_input[3].strip()
            forecast_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            today = datetime.today().date()

            if forecast_date < today or forecast_date > today + timedelta(days=7):
                return "END Date must be within 7 days from today."

            session["date"] = date_str

            # Call ML API
            payload = {
                "county": session["county"],
                "market": session["market"],
                "date": session["date"],
                "type": session["user_type"]
            }

            app.logger.info("Sending payload to ML API: %s", payload)

            res = requests.post(f"{PREDICTION_API_URL}/predict", json=payload)
            if res.status_code == 200:
                price = res.json().get("prediction", "N/A")
                label = "Wholesale" if session["user_type"] == "wholesale" else "Retail"
                return (
                    f"END {label} price for {session['market']} on {session['date']}:\n"
                    f"KES {price}"
                )
            else:
                return "END Prediction service failed."
        except ValueError:
            return "END Invalid date format. Use YYYY-MM-DD."
        except Exception as e:
            app.logger.error(f"Prediction error: {e}")
            return "END Error connecting to prediction API."

    else:
        return "END Invalid input. Please dial again."

if __name__ == "__main__":
    app.run(debug=True)
