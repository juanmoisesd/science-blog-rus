import requests
import os
import json

class ZenodoImprover:
    """
    Utility to fetch and categorize Juan Moisés de la Serna's documents from Zenodo.
    """
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://zenodo.org/api/records"

    def fetch_records(self, query, size=100):
        params = {
            'q': query,
            'size': size,
            'access_token': self.api_key
        }
        response = requests.get(self.base_url, params=params)
        if response.status_code == 200:
            return response.json().get('hits', {}).get('hits', [])
        return []

    def get_author_documents(self):
        query = 'creators.name:"de la Serna, Juan Moisés"'
        records = self.fetch_records(query)

        categorized = {
            "press_releases": [],
            "serna_scales": [],
            "others": []
        }

        for r in records:
            title = r.get('metadata', {}).get('title', '')
            if title.startswith("Press Release"):
                categorized["press_releases"].append(r)
            elif title.startswith("SERNA Scale SS"):
                categorized["serna_scales"].append(r)
            else:
                categorized["others"].append(r)

        return categorized

if __name__ == "__main__":
    # Example usage (API key should be set in environment)
    token = os.getenv("ZENODO_API_TOKEN")
    if token:
        improver = ZenodoImprover(token)
        docs = improver.get_author_documents()
        print(f"Retrieved {len(docs['press_releases'])} Press Releases")
        print(f"Retrieved {len(docs['serna_scales'])} SERNA Scales")
    else:
        print("Please set ZENODO_API_TOKEN environment variable.")
