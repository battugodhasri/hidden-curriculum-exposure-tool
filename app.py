from asyncio import transports
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import json
import os
import PyPDF2

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_equity'

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
SKILLS_FILE = os.path.join(DATA_DIR, 'skills.json')

def load_data(file_path):
    if not os.path.exists(file_path):
        return {}
    with open(file_path, 'r') as f:
        try:
            return json.load(f)
        except:
            return {}

def save_data(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        users = load_data(USERS_FILE)
        
        found_user = None
        for uid, udata in users.items():
            if udata.get('email') == email and udata.get('password') == password:
                found_user = uid
                break
        
        if found_user:
            session['user'] = found_user
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials")
            return redirect(url_for('login'))
            
    return render_template('login.html', admin=False)

@app.route('/signup', methods=['POST'])
def signup():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    branch = request.form.get('branch')
    year = request.form.get('year')
    
    users = load_data(USERS_FILE)
    user_id = "u_" + str(len(users) + 1)
    
    users[user_id] = {
        "name": name,
        "email": email,
        "password": password,
        "branch": branch,
        "year": year,
        "metrics": {
            "career_readiness": 0,
            "roadmap_progress": 0,
            "weekly_streak": 0,
            "weak_areas": [],
            "current_week_task": "Upload Syllabus to Start"
        },
        "extracted_skills": [],
        "gap_analysis": {},
        "quiz_scores": []
    }
    
    save_data(USERS_FILE, users)
    session['user'] = user_id
    return redirect(url_for('dashboard'))

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email == 'admin@admin.com' and password == 'admin123':
            session['admin'] = True
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid Admin Credentials")
            return redirect(url_for('admin_login'))
    return render_template('login.html', admin=True)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session and 'admin' not in session:
        return redirect(url_for('login'))
    
    is_admin = 'admin' in session
    user_data = None
    if not is_admin:
        users = load_data(USERS_FILE)
        user_data = users.get(session['user'], {})
        
    return render_template('dashboard.html', user=user_data, is_admin=is_admin)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file uploaded")
            return redirect(url_for('upload'))
            
        file = request.files['file']
        if file.filename == '':
            flash("No selected file")
            return redirect(url_for('upload'))
            
        if file and file.filename.endswith('.pdf'):
            # Parse PDF
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
                
            text = text.lower()
            
            # Simple keyword parsing against skills
            skills = load_data(SKILLS_FILE)
            found_skills = []
            
            for skill in skills.keys():
                if skill.lower() in text:
                    found_skills.append(skill)
                    
            users = load_data(USERS_FILE)
            user_id = session['user']
            users[user_id]['extracted_skills'] = found_skills
            
            # Compute Gap Analysis
            total_skills = list(skills.keys())
            missing_skills = [s for s in total_skills if s not in found_skills]
            
            gap_data = {
                "found": found_skills,
                "missing": missing_skills,
                "missing_percentage": int((len(missing_skills) / len(total_skills)) * 100) if total_skills else 0
            }
            
            users[user_id]['gap_analysis'] = gap_data
            users[user_id]['metrics']['weak_areas'] = missing_skills[:2] # Top 2 missing
            users[user_id]['metrics']['career_readiness'] = 100 - gap_data['missing_percentage']
            users[user_id]['metrics']['roadmap_progress'] = 0
            users[user_id]['metrics']['weekly_streak'] = 1
            users[user_id]['metrics']['current_week_task'] = "Week 1: Fundamentals"
            
            save_data(USERS_FILE, users)
            return redirect(url_for('gap'))
            
    return render_template('upload.html')

@app.route('/gap')
def gap():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    users = load_data(USERS_FILE)
    user_data = users.get(session['user'], {})
    return render_template('gap.html', user=user_data)

@app.route('/gap-data')
def gap_data():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    users = load_data(USERS_FILE)
    user_data = users.get(session['user'], {})
    gap = user_data.get('gap_analysis', {})
    
    skills = load_data(SKILLS_FILE)
    all_skills = list(skills.keys())
    
    # Generate percentages (100% for found, random low for missing just to show gap dynamically per requirements)
    skill_percentages = []
    for s in all_skills:
        if s in gap.get('found', []):
            skill_percentages.append(85)
        else:
            skill_percentages.append(35)
            
    return jsonify({
        "labels": all_skills,
        "percentages": skill_percentages,
        "missing_percentage": gap.get('missing_percentage', 0)
    })

@app.route('/roadmap')
def roadmap():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    return render_template('roadmap.html')

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    questions = [
        {"q": "What does SQL stand for?", "options": ["Structured Query Language", "Strong Question Language", "System Query Lingo"], "ans": "Structured Query Language"},
        {"q": "Which JOIN returns all matching rows?", "options": ["INNER JOIN", "OUTER JOIN", "CROSS JOIN"], "ans": "INNER JOIN"},
        {"q": "A primary key uniquely identifies a?", "options": ["Table", "Row", "Database"], "ans": "Row"}
    ]
    
    if request.method == 'POST':
        score = 0
        for i, q in enumerate(questions):
            ans = request.form.get(f'q{i}')
            if ans == q['ans']:
                score += 1
                
        users = load_data(USERS_FILE)
        user_id = session['user']
        users[user_id]['quiz_scores'].append({"score": score, "total": len(questions)})
        users[user_id]['metrics']['roadmap_progress'] = min(100, users[user_id]['metrics']['roadmap_progress'] + 20)
        save_data(USERS_FILE, users)
        
        flash(f'Score: {score}/{len(questions)}')
        return render_template('quiz.html', questions=questions, score=score, total=len(questions))
        
    return render_template('quiz.html', questions=questions, score=None)

@app.route('/report')
def report():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    users = load_data(USERS_FILE)
    user_data = users.get(session['user'], {})
    return render_template('report.html', user=user_data)
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
