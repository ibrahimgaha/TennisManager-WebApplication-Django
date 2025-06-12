#!/usr/bin/env python
"""
Simple test script to verify anonymous reservations work correctly.
This script tests the make_reservation endpoint without authentication.
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://127.0.0.1:8000"
MAKE_RESERVATION_URL = f"{BASE_URL}/reservations/"

def test_anonymous_reservation():
    """Test making a reservation without authentication"""
    
    # Sample reservation data
    reservation_data = {
        "terrain_id": 1,  # Assuming terrain with ID 1 exists
        "date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),  # Tomorrow
        "start_time": "14:00",
        "end_time": "15:00"
    }
    
    print("Testing anonymous reservation...")
    print(f"URL: {MAKE_RESERVATION_URL}")
    print(f"Data: {json.dumps(reservation_data, indent=2)}")
    
    try:
        # Make the request without any authentication headers
        response = requests.post(
            MAKE_RESERVATION_URL,
            json=reservation_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"\nResponse Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")
        
        if response.status_code == 200:
            response_data = response.json()
            print("\n✅ SUCCESS: Anonymous reservation created successfully!")
            print(f"User: {response_data['reservation']['user']}")
            print(f"Terrain: {response_data['reservation']['terrain']}")
            print(f"Date: {response_data['reservation']['date']}")
            print(f"Time: {response_data['reservation']['start_time']} - {response_data['reservation']['end_time']}")
            print(f"Total Price: {response_data['reservation']['total_price']}")
        else:
            print(f"\n❌ FAILED: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to the server. Make sure Django is running on http://127.0.0.1:8000")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")

if __name__ == "__main__":
    test_anonymous_reservation()
