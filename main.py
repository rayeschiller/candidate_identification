import os
import tempfile

from flask import Flask, render_template, jsonify, request
import subprocess
import pandas as pd
import boto3
from io import StringIO

app = Flask(__name__)

# Define S3 URI and column mapping
bucket_name = "ts-storagegateway-bucket"
file_key = "Users/riley.noel/Hackathon2024/NC_HD/046_NC_PotentialCandidateCriteria.csv"

# Initialize S3 client
s3_client = boto3.client('s3')

# Fetch the CSV file from S3
response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
csv_content = response['Body'].read().decode('ISO-8859-1')

# Read the CSV into a DataFrame
data = pd.read_csv(StringIO(csv_content), sep=',')

def get_data():
    # Define column mapping for inputs and weights
    columns = {
        "ts__tsmart_local_voter_score": 0.3,
        "intp__length_of_residence": 0.3,
        "ts__tsmart_activist_score": 0.2,
        "tsmart_partisan_score": 0.2,
    }

    # Define the input columns and composite score
    # Normalize columns
    for col in columns.keys():
        min_val, max_val = data[col].min(), data[col].max()
        data[f"norm_{col}"] = (data[col] - min_val) / (max_val - min_val) if max_val > min_val else 0

    # Calculate composite score
    data["composite_score"] = sum(
        data[f"norm_{col}"] * weight for col, weight in columns.items()
    )

    # Define the input columns and composite score
    input_columns = [
        "ts__tsmart_local_voter_score",
        "ts__tsmart_activist_score",
        "tsmart_partisan_score",
        "intp__length_of_residence",
        "composite_score",
        "vf_yob",
        "tsmart_first_name",
        "tsmart_last_name"
    ]


    def categorize_score(score):
        if score > 0.75:
            return "High Potential"
        elif score > 0.5:
            return "Moderate Potential"
        else:
            return "Low Potential"


    data["potential_category"] = data["composite_score"].apply(categorize_score)

    # Save results to a CSV file
    return data.nlargest(10, "composite_score")[input_columns]


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/regions', methods=['GET'])
def get_regions():
    states = ['NC']
    counties = {state: list(["46", "65", "97"]) for state in states}
    return jsonify({"states": states, "counties": counties})


@app.route('/api/candidates', methods=['GET'])
def get_candidates():
    top_10 = get_data()
    state = request.args.get('state')
    county = request.args.get('county')
    top_candidates = [
        {
            "name": f"{row['tsmart_first_name']} {row['tsmart_last_name']}",
            "photo": f"https://picsum.photos/seed/{idx}/100",
            "score": round(row["composite_score"], 2),
            "activist_score": round(row["ts__tsmart_activist_score"], 2),
            "partisan_score": round(row["tsmart_partisan_score"], 2),
            "age": 2024 - row["vf_yob"],  # Assuming vf_yob is valid
            "years_in_residence": round(row["intp__length_of_residence"], 2),
            "local_voter_score": round(row["ts__tsmart_local_voter_score"], 2)
        }
        for idx, row in top_10.iterrows()
    ]

    # Return the data in the expected format
    return jsonify(top_candidates)


@app.route('/api/social_profiles', methods=['GET'])
def get_social_profiles():
    name = request.args.get('name').lower()
    if not name:
        return jsonify({"error": "Name is required"}), 400

    try:
        # Define the output file for the result
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode='w') as tmp_file:
            output_file = tmp_file.name

        # Run Sherlock to save the output
        result = subprocess.run(
            ["sherlock", name, "--site", "LinkedIn", "--output", output_file],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return jsonify({"error": result.stdout.strip()}), 500

            # Parse the output file for the LinkedIn URL
        platform_data = {}
        with open(output_file, "r") as file:
            for line in file:
                line = line.strip()
                if line.startswith("http"):  # Extract only lines with URLs
                    platform_data["LinkedIn"] = line

        os.remove(output_file)  # Clean up the temporary file
        return jsonify(platform_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
