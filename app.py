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

# Define the MCQ questions
MCQ_QUESTIONS = {
    "experiences": [
        "Historical & Cultural",
        "Adventure & Outdoor",
        "Food & Culinary",
        "Nature & Wildlife",
        "Shopping & Entertainment",
        "Festivals & Events"
    ],
    "places": [
        "Historical Sites",
        "Museums",
        "Religious Sites",
        "Hidden Gems",
        "Adventure Spots",
        "resorts and beaches",
        "Nile river destinations",
        "desert landscape"
    ],
    "activities": [
        "Diving, Snorkeling",
        "Hiking",
        "Water Sports",
        "Cultural Experience",
        "Adventure Activity",
        "Relaxation & Wellness",
        "Desert Safari",
        "Fancy Cafe",
        "Fancy Restaurant",
        "Hidden Gems"
    ],
    "seasons": [
        "Spring",
        "Summer",
        "Autumn",
        "Winter"
    ],
    "budget_ranges": [
        "200Egp- 1k egp",
        "1.5k - 2.5k",
        "3k - 5k"
    ]
}

def load_data():
    try:
        current_dir = os.getcwd()
        places_path = os.path.join(current_dir, 'places.xlsx')
        activities_path = os.path.join(current_dir, 'activities.xlsx')

        print(f"Attempting to load files from:")
        print(f"Places: {places_path}")
        print(f"Activities: {activities_path}")

        if not os.path.exists(places_path) or not os.path.exists(activities_path):
            print("Error: One or both data files not found")
            return None, None

        places_df = pd.read_excel(places_path)
        activities_df = pd.read_excel(activities_path)

        return places_df, activities_df

    except Exception as e:
        print(f"Error loading data: {str(e)}")
        print(traceback.format_exc())
        return None, None

def validate_answers(answers):
    """
    Validate the user's answers against the MCQ options
    """
    if not isinstance(answers, list) or len(answers) != 6:  # 5 questions + duration
        return False, "Invalid answer format"

    # Validate experiences
    if not all(exp in MCQ_QUESTIONS["experiences"] for exp in answers[0].split(',')):
        return False, "Invalid experience selection"

    # Validate duration (should be a number)
    try:
        duration = int(answers[1])
        if duration <= 0:
            return False, "Duration must be positive"
    except:
        return False, "Invalid duration"

    # Validate places
    if not all(place in MCQ_QUESTIONS["places"] for place in answers[2].split(',')):
        return False, "Invalid place selection"

    # Validate activities
    if not all(activity in MCQ_QUESTIONS["activities"] for activity in answers[3].split(',')):
        return False, "Invalid activity selection"

    # Validate season
    if answers[4] not in MCQ_QUESTIONS["seasons"]:
        return False, "Invalid season selection"

    # Validate budget
    if answers[5] not in MCQ_QUESTIONS["budget_ranges"]:
        return False, "Invalid budget selection"

    return True, None

def create_prompt(answers, places_df, activities_df):
    """
    Create a structured prompt based on the MCQ answers and available data
    """
    experiences = answers[0].split(',')
    duration = answers[1]
    places = answers[2].split(',')
    activities = answers[3].split(',')
    season = answers[4]
    budget = answers[5]

    # Filter relevant data
    filtered_places = places_df[places_df['Type'].isin(places)]
    filtered_activities = activities_df[activities_df['Type'].isin(activities)]

    prompt = f"""Create a {duration}-day travel itinerary based on the following preferences:

Selected Experiences: {', '.join(experiences)}
Places of Interest: {', '.join(places)}
Preferred Activities: {', '.join(activities)}
Season: {season}
Budget Range: {budget}

Available Places:
{filtered_places[['Name', 'Description', 'Location']].to_string(index=False)}

Available Activities:
{filtered_activities[['Name', 'Description', 'Duration']].to_string(index=False)}

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
    try:
        # Load data
        places_df, activities_df = load_data()
        if places_df is None or activities_df is None:
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
        
        # Validate answers
        is_valid, error_message = validate_answers(answers)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_message
            }), 400

        # Create prompt
        prompt = create_prompt(answers, places_df, activities_df)

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