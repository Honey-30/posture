from flask import Flask, jsonify, request, session
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime, timedelta
import json

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"], supports_credentials=True)
app.secret_key = 'fitness-app-secret-key'

# Database setup
def init_db():
    if not os.path.exists('fitness.db'):
        conn = sqlite3.connect('fitness.db')
        cursor = conn.cursor()
        
        # Basic users table
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                email TEXT UNIQUE,
                password TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Sample user
        cursor.execute('''
            INSERT INTO users (username, email, password) 
            VALUES (?, ?, ?)
        ''', ('demo', 'demo@example.com', 'demo123'))
        
        # Workout sessions
        cursor.execute('''
            CREATE TABLE workout_sessions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                total_exercises INTEGER DEFAULT 0,
                avg_score REAL DEFAULT 0.0
            )
        ''')
        
        # Sample data
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            cursor.execute('''
                INSERT INTO workout_sessions (user_id, start_time, end_time, total_exercises, avg_score)
                VALUES (?, ?, ?, ?, ?)
            ''', (1, date, date + timedelta(hours=1), 5 + i, 70 + i * 3))
        
        # Nutrition logs
        cursor.execute('''
            CREATE TABLE nutrition_logs (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                food_name TEXT,
                meal_type TEXT,
                calories INTEGER,
                protein REAL,
                carbs REAL,
                fats REAL,
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Water intake
        cursor.execute('''
            CREATE TABLE water_intake (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                amount_ml INTEGER,
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Posture logs
        cursor.execute('''
            CREATE TABLE posture_logs (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                posture_score REAL,
                recommendations TEXT,
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

# Routes
@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    return jsonify({
        'id': 1,
        'username': 'demo',
        'email': 'demo@example.com'
    })

@app.route('/api/auth/login', methods=['POST'])
def login():
    session['user_id'] = 1
    return jsonify({'message': 'Logged in successfully'})

@app.route('/api/auth/register', methods=['POST'])
def register():
    session['user_id'] = 1
    return jsonify({'message': 'Registered successfully'})

@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    conn = sqlite3.connect('fitness.db')
    cursor = conn.cursor()
    
    # Weekly trend
    cursor.execute('''
        SELECT DATE(start_time) as date, AVG(avg_score) as avg_score
        FROM workout_sessions 
        WHERE user_id = 1 AND start_time >= date('now', '-7 days')
        GROUP BY DATE(start_time)
        ORDER BY date
    ''')
    weekly_data = [{'date': row[0], 'avg_score': row[1]} for row in cursor.fetchall()]
    
    # Water intake today
    cursor.execute('''
        SELECT COALESCE(SUM(amount_ml), 0) as total_ml
        FROM water_intake 
        WHERE user_id = 1 AND DATE(logged_at) = DATE('now')
    ''')
    total_water = cursor.fetchone()[0]
    
    # Today's nutrition
    cursor.execute('''
        SELECT COALESCE(SUM(calories), 0) as total_calories,
               COALESCE(SUM(protein), 0) as total_protein,
               COALESCE(SUM(carbs), 0) as total_carbs,
               COALESCE(SUM(fats), 0) as total_fats
        FROM nutrition_logs 
        WHERE user_id = 1 AND DATE(logged_at) = DATE('now')
    ''')
    nutrition_row = cursor.fetchone()
    
    # Latest posture data
    cursor.execute('''
        SELECT posture_score, recommendations
        FROM posture_logs 
        WHERE user_id = 1
        ORDER BY logged_at DESC
        LIMIT 1
    ''')
    posture_row = cursor.fetchone()
    
    conn.close()
    
    return jsonify({
        'weekly_trend': weekly_data,
        'water_data': {
            'totalMl': total_water,
            'percentage': min((total_water / 2000) * 100, 100)
        },
        'nutrition_data': {
            'calories': nutrition_row[0] if nutrition_row else 0,
            'protein': nutrition_row[1] if nutrition_row else 0,
            'carbs': nutrition_row[2] if nutrition_row else 0,
            'fats': nutrition_row[3] if nutrition_row else 0
        },
        'posture_data': {
            'score': posture_row[0] if posture_row else 85,
            'status': 'Good' if (posture_row and posture_row[0] > 80) else 'Needs Improvement',
            'recommendations': json.loads(posture_row[1]) if posture_row and posture_row[1] else [
                'Keep your shoulders back and relaxed',
                'Align your ears over your shoulders',
                'Take breaks every 30 minutes to stretch'
            ]
        },
        'stats': {
            'total_workouts': 15,
            'total_minutes': 450,
            'total_calories': 2250,
            'current_streak': 5
        }
    })

@app.route('/api/nutrition/log', methods=['POST'])
def log_nutrition():
    data = request.get_json()
    conn = sqlite3.connect('fitness.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO nutrition_logs (user_id, food_name, meal_type, calories, protein, carbs, fats)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (1, data['food_name'], data['meal_type'], data['calories'], 
          data['protein'], data['carbs'], data['fats']))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Nutrition logged successfully'})

@app.route('/api/nutrition/water', methods=['POST'])
def log_water():
    data = request.get_json()
    conn = sqlite3.connect('fitness.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO water_intake (user_id, amount_ml)
        VALUES (?, ?)
    ''', (1, data['amount']))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Water intake logged successfully'})

@app.route('/api/nutrition/bmi', methods=['POST'])
def calculate_bmi():
    data = request.get_json()
    height_m = data['height'] / 100  # Convert cm to meters
    weight = data['weight']
    bmi = round(weight / (height_m ** 2), 1)
    
    if bmi < 18.5:
        category = 'Underweight'
    elif bmi < 25:
        category = 'Normal'
    elif bmi < 30:
        category = 'Overweight'
    else:
        category = 'Obese'
    
    return jsonify({
        'bmi': bmi,
        'category': category
    })

@app.route('/api/posture/analyze', methods=['POST'])
def analyze_posture():
    # Simulate posture analysis
    import random
    score = random.randint(75, 95)
    
    conn = sqlite3.connect('fitness.db')
    cursor = conn.cursor()
    
    recommendations = json.dumps([
        'Keep your shoulders back and relaxed',
        'Align your ears over your shoulders',
        'Take breaks every 30 minutes to stretch'
    ])
    
    cursor.execute('''
        INSERT INTO posture_logs (user_id, posture_score, recommendations)
        VALUES (?, ?, ?)
    ''', (1, score, recommendations))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'score': score,
        'status': 'Good' if score > 80 else 'Needs Improvement',
        'recommendations': json.loads(recommendations)
    })

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=8002, debug=True)
