from flask import Flask, jsonify, request
from flask_cors import CORS
import joblib
import pandas as pd
import numpy as np
import math 

app = Flask(__name__)
CORS(app)

# Load the pickle file
pickle_file_path = 'svm_model.pkl'  # Ensure this file exists
scorecard = joblib.load(pickle_file_path)

# Convert the scorecard to a dictionary for easy access
score_dict = {}
for _, row in scorecard.iterrows():
    variable = row['Variable']
    cls = row['Class']
    score = row['Score']
    if variable not in score_dict:
        score_dict[variable] = {}
    score_dict[variable][cls] = score

@app.route('/get_scorecard', methods=['GET'])
def get_scorecard():
    return jsonify(score_dict)

@app.route('/calculate_score', methods=['POST'])
def calculate_score():
    data = request.json
    selected_values = data.get('selectedValues', {})

    # Calculate max and min possible scores dynamically
    max_score = sum(max(scores.values()) for scores in score_dict.values())
    min_score = sum(min(scores.values()) for scores in score_dict.values())

    total_score = 0
    decision = "Accepted"
    explanation = []

    for variable, response in selected_values.items():
        if variable == "CRIB_SCORE_slabs" and response == "below 0":
            decision = "Rejected"
            explanation.append(f"{variable}: '{response}' -> Immediate Rejection")
            break
        
        if variable == "TOTAL_INCOME_cluster" and response == "<40000":
            decision = "Rejected"
            explanation.append(f"{variable}: '{response}' -> Immediate Rejection")
            break

        if variable == "CUSTOMER AGE_cluster" and response == "70+":
            decision = "Rejected"
            explanation.append(f"{variable}: '{response}' -> Immediate Rejection")
            break

        elif response in score_dict[variable]:
            score = score_dict[variable][response]
            total_score += score
            explanation.append(f"{variable}: '{response}' -> {score} points")
        else:
            explanation.append(f"{variable}: '{response}' -> 0 points (Unknown or unselected)")

    if decision != "Rejected":
        normalized_score = ((total_score - min_score) / (max_score - min_score)) * 100
        decision = "Accepted" if normalized_score > 40 else "Rejected"
        explanation.append(f"\nFinal Normalized Score: {normalized_score:.2f}% -> Decision: {decision}")

        # Calculate Risk of Default and Probability of Default
        risk_of_default = 100 - normalized_score  # Simple inverse relationship
        probability_of_default = 1 - (1 / (1 + math.exp(-(normalized_score - 50) / 10)))

        
        explanation.append(f"\nFinal Normalized Score: {normalized_score:.2f}% -> Decision: {decision}")
        explanation.append(f"Risk of Default: {risk_of_default:.2f}%")
        explanation.append(f"Probability of Default: {probability_of_default:.4f}")
    else:
        normalized_score = 0
        risk_of_default = 100
        probability_of_default = 1

    return jsonify({
        'normalizedScore': normalized_score,
        'decision': decision,
        'riskOfDefault': risk_of_default,
        'probabilityOfDefault': probability_of_default,
        'explanation': explanation,
        'maxScore': max_score,
        'minScore': min_score
    })

    # else:
    #     normalized_score = 0

    # return jsonify({
    #     'normalizedScore': normalized_score,
    #     'decision': decision,
    #     'explanation': explanation,
    #     'maxScore': max_score,
    #     'minScore': min_score
    # })

####-----------------------------------------------------------------------------





if __name__ == "__main__":
    app.run(debug=True)


# @app.route('/calculate_pd', methods=['POST'])
# def calculate_pd():
#     data = request.json
#     normalized_score = data.get("normalizedScore", None)
    
#     if normalized_score is None:
#         return jsonify({"error": "Normalized score not provided"}), 400

#     # Example logistic function to calculate PD based on normalized score
#     # PD = 1 / (1 + exp(-(score - 50) / 10))
#     pd = 1 / (1 + np.exp(-(normalized_score - 50) / 10))
    
#     return jsonify({"probabilityOfDefault": pd})