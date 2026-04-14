import os
import json
import pandas as pd
from dotenv import load_dotenv
load_dotenv()  # Auto-loads variables from .env file

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from data.db_manager import (
    init_db, get_user, verify_password, insert_review, get_all_reviews,
    get_reviews_by_status, claim_review, resolve_review, insert_capa,
    get_all_capa_logs, get_all_specs, get_all_partners,
    get_category_counts, get_status_counts, get_review_by_id,
    get_all_users, delete_user, create_user,
    insert_chat_message, get_chat_messages, get_live_operations,
    get_distinct_qc_products, get_qc_checklists_by_product,
    insert_batch_record, get_batch_records_by_batch,
    get_batch_records_for_spc, get_distinct_checkpoints,
    insert_spec, delete_spec, update_spec, insert_bulk_specs,
    get_all_products, get_active_products, get_or_create_product,
    get_product_by_name, get_product_by_id, update_product,
    delete_product, get_distinct_batches,
    VALID_DEFECT_TYPES
)
from data.aql_tables import get_aql_sample_size, get_available_aql_values, get_available_inspection_levels
from services.groq_ai import categorize_and_analyze

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "atlas_pharma_secret_key_2026_demo")
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}

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

def role_required(*roles):
    """Restrict a route to specific user roles."""
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                flash("Please log in to access the portal.", "warning")
                return redirect(url_for('login'))
            if session['user']['role'] not in roles:
                flash("You don't have permission to access this page.", "danger")
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ─── Public Routes ───────────────────────────────────────────────────

@app.route('/')
def home():
    return render_template('public/home.html')

@app.route('/catalog')
def catalog():
    products = get_active_products()
    return render_template('public/catalog.html', products=products)

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
    
    # Populate product dropdown from DB
    products = get_all_products()
    return render_template('public/feedback.html', products=products)

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
    products = get_all_products()
    return render_template('internal/specs_partners.html', specs=specs_data, partners=partners_data,
                           products=products, defect_types=VALID_DEFECT_TYPES)

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


# ─── QC Data Entry Routes ────────────────────────────────────────────

@app.route('/portal/qc-entry', methods=['GET', 'POST'])
@login_required
def qc_entry():
    if session['user']['role'] not in ('Quality Manager', 'Executive'):
        flash("Only Quality Managers can access QC Data Entry.", "danger")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        batch_number = data.get('batch_number', '').strip()
        product_name = data.get('product_name', '').strip()
        tests = data.get('tests', [])

        if not batch_number or not product_name or not tests:
            return jsonify({'error': 'Missing required fields'}), 400

        saved_count = 0
        for test in tests:
            try:
                insert_batch_record(
                    batch_number=batch_number,
                    product_name=product_name,
                    checklist_id=int(test['checklist_id']),
                    checkpoint=test['checkpoint'],
                    individual_values=json.dumps(test['values']),
                    sample_count=int(test['sample_count']),
                    mean=float(test['mean']),
                    range_val=float(test['range']),
                    tol_min=float(test['tol_min']) if test.get('tol_min') is not None else None,
                    tol_max=float(test['tol_max']) if test.get('tol_max') is not None else None,
                    status=test['status'],
                    tested_by=session['user']['full_name']
                )
                saved_count += 1
            except Exception as e:
                return jsonify({'error': f'Failed to save {test["checkpoint"]}: {str(e)}'}), 500

        return jsonify({'status': 'ok', 'saved': saved_count}), 201

    products = get_distinct_qc_products()
    return render_template('internal/qc_entry.html', products=products)


@app.route('/api/qc-checklist/<path:product_name>')
@login_required
def api_qc_checklist(product_name):
    """Return QC checklist items for a product as JSON."""
    checklists = get_qc_checklists_by_product(product_name)
    result = []
    for cl in checklists:
        result.append({
            'id': cl['id'],
            'checkpoint': cl['checkpoint'],
            'sample_size': cl['sample_size'],
            'sample_count': cl['sample_count'],
            'tolerance': cl['tolerance'],
            'unit': cl['unit'],
            'tol_min': cl['tol_min'],
            'tol_max': cl['tol_max'],
            'test_type': cl['test_type'],
            'test_method': cl['test_method']
        })
    return jsonify(result), 200


