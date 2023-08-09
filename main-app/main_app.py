from flask import Flask, request, jsonify, render_template, render_template_string, send_from_directory
from flask_restful import Api, Resource
import pickle
import pandas as pd
import requests
import os
import json
import pdb
from elasticapm.contrib.flask import ElasticAPM
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__, template_folder='templates')
api = Api(app)

# Configure logging to write logs to a file and the console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler = RotatingFileHandler('app.log', maxBytes=1024 * 1024, backupCount=5)
log_handler.setLevel(logging.INFO)
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
app.logger.addHandler(log_handler)

app.config['ELASTIC_APM'] = {
  'SERVICE_NAME': 'frontend-service',

  'SECRET_TOKEN': 'nmf61ZubURfIOqGx64',

  'SERVER_URL': 'https://2365a3d24ef243089d6cbfc2aede69c4.apm.us-central1.gcp.cloud.es.io:443',

  'ENVIRONMENT': 'my-environment',

  'CAPTURE_BODY': 'off', # Avoid capturing request/response bodies in logs

  'LOG_LEVEL': 'error',  # Capture all log levels using trace 

  'DEBUG': True # Set to False for production
}

apm = ElasticAPM(app, service_name ='frontend-service', secret_token='nmf61ZubURfIOqGx64', logging=True)

# Add logging statements
#app.logger.debug("Prediction Service is starting...")

#df = pd.read_excel("FlightFare_Dataset.xlsx")
model = pickle.load(open("flight_rf.pkl", "rb"))


