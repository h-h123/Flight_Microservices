from flask import Flask, request, jsonify, render_template
from flask_restful import Api, Resource
import pickle
import pandas as pd
import requests
from flask_cors import CORS  # Import flask_cors

app = Flask(__name__)
api = Api(app)

# Enable CORS for the entire app
CORS(app)

df = pd.read_excel("FlightFare_Dataset.xlsx")
model = pickle.load(open("flight_rf.pkl", "rb"))

@app.route("/")
def home():
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

    # Print the response for debugging
    print(prediction_response.text)
    print("=====================================================================================")
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")

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



# @app.route("/flight_comparison", methods=["POST"])
# def flight_comparison():
#     data = {
#         "airline": request.form["airline"],
#         "source": request.form["Source"],
#         "destination": request.form["Destination"],
#         "min_duration": request.form["min_duration"],
#         "max_duration": request.form["max_duration"]
#     }
#     comparison_response = requests.post("http://localhost:3002/flight_comparison", json=data)
#     flights_list = comparison_response.json()["flights_list"]
#     return render_template("flights_list.html", flights_list=flights_list)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3002, debug=True)
