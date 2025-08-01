from flask import Flask,request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
import requests
from dotenv import load_dotenv

# Load env vars from .env if running locally
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

PREDICTION_API_URL = os.getenv("PREDICTION_API_URL")


class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(20))
    user_type = db.Column(db.String(20))  # 'wholesale' or 'retail'
    county = db.Column(db.String(50))
    market = db.Column(db.String(50))
    date = db.Column(db.String(20))


@app.route('/ussd', methods=['POST'])
def ussd():
    session_id = request.values.get("sessionId")
    phone = request.values.get("phoneNumber")
    text = request.values.get("text", "")

    user_input = text.split("*")
    step = len(user_input)

    session = Session.query.filter_by(session_id=session_id).first()
    if not session:
        session = Session(session_id=session_id, phone=phone)
        db.session.add(session)
        db.session.commit()

    if step == 0 or text == "":
        return (
            "CON Welcome to Price Prediction Assistant\n"
            "Are you a:\n1. Farmer (Wholesale)\n2. Consumer (Retail)"
        )

    elif step == 1:
        choice = user_input[0]
        if choice == "1":
            session.user_type = "wholesale"
        elif choice == "2":
            session.user_type = "retail"
        else:
            return "END Invalid selection. Try again."
        db.session.commit()
        return "CON Enter your COUNTY:"

    elif step == 2:
        session.county = user_input[1].strip()
        db.session.commit()

        try:
            res = requests.get(f"{PREDICTION_API_URL}/markets?county={session.county}")
            if res.status_code == 200:
                markets = res.json().get("markets", [])
                if not markets:
                    return "END No markets found for this county."

                # Save market list temporarily in app memory (not DB)
                market_list = "\n".join(f"{i+1}. {m}" for i, m in enumerate(markets))
                session.market_list = ",".join(markets)  # optional
                session.temp_markets = markets
                db.session.commit()

                return f"CON Select a market:\n{market_list}"
            else:
                return "END Failed to load market list."
        except Exception:
            return "END Error connecting to prediction service."

    elif step == 3:
        try:
            market_index = int(user_input[2]) - 1
            res = requests.get(f"{PREDICTION_API_URL}/markets?county={session.county}")
            markets = res.json().get("markets", [])

            if 0 <= market_index < len(markets):
                session.market = markets[market_index]
                db.session.commit()
                return "CON Enter forecast date (YYYY-MM-DD):"
            else:
                return "END Invalid market selection."
        except Exception:
            return "END Error retrieving market."

    elif step == 4:
        try:
            date_str = user_input[3].strip()
            forecast_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            today = datetime.today().date()

            if forecast_date < today or forecast_date > today + timedelta(days=7):
                return "END Date must be within 7 days from today."

            session.date = date_str
            db.session.commit()

            # Call your ML prediction API
            payload = {
                "county": session.county,
                "market": session.market,
                "date": session.date,
                "type": session.user_type
            }

            res = requests.post(f"{PREDICTION_API_URL}/predict", json=payload)
            if res.status_code == 200:
                price = res.json().get("prediction", "N/A")
                label = "Wholesale" if session.user_type == "wholesale" else "Retail"
                return (
                    f"END{label} price for {session.market} on {session.date}:\n"
                    f"KES {price}"
                )
            else:
                return "END Prediction service failed."

        except ValueError:
            return "END Invalid date format. Use YYYY-MM-DD."
        except Exception:
            return "END Error connecting to prediction API."

    else:
        return "END Invalid input. Please dial again."


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
