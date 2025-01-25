import requests

# URL of the page you want to fetch
url = "https://www.ikea.com/us/en/search/?q=red%20couch"

# Send a GET request
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    print("Page fetched successfully!")
    print(response.text[:500])  # Print the first 500 characters of the page content
else:
    print(f"Failed to fetch page. Status code: {response.status_code}")