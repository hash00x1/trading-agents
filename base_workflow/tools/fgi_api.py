import requests
from base_workflow.data.models import FearGreedIndex
from datetime import datetime, timezone

def get_fear_and_greed_index() -> FearGreedIndex:
    """
    Fetch the Fear and Greed Index from the Alternative.me API.
    
    Returns:
        FearGreedIndex: A structured object containing the index value, classification, and last updated time.
    """
    try:
        response = requests.get("https://api.alternative.me/fng/")
        data = response.json()
        
        index_data = data["data"][0]

        index_value = int(index_data["value"])
        classification = index_data["value_classification"]
        timestamp = int(index_data["timestamp"])

       
        updated_at = datetime.fromtimestamp(timestamp, timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        result = FearGreedIndex(
            value=index_value,
            classification=classification,
            updated_at=updated_at
        )
        return result
    except requests.RequestException as e:
        print(f"Error fetching Fear and Greed Index: {e}")
        return FearGreedIndex(value=0, classification="neutral", updated_at="Unknown") # set to neutral if error occurs
    
if __name__ == "__main__":
    # Example usage
    fgi = get_fear_greed_index()
    print(f"Fear and Greed Index: {fgi.value}, Classification: {fgi.classification}, Updated at: {fgi.updated_at}")