# Add a route to serve the favicon.ico file
@app.route('/favicon.ico')
def favicon():
    try:
        # Send the favicon.ico file from the static folder
        return send_from_directory(app.static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon')
    except Exception as e:
        # Handle errors gracefully
        app.logger.error(f"Error serving favicon: {str(e)}")
        # Send the default favicon icon with appropriate headers
        return send_from_directory(app.static_folder, 'default_favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route("/")
def home():
    app.logger.info("Home route accessed.")
    return render_template("home.html")


@app.route("/predict", methods=["POST"])
def predict():
        # Retrieve the selected price range from the form
    price_range = request.form['PriceRange']
    # Map the selected price range to corresponding values
    if price_range == "low_price":
        Price = 0
    elif price_range == "medium_price":
        Price = 1
    elif price_range == "high_price":
        Price = 2
    else:
        # Handle the case where an invalid option is selected
        return "Invalid price range"
    
    data = {
        "flight_data": {
            "Total_Stops": int(request.form["stops"]),
            "journey_day": int(pd.to_datetime(request.form["Dep_Time"], format="%Y-%m-%d").day),
            "journey_month": int(pd.to_datetime(request.form["Dep_Time"], format="%Y-%m-%d").month),
            "Airline_AirIndia": 0,
            "Airline_GoAir": 0,
            "Airline_IndiGo": 0,
            "Airline_JetAirways": 0,
            "Airline_MultipleCarriers": 0,
            "Airline_SpiceJet": 0,
            "Airline_Vistara": 0,
            "Airline_Other": 0,
            "Source_Banglore": 0,
            "Source_Chennai": 0,
            "Source_Kolkata": 0,
            "Source_Mumbai": 0,
            "Destination_Cochin": 0,
            "Destination_Delhi": 0,
            "Destination_Hyderabad": 0,
            "Destination_Kolkata": 0,
            "Price": Price
        }
    }

    airline = request.form['airline']
    if airline == 'Jet Airways':
        data["flight_data"]["Airline_JetAirways"] = 1
    elif airline == 'IndiGo':
        data["flight_data"]["Airline_IndiGo"] = 1
    elif airline == 'Air India':
        data["flight_data"]["Airline_AirIndia"] = 1
    elif airline == 'Multiple carriers':
        data["flight_data"]["Airline_MultipleCarriers"] = 1
    elif airline == 'SpiceJet':
        data["flight_data"]["Airline_SpiceJet"] = 1
    elif airline == 'Vistara':
        data["flight_data"]["Airline_Vistara"] = 1
    elif airline == 'GoAir':
        data["flight_data"]["Airline_GoAir"] = 1
    else:
        data["flight_data"]["Airline_Other"] = 1

    source = request.form["Source"]
    if source == 'Banglore':
        data["flight_data"]["Source_Banglore"] = 1
    elif source == 'Kolkata':
        data["flight_data"]["Source_Kolkata"] = 1
    elif source == 'Mumbai':
        data["flight_data"]["Source_Mumbai"] = 1
    elif source == 'Chennai':
        data["flight_data"]["Source_Chennai"] = 1

    destination = request.form["Destination"]
    if destination == 'Cochin':
        data["flight_data"]["Destination_Cochin"] = 1
    elif destination == 'Delhi':
        data["flight_data"]["Destination_Delhi"] = 1
    elif destination == 'Hyderabad':
        data["flight_data"]["Destination_Hyderabad"] = 1
    elif destination == 'Kolkata':
        data["flight_data"]["Destination_Kolkata"] = 1

    # Call the prediction service
    prediction_response = requests.post("http://4.224.249.94:3001/predict", json=data)
    #prediction_response = requests.post("http://localhost:3001/predict", json=data)

    # Print the response for debugging
    #print(prediction_response.text)

    # Log user inputs
    app.logger.info(f"User Inputs: {request.form}")
    # Log prediction output
    app.logger.info(f"Prediction Output: {prediction_response.text}")

    # Check if the request was successful (status code 200)
    if prediction_response.status_code == 200:
        # Extract the duration value from the response JSON
        predicted_duration = prediction_response.json()["duration"]
        
        # Convert the predicted duration to hours and minutes
        predicted_duration_hours = int(predicted_duration // 60)
        predicted_duration_minutes = int(predicted_duration % 60)
        
        # Format the duration string
        predicted_duration_str = f"{predicted_duration_hours}h {predicted_duration_minutes}m"
        
        # Render the template with the prediction result
        return render_template("home.html", prediction_text=f"Your Flight Duration is {predicted_duration_str}")
    else:
        # Handle the case when the prediction service returns an error
        return "Prediction Service Error", 500


# Route to display the flight comparison page
@app.route("/flight_comparison")
def flight_comparison_page():
    url = "http://4.224.249.94:3003/"  # Full URL to the flight_comparison.html template
    #url = "http://localhost:3003/"
    response = requests.get(url)
    response_html = response.text

    # Pass the HTML response to the template to render
    return render_template_string(response_html)


# button 
@app.route("/compare_flights", methods=["POST"])
def compare_flights():
    #pdb.set_trace()  # This will start the debugging session
    data = {
        "Source": request.form["Source"],
        "Destination": request.form["Destination"],
    }

    try:
        # Make a POST request to the flight_comparison_service microservice
        response = requests.post("http://4.224.249.94:3003/compare_flights", data=data)
        #response = requests.post("http://localhost:3003/compare_flights", data=data)


        # Check the HTTP response status code
        print("Response Status Code:", response.status_code)

        # Get the HTML response from the flight_comparison_service
        response_html = response.text

        # Print the value of response_html for debugging purposes
        #print("Response HTML:", response_html)

        # Pass the HTML response to the template to render
        return render_template(
            "flight_comparison.html",
            response_html=response_html,
            error_message=None
        )

    except requests.RequestException as e:
        # If there is any exception related to the request (e.g., connection error, timeout, etc.)
        # display an error message
        return render_template(
            "flight_comparison.html",
            response_html="",
            error_message="Flight comparison functionality is currently unavailable. Please try again later."
        )


@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"An error occurred: {str(e)}")
    return "An error occurred.", 500

if __name__ == "__main__":
    app.logger.debug("Starting the application...")
    app.run(host="0.0.0.0", port=3002, debug=True)
