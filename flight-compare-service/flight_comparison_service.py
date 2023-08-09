# flights_microservice.py
from flask import Flask, request, jsonify,render_template
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from sklearn.preprocessing import LabelEncoder
import numpy as np
import json
import plotly.io as pio
# Import plotly.graph_objects
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from flask_cors import CORS
import requests
import os
from elasticapm.contrib.flask import ElasticAPM
import logging
from logging.handlers import RotatingFileHandler
from folium.plugins import AntPath
#from folium import Marker, plugins



app = Flask(__name__, template_folder='templates')

# # Configure logging to write logs to a file and the console
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# log_handler = RotatingFileHandler('app.log', maxBytes=1024 * 1024, backupCount=5)  # Create a rotating log file handler
# log_handler.setLevel(logging.DEBUG)  # Set the log level for the handler
# log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
# app.logger.addHandler(log_handler)  # Attach the handler to the Flask app logger

app.config['ELASTIC_APM'] = {
  'SERVICE_NAME': 'flight-compare-service',

  'SECRET_TOKEN': 'nmf61ZubURfIOqGx64',

  'SERVER_URL': 'https://2365a3d24ef243089d6cbfc2aede69c4.apm.us-central1.gcp.cloud.es.io:443',

  'ENVIRONMENT': 'my-environment',

  'CAPTURE_BODY': 'off',

  'LOG_LEVEL': 'error',  # Capture all log levels using trace

  'DEBUG': True
}

apm = ElasticAPM(app, service_name ='flight-compare-service', secret_token='nmf61ZubURfIOqGx64',logging=True)


# # Get the absolute path of the directory containing the main_app.py script
# script_dir = os.path.dirname(os.path.abspath(__file__))

# # Construct the absolute path to the Excel file
# file_path = os.path.join(script_dir, "../FlightFare_Dataset.xlsx")

# # Read the Excel file
# df = pd.read_excel(file_path)
# Load the flight dataset
df = pd.read_excel("FlightFare_Dataset.xlsx")  # Replace with the actual path to your dataset

# Perform data preprocessing on the 'Duration' column
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
# Convert "Total_Stops" column to numeric values
df.replace({"non-stop": 0, "1 stop": 1, "2 stops": 2, "3 stops": 3, "4 stops": 4}, inplace=True)
# Rename 'New Delhi' to 'Delhi' in the 'Destination' column
df['Destination'].replace({'New Delhi': 'Delhi'}, inplace=True)

# Convert the 'Date_of_Journey' column to datetime format
df['Date_of_Journey'] = pd.to_datetime(df['Date_of_Journey'], format='%d/%m/%Y')

#print(df.head(5))
# Define latitude and longitude values for cities (replace with actual coordinates)
city_coordinates = {
    "Banglore": {"Latitude": 12.9716, "Longitude": 77.5946},
    "Kolkata": {"Latitude": 22.5726, "Longitude": 88.3639},
    "Mumbai": {"Latitude": 19.0760, "Longitude": 72.8777},
    "Delhi": {"Latitude": 28.6139, "Longitude": 77.2090},
    "Chennai": {"Latitude": 13.0827, "Longitude": 80.2707},
    "Cochin": {"Latitude": 9.9312, "Longitude": 76.2673},
    "Hyderabad": {"Latitude": 17.3850, "Longitude": 78.4867}
}

# Add latitude and longitude columns to the DataFrame
df["Latitude_Source"] = df["Source"].map(lambda x: city_coordinates[x]["Latitude"])
df["Longitude_Source"] = df["Source"].map(lambda x: city_coordinates[x]["Longitude"])
df["Latitude_Destination"] = df["Destination"].map(lambda x: city_coordinates[x]["Latitude"])
df["Longitude_Destination"] = df["Destination"].map(lambda x: city_coordinates[x]["Longitude"])


# Create a popup content for flight history details
def create_popup_content(row):
    popup_content = f"""
    <strong>Flight Details:</strong><br>
    Airline: {row['Airline']}<br>
    Date of Journey: {row['Date_of_Journey']}<br>
    Source: {row['Source']}<br>
    Destination: {row['Destination']}<br>
    """
    return folium.Popup(popup_content, max_width=300)


@app.route("/")
def home():
    return render_template("flight_comparison.html")


