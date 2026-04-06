import os
import json
import pandas as pd
from dotenv import load_dotenv
load_dotenv()  # Auto-loads variables from .env file

from flask import Flask, render_template, request, redirect, url_for, session, flash
from data.db_manager import (
    init_db, get_user, verify_password, insert_review, get_all_reviews,
    get_reviews_by_status, claim_review, resolve_review, insert_capa,
    get_all_capa_logs, get_all_specs, get_all_partners,
    get_category_counts, get_status_counts, get_review_by_id,
    get_all_users, delete_user, create_user,
    insert_chat_message, get_chat_messages, get_live_operations
)
from services.groq_ai import categorize_and_analyze

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "atlas_pharma_secret_key_2026_demo")

# Initialize DB and seed data on startup
init_db()

# Auto-seed so fresh deploys have demo data
from data.seed_data import run_all_seeds
run_all_seeds()

# ─── Context Processors & Helpers ─────────────────────────────────────
@app.context_processor
def inject_active_page():
    return {'active_page': request.endpoint}

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("Please log in to access the portal.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ─── Public Routes ───────────────────────────────────────────────────

@app.route('/')
def home():
    return render_template('public/home.html')

@app.route('/catalog')
def catalog():
    return render_template('public/catalog.html')

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        product_type = request.form.get('product_type')
        batch_number = request.form.get('batch_number')
        review_text = request.form.get('review_text')
        
        # Call Gemini AI
        category, sentiment = categorize_and_analyze(review_text)
        
        insert_review(
            batch_number=batch_number,
            product_type=product_type,
            review_text=review_text,
            ai_category=category,
            ai_sentiment=sentiment
        )
        flash("Your feedback has been submitted successfully.", "success")
        return redirect(url_for('home'))
        
    return render_template('public/feedback.html')

@app.route('/about')
def about():
    return render_template('public/about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        flash("Message sent! (Demo mode - no actual email was dispatched)", "success")
        return redirect(url_for('contact'))
    return render_template('public/contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = get_user(username)
        if user and verify_password(password, user['password_hash']):
            session['user'] = {
                'id': user['id'],
                'username': user['username'],
                'full_name': user['full_name'],
                'role': user['role']
            }
            flash(f"Welcome back, {user['full_name']}!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password.", "danger")
            
    return render_template('public/login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("You have been signed out.", "info")
    return redirect(url_for('home'))

# ─── Internal Portal Routes ──────────────────────────────────────────

@app.route('/portal/dashboard')
@login_required
def dashboard():
    reviews = get_all_reviews()
    
    # Process with Pandas
    if not reviews:
        # Fallback if DB is empty
        df = pd.DataFrame(columns=['id', 'ai_category', 'status', 'created_at', 'Month', 'Date'])
        available_months = []
    else:
        # Convert sqlite3.Row elements to dictionary
        df = pd.DataFrame([dict(r) for r in reviews])
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['Month'] = df['created_at'].dt.strftime('%Y-%m')
        df['Date'] = df['created_at'].dt.strftime('%Y-%m-%d')
        df = df.sort_values('created_at')
        
        available_months = sorted(df['Month'].unique().tolist(), reverse=True)
        
    selected_month = request.args.get('month', 'All Time')
    
    # KPIs for Total
    total_all_time = len(df)
    
    # Filter by month if one is selected
    if selected_month != 'All Time' and not df.empty:
        df_filtered = df[df['Month'] == selected_month]
    else:
        df_filtered = df

    # Data for KPIs based on filtered (or all-time) selection
    total_selected = len(df_filtered)
    open_count = len(df_filtered[df_filtered['status'] == 'Open'])
    claimed_count = len(df_filtered[df_filtered['status'] == 'Claimed'])
    resolved_count = len(df_filtered[df_filtered['status'] == 'Resolved'])
    
    kpis = {
        'total_all_time': total_all_time,
        'selected_period': total_selected,
        'open': open_count,
        'claimed': claimed_count,
        'resolved': resolved_count,
        'current_month': selected_month
    }
    
    # Prepare standard charts data
    if not df_filtered.empty:
        cat_counts = df_filtered['ai_category'].value_counts().to_dict()
        status_counts = df_filtered['status'].value_counts().to_dict()
    else:
        cat_counts = {}
        status_counts = {}
        
    # Prepare Time-Series Trend Line Data
    trend_data = []
    if not df_filtered.empty:
        # Count reviews per day per category
        trend_df = df_filtered.groupby(['Date', 'ai_category']).size().reset_index(name='count')
        for cat in ['Critical', 'Major', 'Minor']:
            cat_data = trend_df[trend_df['ai_category'] == cat]
            color = '#dc3545' if cat == 'Critical' else ('#fd7e14' if cat == 'Major' else '#0d6efd')
            trend_data.append({
                'x': cat_data['Date'].tolist(),
                'y': cat_data['count'].tolist(),
                'type': 'scatter',
                'mode': 'lines+markers',
                'name': cat,
                'line': {'color': color, 'width': 3},
                'marker': {'size': 6}
            })
            
    recent_reviews = reviews[:5] if reviews else []
    
    return render_template('internal/dashboard.html', 
                          kpis=kpis, 
                          cat_data=cat_counts, 
                          status_data=status_counts,
                          trend_data_json=json.dumps(trend_data),
                          available_months=available_months,
                          selected_month=selected_month,
                          recent_reviews=recent_reviews)

@app.route('/portal/triage', methods=['GET'])
@login_required
def triage():
    status_filter = request.args.get('status', 'All')
    cat_filter = request.args.get('category', 'All')
    
    reviews = get_all_reviews()
    
    if status_filter != 'All':
        reviews = [r for r in reviews if r['status'] == status_filter]
    if cat_filter != 'All':
        reviews = [r for r in reviews if r['ai_category'] == cat_filter]
        
    return render_template('internal/triage.html', reviews=reviews)

@app.route('/portal/triage/claim/<int:review_id>', methods=['POST'])
@login_required
def claim_ticket(review_id):
    if session['user']['role'] != 'Quality Manager':
        flash("Only Quality Managers can claim tickets.", "danger")
        return redirect(url_for('triage'))
        
    claim_review(review_id, session['user']['full_name'])
    flash(f"Ticket #{review_id} claimed successfully.", "success")
    return redirect(url_for('triage'))

@app.route('/portal/specs')
@login_required
def specs():
    specs_data = get_all_specs()
    partners_data = get_all_partners()
    return render_template('internal/specs_partners.html', specs=specs_data, partners=partners_data)

@app.route('/portal/capa', methods=['GET', 'POST'])
@login_required
def capa():
    if session['user']['role'] != 'Quality Manager':
        flash("Only Quality Managers can log CAPA resolutions.", "danger")
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        review_id = request.form.get('review_id')
        root_cause = request.form.get('root_cause')
        corrective_action = request.form.get('corrective_action')
        preventive_action = request.form.get('preventive_action')
        
        insert_capa(
            review_id=review_id,
            root_cause=root_cause,
            corrective_action=corrective_action,
            preventive_action=preventive_action,
            manager_assigned=session['user']['full_name']
        )
        flash(f"CAPA logged and Ticket #{review_id} resolved.", "success")
        return redirect(url_for('capa'))
        
    claimed_reviews = [r for r in get_all_reviews() if r['status'] == 'Claimed' and r['claimed_by'] == session['user']['full_name']]
    capa_logs = get_all_capa_logs()
    
    return render_template('internal/capa.html', claimed_reviews=claimed_reviews, capa_logs=capa_logs)

@app.route('/portal/workflow')
@login_required
def workflow():
    cat_counts = get_category_counts()
    status_counts = get_status_counts()
    
    kpis = {
        'total': sum(status_counts.values()),
        'open': status_counts.get('Open', 0),
        'claimed': status_counts.get('Claimed', 0),
        'resolved': status_counts.get('Resolved', 0)
    }
    
    return render_template('internal/workflow.html', kpis=kpis, cat_counts=cat_counts)


@app.route('/portal/staff', methods=['GET', 'POST'])
@login_required
def staff():
    if session['user']['role'] != 'Executive':
        flash("Only Executives can access the Staff Directory.", "danger")
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        role = request.form.get('role')
        
        create_user(username, password, full_name, role)
        flash(f"User {full_name} created successfully.", "success")
        return redirect(url_for('staff'))
        
    users = get_all_users()
    
    # Process live operations data (group tickets by Quality Manager)
    live_ops_raw = get_live_operations()
    live_ops = {}
    for row in live_ops_raw:
        qm = row['full_name']
        if qm not in live_ops:
            live_ops[qm] = []
        if row['review_id']:
            live_ops[qm].append(row['review_id'])
            
    return render_template('internal/staff.html', users=users, live_ops=live_ops)


@app.route('/portal/staff/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_staff(user_id):
    if session['user']['role'] != 'Executive':
        flash("Unauthorized action.", "danger")
        return redirect(url_for('dashboard'))
        
    if session['user']['id'] == user_id:
        flash("You cannot delete yourself.", "warning")
        return redirect(url_for('staff'))
        
    delete_user(user_id)
    flash("User removed successfully.", "success")
    return redirect(url_for('staff'))


@app.route('/portal/chat')
@login_required
def chat():
    return render_template('internal/chat.html')


@app.route('/api/chat', methods=['GET', 'POST'])
@login_required
def api_chat():
    from flask import jsonify
    
    if request.method == 'POST':
        data = request.get_json()
        if not data or not data.get('message', '').strip():
            return jsonify({'error': 'Message required'}), 400
            
        insert_chat_message(session['user']['id'], data['message'].strip())
        return jsonify({'status': 'ok'}), 201
        
    messages = get_chat_messages(limit=100)
    # Serialize to dicts
    result = []
    for msg in messages:
        result.append({
            'id': msg['id'],
            'message': msg['message'],
            'created_at': msg['created_at'],
            'full_name': msg['full_name'],
            'role': msg['role'],
            'is_me': msg['full_name'] == session['user']['full_name']
        })
    return jsonify(result), 200

@app.route('/api/review/<int:review_id>', methods=['GET'])
@login_required
def api_review(review_id):
    from flask import jsonify
    
    review = get_review_by_id(review_id)
    if not review:
        return jsonify({'error': 'Review not found'}), 404
        
    return jsonify({
        'id': review['id'],
        'batch_number': review['batch_number'],
        'product_type': review['product_type'],
        'review_text': review['review_text'],
        'ai_category': review['ai_category']
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)
