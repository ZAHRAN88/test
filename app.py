from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure Google Generative AI
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError("No API key found. Make sure GEMINI_API_KEY is set in .env file")

genai.configure(api_key=api_key)

# Add a root route
@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the Travel Plan API"})

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"message": "API is working!"})

@app.route('/api/generate-travel-plan', methods=['POST', 'OPTIONS'])
def generate_travel_plan():
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return '', 200

    try:
        # Get data from request
        data = request.get_json()
        print("Received data:", data)  # Debug print
        
        if not data or 'answers' not in data:
            return jsonify({
                'error': 'Missing required field: answers'
            }), 400
        
        answers = data['answers']
        print("Answers:", answers)  # Debug print
        
        if not isinstance(answers, list):
            return jsonify({
                'error': 'Answers must be a list'
            }), 400

        # Create prompt
        prompt = f"""Create a detailed travel plan following this EXACT format:
        
        ## Destination Overview
        Provide a 2-3 sentence overview of the destination.
        
        ## Daily Itinerary
        Day 1: [Title]
        - [Morning activity]
        - [Afternoon activity]
        - [Evening activity]
        
        Day 2: [Title]
        - [Morning activity]
        - [Afternoon activity]
        - [Evening activity]
        
        Day 3: [Title]
        - [Morning activity]
        - [Afternoon activity]
        - [Evening activity]
        
        ## Essential Packing List
        - Item 1
        - Item 2
        - Item 3
        - Item 4
        - Item 5
        - Item 6
        
        ## Budget Recommendations
        - Accommodation: [cost range]
        - Daily food budget: [cost range]
        - Activities: [cost range]
        - Transportation: [cost range]
        - Total estimated budget: [amount]
        
        ## Cultural Notes
        - Note 1
        - Note 2
        - Note 3
        - Note 4
        
        ## Transportation Guide
        - Getting there: [details]
        - Local transportation: [details]
        - Best ways to move around: [details]
        
        Based on these details: {", ".join(answers)}"""

        print("Generated prompt:", prompt)  # Debug print

        # Generate response
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        return jsonify({
            'success': True,
            'travel_plan': response.text
        }), 200

    except Exception as e:
        print(f"Error occurred: {str(e)}")  # Debug print
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Add CORS headers
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    print("Server starting...")
    print("Available routes:")
    print("  - GET  /")
    print("  - GET  /test")
    print("  - POST /api/generate-travel-plan")
    print("\nServer will run on: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)