@app.route('/api/batch-records/<path:batch_number>')
@login_required
def api_batch_records(batch_number):
    """Return QC test results for a specific batch."""
    records = get_batch_records_by_batch(batch_number)
    result = []
    for r in records:
        result.append({
            'id': r['id'],
            'batch_number': r['batch_number'],
            'checkpoint': r['checkpoint'],
            'individual_values': json.loads(r['individual_values']),
            'sample_count': r['sample_count'],
            'mean': r['mean'],
            'range_val': r['range_val'],
            'tol_min': r['tol_min'],
            'tol_max': r['tol_max'],
            'status': r['status'],
            'tested_by': r['tested_by'],
            'tested_at': r['tested_at'],
            'tolerance': r['tolerance'],
            'unit': r['unit'],
            'sample_size': r['sample_size']
        })
    return jsonify(result), 200


# ─── SPC Dashboard Routes ────────────────────────────────────────────

@app.route('/portal/spc')
@login_required
def spc_dashboard():
    if session['user']['role'] not in ('Quality Manager', 'Executive'):
        flash("Access denied.", "danger")
        return redirect(url_for('dashboard'))

    products = get_distinct_qc_products()
    return render_template('internal/spc_dashboard.html', products=products)


@app.route('/api/spc-data')
@login_required
def api_spc_data():
    """Return SPC chart data for a product+checkpoint combination."""
    product = request.args.get('product', '')
    checkpoint = request.args.get('checkpoint', '')

    if not product or not checkpoint:
        return jsonify({'error': 'Product and checkpoint required'}), 400

    records = get_batch_records_for_spc(product, checkpoint)
    if not records:
        return jsonify({'batches': [], 'means': [], 'ranges': []}), 200

    batches = [r['batch_number'] for r in records]
    means = [r['mean'] for r in records]
    ranges = [r['range_val'] for r in records]
    sample_count = records[0]['sample_count']
    tol_min = records[0]['tol_min']
    tol_max = records[0]['tol_max']

    # Calculate grand mean (X-double-bar) and average range (R-bar)
    x_double_bar = sum(means) / len(means) if means else 0
    r_bar = sum(ranges) / len(ranges) if ranges else 0

    # A2, D3, D4 constants for X-bar and R chart (standard SPC tables)
    spc_constants = {
        1:  {'A2': 2.660, 'D3': 0.000, 'D4': 3.267},
        2:  {'A2': 1.880, 'D3': 0.000, 'D4': 3.267},
        3:  {'A2': 1.023, 'D3': 0.000, 'D4': 2.574},
        4:  {'A2': 0.729, 'D3': 0.000, 'D4': 2.282},
        5:  {'A2': 0.577, 'D3': 0.000, 'D4': 2.114},
        6:  {'A2': 0.483, 'D3': 0.000, 'D4': 2.004},
        7:  {'A2': 0.419, 'D3': 0.076, 'D4': 1.924},
        8:  {'A2': 0.373, 'D3': 0.136, 'D4': 1.864},
        9:  {'A2': 0.337, 'D3': 0.184, 'D4': 1.816},
        10: {'A2': 0.308, 'D3': 0.223, 'D4': 1.777},
    }

    n = min(sample_count, 10)
    constants = spc_constants.get(n, spc_constants[5])

    ucl_xbar = round(x_double_bar + constants['A2'] * r_bar, 4)
    lcl_xbar = round(x_double_bar - constants['A2'] * r_bar, 4)
    ucl_r = round(constants['D4'] * r_bar, 4)
    lcl_r = round(constants['D3'] * r_bar, 4)

    return jsonify({
        'batches': batches,
        'means': means,
        'ranges': ranges,
        'x_double_bar': round(x_double_bar, 4),
        'r_bar': round(r_bar, 4),
        'ucl_xbar': ucl_xbar,
        'lcl_xbar': lcl_xbar,
        'ucl_r': ucl_r,
        'lcl_r': lcl_r,
        'tol_min': tol_min,
        'tol_max': tol_max,
        'sample_count': sample_count
    }), 200


@app.route('/api/checkpoints')
@login_required
def api_checkpoints():
    """Return checkpoints for a product."""
    product = request.args.get('product', '')
    if not product:
        return jsonify([]), 200
    checkpoints = get_distinct_checkpoints(product)
    return jsonify(checkpoints), 200


@app.route('/api/batches')
@login_required
def api_batches():
    """Return distinct batch numbers for a product."""
    product = request.args.get('product', '')
    if not product:
        return jsonify([]), 200
    batches = get_distinct_batches(product)
    return jsonify(batches), 200


