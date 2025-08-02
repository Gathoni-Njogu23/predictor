from flask import Flask, request
import requests
import os

app = Flask(__name__)

PREDICTION_API_URL = os.getenv("PREDICTION_API_URL", "https://7a9b2ad38296.ngrok-free.app")

@app.route("/ussd", methods=["POST"])
def ussd_callback():
    session_id = request.values.get("sessionId")
    service_code = request.values.get("serviceCode")
    phone_number = request.values.get("phoneNumber")
    text = request.values.get("text", "")

    text_array = text.split("*")
    level = len(text_array)

    if text == "":
        response = "CON Welcome to MajiBora Price Forecast\n"
        response += "Are you a:\n1. Farmer\n2. Consumer"

    elif level == 1:
        user_type = text_array[0]
        if user_type not in ["1", "2"]:
            return "END Invalid selection. Choose 1 or 2."
        response = "CON Enter commodity (e.g. Maize):"

    elif level == 2:
        response = "CON Enter county (e.g. Nairobi):"

    elif level == 3:
        county = text_array[2].strip().title()
        try:
            res = requests.get(f"{PREDICTION_API_URL}/markets?county={county}")
            if res.status_code != 200:
                return "END Failed to fetch markets."
            markets = res.json().get("markets", [])
            if not markets:
                return "END No markets found for that county."

            market_list = "\n".join([f"{i+1}. {m}" for i, m in enumerate(markets)])
            response = f"CON Select market:\n{market_list}"
        except Exception as e:
            print("Market fetch error:", e)
            return "END Error retrieving markets."

    elif level == 4:
        response = "CON Enter date (YYYY-MM-DD):"

    elif level == 5:
        user_type = text_array[0]
        commodity = text_array[1].strip().title()
        county = text_array[2].strip().title()
        market_choice = text_array[3]
        date = text_array[4]

        try:
            res = requests.get(f"{PREDICTION_API_URL}/markets?county={county}")
            if res.status_code != 200:
                return "END Failed to fetch markets."
            markets = res.json().get("markets", [])
            market = markets[int(market_choice) - 1]
        except:
            return "END Invalid market selection or error retrieving markets."

        payload = {
            "commodity": commodity,
            "county": county,
            "market": market,
            "date": date,
            "days": 7
        }

        try:
            res = requests.post(f"{PREDICTION_API_URL}/predict", json=payload)
            if res.status_code != 200:
                return "END Failed to get prediction."

            data = res.json()
            prices = data.get("data", {}).get("Predicted_prices", [])

            if not prices:
                return "END No predictions found."

            price = prices[0]
            wholesale = price.get("Wholesale", "N/A")
            retail = price.get("Retail", "N/A")

            user_type_str = "Farmer" if user_type == "1" else "Consumer"

            response = f"END {commodity} price forecast for a {user_type_str} in {market}, {county}:\n"
            response += f"Wholesale: KES {wholesale}\nRetail: KES {retail}"

        except Exception as e:
            print("Prediction error:", e)
            response = "END Error fetching prediction."

    else:
        response = "END Invalid input."

    return response

if __name__ == '__main__':
    import os
    os.environ['FLASK_ENV'] = 'development'  # 🔥 force development mode
    app.run(debug=True)


#if __name__ == "__main__":
    #app.run(port=5000)

