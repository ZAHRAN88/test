import requests

def get_travel_plan(destination, duration, preferences):
    url = 'http://127.0.0.1:5000/api/generate-travel-plan'
    
    answers = [destination, duration, preferences]
    
    payload = {
        'answers': answers
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        data = response.json()
        
        if data['success']:
            print("\nTravel Plan Generated Successfully!")
            print("\n" + data['travel_plan'])
        else:
            print("Error:", data.get('error', 'Unknown error occurred'))
            
    except requests.exceptions.RequestException as e:
        print("Error making request:", e)

# Example usage
if __name__ == "__main__":
    print("Travel Plan Generator")
    print("--------------------")
    
    destination = input("Enter destination: ")
    duration = input("Enter duration (e.g., 3 days, 1 week): ")
    preferences = input("Enter preferences (e.g., cultural, adventure, relaxation): ")
    
    get_travel_plan(destination, duration, preferences)