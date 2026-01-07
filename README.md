# e_commerse_automation
Milestone 1: Data Preparation and User-Item Interaction Matrix

## Objective
Prepare clean, structured datasets for model development.

## Tasks Completed
- Collected user–product interaction data
- Handled missing values and duplicate interactions
- Converted event data into implicit feedback
- Built a scalable user–item interaction matrix (sparse format)

## Files
- cleaning_raw_data.py – Data preparation code
- user_item_interactions.parquet – User–item interaction data

## Dataset Summary
- Raw interactions: ~2.7M rows
- Cleaned interactions: ~1.6M rows

## How to Run
```bash
python cleaning_raw_data.py
