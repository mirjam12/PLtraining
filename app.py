from flask import Flask, render_template, request, jsonify
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Load your secrets
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

# Making sure my there are no URL issues:
if URL:
    TABLE_URL = f"{URL.rstrip('/')}/rest/v1/Trainings"
else:
    print("CRITICAL ERROR: SUPABASE_URL not found in .env file!")
    TABLE_URL = ""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_workout', methods=['POST'])
def add_workout():
    try:
        ui_data = request.json
        print("1. Data received from Website:", ui_data) # Check if data arrived

        # Extract values
        exercise = ui_data.get('exercise')
        weight_raw = ui_data.get('weight')
        reps_raw = ui_data.get('reps')
        user_id = ui_data.get('user_id')
        
        #print(f"2. Variables: Ex={exercise}, W={weight_raw}, R={reps_raw}")

        # Convert to numbers 
        weight = float(weight_raw)
        reps = int(reps_raw)

        # Math
        one_rm = round(weight * (36 / (37 - reps)), 1)
        print(f"3. Calculated 1RM: {one_rm}")

        # Supabase payload 
        payload = {
            "exercise": exercise,
            "Weight": weight, 
            "Reps": reps,     
            "1RM": one_rm,
            "user_id": user_id
        }

        headers = {
            "apikey": KEY,
            "Authorization": f"Bearer {KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }

        print("4. Sending to Supabase...")
        response = requests.post(TABLE_URL, json=payload, headers=headers)
        print(f"5. Supabase Result: {response.status_code}")
        
        if response.status_code in [200, 201]:
            return jsonify({"status": "success", "one_rm": one_rm})
        else:
            print("Supabase Error detail:", response.text)
            return jsonify({"status": "error", "message": response.text}), 400

    except Exception as e:
        # This will print the EXACT error in your terminal
        print("!!! PYTHON CRASHED !!! Error:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_trends', methods=['GET'])
def get_trends():
    headers = {
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}"
    }
    # Where to get the user_id (available on Supabase)
    user_id = request.args.get('user_id')
    
    # Fetch data sorted by date & filter based on user id
    query_url = f"{TABLE_URL}?user_id=eq.{user_id}&select=*&order=created_at.asc"

    response = requests.get(query_url, headers=headers)
    
    return jsonify(response.json())

if __name__ == '__main__':
    app.run(port=5000, debug=True)
