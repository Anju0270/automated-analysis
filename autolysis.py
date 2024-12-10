import os
import openai
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from PIL import Image

# Load the AIPROXY_TOKEN from environment variable
openai.api_key = os.getenv("AIPROXY_TOKEN")

# Function to load and analyze the dataset
def load_and_analyze_data(file_path):
    data = pd.read_csv(file_path)
    
    # Basic Analysis
    summary = data.describe(include='all')
    missing_values = data.isnull().sum()
    column_types = data.dtypes

    # Generate basic insights
    insights = {
        "summary": summary,
        "missing_values": missing_values,
        "column_types": column_types,
    }

    return data, insights

# Function to create visualizations and save as PNG
def create_visualizations(data, output_dir):
    images = []
    
    # Correlation Heatmap
    numeric_data = data.select_dtypes(include="number")
    if not numeric_data.empty:
        corr_matrix = numeric_data.corr()
        plt.figure(figsize=(8, 6))
        sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="coolwarm")
        plt.title("Correlation Heatmap")
        heatmap_path = os.path.join(output_dir, "correlation_heatmap.png")
        plt.savefig(heatmap_path, dpi=100, bbox_inches='tight', pad_inches=0.1, transparent=True)
        
        # Resize to 512x512 px
        with Image.open(heatmap_path) as img:
            img = img.resize((512, 512))  # Resize to 512x512
            img.save(heatmap_path)
        plt.close()
        images.append(heatmap_path)

    # Distribution of Numerical Columns
    for col in numeric_data.columns[:2]:  # Limit to 2 distributions for brevity
        plt.figure(figsize=(6, 4))
        sns.histplot(numeric_data[col], kde=True, bins=30)
        plt.title(f"Distribution of {col}")
        hist_path = os.path.join(output_dir, f"{col}_distribution.png")
        plt.savefig(hist_path, dpi=100, bbox_inches='tight', pad_inches=0.1, transparent=True)
        
        # Resize image to 512x512 px
        with Image.open(hist_path) as img:
            img = img.resize((512, 512))
            img.save(hist_path)
        plt.close()
        images.append(hist_path)

    return images

# Function to generate LLM-based narrative
def generate_narrative(insights, images, output_dir):
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

    # Request narrative from the LLM
    response = openai.Completion.create(
        model="gpt-4.0-mini", 
        prompt=prompt, 
        max_tokens=1500
    )

    narrative = response.choices[0].text.strip()

    # Construct README.md with narrative and images
    readme_path = os.path.join(output_dir, "README.md")
    with open(readme_path, "w") as file:
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
    
    # Extract directory name from the input CSV file (without extension)
    output_dir = os.path.splitext(os.path.basename(file_path))[0]

    # Step 2: Create the directory (if not exists)
    os.makedirs(output_dir, exist_ok=True)

    # Step 3: Create Visualizations and save them as PNGs in the output directory
    images = create_visualizations(data, output_dir=output_dir)
    
    # Step 4: Generate and save the Narrative in README.md
    generate_narrative(insights, images, output_dir=output_dir)

    print(f"Analysis complete. Results saved in {output_dir}/README.md and images in {output_dir}/.")

# Entry point for the script
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: uv run autolysis.py dataset.csv")
    else:
        dataset_file = sys.argv[1]
        main(dataset_file)
