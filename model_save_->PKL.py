# =============================================================================
# SAVE TRAINED MODEL (FOR MILESTONE 4)
# =============================================================================

import pickle

print("\nSaving trained model to PKL file...")

model_artifacts = {
    "best_model": "item_based_cf",
    "user_item_matrix": user_item_matrix,
    "item_similarity_matrix": item_similarity_matrix,
    "user_id_map": user_id_map,
    "item_id_map": item_id_map,
    "reverse_item_id_map": reverse_item_id_map,
    "products_df": products
}

with open("model.pkl", "wb") as f:
    pickle.dump(model_artifacts, f)

print("model.pkl saved successfully!")