@app.route('/api/batch-summary/<path:batch_number>')
@login_required
def api_batch_summary(batch_number):
    """Return all checkpoint results for a batch, with summary stats."""
    records = get_batch_records_by_batch(batch_number)
    if not records:
        return jsonify({'batch_number': batch_number, 'tests': [], 'summary': {}}), 200

    tests = []
    pass_count = 0
    fail_count = 0
    for r in records:
        test = {
            'id': r['id'],
            'checkpoint': r['checkpoint'],
            'individual_values': json.loads(r['individual_values']),
            'sample_count': r['sample_count'],
            'mean': r['mean'],
            'range_val': r['range_val'],
            'tol_min': r['tol_min'],
            'tol_max': r['tol_max'],
            'status': r['status'],
            'tested_by': r['tested_by'],
            'tested_at': r['tested_at'],
            'tolerance': r.get('tolerance', ''),
            'unit': r.get('unit', ''),
            'sample_size': r.get('sample_size', ''),
        }
        tests.append(test)
        if r['status'] == 'PASS':
            pass_count += 1
        else:
            fail_count += 1

    return jsonify({
        'batch_number': batch_number,
        'product_name': records[0]['product_name'] if records else '',
        'tests': tests,
        'summary': {
            'total': len(tests),
            'passed': pass_count,
            'failed': fail_count,
            'tested_by': records[0]['tested_by'] if records else '',
            'tested_at': records[0]['tested_at'] if records else '',
        }
    }), 200


# ─── AQL Sampling API ────────────────────────────────────────────────

@app.route('/api/aql-sample')
@login_required
def api_aql_sample():
    """Calculate AQL sample size per ANSI/ASQ Z1.4 or Z1.9."""
    try:
        batch_size = int(request.args.get('batch_size', 0))
        level = request.args.get('level', 'II')
        aql = float(request.args.get('aql', 1.0))
        sampling_type = request.args.get('type', 'attributes')
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid parameters'}), 400

    if batch_size < 2:
        return jsonify({'error': 'Batch size must be at least 2'}), 400

    result = get_aql_sample_size(batch_size, level, aql, sampling_type)
    return jsonify(result), 200


# ─── Product Management Routes (Executive) ───────────────────────────

@app.route('/portal/products')
@login_required
def product_management():
    if session['user']['role'] != 'Executive':
        flash("Only Executives can access Product Management.", "danger")
        return redirect(url_for('dashboard'))
    products = get_all_products()
    return render_template('internal/product_management.html', products=products)


@app.route('/portal/products/add', methods=['POST'])
@login_required
def add_product():
    if session['user']['role'] != 'Executive':
        flash("Unauthorized.", "danger")
        return redirect(url_for('dashboard'))

    name = request.form.get('product_name', '').strip()
    form = request.form.get('form', '').strip()
    description = request.form.get('description', '').strip()
    category = request.form.get('category', '').strip()
    buy_link = request.form.get('buy_link', '').strip()
    dosage_form = request.form.get('dosage_form', '').strip()

    if not name:
        flash("Product name is required.", "warning")
        return redirect(url_for('product_management'))

    product_id = get_or_create_product(name, form)
    update_product(
        product_id,
        description=description or None,
        category=category or None,
        buy_link=buy_link or None,
        dosage_form=dosage_form or None,
        is_active=1,
    )

    # Handle image upload
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename:
            ext = file.filename.rsplit('.', 1)[-1].lower()
            if ext in ALLOWED_IMAGE_EXTENSIONS:
                upload_dir = os.path.join(app.static_folder, 'images', 'products')
                os.makedirs(upload_dir, exist_ok=True)
                filename = f"product_{product_id}.{ext}"
                file.save(os.path.join(upload_dir, filename))
                update_product(product_id, image_url=f"/static/images/products/{filename}")

    flash(f"Product '{name}' added successfully.", "success")
    return redirect(url_for('product_management'))


