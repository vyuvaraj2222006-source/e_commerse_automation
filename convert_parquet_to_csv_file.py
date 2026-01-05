import pandas as pd

# Read parquet file
df = pd.read_parquet("user_item_interactions.parquet")

# Write to CSV
df.to_csv("data3.csv", index=False)
