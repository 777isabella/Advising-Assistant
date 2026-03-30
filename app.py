from flask import Flask, request, jsonify
from recommendation import RecommendationEngine

app = Flask(__name__)
engine = RecommendationEngine()

@app.route("/recommend", methods=["POST"])
def recommend():
    data = request.json

    completed = data["completed"]
    degree_plan = data["degree_plan"]
    prereqs = data["prereqs"]

    result = engine.generate(completed, degree_plan, prereqs)

    return jsonify({"recommended": result})

if __name__ == "__main__":
    app.run(debug=True)