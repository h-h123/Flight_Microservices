# prediction_service.py
from flask import Flask, request, jsonify, render_template
from flask_restful import Api, Resource
import pickle
import pandas as pd
import requests
from flask_cors import CORS  # Import flask_cors

app = Flask(__name__)
# Enable CORS for the entire app
CORS(app)

@app.route("/", methods=["GET"])
def home():
    return "Prediction Service is running successfully!"

df = pd.read_excel("FlightFare_Dataset.xlsx")
model = pickle.load(open("flight_rf.pkl", "rb"))

def preprocess_duration(duration_str):
    if 'h' in duration_str and 'm' in duration_str:
        hours, minutes = duration_str.split()
        hours = int(hours[:-1])  # Extract the numeric value of hours
        minutes = int(minutes[:-1])  # Extract the numeric value of minutes
    elif 'h' in duration_str:
        hours = int(duration_str[:-1])
        minutes = 0
    elif 'm' in duration_str:
        hours = 0
        minutes = int(duration_str[:-1])
    else:
        raise ValueError("Invalid duration format: " + duration_str)
    total_minutes = hours * 60 + minutes
    return total_minutes


# Apply the preprocessing function to the 'Duration' column
df['Duration(min)'] = df['Duration'].apply(preprocess_duration)

# Drop the original 'Duration' column from the DataFrame
df.drop('Duration', axis=1, inplace=True)


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

    print("this is my prediction@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",prediction)
    print("==========================================================================")
    return prediction

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    flight_data = data.get("flight_data")

    # Call the prediction function on the flight data and get the duration prediction.
    predicted_duration_minutes = predict_flight_duration(flight_data)

    # Preprocess the duration
    predicted_duration = preprocess_duration(predicted_duration_minutes)


    # Print the predicted duration for debugging
    print(predicted_duration)
    print("=====================================================================================")
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")

    # Return the predicted duration in the response
    response_data = {"duration": predicted_duration}
    return jsonify(response_data), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3001, debug=True)
