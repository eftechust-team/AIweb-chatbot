"""
Data.gov API Integration Module

This module provides utilities for accessing various government APIs through api.data.gov
Documentation: https://api.data.gov/docs/developer-manual/

API Key can be obtained from: https://api.data.gov/
"""

import requests
import os
from typing import Dict, Any, Optional

# Data.gov API Configuration
DATA_GOV_API_KEY = os.getenv('DATA_GOV_API_KEY', 'DEMO_KEY')  # Get from environment or use DEMO_KEY
DATA_GOV_BASE_URL = "https://api.data.gov"

class DataGovAPIClient:
    """
    Client for interacting with data.gov APIs.
    
    Supports three authentication methods:
    1. HTTP Header: X-Api-Key
    2. Query Parameter: api_key
    3. HTTP Basic Auth: key@domain.com
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize the Data.gov API client.
        
        Args:
            api_key: Your data.gov API key. If None, uses DATA_GOV_API_KEY env variable or DEMO_KEY
        """
        self.api_key = api_key or DATA_GOV_API_KEY
        self.base_url = DATA_GOV_BASE_URL
        self.session = requests.Session()
        
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with API key included (preferred method)."""
        return {
            'X-Api-Key': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def _get_params(self, **kwargs) -> Dict[str, Any]:
        """Get query parameters with API key included (fallback method)."""
        params = {'api_key': self.api_key}
        params.update(kwargs)
        return params
    
    def make_request(
        self,
        endpoint: str,
        method: str = 'GET',
        use_query_param: bool = False,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Make a request to a data.gov API endpoint.
        
        Args:
            endpoint: The full URL or relative path to the API endpoint
            method: HTTP method (GET, POST, PUT, DELETE)
            use_query_param: If True, pass API key as query parameter instead of header
            **kwargs: Additional request parameters (params, json, data, etc.)
        
        Returns:
            JSON response as dictionary, or None if request failed
        """
        try:
            # Construct full URL if relative path provided
            url = endpoint if endpoint.startswith('http') else f"{self.base_url}{endpoint}"
            
            # Set authentication method
            if use_query_param:
                # Add API key as query parameter
                params = self._get_params(**kwargs.get('params', {}))
                kwargs['params'] = params
            else:
                # Use X-Api-Key header (preferred)
                headers = kwargs.get('headers', {})
                headers.update(self._get_headers())
                kwargs['headers'] = headers
            
            # Make the request
            response = self.session.request(method, url, timeout=10, **kwargs)
            
            # Check for rate limit headers
            rate_limit = response.headers.get('X-RateLimit-Limit')
            rate_remaining = response.headers.get('X-RateLimit-Remaining')
            
            if rate_limit and rate_remaining:
                print(f"Rate Limit: {rate_remaining}/{rate_limit} requests remaining")
            
            # Handle errors
            if response.status_code == 429:
                print("ERROR: Rate limit exceeded. Please wait before making more requests.")
                return None
            elif response.status_code == 403:
                print("ERROR: API key invalid, disabled, or unauthorized.")
                return None
            elif response.status_code == 400:
                print("ERROR: Invalid request or HTTPS required.")
                return None
            elif response.status_code == 404:
                print("ERROR: API endpoint not found.")
                return None
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            print("ERROR: Request timeout. Please try again.")
            return None
        except requests.exceptions.ConnectionError:
            print("ERROR: Connection failed. Check your internet connection.")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"ERROR: HTTP Error {response.status_code}: {e}")
            return None
        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")
            return None
    
    def search_food_nutrition(
        self,
        query: str,
        api_service: str = "NREL",
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Search for food nutrition information through data.gov.
        
        Note: The specific endpoint depends on which agency's API you're using.
        
        Args:
            query: Search query (food name, etc.)
            api_service: Which API service to use (NREL, USDA, etc.)
            **kwargs: Additional query parameters
        
        Returns:
            JSON response with search results
        """
        params = {'query': query}
        params.update(kwargs)
        
        # Example endpoint - adjust based on actual data.gov API structure
        endpoint = f"/api/{api_service}/food/search"
        
        return self.make_request(endpoint, params=params)
    
    def test_connection(self) -> bool:
        """
        Test the API connection with a simple request.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to access the API root or a simple endpoint
            endpoint = f"{self.base_url}/api/discovery/v1"
            result = self.make_request(endpoint)
            return result is not None
        except Exception:
            return False


def get_datagov_client(api_key: str = None) -> DataGovAPIClient:
    """
    Factory function to get a data.gov API client.
    
    Args:
        api_key: Optional API key. If not provided, uses environment variable or DEMO_KEY
    
    Returns:
        Configured DataGovAPIClient instance
    """
    return DataGovAPIClient(api_key)


# Example usage and testing
if __name__ == "__main__":
    # Initialize client
    client = DataGovAPIClient()
    
    print("=" * 60)
    print("Data.gov API Client Test")
    print("=" * 60)
    
    # Test connection
    print("\n1. Testing API Connection...")
    if client.test_connection():
        print("✓ Connection successful!")
    else:
        print("✗ Connection failed. Check your API key and internet connection.")
    
    print("\n2. Current API Key Status:")
    print(f"   Using API Key: {client.api_key[:10]}...***")
    print(f"   Base URL: {client.base_url}")
    
    print("\n3. How to use the Data.gov API:")
    print("   - Get your API key at: https://api.data.gov/")
    print("   - Set environment variable: export DATA_GOV_API_KEY='your-key-here'")
    print("   - Or pass to client: DataGovAPIClient(api_key='your-key-here')")
    
    print("\n" + "=" * 60)