@app.route("/compare_flights", methods=["POST"])
def compare_flights():
    # Get user inputs from the request
    data = request.form
    source = data.get("Source")
    destination = data.get("Destination")

    print("User Input:")
    print("Source:", source)
    print("Destination:", destination)

    # Filter the dataset based on user inputs
    # filtered_data = df[
    #     df["Source"].isin([source]) &
    #     df["Destination"].isin([destination])
    # ]
    filtered_data = df[
        (df["Source"].str.capitalize() == source.capitalize()) &
        (df["Destination"].str.capitalize() == destination.capitalize())
    ]
    
    #print("Filtered Data:")
    #print(filtered_data)

    if filtered_data.empty:
        return "No flights found for the selected source and destination."
    

    # Create a folium map centered around India
    india_map = folium.Map(location=[20.5937, 78.9629], zoom_start=5)

    # Add markers for all city locations
    for city, coords in city_coordinates.items():
        folium.Marker(location=[coords["Latitude"], coords["Longitude"]],
                    popup=city).add_to(india_map)

    # # Check if user inputs are valid cities
    # if source not in city_coordinates or destination not in city_coordinates:
    #     print("Invalid source or destination.")
    # else:
    #     # Add the flight route as a line if user inputs are valid cities
    #     folium.PolyLine(locations=[(city_coordinates[source]["Latitude"], city_coordinates[source]["Longitude"]),
    #                             (city_coordinates[destination]["Latitude"], city_coordinates[destination]["Longitude"])],
    #                     color='blue').add_to(india_map)

    if source not in city_coordinates or destination not in city_coordinates:
        print("Invalid source or destination.")
    else:
        source_coords = [city_coordinates[source]["Latitude"], city_coordinates[source]["Longitude"]]
        dest_coords = [city_coordinates[destination]["Latitude"], city_coordinates[destination]["Longitude"]]

        # Create an AntPath connecting the source and destination cities
        ant_path = AntPath(
            locations=[source_coords, dest_coords],
            color='blue',
            delay=1000
        )
        # Add the AntPath and PlaneMarker to the map
        ant_path.add_to(india_map)
        
        # Add time slider plugin for the previous three flights
        # time_slider = plugins.TimestampedGeoJson({
        #     'type': 'FeatureCollection',
        #     'features': [
        #         {
        #             'type': 'Feature',
        #             'geometry': {
        #                 'type': 'Point',
        #                 'coordinates': (city_coordinates[flight["Source"]]["Longitude"], city_coordinates[flight["Source"]]["Latitude"]),
        #             },
        #             'properties': {
        #                 'time': flight["Date_of_Journey"].strftime('%Y-%m-%d'),
        #                 'icon': 'circle',
        #                 'iconstyle': {
        #                     'fillColor': 'blue',
        #                     'fillOpacity': 0.6,
        #                     'stroke': 'true',
        #                     'radius': 5,
        #                 },
        #             }
        #         } for index, flight in df.head(3).iterrows()  # Modify this line to use the last three rows
        #     ]
        # })
        # time_slider.add_to(india_map)
        # # Create a curved polyline connecting the source and destination cities with popup details
        # curved_polyline = [
        #     [city_coordinates[source]["Latitude"], city_coordinates[source]["Longitude"]],
        #     [city_coordinates[destination]["Latitude"], city_coordinates[destination]["Longitude"]]
        # ]
        # folium.PolyLine(curved_polyline, color='red', curve=True, dash_array=[10, 20]).add_to(india_map)

        # # Plot flight history using markers and curved lines for the previous three flights
        # for index, flight in df.tail(3).iterrows():
        #     source_coords = (city_coordinates[flight["Source"]]["Latitude"], city_coordinates[flight["Source"]]["Longitude"])
        #     dest_coords = (city_coordinates[flight["Destination"]]["Latitude"], city_coordinates[flight["Destination"]]["Longitude"])
            
        #     # Add the flight route as a curved line if user inputs are valid cities
        #     curved_flight_path = [
        #         [city_coordinates[flight["Source"]]["Latitude"], city_coordinates[flight["Source"]]["Longitude"]],
        #         [city_coordinates[flight["Destination"]]["Latitude"], city_coordinates[flight["Destination"]]["Longitude"]]
        #     ]
        #     folium.PolyLine(curved_flight_path, color='green', curve=True).add_to(india_map)
            
        #     # Add markers with popup content for flight history
        #     folium.Marker(location=source_coords, icon=folium.Icon(color='blue'), popup=create_popup_content(flight)).add_to(india_map)
        #     folium.Marker(location=dest_coords, icon=folium.Icon(color='green'), popup=create_popup_content(flight)).add_to(india_map)



    # Convert the folium map to HTML
    india_map_html = india_map._repr_html_()

    # Group the filtered data by Airline and calculate the average price and duration for each group
    grouped_data = filtered_data.groupby("Airline", as_index=False).agg({"Price": "mean", "Duration(min)": "mean"})

    # Create two pie charts using Plotly
    fig_pie1 = go.Figure(data=[go.Pie(
        labels=grouped_data["Airline"],
        values=grouped_data["Price"],
        hole=0.4,
        hoverinfo='label+text',
        hovertemplate="%{label}: Rs%{value:.2f}"
    )])
    fig_pie1.update_layout(title=f"Average Prices by Airlines from {source} to {destination}", width=500, height=500)

    fig_pie2 = go.Figure(data=[go.Pie(
        labels=grouped_data["Airline"],
        values=grouped_data["Duration(min)"],
        hole=0.4,
        hoverinfo='label+text',
        hovertemplate="%{label}: %{value:.2f} mins"
    )])
    fig_pie2.update_layout(title=f"Average Durations by Airlines from {source} to {destination}", width=500, height=500)

    
    # Create a bar graph to show the number of flights for each airline
    flights_count = filtered_data["Airline"].value_counts()
    fig_bar = px.bar(flights_count, x=flights_count.index, y=flights_count.values)
    fig_bar.update_layout(title="Number of Flights for each Airline", xaxis_title="Airline", yaxis_title="Number of Flights")

    # Convert the folium map to HTML
    india_map_html = india_map._repr_html_()

    # Convert the pie charts to HTML
    fig_pie1_html = fig_pie1.to_html(full_html=False, include_plotlyjs='cdn')
    fig_pie2_html = fig_pie2.to_html(full_html=False, include_plotlyjs='cdn')

    fig_bar_html = fig_bar.to_html(full_html=False, include_plotlyjs='cdn')

    # Render the HTML template with the plot data
    return render_template("flight_comparison.html", india_map_html=india_map_html, pie_chart1_html=fig_pie1_html, pie_chart2_html=fig_pie2_html, bar_graph_html=fig_bar_html)

@app.route("/simulate_failure")
def simulate_failure():
    # Intentionally raise an exception to simulate a failure
    raise Exception("This is a simulated failure for testing purposes.")



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3003, debug=True)
