from flask import Flask, request
import requests
import os

app = Flask(__name__)

PREDICTION_API_URL = os.environ.get("PREDICTION_API_URL", "https://7a9b2ad38296.ngrok-free.app")

@app.route('/ussd', methods=['POST'])
def ussd():
    session_id = request.values.get("sessionId", "")
    phone = request.values.get("phoneNumber", "")
    text = request.values.get("text", "")

    inputs = text.split("*")
    step = len(inputs)

    try:
        if text == "":
            response = "CON Welcome to MaliYaLeo!\n1. Farmer (Wholesale)\n2. Consumer (Retail)"

        elif step == 1:
            # Get commodities from API
            role = "wholesale" if inputs[0] == "1" else "retail"
            r = requests.get(f"{PREDICTION_API_URL}/commodities?user_type={role}")
            if r.status_code == 200:
                commodities = r.json().get("commodities", [])
                if not commodities:
                    response = "END No commodities found."
                else:
                    response = "CON Choose commodity:\n" + "\n".join(
                        [f"{i+1}. {c}" for i, c in enumerate(commodities)]
                    )
            else:
                response = "END Could not fetch commodities."

        elif step == 2:
            role = "wholesale" if inputs[0] == "1" else "retail"
            commodity_index = int(inputs[1]) - 1
            # Fetch commodities to map index to name
            r = requests.get(f"{PREDICTION_API_URL}/commodities?user_type={role}")
            commodities = r.json().get("commodities", [])
            if commodity_index >= len(commodities):
                return "END Invalid commodity selected.", 200, {'Content-Type': 'text/plain'}
            commodity = commodities[commodity_index]

            r = requests.get(f"{PREDICTION_API_URL}/counties?commodity={commodity}")
            counties = r.json().get("counties", [])
            response = "CON Choose county:\n" + "\n".join(
                [f"{i+1}. {c}" for i, c in enumerate(counties)]
            )

        elif step == 3:
            role = "wholesale" if inputs[0] == "1" else "retail"
            commodity_index = int(inputs[1]) - 1
            county_index = int(inputs[2]) - 1

            # Fetch commodity + county
            r1 = requests.get(f"{PREDICTION_API_URL}/commodities?user_type={role}")
            commodity = r1.json().get("commodities", [])[commodity_index]

            r2 = requests.get(f"{PREDICTION_API_URL}/counties?commodity={commodity}")
            county = r2.json().get("counties", [])[county_index]

            # Get markets
            r3 = requests.get(f"{PREDICTION_API_URL}/markets?county={county}")
            markets = r3.json().get("markets", [])
            response = "CON Choose market:\n" + "\n".join(
                [f"{i+1}. {m}" for i, m in enumerate(markets)]
            )

        elif step == 4:
            role = "wholesale" if inputs[0] == "1" else "retail"
            commodity_index = int(inputs[1]) - 1
            county_index = int(inputs[2]) - 1
            market_index = int(inputs[3]) - 1

            r1 = requests.get(f"{PREDICTION_API_URL}/commodities?user_type={role}")
            commodity = r1.json().get("commodities", [])[commodity_index]

            r2 = requests.get(f"{PREDICTION_API_URL}/counties?commodity={commodity}")
            county = r2.json().get("counties", [])[county_index]

            r3 = requests.get(f"{PREDICTION_API_URL}/markets?county={county}")
            market = r3.json().get("markets", [])[market_index]

            # Get forecast dates
            r4 = requests.get(f"{PREDICTION_API_URL}/forecast_dates")
            dates = r4.json().get("dates", [])
            response = "CON Choose forecast date:\n" + "\n".join(
                [f"{i+1}. {d}" for i, d in enumerate(dates)]
            )

        elif step == 5:
            role = "wholesale" if inputs[0] == "1" else "retail"
            commodity_index = int(inputs[1]) - 1
            county_index = int(inputs[2]) - 1
            market_index = int(inputs[3]) - 1
            date_index = int(inputs[4]) - 1

            r1 = requests.get(f"{PREDICTION_API_URL}/commodities?user_type={role}")
            commodity = r1.json().get("commodities", [])[commodity_index]

            r2 = requests.get(f"{PREDICTION_API_URL}/counties?commodity={commodity}")
            county = r2.json().get("counties", [])[county_index]

            r3 = requests.get(f"{PREDICTION_API_URL}/markets?county={county}")
            market = r3.json().get("markets", [])[market_index]

            r4 = requests.get(f"{PREDICTION_API_URL}/forecast_dates")
            forecast_date = r4.json().get("dates", [])[date_index]

            # Call final prediction API
            payload = {
                "user_type": role,
                "commodity": commodity,
                "county": county,
                "market": market,
                "forecast_date": forecast_date
            }
            r = requests.post(f"{PREDICTION_API_URL}/predict", json=payload)
            if r.status_code == 200:
                price = r.json().get("predicted_price", "N/A")
                response = (
                    f"END {role.title()} price for {commodity} in {market} "
                    f"on {forecast_date} is Ksh {price}"
                )
            else:
                response = "END Could not retrieve prediction."

        else:
            response = "END Invalid input. Please try again."

    except Exception as e:
        print("USSD error:", e)
        response = "END Something went wrong. Try again."

    return response, 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    app.run()
