"""
Check your data.gov API usage and rate limits
"""

from datagov_api import DataGovAPIClient
import os

# Set your API key
API_KEY = os.getenv('DATA_GOV_API_KEY', 'rgYEsT2yTXur8DRDdPKT2JVm46JZxsc1qsE7Ls3s')

print("=" * 60)
print("DATA.GOV API USAGE CHECKER")
print("=" * 60)

# Initialize client
client = DataGovAPIClient(api_key=API_KEY)

print(f"\nAPI Key: {API_KEY[:20]}...***")
print(f"Checking current usage...\n")

# Make a simple test request to check rate limits
response = client.make_request(
    endpoint='https://api.nal.usda.gov/fdc/v1/foods/search',
    params={'query': 'apple', 'pageSize': 1}
)

if response:
    print("\n" + "=" * 60)
    print("CURRENT API STATUS")
    print("=" * 60)
    
    # The rate limit info is printed by the client automatically
    # Let's make another request to see the updated count
    
    print("\nMaking another test request to see usage update...")
    response2 = client.make_request(
        endpoint='https://api.nal.usda.gov/fdc/v1/foods/search',
        params={'query': 'banana', 'pageSize': 1}
    )
    
    print("\n" + "=" * 60)
    print("API LIMITS INFORMATION")
    print("=" * 60)
    
    if API_KEY == 'DEMO_KEY':
        print("\n⚠️  You're using DEMO_KEY")
        print("   Rate Limits:")
        print("   - 30 requests per hour per IP")
        print("   - 50 requests per day per IP")
        print("\n   Get your own key at: https://api.data.gov/")
    else:
        print("\n✓ Using personal API key")
        print("   Default Rate Limits:")
        print("   - 1,000 requests per hour")
        print("   - Rolling window (continuous reset)")
        
    print("\n" + "=" * 60)
    print("\nTo monitor usage in your Flask app:")
    print("1. Check the terminal output - rate limits are logged")
    print("2. Look for 'Rate Limit: X/Y requests remaining'")
    print("3. If you hit the limit, you'll see a 429 error")
    
else:
    print("\n❌ Failed to check API usage")
    print("   Possible reasons:")
    print("   - Invalid API key")
    print("   - Rate limit exceeded")
    print("   - Internet connection issue")
    
print("\n" + "=" * 60)
