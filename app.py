from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
import pandas as pd
import os
import traceback  # Add this for better error tracking

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
        file_path = os.path.join(current_dir, 'places.xlsx')
        
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
        print(traceback.format_exc())  # Print full error traceback
        return None

@app.route('/api/generate-travel-plan', methods=['POST'])
def generate_travel_plan():
    try:
        # Load data first
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
                'error': 'Missing required field: answers'
            }), 400

        answers = data['answers']
        print(f"Received answers: {answers}")  # Debug print

        # Create simple prompt for testing
        prompt = f"""Create a travel plan for {answers[0]} for {answers[1]}.
        Include only places from the provided list."""

        # Generate response
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)

        return jsonify({
            'success': True,
            'travel_plan': response.text
        }), 200

    except Exception as e:
        print(f"Error in generate_travel_plan: {str(e)}")
        print(traceback.format_exc())  # Print full error traceback
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("Starting server...")
    print(f"Current directory: {os.getcwd()}")
    app.run(debug=True)