from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

app = Flask(__name__)

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(URL, KEY)


# =========================
# AUTH HELPERS
# =========================
def get_user_from_token(token):
    if not token:
        return None

    user = supabase.auth.get_user(token)
    if not user or not user.user:
        return None

    return user.user


def get_profile(user_id):
    return supabase.table("profiles") \
        .select("user_id,name,is_admin") \
        .eq("user_id", user_id) \
        .single() \
        .execute() \
        .data


def require_admin(token):
    user = get_user_from_token(token)
    if not user:
        return None, "Unauthorized"

    profile = get_profile(user.id)

    if not profile or not profile.get("is_admin"):
        return None, "Forbidden"

    return profile, None


# =========================
# FRONTEND ROUTES
# =========================
@app.route('/')
def index():
    return render_template("index.html")

# checking if coach or not
@app.route('/coach')
def coach():
    token = request.args.get("token")

    if not token:
        return "Unauthorized", 401

    user = supabase.auth.get_user(token)

    if not user or not user.user:
        return "Unauthorized", 401

    profile = supabase.table("profiles") \
        .select("is_admin") \
        .eq("user_id", user.user.id) \
        .single() \
        .execute() \
        .data

    if not profile or not profile.get("is_admin"):
        return "Forbidden", 403

    return render_template("coach.html")


# =========================
# ROLE CHECK
# =========================
@app.route('/me')
def me():
    token = request.args.get("token")

    user = get_user_from_token(token)
    if not user:
        return jsonify({"error": "invalid token"}), 401

    profile = get_profile(user.id)
    return jsonify(profile)


# =========================
# USERS (ADMIN ONLY)
# =========================
@app.route('/get_users')
def get_users():
    token = request.args.get("token")

    profile, err = require_admin(token)
    if err:
        return jsonify({"error": err}), 403

    users = supabase.table("profiles") \
        .select("user_id,name,is_admin") \
        .execute() \
        .data

    return jsonify(users)


# =========================
# TRAINING DATA
# =========================
@app.route('/get_trends')
def get_trends():
    user_id = request.args.get('user_id')

    data = supabase.table("Trainings") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("created_at", desc=False) \
        .execute()

    return jsonify(data.data)


@app.route('/get_user_progress')
def get_user_progress():
    user_id = request.args.get('user_id')

    data = supabase.table("Trainings") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("created_at", desc=False) \
        .execute()

    return jsonify(data.data)


# =========================
# ADD WORKOUT
# =========================
@app.route('/add_workout', methods=['POST'])
def add_workout():
    try:
        ui_data = request.json

        exercise = ui_data.get('exercise')
        weight = float(ui_data.get('weight'))
        reps = int(ui_data.get('reps'))
        rpe = float(ui_data.get('rpe') or 10)
        user_id = ui_data.get('user_id')

        RPE_TABLE = {
            10:  [100, 95.5, 92.2, 89.2, 86.3, 83.7],
            9:   [95.5, 92.2, 89.2, 86.3, 83.7, 81.1],
            8:   [92.2, 89.2, 86.3, 83.7, 81.1, 78.6],
            7:   [89.2, 86.3, 83.7, 81.1, 78.6, 76.2],
            6:   [86.3, 83.7, 81.1, 78.6, 76.2, 73.9],
            5:   [83.7, 81.1, 78.6, 76.2, 73.9, 70.7]
        }

        def get_pct(rpe, reps):
            row = RPE_TABLE.get(rpe, RPE_TABLE[10])
            idx = max(0, min(reps - 1, len(row) - 1))
            return row[idx]

        pct = get_pct(rpe, reps)
        one_rm = round(weight / (pct / 100), 1)

        payload = {
            "exercise": exercise,
            "weight": weight,
            "reps": reps,
            "rpe": rpe,
            "one_rm": one_rm,
            "user_id": user_id
        }

        supabase.table("Trainings").insert(payload).execute()

        return jsonify({"status": "success", "one_rm": one_rm})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# =========================
# RUN
# =========================
if __name__ == '__main__':
    app.run(port=8000, debug=True)