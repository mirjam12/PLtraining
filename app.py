# =========================
# terminal

# (base) mirjams-MacBook-Air:my_workout_project macbook$
# =========================


# ===========================
# if I want to use chatGPT in my personal project:
# from langchain_openai import ChatOpenAI
# 11m = ChatOpenAI (model="gpt-40-mini")
# ==========================

from flask import Flask, render_template, request, jsonify
import requests
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

app = Flask(__name__)

# =========================
# ENV VARIABLES
# =========================
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

if not URL or not KEY:
    raise Exception("Missing SUPABASE_URL or SUPABASE_KEY in .env or .env file!")

supabase = create_client(URL, KEY)


# =========================
# FRONTEND
# =========================
@app.route('/')
def index():
    return render_template('index.html')


# =========================
# ADD WORKOUT
# =========================
@app.route('/add_workout', methods=['POST'])
def add_workout():
    try:
        ui_data = request.json

        exercise = ui_data.get('exercise')
        weight_raw = ui_data.get('weight')
        reps_raw = ui_data.get('reps')
        user_id = ui_data.get('user_id')
        rpe_raw = ui_data.get('rpe')

        weight = float(weight_raw)
        reps = int(reps_raw)
        rpe = float(rpe_raw) if rpe_raw not in [None, ""] else 10

        if rpe < 1 or rpe > 10:
            return jsonify({"status": "error", "message": "RPE must be 1–10"}), 400

        # 1RM calculation
        base_one_rm = weight * (36 / (37 - reps))
        rpe_factor_map = {
            10: 1.00,
            9.5: 0.97,
            9: 0.94,
            8.5: 0.90,
            8: 0.86,
            7.5: 0.82,
            7: 0.78
        }

        rpe_factor = rpe_factor_map.get(rpe, 1.0)
        one_rm = round(base_one_rm / rpe_factor, 1)
        print(f"3. Calculated 1RM: {one_rm}")

        # if error, check if column names match Supabase table EXACTLY
        payload = {
            "exercise": exercise,
            "weight": weight,
            "reps": reps,
            "rpe": rpe,
            "one_rm": one_rm,
            "user_id": user_id
        }

        headers = {
                "apikey": KEY,
                "Authorization": f"Bearer {KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
        }

        print("4. Sending to Supabase...")
        response = requests.post(URL, json=payload, headers=headers)
        print(f"5. Supabase Result: {response.status_code}")
                
        response = supabase.table("Trainings").insert(payload).execute()

        if response.data:
            return jsonify({"status": "success", "one_rm": one_rm})
        else:
            return jsonify({
                "status": "error",
                "message": str(response)
            }), 400

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500


# =========================
# GET TRENDS
# =========================
@app.route('/get_trends', methods=['GET'])
def get_trends():
    headers = {
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}"
    }
    # user_id (available on Supabase)
    user_id = request.args.get('user_id')
    
    # data sorted by date & filter based on user id
    query_url = f"{URL}?user_id=eq.{user_id}&select=*&order=created_at.asc"

    response = requests.get(query_url, headers=headers)
    
    return jsonify(response.json())


if __name__ == '__main__':
    app.run(port=8000, debug=True)
