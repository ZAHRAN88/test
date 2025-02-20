from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
import pandas as pd
import os
import traceback
import json

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
        current_dir = os.getcwd()
        places_path = os.path.join(current_dir, 'places.xlsx')
        activities_path = os.path.join(current_dir, 'activities.xlsx')
        
        print(f"Loading files from: {current_dir}")
        print(f"Places path: {places_path}")
        print(f"Activities path: {activities_path}")
        
        places_df = pd.read_excel(places_path)
        activities_df = pd.read_excel(activities_path)
        
        print("Successfully loaded both files")
        return places_df, activities_df
        
    except Exception as e:
        print(f"Error loading Excel files: {str(e)}")
        print(traceback.format_exc())
        return None, None

def format_list_items(items):
    """Helper function to format list items for the prompt"""
    if isinstance(items, list):
        return ', '.join(items)
    return str(items)

def create_travel_prompt(answers, places_df, activities_df):
    """
    Create a structured prompt handling multiple selections for each preference.
    """
    experiences = format_list_items(answers[0])
    duration = answers[1]
    places = format_list_items(answers[2])
    activities = format_list_items(answers[3])
    season = answers[4]
    budget = answers[5]

    prompt = f"""Create a detailed {duration}-day travel itinerary based on these multiple preferences:

Selected Experiences: {experiences}
Places of Interest: {places}
Preferred Activities: {activities}
Season: {season}
Budget Range: {budget}

Available Places:
{places_df.to_string(index=False)}

Available Activities:
{activities_df.to_string(index=False)}

Requirements:
1. Only use places and activities from the provided lists
2. Create a {duration}-day schedule
3. Stay within {budget} budget
4. Plan should be suitable for {season}
5. Include cost estimates for each activity
6. Try to incorporate as many selected preferences as possible
7. Ensure activities match with the selected places

Format the response as JSON:
{{
    "itinerary": {{
        "total_days": {duration},
        "total_budget": "{budget}",
        "days": [
            {{
                "day": 1,
                "morning": {{
                    "place": "place_name",
                    "activity": "activity_name",
                    "cost": "amount"
                }},
                "afternoon": {{
                    "place": "place_name",
                    "activity": "activity_name",
                    "cost": "amount"
                }},
                "evening": {{
                    "place": "place_name",
                    "activity": "activity_name",
                    "cost": "amount"
                }}
            }}
        ]
    }}
}}"""

    return prompt

def parse_response(response_text):
    """
    Parse and validate the AI response
    """
    try:
        # Clean up the response if needed
        cleaned_response = response_text.strip()
        
        # Find the JSON part in the response
        start_idx = cleaned_response.find('{')
        end_idx = cleaned_response.rfind('}') + 1
        if start_idx >= 0 and end_idx > start_idx:
            json_str = cleaned_response[start_idx:end_idx]
            return json.loads(json_str)
        
        return cleaned_response
        
    except Exception as e:
        print(f"Error parsing response: {str(e)}")
        return response_text

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
        print(f"Received answers: {answers}")

        # Validate answers
        if len(answers) != 6:
            return jsonify({
                'success': False,
                'error': 'Invalid number of answers'
            }), 400

        # Create prompt
        prompt = create_travel_prompt(answers, places_df, activities_df)

        try:
            # Generate response
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model.generate_content(prompt)
            
            # Parse and format the response
            formatted_response = parse_response(response.text)

            return jsonify({
                'success': True,
                'travel_plan': formatted_response
            }), 200

        except Exception as e:
            error_message = str(e)
            if "quota" in error_message.lower():
                return jsonify({
                    'success': False,
                    'error': 'API quota exceeded. Please try again later.'
                }), 429
            else:
                return jsonify({
                    'success': False,
                    'error': f'Error generating travel plan: {error_message}'
                }), 500

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