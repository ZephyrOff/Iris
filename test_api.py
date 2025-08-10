import requests

BASE_URL = "http://127.0.0.1:5000/api"

def test_api_with_token(script_name, token=None):
    print(f"\n--- Testing API: {script_name} with token ---")
    if token:
        headers = {"Authorization": f"Bearer {token}"}
    else:
        headers = None

    response = requests.get(f"{BASE_URL}/{script_name}?nom=toto", headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")


if __name__ == "__main__":
    test_api_with_token("salutation", "ea69843b-82e1-4837-a353-89df8eb8ec6e")
