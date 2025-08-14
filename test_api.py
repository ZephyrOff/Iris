import requests

BASE_URL = "http://127.0.0.1:5001/api"

def test_api_with_token(script_name, token=None):
    print(f"\n--- Testing API: {script_name} with token ---")
    if token:
        headers = {"Authorization": f"Bearer {token}"}
    else:
        headers = None

    response = requests.get(f"{BASE_URL}/{script_name}?quadri=WCOM", headers=headers)
    #print(response.text)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")


if __name__ == "__main__":
    test_api_with_token("mappicache", "16d39140-696d-4508-b0e1-2a0b27905339")
    """
    test_api_with_token("mappicache")
    """
