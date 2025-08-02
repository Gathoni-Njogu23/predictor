from flask import Flask, request
import requests
import os

app = Flask(__name__)

# Get the base URL of the prediction API from environment variables
PREDICTION_API_URL = os.environ.get("PREDICTION_API_URL", "https://7a9b2ad38296.ngrok-free.app")

@app.route("/ussd", methods=["POST"])
def forward_ussd():
    try:
        # Forward the POST request (with form data) to teammate's /ussd endpoint
        api_response = requests.post(f"{PREDICTION_API_URL}/ussd", data=request.form)

        # Return the response as plain text (important for Africa's Talking)
        return api_response.text, api_response.status_code, {'Content-Type': 'text/plain'}

    except Exception as e:
        print("Error forwarding USSD request:", e)
        return "END Service temporarily unavailable. Please try again later.", 200, {'Content-Type': 'text/plain'}

if __name__ == "__main__":
    app.run(debug=True)
