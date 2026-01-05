"""
Test script to verify your API key works with data.gov integration
"""

from datagov_api import DataGovAPIClient
import json

# Your API key
API_KEY = "rgYEsT2yTXur8DRDdPKT2JVm46JZxsc1qsE7Ls3s"

print("=" * 60)
print("Testing Data.gov API Integration")
print("=" * 60)

# Initialize client with your API key
client = DataGovAPIClient(api_key=API_KEY)

print(f"\n1. Client Configuration:")
print(f"   API Key: {API_KEY[:15]}...***")
print(f"   Auth Method: X-Api-Key header (recommended)")

# Test 1: Search for a simple food
print(f"\n2. Testing Food Search (chicken breast)...")
response = client.make_request(
    endpoint='https://api.nal.usda.gov/fdc/v1/foods/search',
    params={
        'query': 'chicken breast',
        'pageSize': 5
    }
)

if response:
    print(f"   SUCCESS! Found {response.get('totalHits', 0)} foods")
    foods = response.get('foods', [])
    
    if foods:
        print(f"\n   First 3 results:")
        for i, food in enumerate(foods[:3], 1):
            print(f"   {i}. {food.get('description', 'N/A')} (FDC ID: {food.get('fdcId', 'N/A')})")
        
        # Test 2: Get detailed nutrition for first food
        print(f"\n3. Testing Nutrition Details (first result)...")
        fdc_id = foods[0].get('fdcId')
        
        nutrition_response = client.make_request(
            endpoint=f'https://api.nal.usda.gov/fdc/v1/food/{fdc_id}'
        )
        
        if nutrition_response:
            print(f"   SUCCESS! Got nutrition data for: {nutrition_response.get('description')}")
            
            nutrients = nutrition_response.get('foodNutrients', [])
            print(f"   Found {len(nutrients)} nutrients")
            
            # Display key nutrients
            print(f"\n   Key Nutrients (per 100g):")
            for nutrient in nutrients[:10]:
                name = nutrient.get('nutrient', {}).get('name', 'Unknown')
                amount = nutrient.get('amount', 0)
                unit = nutrient.get('nutrient', {}).get('unitName', '')
                print(f"   - {name}: {amount} {unit}")
        else:
            print(f"   FAILED to get nutrition details")
else:
    print(f"   FAILED! Check your API key and internet connection")

print("\n" + "=" * 60)
print("API Key Status: WORKING!" if response else "API Key Status: NOT WORKING")
print("=" * 60)

if response:
    print("\nNext steps:")
    print("1. Set environment variable:")
    print(f"   $env:DATA_GOV_API_KEY = '{API_KEY}'")
    print("\n2. Update main.py to use the data.gov client")
    print("   See example_datagov_usage.py for code examples")
