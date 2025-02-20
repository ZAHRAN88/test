def load_data():
    """
    Load data from both Excel files.
    Returns two Pandas DataFrames if successful, otherwise None.
    """
    try:
        # Get the absolute path of the current directory
        current_dir = os.getcwd()
        places_path = os.path.join(current_dir, 'places.xlsx')
        activities_path = os.path.join(current_dir, 'activities.xlsx')
        
        # Print file paths for debugging
        print(f"Attempting to load files from:")
        print(f"Places: {places_path}")
        print(f"Activities: {activities_path}")
        
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
        
        print(f"Successfully loaded {len(places_df)} places and {len(activities_df)} activities")
        return places_df, activities_df
    except Exception as e:
        print(f"Error loading Excel files: {str(e)}")
        print(traceback.format_exc())
        return None, None

def create_prompt(answers, places_df, activities_df):
    """
    Create a structured prompt based on the MCQ answers and available data.
    """
    experiences = answers[0]
    duration = answers[1]
    places = answers[2]
    activities = answers[3]
    season = answers[4]
    budget = answers[5]
    
    prompt = f"""Create a {duration}-day travel itinerary based on the following preferences:

Selected Experiences: {experiences}
Places of Interest: {places}
Preferred Activities: {activities}
Season: {season}
Budget Range: {budget}

Available Places:
{places_df.to_string(index=False)}

Available Activities:
{activities_df.to_string(index=False)}

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
    """
    Generate a travel plan based on user input and available data.
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
        print(f"Received answers: {answers}")  # Debug print
        
        # Validate answers length
        if len(answers) != 6:
            return jsonify({
                'success': False,
                'error': 'Invalid number of answers. Expected 6.'
            }), 400
        
        # Create prompt
        prompt = create_prompt(answers, places_df, activities_df)
        
        # Generate response using Gemini API
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