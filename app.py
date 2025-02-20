from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
import pandas as pd
import os
import traceback
import logging
from datetime import datetime
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Configure Google Generative AI
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")
genai.configure(api_key=api_key)

def load_data():
    """
    Load places and activities data from Excel files
    """
    try:
        current_dir = os.getcwd()
        places_path = os.path.join(current_dir, 'places.xlsx')
        activities_path = os.path.join(current_dir, 'activities.xlsx')
        
        # Check if files exist
        for file_path in [places_path, activities_path]:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Required file not found: {file_path}")
        
        logger.info(f"Loading files from: {current_dir}")
        logger.info(f"Places path: {places_path}")
        logger.info(f"Activities path: {activities_path}")
        
        # Load both files
        places_df = pd.read_excel(places_path)
        activities_df = pd.read_excel(activities_path)
        
        logger.info("Successfully loaded both files")
        return places_df, activities_df
        
    except Exception as e:
        logger.error(f"Error loading Excel files: {str(e)}")
        logger.error(traceback.format_exc())
        return None, None

def validate_answers(answers):
    """
    Validate the structure and content of user answers
    """
    try:
        if len(answers) != 6:
            return False
        
        # Validate experiences (multiple selection)
        if not isinstance(answers[0], list) or not answers[0]:
            return False
        valid_experiences = [
            "Historical & Cultural", "Adventure & Outdoor", 
            "Food & Culinary", "Nature & Wildlife",
            "Shopping & Entertainment", "Festivals & Events"
        ]
        if not all(exp in valid_experiences for exp in answers[0]):
            return False
            
        # Validate duration
        if not str(answers[1]).isdigit() or int(answers[1]) <= 0:
            return False
            
        # Validate places (multiple selection)
        if not isinstance(answers[2], list) or not answers[2]:
            return False
        valid_places = [
            "Historical Sites", "Museums", "Religious Sites",
            "Hidden Gems", "Adventure Spots", "resorts and beaches",
            "Nile river destinations", "desert landscape"
        ]
        if not all(place in valid_places for place in answers[2]):
            return False
            
        # Validate activities (multiple selection)
        if not isinstance(answers[3], list) or not answers[3]:
            return False
        valid_activities = [
            "Diving, Snorkeling", "Hiking", "Water Sports",
            "Cultural Experience", "Adventure Activity",
            "Relaxation & Wellness", "Desert Safari",
            "Fancy Cafe", "Fancy Restaurant", "Hidden Gems"
        ]
        if not all(activity in valid_activities for activity in answers[3]):
            return False
            
        # Validate season (multiple selection)
        if not isinstance(answers[4], list) or not answers[4]:
            return False
        valid_seasons = ["Spring", "Summer", "Autumn", "Winter"]
        if not all(season in valid_seasons for season in answers[4]):
            return False
            
        # Validate budget
        valid_budgets = ['200egp -1k egp', '1.5egp -2.5 egp', '3k egp -5kegp']
        if not answers[5] or answers[5] not in valid_budgets:
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error in validate_answers: {str(e)}")
        return False

def create_travel_prompt(answers, places_df, activities_df):
    """
    Create a structured prompt for the travel itinerary based on user answers and available data
    """
    experiences = ', '.join(answers[0]) if isinstance(answers[0], list) else answers[0]
    duration = answers[1]
    places = ', '.join(answers[2]) if isinstance(answers[2], list) else answers[2]
    activities = ', '.join(answers[3]) if isinstance(answers[3], list) else answers[3]
    season = ', '.join(answers[4]) if isinstance(answers[4], list) else answers[4]
    budget = answers[5]

    # Filter relevant places and activities
    filtered_places = places_df[places_df['type'].isin(places.split(', '))]
    filtered_activities = activities_df[activities_df['type'].isin(activities.split(', '))]

    prompt = f"""Create a detailed {duration}-day travel itinerary based on the following preferences:

Selected Experiences: {experiences}
Places of Interest: {places}
Preferred Activities: {activities}
Season: {season}
Budget Range: {budget}

Available Places:
{filtered_places.to_string(index=False)}

Available Activities:
{filtered_activities.to_string(index=False)}

Please provide a comprehensive day-by-day itinerary that:
1. Only includes places and activities from the provided lists
2. Fits within the {duration}-day duration
3. Stays within the budget of {budget}
4. Is appropriate for {season} season
5. Includes estimated costs for each activity
6. Considers the selected experiences: {experiences}
7. Balances different types of activities throughout the day

Format the response as follows:
Day 1:
- Morning: [Activity/Place] (Estimated cost: X EGP)
- Afternoon: [Activity/Place] (Estimated cost: X EGP)
- Evening: [Activity/Place] (Estimated cost: X EGP)

[Continue for each day]

Total Estimated Budget: X EGP"""

    return prompt

def format_travel_plan(response_text):
    """
    Format the travel plan response
    """
    try:
        formatted_plan = {
            'daily_schedule': response_text,
            'generated_at': datetime.now().isoformat(),
            'version': '1.0'
        }
        return formatted_plan
    except Exception as e:
        logger.error(f"Error formatting travel plan: {str(e)}")
        return {'error': str(e)}

@app.route('/api/generate-travel-plan', methods=['POST'])
@limiter.limit("10 per minute")
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
        logger.info(f"Received answers: {answers}")

        # Validate answers
        if not validate_answers(answers):
            return jsonify({
                'success': False,
                'error': 'Invalid answers format or content'
            }), 400

        # Create prompt
        prompt = create_travel_prompt(answers, places_df, activities_df)

        # Generate response
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)

        # Format the response
        formatted_plan = format_travel_plan(response.text)

        return jsonify({
            'success': True,
            'travel_plan': formatted_plan,
            'selected_preferences': {
                'experiences': answers[0],
                'duration': answers[1],
                'places': answers[2],
                'activities': answers[3],
                'season': answers[4],
                'budget': answers[5]
            }
        }), 200

    except Exception as e:
        logger.error(f"Error in generate_travel_plan: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    logger.info("Starting server...")
    logger.info(f"Current directory: {os.getcwd()}")
    app.run(debug=True)