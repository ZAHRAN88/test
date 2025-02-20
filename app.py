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
        current_dir = os.getcwd()
        print(f"Current working directory: {current_dir}")

        # Define file paths
        places_path = os.path.join(current_dir, 'places.xlsx')
        activities_path = os.path.join(current_dir, 'activities.xlsx')
        
        print(f"Looking for files at:")
        print(f"Places: {places_path}")
        print(f"Activities: {activities_path}")

        # Check if files exist
        if not os.path.exists(places_path):
            raise FileNotFoundError(f"Places file not found at: {places_path}")
        if not os.path.exists(activities_path):
            raise FileNotFoundError(f"Activities file not found at: {activities_path}")

        # Load the files
        print("Loading places file...")
        places_df = pd.read_excel(places_path)
        print(f"Places file loaded successfully with {len(places_df)} rows")

        print("Loading activities file...")
        activities_df = pd.read_excel(activities_path)
        print(f"Activities file loaded successfully with {len(activities_df)} rows")

        return places_df, activities_df

    except FileNotFoundError as e:
        print(f"File not found error: {str(e)}")
        return None, None
    except Exception as e:
        print(f"Error loading Excel files: {str(e)}")
        print("Full error traceback:")
        print(traceback.format_exc())
        return None, None

@app.route('/api/generate-travel-plan', methods=['POST'])
def generate_travel_plan():
    try:
        # Load data first
        places_df, activities_df = load_data()
        if places_df is None or activities_df is None:
            return jsonify({
                'success': False,
                'error': 'Failed to load Excel files. Check server logs for details.'
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

        # Create a simple test response first
        return jsonify({
            'success': True,
            'travel_plan': f"Test plan for {answers[0]} for {answers[1]}"
        }), 200

    except Exception as e:
        print(f"Error in generate_travel_plan: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("\nStarting server...")
    print(f"Current directory: {os.getcwd()}")
    
    # Test loading files before starting server
    print("\nTesting file loading...")
    places_df, activities_df = load_data()
    if places_df is not None and activities_df is not None:
        print("Files loaded successfully!")
        print(f"Places: {len(places_df)} rows")
        print(f"Activities: {len(activities_df)} rows")
        app.run(debug=True)
    else:
        print("\nError: Could not load required files. Please check the file paths and names.")