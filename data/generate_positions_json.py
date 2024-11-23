import json
import random

# Function to generate a single instrument entry with weights summing to 1
def generate_instrument_with_weights(instrument_id):
    weights = [random.random() for _ in range(4)]
    total = sum(weights)
    normalized_weights = [round(w / total, 16) for w in weights]  # Normalize and ensure precision
    return {
        "instrument_id": instrument_id,
        "weight_1": normalized_weights[0],
        "weight_2": normalized_weights[1],
        "weight_3": normalized_weights[2],
        "weight_4": normalized_weights[3],
        "is_laggard": random.choice([True, False])
    }

# Generate 20k positions ensuring weights sum precisely to 1
positions_precise = [generate_instrument_with_weights(i) for i in range(1, 20000)]

# Construct the JSON structure
positions_json_precise = {
    "positions_json": positions_precise,
    "analytics_list_json": {
        "analytics": ["yaml/0002.yaml", "yaml/0001.yaml"]
    }
}

# Save to a file
file_path_precise = "positions_20k_precise.json"
with open(file_path_precise, "w") as f:
    json.dump(positions_precise, f, indent=4)

print(f"File successfully generated at: {file_path_precise}")


# curl -X POST http://localhost:8088/analytics -H "Content-Type: application/json" -d '{
#   "positions_json": "[{\"instrument_id\": 1, \"weight_1\": 0.00005, \"weight_2\": 0.00004, \"weight_3\": 0.00003, \"weight_4\": 0.00005, \"is_laggard\": true}, {\"instrument_id\": 2, \"weight_1\": 0.00007, \"weight_2\": 0.00006, \"weight_3\": 0.00007, \"weight_4\": 0.00006, \"is_laggard\": false}, {\"instrument_id\": 3, \"weight_1\": 0.0001, \"weight_2\": 0.00008, \"weight_3\": 0.00002, \"weight_4\": 0.0001, \"is_laggard\": true}, {\"instrument_id\": 4, \"weight_1\": 0.00002, \"weight_2\": 0.00005, \"weight_3\": 0.00009, \"weight_4\": 0.00002, \"is_laggard\": true}, {\"instrument_id\": 5, \"weight_1\": 0.00009, \"weight_2\": 0.00007, \"weight_3\": 0.00005, \"weight_4\": 0.00007, \"is_laggard\": false}]",
#   "analytics_list_json": "{\"analytics\": [\"yaml/0002.yaml\", \"yaml/0001.yaml\"]}"
# }'
