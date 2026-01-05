"""
Example: How to Integrate data.gov API with Your Flask App

This file shows how to update your main.py to use the data.gov API
instead of directly calling individual APIs.
"""

# ============================================================================
# OPTION 1: Using data.gov API for Food Nutrition Data
# ============================================================================

from datagov_api import get_datagov_client
import os

# Example 1: Search for food nutrition data through data.gov
def search_food_via_datagov(food_name: str):
    """
    Search for food using the data.gov API gateway.
    
    This demonstrates the recommended approach:
    1. Initialize client with your API key
    2. Make authenticated requests using X-Api-Key header
    3. Handle responses and errors appropriately
    """
    
    # Get the data.gov API client (uses X-Api-Key header - recommended)
    client = get_datagov_client()
    
    # Example: Search through USDA FoodData Central via data.gov
    # Note: Actual endpoint depends on how data.gov routes the request
    response = client.make_request(
        endpoint='https://api.nal.usda.gov/fdc/v1/foods/search',
        params={
            'query': food_name,
            'pageSize': 10
        }
    )
    
    if response:
        print(f"Found {len(response.get('foods', []))} foods matching '{food_name}'")
        return response
    else:
        print("Error searching for food. Check API key and rate limits.")
        return None


# Example 2: Get detailed nutrition information
def get_nutrition_via_datagov(fdc_id: str):
    """
    Get detailed nutrition information for a food using data.gov API.
    """
    
    client = get_datagov_client()
    
    response = client.make_request(
        endpoint=f'https://api.nal.usda.gov/fdc/v1/food/{fdc_id}'
    )
    
    if response:
        nutrients = response.get('foodNutrients', [])
        print(f"Food: {response.get('description')}")
        print(f"Found {len(nutrients)} nutrients")
        return response
    else:
        return None


# ============================================================================
# OPTION 2: How to Update Your Existing main.py Functions
# ============================================================================

# BEFORE (Current implementation):
"""
def search_usda_food(food_name):
    try:
        params = {
            'query': food_name,
            'pageSize': 10,
            'api_key': USDA_API_KEY
        }
        response = requests.get(f"{USDA_API_URL}/foods/search", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error searching USDA API: {e}")
        return None
"""

# AFTER (Using data.gov API):
def search_usda_food_datagov(food_name):
    """
    IMPROVED VERSION: Uses data.gov API client with proper authentication.
    """
    client = get_datagov_client()
    
    # The data.gov client handles:
    # ✓ X-Api-Key header authentication (recommended)
    # ✓ Rate limit checking
    # ✓ Error handling and logging
    # ✓ Timeout management
    # ✓ Proper error codes (API_KEY_MISSING, OVER_RATE_LIMIT, etc.)
    
    response = client.make_request(
        endpoint='https://api.nal.usda.gov/fdc/v1/foods/search',
        params={
            'query': food_name,
            'pageSize': 10
        }
    )
    
    return response


# ============================================================================
# OPTION 3: Fallback to Query Parameter (if header doesn't work)
# ============================================================================

def search_usda_food_query_param(food_name):
    """
    Alternative method using query parameter for API key.
    Use only if X-Api-Key header method fails.
    """
    client = get_datagov_client()
    
    response = client.make_request(
        endpoint='https://api.nal.usda.gov/fdc/v1/foods/search',
        use_query_param=True,  # Pass API key as query parameter instead
        params={
            'query': food_name,
            'pageSize': 10
        }
    )
    
    return response


# ============================================================================
# OPTION 4: Complete Flask Route Integration
# ============================================================================

# Add this to your main.py Flask app:

from flask import Flask, jsonify

# Example Flask route using data.gov API
"""
@app.route('/api/search-food', methods=['POST'])
def search_food():
    # Get food name from request
    food_name = request.json.get('food_name')
    
    if not food_name:
        return jsonify({'error': 'food_name required'}), 400
    
    # Use data.gov API client
    client = get_datagov_client()
    
    try:
        # Search for food
        result = client.make_request(
            endpoint='https://api.nal.usda.gov/fdc/v1/foods/search',
            params={
                'query': food_name,
                'pageSize': 10
            }
        )
        
        if result is None:
            return jsonify({
                'error': 'Failed to search. Check API key and rate limits.'
            }), 500
        
        return jsonify({
            'success': True,
            'foods': result.get('foods', []),
            'total': result.get('totalHits', 0)
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500
"""


# ============================================================================
# SETUP INSTRUCTIONS
# ============================================================================

"""
1. Get your API key:
   - Visit: https://api.data.gov/
   - Sign up and copy your API key

2. Set environment variable:
   On Windows PowerShell:
   $env:DATA_GOV_API_KEY = 'your-key-here'

3. Update your main.py:
   from datagov_api import get_datagov_client
   
   client = get_datagov_client()
   response = client.make_request(endpoint='...', params={...})

4. Test your setup:
   python datagov_api.py
"""


# ============================================================================
# QUICK REFERENCE
# ============================================================================

"""
DataGovAPIClient Methods:

1. make_request(endpoint, method='GET', use_query_param=False, **kwargs)
   - Main method for making API requests
   - Handles authentication automatically
   - Supports X-Api-Key header (default) or query parameter
   
2. test_connection()
   - Test if API connection is working
   - Returns True/False

3. search_food_nutrition(query, api_service='NREL', **kwargs)
   - Search for food/nutrition data
   - Can specify different API services

Common Error Codes:
- API_KEY_MISSING (403): Add X-Api-Key header
- API_KEY_INVALID (403): Check your API key
- OVER_RATE_LIMIT (429): Wait before more requests
- HTTPS_REQUIRED (400): Use https:// not http://
- NOT_FOUND (404): Check your endpoint URL

Rate Limits:
- Default: 1,000 requests/hour
- DEMO_KEY: 30 requests/hour, 50 requests/day
- Use X-RateLimit-Remaining header to check remaining requests
"""


if __name__ == "__main__":
    print("Data.gov API Integration Examples")
    print("=" * 50)
    print("\nExample 1: Search for food")
    result = search_food_via_datagov("chicken breast")
    
    print("\nExample 2: Get nutrition details")
    if result and result.get('foods'):
        fdc_id = result['foods'][0]['fdcId']
        nutrition = get_nutrition_via_datagov(fdc_id)
    
    print("\n✓ Check DATAGOV_INTEGRATION.md for complete documentation")
