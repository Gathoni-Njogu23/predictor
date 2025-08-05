from flask import Flask, request
import requests
import os

app = Flask(__name__)

# Use updated deployed API URL
PREDICTION_API_URL = os.getenv("PREDICTION_API_URL", "https://maliyaleo.onrender.com")

@app.route("/ussd", methods=["POST"])
def ussd_callback():
    session_id = request.values.get("sessionId")
    service_code = request.values.get("serviceCode")
    phone_number = request.values.get("phoneNumber")
    text = request.values.get("text", "")

    text_array = text.split("*")
    level = len(text_array)

    if text == "":
        return "CON Welcome to MajiBora Price Forecast\n1. Farmer\n2. Consumer"

    elif level == 1:
        if text_array[0] not in ["1", "2"]:
            return "END Invalid choice. Select 1 or 2."
        return "CON Enter commodity (e.g. Maize):"

    elif level == 2:
        return "CON Enter county (e.g. Kiambu):"

    elif level == 3:
        commodity = text_array[1].strip().title()
        county = text_array[2].strip().title()

        try:
            res = requests.get(
                f"{PREDICTION_API_URL}/markets",
                params={"county": county, "commodity": commodity}
            )

            if res.status_code != 200:
                return "END Failed to fetch markets."

            markets = res.json().get("markets", [])
            if not markets:
                return "END No markets found for that county and commodity."

            # Show market list with numbers
            market_list = "\n".join([f"{i+1}. {m}" for i, m in enumerate(markets)])
            return f"CON Select market:\n{market_list}"

        except Exception as e:
            print("ERROR fetching markets:", str(e))
            return "END Error retrieving markets."

    elif level == 4:
        return "CON Enter date (YYYY-MM-DD):"

    elif level == 5:
        user_type = text_array[0]
        commodity = text_array[1].strip().title()
        county = text_array[2].strip().title()
        market_choice = text_array[3]
        date = text_array[4]

        try:
            res = requests.get(
                f"{PREDICTION_API_URL}/markets",
                params={"county": county, "commodity": commodity}
            )
            markets = res.json().get("markets", [])

            market_index = int(market_choice) - 1
            if market_index < 0 or market_index >= len(markets):
                return "END Invalid market selection."

            market = markets[market_index]

        except ValueError:
            return "END Market selection must be a number."
        except Exception as e:
            print("Market selection error:", str(e))
            return "END Error selecting market."

        payload = {
            "commodity": commodity,
            "county": county,
            "market": market,
            "d
