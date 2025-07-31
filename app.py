from flask import Flask, request
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env
app = Flask(__name__)
API_BASE_URL = os.getenv("API_BASE_URL")

# --- Full commodity and market lists ---
all_commodities = [
    "maize", "beans", "tomatoes", "cabbage", "onions",
    "carrots", "peas", "spinach", "kale", "sorghum",
    "millet", "potatoes", "rice"
]

all_markets = [
    "wakulima", "gikomba", "kawangware", "kangemi", "makongeni",
    "thika", "kisumu", "mombasa", "embu", "nyeri"
]

# --- Mock prices for testing ---
mock_prices = {
    ("maize", "wakulima", "farmer", "2025-08-30"): 2700,
    ("maize", "wakulima", "consumer", "2025-08-30"): 3000
}

@app.route('/')
def home():
    # Test API connection (optional)
    if API_BASE_URL:
        try:
            response = requests.get(f"{API_BASE_URL}/some-endpoint")
            return response.text
        except Exception as e:
            return f"API request failed: {e}"
    return "MaliYaLeo is running."

@app.route("/ussd", methods=["POST"])
def ussd():
    session_id = request.form.get("sessionId", "")
    phone_number = request.form.get("phoneNumber", "")
    text = request.form.get("text", "")
    
    text_array = text.split("*") if text else []
    level = len(text_array)
    response = ""

    if level == 0:
        response = "CON Welcome to MaliYaLeo 📊\n1. Farmer\n2. Consumer"

    elif level == 1 or (level == 2 and text_array[1] in ["N", "B"]):
        page = 0
        if level == 2:
            current = text_array[1]
            page = int(text_array[2]) if len(text_array) > 2 else 0
            if current == "N":
                page += 1
            elif current == "B":
                page -= 1

        start = page * 5
        end = start + 5
        items = all_commodities[start:end]

        response = "CON Select commodity:\n"
        for i, item in enumerate(items, 1):
            response += f"{i}. {item.title()}\n"

        if end < len(all_commodities):
            response += f"{len(items)+1}. Next\n"
        if page > 0:
            response += f"{len(items)+2}. Back\n"

        response += f"\n(Commodities Page {page+1})"

    elif level == 2 or level == 3:
        page = 0
        if text_array[1] in ["N", "B"]:
            page = int(text_array[2])
            selected = int(text_array[3]) - 1
            offset = page * 5
        else:
            selected = int(text_array[1]) - 1
            offset = 0

        try:
            commodity = all_commodities[offset + selected]
        except IndexError:
            return "END Invalid commodity selection."

        role = "farmer" if text_array[0] == "1" else "consumer"
        full_text = f"{text_array[0]}*{commodity}"

        response = market_menu(full_text, 0)

    elif len(text_array) >= 2 and text_array[1] in all_commodities:
        commodity = text_array[1]
        role = "farmer" if text_array[0] == "1" else "consumer"

        if len(text_array) == 3 and text_array[2] in ["N", "B"]:
            current_page = int(text_array[3]) if len(text_array) > 3 else 0
            new_page = current_page + 1 if text_array[2] == "N" else current_page - 1
            full_text = f"{text_array[0]}*{commodity}"
            response = market_menu(full_text, new_page)

        elif len(text_array) >= 3:
            try:
                market_index = int(text_array[2]) - 1
                market = all_markets[market_index]
            except:
                return "END Invalid market choice."

            full_text = f"{text_array[0]}*{commodity}*{market}"
            response = "CON Choose time range:\n1. Tomorrow\n2. In 3 days\n3. In a week\n4. In a month"

    elif len(text_array) == 4:
        role = "farmer" if text_array[0] == "1" else "consumer"
        commodity = text_array[1]
        market = text_array[2]
        days_map = {"1": 1, "2": 3, "3": 7, "4": 30}
        days = days_map.get(text_array[3], 0)
        future_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

        predicted_price = query_real_api(commodity, market, role, future_date)

        if predicted_price:
            response = f"END Predicted {role} price for {commodity.title()} in {market.title()} on {future_date} is KES {predicted_price}"
        else:
            response = "END Sorry, no prediction available for your selection."

    else:
        response = "END Invalid input."

    return response

def query_real_api(commodity, market, role, date):
    return mock_prices.get((commodity, market, role, date))

def market_menu(base_text, page):
    start = page * 5
    end = start + 5
    items = all_markets[start:end]

    response = "CON Select market:\n"
    for i, item in enumerate(items, 1):
        response += f"{i}. {item.title()}\n"

    if end < len(all_markets):
        response += f"{len(items)+1}. Next\n"
    if page > 0:
        response += f"{len(items)+2}. Back\n"

    response += f"\n(Markets Page {page+1})"
    return response

if __name__ == "__main__":
    app.run(debug=True)
