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
    """
    try:
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Define file paths
        places_path = os.path.join(script_dir, 'data', 'places.xlsx')
        activities_path = os.path.join(script_dir, 'data', 'activities.xlsx')
        
        print(f"Loading data from:")
        print(f"Places path: {places_path}")
        print(f"Activities path: {activities_path}")

        # Load the files
        try:
            places_df = pd.read_excel(places_path)
            activities_df = pd.read_excel(activities_path)
            print("Successfully loaded both files")
            return places_df, activities_df
        except Exception as e:
            print(f"Error reading Excel files: {str(e)}")
            return None, None

    except Exception as e:
        print(f"Error in load_data: {str(e)}")
        traceback.print_exc()
        return None, None

def create_prompt(answers, places_df, activities_df):
    """
    Create a structured prompt based on the MCQ answers and available data.
    """
    experiences = answers[0]
    duration = answers[1]
    places = answers[2]
    activities = answers[3]
    season = answers[4]
    budget = answers[5]
    
    # Create the combined data string
    places_data = places_df.to_string(index=False) if places_df is not None else "No places data available"
    activities_data = activities_df.to_string(index=False) if activities_df is not None else "No activities data available"
    
    prompt = f"""Create a {duration}-day travel itinerary based on the following preferences:

Selected Experiences: {experiences}
Places of Interest: {places}
Preferred Activities: {activities}
Season: {season}
Budget Range: {budget}

Available Places:
{places_data}

Available Activities:
{activities_data}

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
        places_df, activities_df = load_data()
        if places_df is None and activities_df is None:
            return jsonify({
                'success': False,
                'error': 'Failed to load data files'
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
        
        # Validate answers length
        if len(answers) != 6:
            return jsonify({
                'success': False,
                'error': 'Invalid number of answers. Expected 6.'
            }), 400
        
        # Create prompt
        prompt = create_prompt(answers, places_df, activities_df)
        
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