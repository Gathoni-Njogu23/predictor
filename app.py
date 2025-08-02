from flask import Flask, request
import requests
import os

app = Flask(__name__)

# Set this to your real API base URL
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
                print("Error fetching markets:", res.status_code, res.text)
                return "END Failed to fetch markets."

            markets = res.json().get("markets", [])
            if not markets:
                return "END No markets found for that county and commodity."

            market_list = "\n".join([f"{i+1}. {m}" for i, m in enumerate(markets)])
            return f"CON Select market:\n{market_list}"

        except Exception as e:
            print("Exception fetching markets:", str(e))
            return "END Error retrieving markets."

    elif level == 4:
        return "CON Enter date (YYYY-MM-DD):"

    elif level == 5:
        user_type = text_array[0]
        commodity = text_array[1].strip().title()
        county = text_array[2].strip().title()
        market_index = int(text_array[3]) - 1
        date = text_array[4]

        try:
            res = requests.get(
                f"{PREDICTION_API_URL}/markets",
                params={"county": county, "commodity": commodity}
            )
            if res.status_code != 200:
                print("Error refetching markets:", res.status_code, res.text)
                return "END Failed to fetch markets again."

            markets = res.json().get("markets", [])
            market = markets[market_index]
        except Exception as e:
            print("Market selection error:", str(e))
            return "END Invalid market selection."

        payload = {
            "commodity": commodity,
            "county": county,
            "market": market,
            "date": date,
            "days": 7
        }

        try:
            pred_res = requests.post(f"{PREDICTION_API_URL}/predict", json=payload)
            if pred_res.status_code != 200:
                print("Prediction fetch failed:", pred_res.status_code, pred_res.text)
                return "END Failed to get prediction."

            prices = pred_res.json().get("data", {}).get("Predicted_prices", [])
            if not prices:
                return "END No prediction data found."

            price = prices[0]
            wholesale = price.get("Wholesale", "N/A")
            retail = price.get("Retail", "N/A")
            user_str = "Farmer" if user_type == "1" else "Consumer"

            return (
                f"END {commodity} forecast for {user_str} in {market}, {county} on {date}:\n"
                f"Wholesale: KES {wholesale}\nRetail: KES {retail}"
            )

        except Exception as e:
            print("Prediction error:", str(e))
            return "END Error fetching prediction."

    else:
        return "END Invalid input."

if __name__ == "__main__":
    os.environ['FLASK_ENV'] = 'development'
    app.run(debug=True, port=5000)
