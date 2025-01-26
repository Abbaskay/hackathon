import streamlit as st
import openrouteservice
import folium
from streamlit_folium import st_folium
import requests
import datetime
import json
import pandas as pd

# Set wide layout
st.set_page_config(page_title="Smart Living App", layout="wide")

# API keys
ORS_API_KEY = "5b3ce3597851110001cf6248baa56bd554504f97bfe1df91f4b588d1"
OPENWEATHER_API_KEY = "90c04cb057d14979bddf52105b2ecf32"
WAQI_TOKEN = "37b12b24c5d77665fe387be337f26bf390221421"


# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "Home"

if "travel_results" not in st.session_state:
    st.session_state.travel_results = None

if "school_results" not in st.session_state:
    st.session_state.school_results = None

if "zen_results" not in st.session_state:
    st.session_state.zen_results = None

if "traffic_reports" not in st.session_state:
    st.session_state.traffic_reports = []

if "user_points" not in st.session_state:
    st.session_state.user_points = {}
if "leaderboard" not in st.session_state:
    st.session_state.leaderboard = pd.DataFrame(columns=["User", "Points"])

def navigate_to(page):
    st.session_state.page = page

# Geocoding function
def geocode_location(location):
    try:
        # OpenRouteService API endpoint and parameters
        params = {
            "5b3ce3597851110001cf6248baa56bd554504f97bfe1df91f4b588d1": ORS_API_KEY,  # Replace with your valid API key
            "text": location,
            "size": 1  # Limit results to the best match
        }
        response = requests.get("https://api.openrouteservice.org/geocode/search", params=params)
        
        # Check if the request was successful
        if response.status_code == 200:
            results = response.json()
            
            # Ensure there are results and extract coordinates
            if results.get("features"):
                coords = results["features"][0]["geometry"]["coordinates"]
                return coords[0], coords[1]  # Longitude, Latitude
            else:
                st.error(f"No results found for location: {location}")
                return None, None
        else:
            st.error(f"Geocoding request failed with status code: {response.status_code}")
            return None, None
    except Exception as e:
        st.error(f"Error during geocoding: {e}")
        return None, None
    
# Function to log eco-friendly activities
def log_activity(user, activity_type):
    activity_points = {
        "Walking": 10,
        "Cycling": 15,
        "Public Transport": 8,
    }
    points = activity_points.get(activity_type, 0)
    
    if user not in st.session_state.user_points:
        st.session_state.user_points[user] = 0
    st.session_state.user_points[user] += points


