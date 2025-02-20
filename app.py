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
        # Get the absolute path of the current directory
        current_dir = os.getcwd()
        
        # Load places.xlsx
        places_path = os.path.join(current_dir, 'places.xlsx')
        activities_path = os.path.join(current_dir, 'activities.xlsx')
        
        print(f"Loading files from: {current_dir}")
        
        # Load both files
        places_df = pd.read_excel(places_path)
        activities_df = pd.read_excel(activities_path)
        
        print("Successfully loaded both files")
        return places_df, activities_df
        
    except Exception as e:
        print(f"Error loading Excel files: {str(e)}")
        print(traceback.format_exc())
        return None, None

@app.route('/api/generate-travel-plan', methods=['POST'])
def generate_travel_plan():
    try:
        # Load data
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
                'error': 'Missing answers in request'
            }), 400

        answers = data['answers']
        print(f"Received answers: {answers}")  # Debug print

        # Create prompt
        experiences = answers[0]
        duration = answers[1]
        places = answers[2]
        activities = answers[3]
        season = answers[4]
        budget = answers[5]

        prompt = f"""Create a {duration}-day travel itinerary based on the following preferences:

Selected Experiences: {experiences}
Places of Interest: {places}
Preferred Activities: {activities}
Season: {season}
Budget Range: {budget}

Available Places:
{places_df.to_string(index=False)}

Available Activities:
{activities_df.to_string(index=False)}

Please provide a day-by-day itinerary that:
1. Only includes places and activities from the provided lists
2. Fits within the {duration}-day duration
3. Stays within the budget of {budget}
4. Is appropriate for {season} season
5. Includes estimated costs for each activity

Format as a daily schedule with morning, afternoon, and evening activities."""

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