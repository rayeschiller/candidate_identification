from flask import Flask, render_template, jsonify, request
import subprocess
import json

app = Flask(__name__)

# Updated voter data with full names
voter_data = {
    "NC": {
        "46": [
            {"name": "Alice Johnson", "score": 95, "photo": "https://picsum.photos/seed/alice/100",
             "activist_score": 92, "partisan_score": 88, "age": 34, "years_in_residence": 12},
            {"name": "Bob Smith", "score": 85, "photo": "https://picsum.photos/seed/bob/100", "activist_score": 75,
             "partisan_score": 62, "age": 40, "years_in_residence": 5},
            {"name": "Charlie Brown", "score": 75, "photo": "https://picsum.photos/seed/charlie/100",
             "activist_score": 58, "partisan_score": 65, "age": 29, "years_in_residence": 2}
        ]
    }
}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/regions', methods=['GET'])
def get_regions():
    states = list(voter_data.keys())
    counties = {state: list(voter_data[state].keys()) for state in states}
    return jsonify({"states": states, "counties": counties})


@app.route('/api/candidates', methods=['GET'])
def get_candidates():
    state = request.args.get('state')
    county = request.args.get('county')
    data = voter_data.get(state, {}).get(county, [])
    return jsonify(data)


@app.route('/api/social_profiles', methods=['GET'])
def get_social_profiles():
    name = request.args.get('name')
    if not name:
        return jsonify({"error": "Name is required"}), 400

    try:
        # Run sherlock for the given name
        result = subprocess.run(
            ["sherlock", name, "--json"],
            capture_output=True,
            text=True
        )

        # Check for errors
        if result.returncode != 0:
            return jsonify({"error": result.stderr.strip()}), 500

        # Parse and return the results
        profiles = json.loads(result.stdout.strip())
        return jsonify(profiles)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