@app.route('/portal/products/edit/<int:product_id>', methods=['POST'])
@login_required
def edit_product(product_id):
    if session['user']['role'] != 'Executive':
        flash("Unauthorized.", "danger")
        return redirect(url_for('dashboard'))

    name = request.form.get('product_name', '').strip()
    form = request.form.get('form', '').strip()
    description = request.form.get('description', '').strip()
    category = request.form.get('category', '').strip()
    buy_link = request.form.get('buy_link', '').strip()
    dosage_form = request.form.get('dosage_form', '').strip()

    update_product(
        product_id,
        product_name=name or None,
        form=form or None,
        description=description or None,
        category=category or None,
        buy_link=buy_link or None,
        dosage_form=dosage_form or None,
    )

    # Handle image upload
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename:
            ext = file.filename.rsplit('.', 1)[-1].lower()
            if ext in ALLOWED_IMAGE_EXTENSIONS:
                upload_dir = os.path.join(app.static_folder, 'images', 'products')
                os.makedirs(upload_dir, exist_ok=True)
                filename = f"product_{product_id}.{ext}"
                file.save(os.path.join(upload_dir, filename))
                update_product(product_id, image_url=f"/static/images/products/{filename}")

    flash(f"Product updated successfully.", "success")
    return redirect(url_for('product_management'))


@app.route('/portal/products/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product_route(product_id):
    if session['user']['role'] != 'Executive':
        flash("Unauthorized.", "danger")
        return redirect(url_for('dashboard'))

    if session['user']['id'] == product_id:
        flash("Cannot delete.", "warning")
        return redirect(url_for('product_management'))

    delete_product(product_id)
    flash("Product deactivated.", "success")
    return redirect(url_for('product_management'))


@app.route('/portal/products/upload-image/<int:product_id>', methods=['POST'])
@login_required
def upload_product_image(product_id):
    if session['user']['role'] != 'Executive':
        return jsonify({'error': 'Unauthorized'}), 403

    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    if not file.filename:
        return jsonify({'error': 'No file selected'}), 400

    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({'error': f'Invalid file type. Allowed: {ALLOWED_IMAGE_EXTENSIONS}'}), 400

    upload_dir = os.path.join(app.static_folder, 'images', 'products')
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"product_{product_id}.{ext}"
    file.save(os.path.join(upload_dir, filename))
    image_url = f"/static/images/products/{filename}"
    update_product(product_id, image_url=image_url)

    return jsonify({'status': 'ok', 'image_url': image_url}), 200


@app.route('/portal/specs/import', methods=['POST'])
@login_required
def import_specs():
    """Bulk import specifications from JSON (parsed Excel)."""
    if session['user']['role'] not in ('Quality Manager', 'Executive'):
        flash("Unauthorized.", "danger")
        return redirect(url_for('specs'))

    product_name = request.form.get('product_name')
    form = request.form.get('form')
    rows_json = request.form.get('rows_json')

    if not all([product_name, form, rows_json]):
        flash("Missing import data.", "warning")
        return redirect(url_for('specs'))

    try:
        rows = json.loads(rows_json)
        insert_bulk_specs(product_name, form, rows)
        flash(f"Successfully imported {len(rows)} specifications for {product_name}.", "success")
    except Exception as e:
        flash(f"Import failed: {str(e)}", "danger")

    return redirect(url_for('specs'))


@app.route('/portal/specs/add', methods=['POST'])
@login_required
def add_spec():
    if session['user']['role'] not in ('Quality Manager', 'Executive'):
        flash("Unauthorized.", "danger")
        return redirect(url_for('specs'))

    # Match new schema
    p_name = request.form.get('product_name')
    form = request.form.get('form')
    checkpoint = request.form.get('checkpoint')
    sample = request.form.get('sample_size')
    method = request.form.get('test_method')
    tolerance = request.form.get('tolerance')
    pass_fail = request.form.get('pass_fail')
    defect = request.form.get('defect_type')

    if all([p_name, form, checkpoint]):
        insert_spec(p_name, form, checkpoint, sample, method, tolerance, pass_fail, defect)
        flash("Specification added.", "success")
    else:
        flash("All fields are required.", "warning")

    return redirect(url_for('specs'))


@app.route('/portal/specs/delete/<int:spec_id>', methods=['POST'])
@login_required
def remove_spec(spec_id):
    if session['user']['role'] not in ('Quality Manager', 'Executive'):
        flash("You don't have permission to delete specifications.", "danger")
        return redirect(url_for('specs'))

    delete_spec(spec_id)
    flash("Specification removed.", "success")
    return redirect(url_for('specs'))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Enable Debug Mode so templates reload instantly and code changes auto-restart.
    app.run(debug=True, host='0.0.0.0', port=port)
