from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
import pandas as pd
import os
import traceback

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure Google Generative AI
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

genai.configure(api_key=api_key)

def load_data():
    try:
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        places_path = os.path.join(current_dir, 'places.xlsx')
        activities_path = os.path.join(current_dir, 'activities.xlsx')
        
        # Print file paths for debugging
        print(f"Attempting to load files from: \nPlaces: {places_path}\nActivities: {activities_path}")
        
        # Load the files
        places_df = pd.read_excel(places_path)
        activities_df = pd.read_excel(activities_path)
        
        print(f"Successfully loaded data:\nPlaces: {len(places_df)} records\nActivities: {len(activities_df)} records")
        return places_df, activities_df
    except Exception as e:
        print(f"Error loading Excel files: {str(e)}")
        print(traceback.format_exc())
        return None, None

def create_detailed_prompt(places_df, activities_df, answers):
    # Format places data
    places_info = "Available Places:\n"
    for _, row in places_df.iterrows():
        places_info += f"- {row['Name']}: {row['Description']}\n"
        places_info += f"  Location: {row['Address']}\n"
        places_info += f"  Hours: {row['open time']} - {row['close time']}\n"
        places_info += f"  Entry Fee: {row['Entry Fee']}\n"
        if pd.notna(row['cultural tip']):
            places_info += f"  Cultural Tip: {row['cultural tip']}\n"
        places_info += "\n"

    # Format activities data
    activities_info = "Available Activities:\n"
    for _, row in activities_df.iterrows():
        activities_info += f"- {row['Name']}: {row['Description']}\n"
        if 'Duration' in activities_df.columns:
            activities_info += f"  Duration: {row['Duration']}\n"
        if 'Entry Fee' in activities_df.columns:
            activities_info += f"  Entry Fee: {row['Entry Fee']}\n"
        activities_info += "\n"

    return f"""Based on the following places and activities, create a detailed travel plan for {answers[0]} for {answers[1]}.

{places_info}

{activities_info}

Please create a comprehensive travel plan following this format:

## Destination Overview
Provide a brief overview of {answers[0]} based on the available attractions and activities.

## Daily Itinerary
For each day, include:
- Morning activity (with opening times and cultural tips)
- Afternoon activity (with cultural tips)
- Evening activity (with closing times and cultural tips)
Make sure to:
- Only include places and activities from the provided lists
- Consider opening and closing times
- Group nearby locations together
- Include relevant cultural tips
- Mention entry fees

## Cultural Tips and Dress Code
- List important cultural considerations from the data
- Include dress code requirements
- Mention timing considerations

## Budget Breakdown
- List entry fees for each place/activity
- Provide estimated total cost

## Transportation and Logistics
- Suggest efficient routes between locations
- Include practical transportation tips
- Mention best times to visit each location

Additional preferences: {', '.join(answers[2:] if len(answers) > 2 else [])}

Important: Only recommend places and activities that are explicitly listed in the provided data."""

@app.route('/api/generate-travel-plan', methods=['POST'])
def generate_travel_plan():
    try:
        # Load data first
        places_df, activities_df = load_data()
        if places_df is None or activities_df is None:
            return jsonify({
                'success': False,
                'error': 'Failed to load data from Excel files'
            }), 500

        # Get request data
        data = request.get_json()
        if not data or 'answers' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: answers'
            }), 400

        answers = data['answers']
        print(f"Received answers: {answers}")

        # Create detailed prompt
        prompt = create_detailed_prompt(places_df, activities_df, answers)

        # Generate response
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)

        return jsonify({
            'success': True,
            'travel_plan': response.text
        }), 200

    except Exception as e:
        print(f"Error in generate_travel_plan: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("Starting server...")
    print(f"Current directory: {os.getcwd()}")
    app.run(debug=True)