# Pollution Data (AQI)
def get_aqi(lat, lon):
    try:
        response = requests.get(f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={WAQI_TOKEN}")
        data = response.json()
        if data.get("status") == "ok":
            return data["data"]["aqi"]
        return None
    except Exception as e:
        st.error(f"Error fetching AQI: {e}")
        return None

# Eco-friendly Tips Function
def eco_friendly_tips(mode, carbon_footprint):
    tips = []
    if mode == "driving-car":
        if carbon_footprint > 1:
            tips.append("Consider carpooling to reduce emissions.")
        tips.append("Maintain your vehicle to ensure optimal fuel efficiency.")
    elif mode == "cycling-regular":
        tips.append("Ensure your bicycle is well-maintained for a smooth ride.")
    elif mode == "foot-walking":
        tips.append("Walking is great for health and the environment!")
    return tips

# Home Page
if st.session_state.page == "Home":
    st.title("🌟 Welcome to the Smart Living App")
    st.write("Choose your desired application:")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Smart Travel Application"):
            navigate_to("Travel")
    with col2:
        if st.button("Smart School Route Planner"):
            navigate_to("School")
        

# Smart Travel Application
elif st.session_state.page == "Travel":
    st.title("🚗 Smart Travel Application")
    st.write("Plan your trip with real-time pollution, weather, and eco-friendly insights.")

    origin = st.text_input("Enter your starting location:")
    destination = st.text_input("Enter your destination:")
    mode = st.selectbox("Select Mode of Transport", ["driving-car", "cycling-regular", "foot-walking"])

    if st.button("Get Route"):
        if origin and destination:
            try:
                client = openrouteservice.Client(key=ORS_API_KEY)

                # Geocoding function
                def geocode_location(location):
                    params = {"api_key": ORS_API_KEY, "text": location}
                    response = requests.get("https://api.openrouteservice.org/geocode/search", params=params)
                    results = response.json()
                    if results["features"]:
                        coords = results["features"][0]["geometry"]["coordinates"]
                        return coords[0], coords[1]
                    else:
                        st.error(f"Could not find location: {location}")
                        return None, None

                origin_coords = geocode_location(origin)
                dest_coords = geocode_location(destination)

                if None not in origin_coords and None not in dest_coords:
                    # Route Calculation
                    route = client.directions(
                        coordinates=[origin_coords, dest_coords],
                        profile=mode,
                        format="geojson",
                    )

                    # Pollution Data (AQI)
                    def get_aqi(lat, lon):
                        response = requests.get(f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={WAQI_TOKEN}")
                        data = response.json()
                        if data.get("status") == "ok":
                            return data["data"]["aqi"]
                        return None

                    origin_aqi = get_aqi(origin_coords[1], origin_coords[0])
                    dest_aqi = get_aqi(dest_coords[1], dest_coords[0])

                    # Weather Forecast
                    def get_weather(lat, lon):
                        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
                        response = requests.get(url)
                        return response.json()

                    origin_weather = get_weather(origin_coords[1], origin_coords[0])
                    dest_weather = get_weather(dest_coords[1], dest_coords[0])

                    # Carbon Footprint Calculation
                    distance_km = route["features"][0]["properties"]["segments"][0]["distance"] / 1000
                    carbon_footprint = {
                        "driving-car": distance_km * 0.120,  # 120g CO2/km
                        "cycling-regular": distance_km * 0.021,  # 21g CO2/km
                        "foot-walking": 0,  # No emissions
                    }[mode]

                    # Store Results
                    st.session_state.travel_results = {
                        "route": route,
                        "origin_aqi": origin_aqi,
                        "dest_aqi": dest_aqi,
                        "origin_weather": origin_weather,
                        "dest_weather": dest_weather,
                        "distance_km": distance_km,
                        "carbon_footprint": carbon_footprint,
                        "eco_tips": eco_friendly_tips(mode, carbon_footprint),
                    }
            except Exception as e:
                st.error(f"An error occurred: {e}")

    # Display Results
    if st.session_state.travel_results:
        results = st.session_state.travel_results
        col1, col2 = st.columns([2, 1])

        with col1:
            # Map
            route_map = folium.Map(location=[results["route"]["features"][0]["geometry"]["coordinates"][0][1],
                                             results["route"]["features"][0]["geometry"]["coordinates"][0][0]],
                                   zoom_start=12)
            folium.GeoJson(results["route"], name="Route").add_to(route_map)
            st.subheader("Route Map")
            st_folium(route_map, width=700, height=500)

        with col2:
            # Route Information
            st.subheader("Route and Environmental Insights")
            st.write(f"**Route Distance**: {results['distance_km']:.2f} km")
            st.write(f"**Carbon Footprint**: {results['carbon_footprint']:.2f} kg CO2")
            st.write(f"**Origin AQI**: {results['origin_aqi']}")
            st.write(f"**Destination AQI**: {results['dest_aqi']}")
            st.write(f"**Origin Weather**: {results['origin_weather']['weather'][0]['description'].capitalize()}, {results['origin_weather']['main']['temp']}°C")
            st.write(f"**Destination Weather**: {results['dest_weather']['weather'][0]['description'].capitalize()}, {results['dest_weather']['main']['temp']}°C")

            # Eco-friendly Tips
            st.subheader("Eco-friendly Tips")
            for tip in results["eco_tips"]:
                st.write(f"• {tip}")

            # Update leaderboard
    leaderboard = st.session_state.leaderboard
    points = st.session_state.user_points.get(st.session_state.username, 0)
    if st.session_state.username in leaderboard["User"].values:
        leaderboard.loc[leaderboard["User"] == st.session_state.username, "Points"] += points
    else:
        new_entry = {"User": st.session_state.username, "Points": points}
        st.session_state.leaderboard = pd.concat([leaderboard, pd.DataFrame([new_entry])], ignore_index=True)

    st.session_state.leaderboard.sort_values(by="Points", ascending=False, inplace=True)
    st.session_state.leaderboard.reset_index(drop=True, inplace=True)

# Display the gamification interface
st.title("Gamification for Sustainable Behavior")
st.subheader("Log Your Eco-Friendly Activities")

# User input for logging activities
user_name = st.text_input("Enter your name:")
activity = st.selectbox("Select an eco-friendly activity:", ["Walking", "Cycling", "Public Transport"])
if st.button("Log Activity"):
    if user_name and activity:
        log_activity(user_name, activity)
        st.success(f"{activity} logged! You've earned points!")
    else:
        st.warning("Please enter your name and select an activity.")

# Display badges based on points
st.subheader("Your Rewards")
if user_name in st.session_state.user_points:
    user_points = st.session_state.user_points[user_name]
    st.write(f"Total Points: {user_points}")
    
    # Display badges based on milestones
    if user_points >= 100:
        st.write("🏆 **Gold Badge: Sustainability Champion!**")
    elif user_points >= 50:
        st.write("🥈 **Silver Badge: Eco Enthusiast!**")
    elif user_points >= 20:
        st.write("🥉 **Bronze Badge: Green Starter!**")
    else:
        st.write("🌱 Keep going! More rewards await!")

# Display leaderboard
st.subheader("Leaderboard")
if not st.session_state.leaderboard.empty:
    st.table(st.session_state.leaderboard)
else:
    st.write("No activities logged yet. Be the first to contribute!")

if st.button("Back to Home"):
            navigate_to("Home")

# Smart School Route Planner
if st.session_state.page == "School":
    st.title("🚌 Smart School Route Planner")
    st.write("Optimize school routes for safety and eco-friendliness.")

    kid_location = st.text_input("Enter your kid's location:")
    school_location = st.text_input("Enter the school location:")

    if st.button("Plan School Route"):
        if kid_location and school_location:
            try:
                client = openrouteservice.Client(key=ORS_API_KEY)
                kid_coords = geocode_location(kid_location)
                school_coords = geocode_location(school_location)

                

                if None not in kid_coords and None not in school_coords:
                    # Route Calculation
                    route = client.directions(
                        coordinates=[kid_coords, school_coords],
                        profile="driving-car",
                        format="geojson",
                    )

                    # Pollution Data
                    kid_aqi = get_aqi(kid_coords[1], kid_coords[0])
                    school_aqi = get_aqi(school_coords[1], school_coords[0])

                    # Safety and Environmental Tips
                    tips = []
                    if kid_aqi and school_aqi:
                        if kid_aqi > 100 or school_aqi > 100:
                            tips.append("Consider wearing masks to protect from pollution.")
                        else:
                            tips.append("Air quality is good for today's commute!")

                    tips.append("Encourage carpooling to reduce emissions.")

                    # Store Results
                    st.session_state.school_results = {
                        "route": route,
                        "kid_aqi": kid_aqi,
                        "school_aqi": school_aqi,
                        "tips": tips,
                    }
            except Exception as e:
                st.error(f"An error occurred: {e}")

    # Display Results
    if st.session_state.school_results:
        results = st.session_state.school_results
        col1, col2 = st.columns([2, 1])

        with col1:
            # Map
            route_map = folium.Map(location=[results["route"]["features"][0]["geometry"]["coordinates"][0][1],
                                             results["route"]["features"][0]["geometry"]["coordinates"][0][0]],
                                   zoom_start=12)
            folium.GeoJson(results["route"], name="Route").add_to(route_map)
            st.subheader("Route Map")
            st_folium(route_map, width=700, height=500)

        with col2:
            # Route Information
            st.subheader("Route and Safety Insights")
            st.write(f"**Kid's Location AQI**: {results['kid_aqi']}")
            st.write(f"**School Location AQI**: {results['school_aqi']}")
            st.subheader("Tips")
            for tip in results["tips"]:
                st.write(f"• {tip}")

    if st.button("Back to Home"):
        navigate_to("Home")






