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

Recommendation System - Milestone 2
A memory-efficient recommendation system built using collaborative filtering, matrix factorization, and hybrid approaches.
🎯 Project Overview
This project implements a scalable recommendation engine capable of handling large-scale user-product interaction data with minimal memory footprint using sparse matrices.
📊 Dataset

Products: 131,864 items across multiple categories
Users: 979,981 registered users
Interactions: 1,000,000 user-product interactions
Sparsity: 99.99% (typical for recommendation systems)

🚀 Features

Memory-Optimized: Uses sparse matrices to handle large datasets efficiently
Multiple Algorithms: 4 different recommendation approaches
Hybrid Model: Combines multiple models for better accuracy
Scalable: Processes millions of interactions with <1GB RAM
Production-Ready: Clean, documented code ready for deployment

🏆 Model Performance
ModelRMSEMAERankItem-Based CF1.05660.8348🥇Hybrid Model1.10010.9787🥈ALS (Matrix Factorization)1.44501.1125🥉Popularity-Based1.46561.22184th
📁 Project Structure
recommendation-system/
├── data/
│   ├── products0.parquet
│   ├── users0.parquet
│   └── interactions_part_0.parquet
├── notebooks/
│   └── milestone2_model_building.ipynb
├── results/
│   ├── model_performance_results.csv
│   └── product_popularity_scores.csv
├── requirements.txt
├── README.md
└── .gitignore
🔧 Installation
Prerequisites

Python 3.8+
pip

Setup
bash# Clone the repository
git clone https://github.com/yourusername/recommendation-system.git
cd recommendation-system

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
📦 Dependencies
pandas>=1.5.0
numpy>=1.23.0
scikit-learn>=1.2.0
scipy>=1.10.0
matplotlib>=3.6.0
seaborn>=0.12.0
pyarrow>=10.0.0
🎮 Usage
Quick Start
pythonimport pandas as pd
from recommendation_system import get_recommendations

# Load the trained model (after running the notebook)
recommendations = get_recommendations(user_id=123456, n=10, method='hybrid')

print("Top 10 Recommendations:")
for i, product_id in enumerate(recommendations, 1):
    print(f"{i}. Product ID: {product_id}")
Running the Notebook

Place your parquet files in the data/ folder
Open notebooks/milestone2_model_building.ipynb
Run all cells sequentially

In Google Colab
python# Mount Google Drive
from google.colab import drive
drive.mount('/content/drive')

# Update file paths to your Drive location
products_df = pd.read_parquet('/content/drive/MyDrive/data/products0.parquet')
users_df = pd.read_parquet('/content/drive/MyDrive/data/users0.parquet')
interactions_df = pd.read_parquet('/content/drive/MyDrive/data/interactions_part_0.parquet')
🧠 Algorithms Implemented
1. Item-Based Collaborative Filtering

Uses cosine similarity between items
Memory-efficient sparse matrix implementation
Best performance: RMSE 1.0566

2. Matrix Factorization (ALS)

Alternating Least Squares algorithm
15 latent factors
Handles implicit feedback

3. Popularity-Based

Baseline model using product popularity
Weighted by rating and interaction count
Cold-start solution

4. Hybrid Model

Weighted ensemble of all models
Weights: Item-CF (50%), ALS (40%), Popularity (10%)
Balanced accuracy and coverage

📈 Performance Metrics

RMSE (Root Mean Square Error): Lower is better
MAE (Mean Absolute Error): Lower is better
Evaluated on 5,000 test samples

🔬 Key Technical Highlights
Memory Optimization

Sparse Matrix Storage: Reduces 23GB to 0.36MB
Selective Similarity Computation: Only top 1000 items
Batch Processing: Efficient memory management

Data Processing

Deduplication of interactions
Interaction type to score conversion
Train-test split (80-20)
User/product filtering (min 5 interactions)

📊 Visualization
The notebook includes:

Interaction distribution histograms
Top product bar charts
Model performance comparison charts
Actual vs Predicted scatter plots

🎯 Milestone Achievements
✅ Milestone 2 Objectives Met:

✅ Core recommendation model developed
✅ Multiple algorithms implemented and trained
✅ Initial performance benchmarks established
✅ Memory-efficient implementation
✅ Recommendation generation working
