# Data.gov API Integration Guide

## Overview

The data.gov API is a consolidated interface provided by the U.S. General Services Administration (GSA) for accessing various government APIs. It requires proper authentication with an API key.

**Documentation:** https://api.data.gov/docs/developer-manual/

## Getting Your API Key

1. Visit: https://api.data.gov/
2. Sign up for a free account
3. You'll receive a unique 40-character API key
4. **Keep it private** - it uniquely identifies you

### DEMO_KEY (Testing Only)
- You can use `DEMO_KEY` for initial testing
- Rate limits are very restrictive:
  - 30 requests per hour per IP address
  - 50 requests per day per IP address
- Get your own key for production use

## Three Ways to Pass Your API Key

### 1. HTTP Header (RECOMMENDED ✓)
```python
headers = {'X-Api-Key': 'YOUR_API_KEY'}
response = requests.get(url, headers=headers)
```

### 2. Query Parameter
```python
params = {'api_key': 'YOUR_API_KEY'}
response = requests.get(url, params=params)
```

### 3. HTTP Basic Auth
```python
response = requests.get('https://YOUR_API_KEY@api.endpoint.com/resource')
```

## Using the DataGovAPIClient

### Basic Setup

```python
from datagov_api import DataGovAPIClient

# Initialize with your API key
client = DataGovAPIClient(api_key='YOUR_API_KEY_HERE')

# Or use environment variable
import os
os.environ['DATA_GOV_API_KEY'] = 'YOUR_API_KEY_HERE'
client = DataGovAPIClient()
```

### Making Requests

```python
# Make a GET request
response = client.make_request(
    endpoint='/api/v1/resource',
    params={'param1': 'value1'}
)

# Make a POST request
response = client.make_request(
    endpoint='/api/v1/resource',
    method='POST',
    json={'data': 'value'}
)

# Use query parameter authentication (fallback)
response = client.make_request(
    endpoint='/api/v1/resource',
    use_query_param=True,
    params={'param1': 'value1'}
)
```

## Integration with Your Flask App

### Option 1: Using Environment Variable (RECOMMENDED)

1. **Set up environment variable:**
   ```bash
   # On Windows PowerShell:
   $env:DATA_GOV_API_KEY = 'your-key-here'
   
   # Or add to your .env file:
   DATA_GOV_API_KEY=your-key-here
   ```

2. **Use in your Flask app:**
   ```python
   from datagov_api import get_datagov_client
   
   # In your route
   @app.route('/api/food-info')
   def get_food_info():
       client = get_datagov_client()
       result = client.make_request(endpoint='/api/nutrition/v1/foods')
       return jsonify(result)
   ```

### Option 2: Hardcode (NOT RECOMMENDED for production)

```python
from datagov_api import DataGovAPIClient

client = DataGovAPIClient(api_key='rgYEsT2yTXur8DRDdPKT2JVm46JZxsc1qsE7Ls3s')
```

## Error Handling

### Common Errors

| Error Code | Status | Meaning | Solution |
|-----------|--------|---------|----------|
| API_KEY_MISSING | 403 | No API key provided | Add X-Api-Key header or api_key parameter |
| API_KEY_INVALID | 403 | Invalid API key | Check your key spelling |
| API_KEY_DISABLED | 403 | Account disabled | Contact the API owner |
| API_KEY_UNAUTHORIZED | 403 | Key not authorized for service | Request access to specific service |
| API_KEY_UNVERIFIED | 403 | Email not verified | Check your email and verify the key |
| HTTPS_REQUIRED | 400 | Must use HTTPS | Change http:// to https:// |
| OVER_RATE_LIMIT | 429 | Rate limit exceeded | Wait before making more requests |
| NOT_FOUND | 404 | Endpoint not found | Check your URL |

## Rate Limiting

### Default Limits
- **Hourly:** 1,000 requests per hour
- **Rolling window:** Counters reset continuously

### Check Current Usage
```python
# Headers returned in every response:
# X-RateLimit-Limit: 1000
# X-RateLimit-Remaining: 998
```

### Need Higher Limits?
Contact the specific agency that owns the API you're using. Check the API documentation for contact information.

## Finding the Right API

Different government agencies provide APIs through data.gov for:
- **NREL:** Energy data
- **USDA:** Food and agriculture data (FoodData Central)
- **EPA:** Environmental data
- **NOAA:** Weather and climate data
- And many more...

Visit https://api.data.gov/ to browse available APIs.

## Example: Using USDA FoodData Central via data.gov

```python
from datagov_api import DataGovAPIClient

client = DataGovAPIClient(api_key='YOUR_KEY')

# Search for foods
response = client.make_request(
    endpoint='https://api.nal.usda.gov/fdc/v1/foods/search',
    params={
        'query': 'chicken breast',
        'pageSize': 10
    }
)

# Get detailed nutrition info
if response and 'foods' in response:
    fdc_id = response['foods'][0]['fdcId']
    nutrition = client.make_request(
        endpoint=f'https://api.nal.usda.gov/fdc/v1/food/{fdc_id}'
    )
```

## Troubleshooting

### Issue: "API_KEY_MISSING"
**Solution:** Make sure you're passing the API key in the header or query parameter:
```python
# Check your headers or params include the key
print(response.headers.get('X-Api-Key'))
```

### Issue: Connection Timeout
**Solution:** The server might be slow. Retry after a short delay:
```python
import time
time.sleep(2)
# Retry your request
```

### Issue: Rate Limited (429 Error)
**Solution:** Wait 1 hour or request higher rate limits from the API owner

### Issue: HTTPS Required
**Solution:** Make sure your endpoint URL starts with `https://` not `http://`

## Testing Your Setup

```python
from datagov_api import DataGovAPIClient

# Test the connection
client = DataGovAPIClient(api_key='YOUR_API_KEY')
if client.test_connection():
    print("✓ API connection working!")
else:
    print("✗ API connection failed")
```

Or run the test script:
```bash
python datagov_api.py
```

## Next Steps

1. **Get your API key:** https://api.data.gov/
2. **Set environment variable:**
   ```bash
   $env:DATA_GOV_API_KEY = 'your-key-here'
   ```
3. **Import and use in your Flask app:**
   ```python
   from datagov_api import get_datagov_client
   client = get_datagov_client()
   ```
4. **Test the connection:**
   ```python
   if client.test_connection():
       print("Ready to use data.gov API!")
   ```

## References

- **API Documentation:** https://api.data.gov/docs/developer-manual/
- **API Discovery:** https://api.data.gov/
- **USDA FoodData Central:** https://fdc.nal.usda.gov/api-guide.html
- **Data.gov:** https://data.gov/
