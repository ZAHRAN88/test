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
    """
    Load data from the Excel files.
    Returns a tuple of Pandas DataFrames if successful, otherwise None.
    """
    try:
        # Get the absolute path of the current directory
        current_dir = os.getcwd()
        
        places_file_path = os.path.join(current_dir, 'places.xlsx')
        activities_file_path = os.path.join(current_dir, 'activities.xlsx')

        # Print file paths for debugging
        print(f"Attempting to load places file from: {places_file_path}")
        print(f"Attempting to load activities file from: {activities_file_path}")

        # Check if files exist
        if not os.path.exists(places_file_path) or not os.path.exists(activities_file_path):
            print(f"Error: One or more files not found.")
            return None

        # Load the files
        df_places = pd.read_excel(places_file_path)
        df_activities = pd.read_excel(activities_file_path)

        print(f"Successfully loaded {len(df_places)} records from places Excel file")
        print(f"Successfully loaded {len(df_activities)} records from activities Excel file")

        return df_places, df_activities
    except Exception as e:
        print(f"Error loading Excel files: {str(e)}")
        print(traceback.format_exc())
        return None

def create_prompt(answers, df_places, df_activities):
    """
    Create a structured prompt based on the MCQ answers and available data.
    """
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
{df_places.to_string(index=False)}

Available Activities:
{df_activities.to_string(index=False)}

Please provide a day-by-day itinerary that:
1. Only includes places and activities from the provided lists
2. Fits within the {duration}-day duration
3. Stays within the budget of {budget}
4. Is appropriate for {season} season
5. Includes estimated costs for each activity
Format as a daily schedule with morning, afternoon, and evening activities."""
    return prompt

@app.route('/api/generate-travel-plan', methods=['POST'])
def generate_travel_plan():
    """
    Generate a travel plan based on user input and available data.
    """
    try:
        # Load data
        data = load_data()
        if data is None:
            return jsonify({
                'success': False,
                'error': 'Failed to load data from Excel files'
            }), 500
        
        df_places, df_activities = data

        # Get request data
        data = request.get_json()
        if not data or 'answers' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing answers in request'
            }), 400
        
        answers = data['answers']
        print(f"Received answers: {answers}")  # Debug print
        
        # Validate answers length
        if len(answers) != 6:
            return jsonify({
                'success': False,
                'error': 'Invalid number of answers. Expected 6.'
            }), 400
        
        # Create prompt
        prompt = create_prompt(answers, df_places, df_activities)
        
        # Generate response using Gemini API
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