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
    Load data from the Excel file.
    Returns a Pandas DataFrame if successful, otherwise None.
    """
    try:
        # Get the absolute path of the current directory
        current_dir = os.getcwd()
        file_path = os.path.join(current_dir, 'places.xlsx')  # Adjust the path if necessary
        
        # Print file path for debugging
        print(f"Attempting to load file from: {file_path}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"Error: File not found at {file_path}")
            return None
            
        # Load the file
        df = pd.read_excel(file_path)
        print(f"Successfully loaded {len(df)} records from Excel file")
        return df
    except Exception as e:
        print(f"Error loading Excel file: {str(e)}")
        print(traceback.format_exc())
        return None

def create_prompt(answers, df):
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
Available Places and Activities:
{df.to_string(index=False)}
Please provide a day-by-day itinerary that:
1. Only includes places and activities from the provided list
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
        df = load_data()
        if df is None:
            return jsonify({
                'success': False,
                'error': 'Failed to load data from Excel file'
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
        prompt = create_prompt(answers, df)
        
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