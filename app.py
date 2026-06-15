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
# ==========================
@app.route('/')
def index():
    return render_template('index.html')


# =========================
# ADD WORKOUT
# ===============================
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
        # old calculation, overinflated
        # base_one_rm = weight * (36 / (37 - reps))
        RPE_TABLE = {
            10:   [1, 0.955, 0.922, 0.892, 0.863, 0.837, 0.811, 0.786, 0.762, 0.739, 0.707, 0.68, 0.653, 0.626, 0.599],
            9.5:  [0.977, 0.939, 0.907, 0.877, 0.85, 0.824, 0.798, 0.774, 0.75, 0.723, 0.693, 0.667, 0.639, 0.612, 0.585],
            9:    [0.955, 0.922, 0.892, 0.863, 0.837, 0.811, 0.786, 0.762, 0.739, 0.707, 0.68, 0.653, 0.626, 0.599, 0.572],
            8.5:  [0.939, 0.907, 0.877, 0.85, 0.824, 0.798, 0.774, 0.75, 0.723, 0.693, 0.667, 0.639, 0.612, 0.585, 0.558],
            8:    [0.922, 0.892, 0.863, 0.837, 0.811, 0.786, 0.762, 0.739, 0.707, 0.68, 0.653, 0.626, 0.599, 0.572, 0.545],
            7.5:  [0.764, 0.7505, 0.723, 0.6935, 0.665, 0.636, 0.6125, 0.5855, 0.5585, 0.5315, 0.5045, 0.4775, 0.4505, 0.4235, 0.3965],
            7:    [0.762, 0.739, 0.707, 0.68, 0.653, 0.626, 0.599, 0.572, 0.545, 0.518, 0.491, 0.464, 0.437, 0.41, 0.383],
            6.5:  [0.7505, 0.723, 0.6935, 0.665, 0.6395, 0.6125, 0.5855, 0.5585, 0.5315, 0.5045, 0.4775, 0.4505, 0.4235, 0.3965, 0.3695],
            6:    [0.739, 0.707, 0.68, 0.653, 0.626, 0.599, 0.572, 0.545, 0.518, 0.491, 0.464, 0.437, 0.41, 0.383, 0.356],
            5.5:  [0.739, 0.707, 0.68, 0.653, 0.626, 0.599, 0.572, 0.545, 0.518, 0.491, 0.464, 0.437, 0.41, 0.383, 0.356],
            5:    [0.707, 0.68, 0.653, 0.626, 0.599, 0.572, 0.545, 0.518, 0.491, 0.464, 0.437, 0.41, 0.383, 0.356, 0.329],
            4.5:  [0.68, 0.653, 0.626, 0.599, 0.572, 0.545, 0.518, 0.491, 0.464, 0.437, 0.41, 0.383, 0.356, 0.329],
            4:    [0.653, 0.626, 0.599, 0.572, 0.545, 0.518, 0.491, 0.464, 0.437, 0.41, 0.383, 0.356, 0.329]
        }

        '''rpe_factor = rpe_factor_map.get(rpe, 1.0)
        one_rm = round(base_one_rm / rpe_factor, 1)'''
        def get_rpe_multiplier(rpe, reps):
            if rpe not in RPE_TABLE:
                return 1.0

            reps_index = reps - 1  # reps=1 → index 0

            row = RPE_TABLE[rpe]

            if reps_index < 0:
                return row[0]
            if reps_index >= len(row):
                return row[-1]

            return row[reps_index]
            
        base_one_rm = weight / get_rpe_multiplier(rpe, reps)
        one_rm = round(base_one_rm, 1)

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
        #duplicated part:
        '''headers = {
                "apikey": KEY,
                "Authorization": f"Bearer {KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
        }

        print("4. Sending to Supabase...")
        response = requests.post(URL, json=payload, headers=headers)
        print(f"5. Supabase Result: {response.status_code}") '''
        # end of duplication 
           
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


# ==========================
# GET TRENDS
# =========================
'''@app.route('/get_trends', methods=['GET'])
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
    
    return jsonify(response.json())'''
    #end of old version

@app.route('/get_trends', methods=['GET'])
def get_trends():
    user_id = request.args.get('user_id')

    response = (
        supabase
        .table("Trainings")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=False)
        .execute()
    )

    return jsonify(response.data)


if __name__ == '__main__':
    app.run(port=8000, debug=True)
