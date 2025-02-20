import requests

def get_travel_plan():
    url = 'http://127.0.0.1:5000/api/generate-travel-plan'
    
    # Example preferences
    preferences = {
        'answers': [
            'Historical sites and museums',
            '3 days',
            'Prefer morning visits',
            'Interested in cultural experiences'
        ]
    }
    
    try:
        response = requests.post(url, json=preferences)
        response.raise_for_status()
        
        data = response.json()
        
        if data['success']:
            print("\nTravel Plan Generated Successfully!")
            print("\n" + data['travel_plan'])
        else:
            print("Error:", data.get('error', 'Unknown error occurred'))
            
    except requests.exceptions.RequestException as e:
        print("Error making request:", e)

if __name__ == "__main__":
    get_travel_plan()