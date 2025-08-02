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
        response += "Enter commodity (e.g. Maize):"

    elif level == 1:
        response = "CON Enter county (e.g. Nairobi):"

    elif level == 2:
        county = text_array[1].title()

        try:
            market_res = requests.get(f"{PREDICTION_API_URL}/markets?county={county}")
            market_list = market_res.json().get("markets", [])
        except:
            return "END Error fetching markets from API."

        if not market_list:
            return "END No markets found for that county."

        markets_str = "\n".join([f"{i+1}. {m}" for i, m in enumerate(market_list)])
        response = f"CON Select market in {county}:\n{markets_str}"

    elif level == 3:
        commodity = text_array[0]
        county = text_array[1].title()
        market_choice = text_array[2]

        try:
            market_res = requests.get(f"{PREDICTION_API_URL}/markets?county={county}")
            market_list = market_res.json().get("markets", [])
            market = market_list[int(market_choice) - 1]
        except:
            return "END Invalid market choice."

        response = "CON Enter date (YYYY-MM-DD):"

    elif level == 4:
        commodity = text_array[0]
        county = text_array[1].title()
        market_choice = text_array[2]
        date = text_array[3]

        try:
            market_res = requests.get(f"{PREDICTION_API_URL}/markets?county={county}")
            market_list = market_res.json().get("markets", [])
            market = market_list[int(market_choice) - 1]
        except:
            return "END Invalid market selection."

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

            response = f"END {commodity} in {market}, {county}\n"
            response += f"Wholesale: KES {wholesale}\nRetail: KES {retail}"

        except Exception as e:
            print("Prediction error:", e)
            response = "END Error fetching prediction."

    else:
        response = "END Invalid input."

    return response

if __name__ == "__main__":
    app.run(port=5000)
