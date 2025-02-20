from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
import pandas as pd
import os

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure Google Generative AI
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Load Excel files
def load_data():
    try:
        # Adjust the column names based on your Excel files
        places_df = pd.read_excel('places.xlsx', engine='openpyxl')
        activities_df = pd.read_excel('activities.xlsx', engine='openpyxl')
        return places_df, activities_df
    except Exception as e:
        print(f"Error loading Excel files: {e}")
        return None, None

def format_data_for_prompt(df):
    formatted_data = "\nAvailable Places and Activities:\n"
    
    # Group by Category
    for category in df['Category'].unique():
        formatted_data += f"\n{category.upper()}:\n"
        category_places = df[df['Category'] == category]
        
        for _, row in category_places.iterrows():
            formatted_data += f"- {row['Name']}: {row['Description']}\n"
            formatted_data += f"  Location: {row['Address']}\n"
            formatted_data += f"  Hours: {row['open time']} - {row['close time']}\n"
            formatted_data += f"  Entry Fee: {row['Entry Fee']}\n"
            if row['cultural tip']:
                formatted_data += f"  Cultural Tip: {row['cultural tip']}\n"
            formatted_data += "\n"
    
    return formatted_data

@app.route('/api/generate-travel-plan', methods=['POST'])
def generate_travel_plan():
    try:
        # Get data from request
        data = request.get_json()
        
        if not data or 'answers' not in data:
            return jsonify({
                'error': 'Missing required field: answers'
            }), 400
        
        answers = data['answers']
        
        # Load data from Excel file
        places_df, _ = load_data()
        if places_df is None:
            return jsonify({
                'error': 'Error loading data files'
            }), 500
        
        # Format the available data
        available_data = format_data_for_prompt(places_df)
        
        prompt = f"""Create a detailed travel plan using ONLY the places and activities provided in this list. 
        Do not include any places or activities that are not in this list.
        
        {available_data}
        
        Please create the plan following this EXACT format:
        
        ## Destination Overview
        Provide a 2-3 sentence overview focusing on the types of attractions available (historical, entertainment, nature spots, etc.).
        
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
        print(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("Server starting at http://127.0.0.1:5000")
    app.run(debug=True)