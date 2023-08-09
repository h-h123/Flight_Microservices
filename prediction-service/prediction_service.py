# prediction_service.py
from flask import Flask, request, jsonify, render_template
from flask_restful import Api, Resource
import pickle
import pandas as pd
import requests
from elasticapm.contrib.flask import ElasticAPM
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

# # Configure logging to write logs to a file and the console
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# log_handler = RotatingFileHandler('app.log', maxBytes=1024 * 1024, backupCount=5)  # Create a rotating log file handler
# log_handler.setLevel(logging.DEBUG)  # Set the log level for the handler
# log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
# app.logger.addHandler(log_handler)  # Attach the handler to the Flask app logger

app.config['ELASTIC_APM'] = {
  'SERVICE_NAME': 'prediction -service',

  'SECRET_TOKEN': 'nmf61ZubURfIOqGx64',

  'SERVER_URL': 'https://2365a3d24ef243089d6cbfc2aede69c4.apm.us-central1.gcp.cloud.es.io:443',

  'ENVIRONMENT': 'my-environment',

  'CAPTURE_BODY': 'off',

  'LOG_LEVEL': 'error',  

  'DEBUG': True
}

apm = ElasticAPM(app, service_name ='prediction -service', secret_token='nmf61ZubURfIOqGx64', logging=True)


@app.route("/", methods=["GET"])
def home():
    return "Prediction Service is running successfully!"

#df = pd.read_excel("FlightFare_Dataset.xlsx")
model = pickle.load(open("flight_rf.pkl", "rb"))

def preprocess_duration(duration_minutes):
    hours = int(duration_minutes // 60)
    minutes = int(duration_minutes % 60)
    total_minutes = hours * 60 + minutes
    return total_minutes

def predict_flight_duration(flight_data):
    prediction = model.predict([[
        flight_data["Total_Stops"],
        flight_data["journey_day"],
        flight_data["journey_month"],
        flight_data["Airline_AirIndia"],
        flight_data["Airline_GoAir"],
        flight_data["Airline_IndiGo"],
        flight_data["Airline_JetAirways"],
        flight_data["Airline_MultipleCarriers"],
        flight_data["Airline_Other"],
        flight_data["Airline_SpiceJet"],
        flight_data["Airline_Vistara"],
        flight_data["Source_Banglore"],
        flight_data["Source_Chennai"],
        flight_data["Source_Kolkata"],
        flight_data["Source_Mumbai"],
        flight_data["Destination_Cochin"],
        flight_data["Destination_Delhi"],
        flight_data["Destination_Hyderabad"],
        flight_data["Destination_Kolkata"],
        flight_data["Price"]  
    ]])

    # Get the predicted duration in minutes directly
    predicted_duration_minutes = prediction[0]

    # Preprocess the duration to convert to the total number of minutes
    predicted_duration = preprocess_duration(predicted_duration_minutes)

    #print("this is my prediction@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@", prediction)
    #print("==========================================================================")
    return predicted_duration

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    flight_data = data.get("flight_data")

    # Call the prediction function on the flight data and get the duration prediction.
    predicted_duration = predict_flight_duration(flight_data)

    # Print the predicted duration for debugging
    #print(predicted_duration)
    #print("=====================================================================================")
    #print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")

    # Return the predicted duration in the response
    response_data = {"duration": predicted_duration}
    return jsonify(response_data), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3001, debug=True)
