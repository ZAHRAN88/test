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
    """
    Load data from Excel files
    """
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
    """
    Format list items for the prompt
    """
    if isinstance(items, list):
        return ', '.join(items)
    return str(items)

def create_travel_prompt(answers, places_df, activities_df):
    """
    Create structured prompt for travel itinerary
    """
    experiences = format_list_items(answers[0])
    duration = answers[1]
    places = format_list_items(answers[2])
    activities = format_list_items(answers[3])
    season = answers[4]
    budget = answers[5]

    prompt = f"""Create a {duration}-day travel itinerary based on these preferences:

User Preferences:
- Experiences: {experiences}
- Places: {places}
- Activities: {activities}
- Season: {season}
- Budget: {budget}

Available Places Data:
{places_df.to_string(index=False)}

Available Activities Data:
{activities_df.to_string(index=False)}

Generate a response in exactly this JSON format:
{{
    "success": true,
    "travel_plan": {{
        "itinerary": {{
            "days": [
                {{
                    "day1": {{
                        "place": {{
                            "name": "place_name",
                            "desc": "place_description",
                            "entryCost": "cost_in_EGP",
                            "duration": "duration_in_hours"
                        }},
                        "activity": {{
                            "name": "activity_name",
                            "desc": "activity_description",
                            "entryCost": "cost_in_EGP",
                            "duration": "duration_in_hours"
                        }}
                    }}
                }}
            ],
            "total_budget": "{budget}",
            "total_days": {duration}
        }}
    }}
}}

Requirements:
1. Use only places and activities from the provided data
2. Each day must have exactly one place and one matching activity
3. Include accurate descriptions, costs, and durations
4. Stay within the total budget of {budget}
5. All activities must be suitable for {season}
6. Follow the exact JSON format shown above
7. All costs must be in EGP
8. Duration must be in hours
9. Ensure place and activity combinations make logical sense"""

    return prompt

def parse_response(response_text):
    """
    Parse and validate the AI response
    """
    try:
        # Clean up the response
        cleaned_response = response_text.strip()
        
        # Extract JSON from response
        start_idx = cleaned_response.find('{')
        end_idx = cleaned_response.rfind('}') + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            json_str = cleaned_response[start_idx:end_idx]
            parsed_json = json.loads(json_str)
            
            # Validate JSON structure
            if not all(key in parsed_json for key in ['success', 'travel_plan']):
                raise ValueError("Invalid response format - missing required keys")
            
            # Validate itinerary structure
            itinerary = parsed_json.get('travel_plan', {}).get('itinerary', {})
            if not all(key in itinerary for key in ['days', 'total_budget', 'total_days']):
                raise ValueError("Invalid itinerary format - missing required fields")
            
            return parsed_json
            
        raise ValueError("No valid JSON found in response")
        
    except Exception as e:
        print(f"Error parsing response: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to parse response: {str(e)}"
        }

@app.route('/api/generate-travel-plan', methods=['POST'])
def generate_travel_plan():
    """
    Generate travel plan based on user preferences
    """
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
                'error': 'Invalid number of answers. Expected 6 items.'
            }), 400

        try:
            # Create prompt and generate response
            prompt = create_travel_prompt(answers, places_df, activities_df)
            model = genai.GenerativeModel('gemini-1.0-pro')
            
            generation_config = {
                'temperature': 0.7,
                'top_p': 0.8,
                'top_k': 40,
                'max_output_tokens': 2048,
            }

            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # Parse and validate response
            parsed_response = parse_response(response.text)
            
            if not parsed_response.get('success'):
                return jsonify(parsed_response), 400

            return jsonify(parsed_response), 200

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

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        'status': 'healthy',
        'message': 'Service is running'
    }), 200

if __name__ == '__main__':
    print("Starting server...")
    print(f"Current directory: {os.getcwd()}")
    app.run(debug=True)