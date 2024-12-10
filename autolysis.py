# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "pandas",
#   "seaborn",
#   "matplotlib",
#   "pillow",
# ]
# ///

import os
import requests
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from PIL import Image

# Load the AIPROXY_TOKEN from environment variable
api_key = os.getenv("AIPROXY_TOKEN")

# Function to load and analyze the dataset
def load_and_analyze_data(file_path):
    try:
        # Attempt to read the file with UTF-8 encoding
        data = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        # If UTF-8 fails, try with a fallback encoding
        data = pd.read_csv(file_path, encoding='latin1')
    
    # Basic Analysis
    summary = data.describe(include='all')
    missing_values = data.isnull().sum()
    column_types = data.dtypes
    data_info = data.info()

    # Generate basic insights
    insights = {
        "summary": summary,
        "missing_values": missing_values,
        "column_types": column_types,
        "data_info": data_info,
    }

    return data, insights

# Function to create visualizations and save as PNG
def create_visualizations(data, labels=None):
    images = []
    
    # Correlation Heatmap
    numeric_data = data.select_dtypes(include="number")
    if not numeric_data.empty:
        corr_matrix = numeric_data.corr()
        plt.figure(figsize=(8, 6))
        sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="coolwarm")
        plt.title("Correlation Heatmap")
        heatmap_path = "correlation_heatmap.png"
        plt.savefig(heatmap_path, dpi=100, bbox_inches='tight', pad_inches=0.1, transparent=True)
        
        # Resize to 512x512 px
        with Image.open(heatmap_path) as img:
            img = img.resize((512, 512))
            img.save(heatmap_path)
        plt.close()
        images.append(heatmap_path)

    # Distribution of Numerical Columns
    for col in numeric_data.columns[:2]:  # Limit to 2 distributions for brevity
        plt.figure(figsize=(6, 4))
        sns.histplot(numeric_data[col], kde=True, bins=30)
        plt.title(f"Distribution of {col}")
        hist_path = f"{col}_distribution.png"
        plt.savefig(hist_path, dpi=100, bbox_inches='tight', pad_inches=0.1, transparent=True)
        
        # Resize image to 512x512 px
        with Image.open(hist_path) as img:
            img = img.resize((512, 512))
            img.save(hist_path)
        plt.close()
        images.append(hist_path)

    # Scatter Plot (if labels available)
    if labels is not None and numeric_data.shape[1] >= 2:
        plt.figure(figsize=(8, 6))
        plt.scatter(numeric_data.iloc[:, 0], numeric_data.iloc[:, 1], c=labels, cmap="viridis")
        plt.title("Clustering Scatter Plot")
        scatter_path = "clustering_scatter.png"
        plt.savefig(scatter_path, dpi=100, bbox_inches='tight', pad_inches=0.1, transparent=True)
        
        # Resize image to 512x512 px
        with Image.open(scatter_path) as img:
            img = img.resize((512, 512))
            img.save(scatter_path)
        plt.close()
        images.append(scatter_path)

    return images

# Function to generate LLM-based narrative using the custom endpoint
def generate_narrative(insights, images):
    prompt = f"""
    Dataset Analysis Report:
    Dataset Summary: {insights['summary']}
    Missing Values: {insights['missing_values']}
    Column Types: {insights['column_types']}
    
    Please write a detailed narrative that includes:
    1. A brief description of the dataset.
    2. The analysis carried out, including key observations.
    3. Insights discovered from the analysis.
    4. The implications of these insights and potential actions.
    5. Embed relevant visualizations that help illustrate the insights.
    """

    # Send the request to the custom API
    response = requests.post(
        "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": prompt}
            ]
        }
    )
    
    if response.status_code == 200:
        narrative = response.json()["choices"][0]["message"]["content"].strip()
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

    # Construct README.md with narrative and images
    with open("README.md", "w") as file:
        file.write("# Automated Data Analysis Report\n")
        file.write("## Narrative\n")
        file.write(narrative)
        file.write("\n\n## Visualizations\n")
        
        # Embed images in README.md
        for image in images:
            file.write(f"![{image}]({image})\n")

# Main execution function
def main(file_path):
    # Step 1: Load and Analyze the Data
    data, insights = load_and_analyze_data(file_path)
    
    # Step 2: Create Visualizations and save them as PNGs
    images = create_visualizations(data)
    
    # Step 3: Generate and save the Narrative in README.md
    generate_narrative(insights, images)

    print(f"Analysis complete. Results saved in README.md and images {', '.join(images)}.")

# Entry point for the script
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: uv run autolysis.py dataset.csv")
    else:
        dataset_file = sys.argv[1]
        main(dataset_file)
