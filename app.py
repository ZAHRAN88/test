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
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Add root route (this was missing before)
@app.route('/')
def index():
    return jsonify({
        "status": "online",
        "message": "Welcome to Travel Plan API",
        "endpoints": {
            "/": "This welcome message",
            "/test": "Test endpoint",
            "/api/generate-travel-plan": "Generate travel plan (POST)"
        }
    })

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"message": "API is working!"})

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

        # Generate response
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        return jsonify({
            'success': True,
            'travel_plan': response.text
        }), 200

    except Exception as e:
        print(f"Error: {str(e)}")  # This will show in your terminal
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
    print("Server starting at http://127.0.0.1:5000")
    print("Available endpoints:")
    print("  GET  / - Welcome message")
    print("  GET  /test - Test endpoint")
    print("  POST /api/generate-travel-plan - Generate travel plan")
    app.run(debug=True)