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
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Load both Excel files
        places_path = os.path.join(current_dir, 'places.xlsx')
        activities_path = os.path.join(current_dir, 'activities.xlsx')
        
        print(f"Attempting to load files from:\nPlaces: {places_path}\nActivities: {activities_path}")
        
        # Check if files exist
        if not os.path.exists(places_path):
            print(f"Error: Places file not found at {places_path}")
            return None, None
        if not os.path.exists(activities_path):
            print(f"Error: Activities file not found at {activities_path}")
            return None, None
            
        # Load the files
        places_df = pd.read_excel(places_path)
        activities_df = pd.read_excel(activities_path)
        
        print(f"Successfully loaded:\n{len(places_df)} places\n{len(activities_df)} activities")
        return places_df, activities_df
    except Exception as e:
        print(f"Error loading Excel files: {str(e)}")
        print(traceback.format_exc())
        return None, None

def format_places_data(df):
    formatted_data = "\nAVAILABLE PLACES:\n"
    
    # Group by Category
    categories = df['Category'].unique()
    for category in categories:
        formatted_data += f"\n{category.upper()}:\n"
        category_places = df[df['Category'] == category]
        
        for _, row in category_places.iterrows():
            formatted_data += f"- {row['Name']}\n"
            formatted_data += f"  Description: {row['Description']}\n"
            formatted_data += f"  Location: {row['Address']}\n"
            formatted_data += f"  Hours: {row['open time']} - {row['close time']}\n"
            formatted_data += f"  Entry Fee: {row['Entry Fee']}\n"
            if pd.notna(row['cultural tip']):
                formatted_data += f"  Cultural Tip: {row['cultural tip']}\n"
            formatted_data += "\n"
    
    return formatted_data

def format_activities_data(df):
    formatted_data = "\nAVAILABLE ACTIVITIES:\n"
    
    # Group by Category if it exists in your activities file
    # Modify this according to your activities Excel file structure
    for _, row in df.iterrows():
        formatted_data += f"- {row['Name']}\n"
        if 'Description' in df.columns:
            formatted_data += f"  Description: {row['Description']}\n"
        if 'Duration' in df.columns:
            formatted_data += f"  Duration: {row['Duration']}\n"
        if 'Entry Fee' in df.columns:
            formatted_data += f"  Entry Fee: {row['Entry Fee']}\n"
        formatted_data += "\n"
    
    return formatted_data

@app.route('/api/generate-travel-plan', methods=['POST'])
def generate_travel_plan():
    try:
        # Load data first
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
                'error': 'Missing required field: answers'
            }), 400

        answers = data['answers']
        print(f"Received answers: {answers}")

        # Format both datasets
        places_data = format_places_data(places_df)
        activities_data = format_activities_data(activities_df)

        # Create prompt
        prompt = f"""Create a detailed travel plan using ONLY the places and activities provided in these lists.
        Do not include any places or activities that are not in these lists.
        
        {places_data}
        
        {activities_data}
        
        Please create the plan following this EXACT format:
        
        ## Destination Overview
        Provide a 2-3 sentence overview focusing on the types of attractions available.
        
        ## Daily Itinerary
        Create a daily plan that:
        - Respects the opening and closing times of each place
        - Groups nearby locations together to minimize travel time
        - Includes cultural tips for each place
        - Mentions entry fees
        
        Day 1: [Title]
        - Morning: [Place/Activity] (include opening time and cultural tip)
        - Afternoon: [Place/Activity] (include cultural tip)
        - Evening: [Place/Activity] (include closing time and cultural tip)
        
        [Continue for requested number of days...]
        
        ## Essential Tips
        - List relevant cultural tips from the data
        - Include dress code requirements
        - Mention timing considerations
        
        ## Budget Breakdown
        - List all entry fees from the selected places
        - Total cost for attractions
        
        ## Practical Information
        - Opening and closing times for each place
        - Location details
        - Cultural considerations
        
        Based on these preferences: {", ".join(answers)}
        
        Important: Only include places and activities that are explicitly listed in the provided data."""

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