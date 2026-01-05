# Data.gov API Setup - Quick Start

## Problem Summary

Your AI Recipe Chatbot project needs to integrate with the data.gov API. The data.gov API requires proper authentication using an API key passed via HTTP headers or query parameters.

## What I've Created

I've created a complete data.gov API integration for your project:

### 1. **datagov_api.py** - Main API Client Module
- Complete `DataGovAPIClient` class with proper authentication
- Supports 3 authentication methods (header, query param, basic auth)
- Built-in error handling for all API error codes
- Rate limit tracking and management
- Simple and clean interface

### 2. **DATAGOV_INTEGRATION.md** - Complete Documentation
- Full API usage guide
- How to get your API key
- Authentication methods explained
- Error handling reference
- Integration examples

### 3. **example_datagov_usage.py** - Usage Examples
- Before/after code comparisons
- How to update your existing functions
- Complete Flask route examples
- Quick reference guide

## Quick Setup (3 Steps)

### Step 1: Get Your API Key
```
1. Visit: https://api.data.gov/
2. Sign up (free)
3. Copy your API key
```

### Step 2: Set Environment Variable (Windows PowerShell)
```powershell
$env:DATA_GOV_API_KEY = 'your-40-character-key-here'
```

Or add to `.env` file:
```
DATA_GOV_API_KEY=your-key-here
```

### Step 3: Use in Your Code
```python
from datagov_api import get_datagov_client

# Get the client (automatically reads DATA_GOV_API_KEY from environment)
client = get_datagov_client()

# Make authenticated requests
response = client.make_request(
    endpoint='https://api.nal.usda.gov/fdc/v1/foods/search',
    params={'query': 'chicken breast', 'pageSize': 10}
)
```

## How It Works

### Authentication (Recommended: X-Api-Key Header)
```python
# The client automatically adds this header:
headers = {'X-Api-Key': 'YOUR_API_KEY'}
```

### The Client Handles:
✓ Proper HTTP header authentication (X-Api-Key)  
✓ Fallback to query parameter authentication  
✓ Rate limit checking and warnings  
✓ All error codes (API_KEY_MISSING, OVER_RATE_LIMIT, etc.)  
✓ Timeout and connection error handling  
✓ Proper error messages and logging  

## Integration with Your Flask App

### Current Code (main.py):
```python
def search_usda_food(food_name):
    params = {
        'query': food_name,
        'pageSize': 10,
        'api_key': USDA_API_KEY  # ← Not using proper authentication
    }
    response = requests.get(f"{USDA_API_URL}/foods/search", params=params, timeout=10)
    ...
```

### Updated Code:
```python
from datagov_api import get_datagov_client

def search_usda_food(food_name):
    client = get_datagov_client()  # Reads from environment variable
    response = client.make_request(
        endpoint='https://api.nal.usda.gov/fdc/v1/foods/search',
        params={'query': food_name, 'pageSize': 10}
    )
    return response
```

## Why This Is Important

### Before (Current):
```python
api_key = USDA_API_KEY  # Hardcoded in code ❌
response = requests.get(url, params={'api_key': key})  # Using query param
```

**Problems:**
- API key hardcoded in source code (security risk)
- Not using recommended HTTP header authentication
- Manual error handling needed
- No rate limit management

### After (With data.gov API):
```python
from datagov_api import get_datagov_client

client = get_datagov_client()  # Reads from secure environment variable ✓
response = client.make_request(endpoint=url, params={...})  # Header auth ✓
```

**Benefits:**
- ✓ API key in environment variable (secure)
- ✓ Uses recommended X-Api-Key header authentication
- ✓ Automatic error handling with proper error codes
- ✓ Built-in rate limit management
- ✓ Timeout and connection error handling
- ✓ Professional error messages

## Testing Your Setup

### Test the Connection:
```python
from datagov_api import DataGovAPIClient

client = DataGovAPIClient(api_key='your-key-here')
if client.test_connection():
    print("API connection working!")
else:
    print("Connection failed - check your API key")
```

### Test with DEMO_KEY (Limited):
```python
# Uses DEMO_KEY by default
client = DataGovAPIClient()
# Limited to: 30 requests/hour, 50 requests/day
```

## Common Issues & Solutions

### Issue: "API_KEY_MISSING" Error
**Cause:** No API key being sent  
**Solution:** Set environment variable:
```powershell
$env:DATA_GOV_API_KEY = 'your-key-here'
```

### Issue: "API_KEY_INVALID" Error
**Cause:** Wrong or expired API key  
**Solution:** Check your key at https://api.data.gov/

### Issue: "OVER_RATE_LIMIT" (429 Error)
**Cause:** Made too many requests  
**Solution:** Wait 1 hour, or upgrade to your own key

### Issue: Rate Limit Warnings
**Solution:** Check remaining requests:
```python
response = client.make_request(endpoint=url)
# Client will print: "Rate Limit: 998/1000 requests remaining"
```

## API Key Security

### DO:
✓ Store in environment variables  
✓ Add to `.env` file (excluded from git)  
✓ Rotate periodically  
✓ Use for server-side requests only  

### DON'T:
✗ Commit to git repository  
✗ Share with others  
✗ Hardcode in source files  
✗ Use DEMO_KEY in production  

## File Locations

```
AI-recipe-chatbot/
├── datagov_api.py              # ← Main API client module
├── DATAGOV_INTEGRATION.md      # ← Complete documentation
├── example_datagov_usage.py    # ← Code examples
├── main.py                     # ← Your Flask app (update this)
├── .env                        # ← Add API key here (create if needed)
└── ...
```

## Next Steps

1. **Get API key:** https://api.data.gov/
2. **Add to environment:**
   ```powershell
   $env:DATA_GOV_API_KEY = 'your-key-here'
   ```
3. **Test:**
   ```python
   from datagov_api import DataGovAPIClient
   client = DataGovAPIClient()
   if client.test_connection():
       print("Working!")
   ```
4. **Update main.py** to use `get_datagov_client()` instead of hardcoded API key
5. **Remove hardcoded API key** from main.py (line 40)

## Documentation Files

- **DATAGOV_INTEGRATION.md** - Full API documentation and examples
- **example_datagov_usage.py** - Code examples showing how to use the client
- **datagov_api.py** - The actual implementation (fully documented)

## Questions?

Refer to the official documentation:
- API Manual: https://api.data.gov/docs/developer-manual/
- Get Key: https://api.data.gov/
- Data.gov: https://data.gov/
