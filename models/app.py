from flask import Flask, request, jsonify
import pickle
import numpy as np
import pandas as pd
import json

app = Flask(__name__)

BASE_PATH = r"C:\Users\ASUS\Desktop\New folder (5)\models"

with open(f"{BASE_PATH}\\recommendation_model.pkl", "rb") as f:
    model = pickle.load(f)

with open(f"{BASE_PATH}\\item_metadata.pkl", "rb") as f:
    items = pickle.load(f)

matrix_data = np.load(
    f"{BASE_PATH}\\user_item_matrix.npz",
    allow_pickle=True
)

user_item_matrix = matrix_data["matrix"]

with open(f"{BASE_PATH}\\model_config.json", "r") as f:
    config = json.load(f)

print("All models loaded successfully")

@app.route("/recommend", methods=["GET"])
def recommend():
    try:
        user_id = int(request.args.get("user_id"))
    except:
        return jsonify({"error": "Invalid user_id"})

    # Check range
    if user_id < 0 or user_id >= user_item_matrix.shape[0]:
        return jsonify({"error": "User not found"})

    # Get user vector
    user_vector = user_item_matrix[user_id].reshape(1, -1)

    # Predict scores
    scores = model.predict(user_vector)[0]

    # Top 5 items
    top_indices = np.argsort(scores)[::-1][:5]

    recommended = items.iloc[top_indices][
        ["product_id", "product_name"]
    ]

    return jsonify({
        "user_id": user_id,
        "recommendations": recommended.to_dict(orient="records")
    })


if __name__ == "__main__":
    app.run(debug=True)
