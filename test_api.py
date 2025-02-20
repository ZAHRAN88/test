import requests

def test_travel_plan():
    url = 'http://127.0.0.1:5000/api/generate-travel-plan'
    
    payload = {
        'answers': [
            'Cairo',
            '3 days',
            'Historical sites',
            'Cultural experiences',
            'Morning visits preferred'
        ]
    }
    
    print("Sending request to:", url)
    print("With payload:", payload)
    
    try:
        response = requests.post(url, json=payload)
        print(f"Response status code: {response.status_code}")
        
        try:
            data = response.json()
            if response.status_code == 200 and data.get('success'):
                print("\nTravel Plan:")
                print(data['travel_plan'])
            else:
                print("\nError in response:")
                print(f"Status code: {response.status_code}")
                print(f"Error message: {data.get('error', 'No error message provided')}")
        except ValueError as e:
            print("Error parsing JSON response:", e)
            print("Raw response:", response.text)
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure the Flask app is running.")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    test_travel_plan()