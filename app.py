from flask import Flask, request
import requests
import os

app = Flask(__name__)

# Replace with your actual prediction API base URL
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
        return "CON Welcome to MaliYaLeo \n1. Farmer\n2. Consumer"

    elif level == 1:
        if text_array[0] not in ["1", "2"]:
            return "END Invalid choice. Select 1 or 2."
        return "CON Enter commodity (e.g. Maize):"

    elif level == 2:
        return "CON Enter county (e.g. Kirinyaga):"

    elif level == 3:
        return "CON Enter market (e.g. Kerugoya):"

    elif level == 4:
        return "CON Enter date (YYYY-MM-DD):"

    elif level == 5:
        try:
            user_type = text_array[0]
            commodity = text_array[1].strip().title()
            county = text_array[2].strip().title()
            market = text_array[3].strip().title()
            date = text_array[4].strip()

            # POST request to the /predict endpoint
            response = requests.post(
                f"{PREDICTION_API_URL}/predict",
                json={
                    "commodity": commodity,
                    "county": county,
                    "market": market,
                    "date": date,
                    "days": 7
                }
            )

            if response.status_code == 200:
                data = response.json()
                prediction = data.get("predicted_price", "N/A")
                return f"END Forecasted price for {commodity} in {market}, {county} on {date} is:\nKES {prediction:.2f}"
            else:
                return "END Failed to fetch prediction."

        except Exception as e:
            print("Prediction error:", str(e))
            return "END  Error during prediction request."

    else:
        return "END Invalid input. Please start again."


if __name__ == "__main__":
    app.run(port=10000, debug=True)
