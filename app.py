#import pandas as pd

# Read parquet file
#df = pd.read_parquet("test.parquet")

# Write to CSV
#df.to_csv("data2.csv", index=False)
# =====================================
# Milestone 1 : Data Preparation
# =====================================

# =====================================
# Milestone 1 : Data Preparation
# SCALABLE VERSION (NO MEMORY CRASH)
# =====================================

import pandas as pd

# ---------- 1. Load Parquet ----------
DATA_PATH = "test.parquet"

df = pd.read_parquet(DATA_PATH)

print("Raw Data Shape:", df.shape)

# ---------- 2. Define Columns ----------
USER_COL = "user_id"
ITEM_COL = "product_id"
EVENT_COL = "event_type"

# ---------- 3. Drop Missing ----------
df = df.dropna(subset=[USER_COL, ITEM_COL])

# ---------- 4. Convert Events → Interaction Score ----------
event_weights = {
    "view": 1,
    "cart": 2,
    "purchase": 3
}

df["interaction"] = df[EVENT_COL].map(event_weights)
df = df.dropna(subset=["interaction"])

# ---------- 5. Aggregate User–Item Interactions ----------
interaction_df = (
    df.groupby([USER_COL, ITEM_COL], as_index=False)
      .agg({"interaction": "sum"})
)

print("Cleaned Interaction Data Shape:", interaction_df.shape)

# ---------- 6. Save Interaction Matrix (Sparse / COO Format) ----------
# This IS the user–item interaction matrix (industry standard)
interaction_df.to_parquet("user_item_interactions.parquet")

print("Milestone 1 completed successfully.")
print("User–Item matrix stored in sparse (COO) format.")
