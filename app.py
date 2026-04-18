import os
import json
import pandas as pd
from dotenv import load_dotenv
load_dotenv()  # Auto-loads variables from .env file

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from data.db_manager import (
    init_db, get_user, verify_password, insert_review, get_all_reviews,
    get_reviews_by_status, claim_review, resolve_review, insert_capa,
    get_all_capa_logs, get_all_partners,
    get_category_counts, get_status_counts, get_review_by_id,
    get_all_users, delete_user, create_user,
    insert_chat_message, get_chat_messages, get_live_operations,
    get_distinct_qc_products, get_qc_checklists_by_product,
    insert_batch_record, get_batch_records_by_batch,
    get_batch_records_for_spc, get_distinct_checkpoints,
    get_all_products, get_active_products, get_or_create_product,
    get_product_by_name, get_product_by_id, update_product,
    delete_product, get_distinct_batches,
    VALID_DEFECT_TYPES,
    # Stage-based manufacturing
    get_all_stages, get_stage_by_code, get_stage_by_id, get_checkpoints_by_stage,
    get_checkpoint_by_id, get_stages_for_product,
    create_material_lot, get_all_material_lots, get_material_lot_by_id,
    update_material_lot_status,
    create_batch, get_batch, get_batch_by_number, get_all_batches, update_batch_status,
    link_batch_material, get_batch_materials,
    insert_batch_stage_result, get_batch_stage_results, get_stage_result, can_start_stage,
    insert_capa_from_qc, get_all_capa_logs_extended,
    # Stage checkpoint library
    get_stage_library, update_stage_checkpoint_field, insert_custom_stage_checkpoint,
    deactivate_stage_checkpoint, get_checkpoint_audit_log, EDITABLE_CHECKPOINT_FIELDS,
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
    """Stage Checkpoint Library — the GMP master spec page."""
    library = get_stage_library()
    partners_data = get_all_partners()
    # Stats for the header
    total_checkpoints = sum(len(st['checkpoints']) for layer in library for st in layer['stages'])
    total_stages = sum(len(layer['stages']) for layer in library)
    return render_template(
        'internal/specs_partners.html',
        library=library,
        partners=partners_data,
        total_checkpoints=total_checkpoints,
        total_stages=total_stages,
        defect_types=['Critical', 'Major', 'Minor', 'Informational'],
    )

@app.route('/portal/capa', methods=['GET', 'POST'])
@login_required
def capa():
    if session['user']['role'] not in ('Quality Manager', 'Admin'):
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
    capa_logs = get_all_capa_logs_extended()
    batches = get_all_batches(status='In-Progress')
    stages = get_all_stages()

    return render_template('internal/capa.html', claimed_reviews=claimed_reviews,
                           capa_logs=capa_logs, batches=batches, stages=stages)

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


@app.route('/api/batch-info/<int:batch_id>')
@login_required
def api_batch_info(batch_id):
    """Return basic batch info (batch_number, batch_size, product_name) for pre-filling AQL."""
    b = get_batch(batch_id)
    if not b:
        return jsonify({'error': 'Batch not found'}), 404
    return jsonify({
        'batch_number': b['batch_number'],
        'batch_size': b['batch_size'],
        'product_name': b['product_name'],
        'status': b['status'],
    })


@app.route('/api/stage-qc-submit', methods=['POST'])
@login_required
def api_stage_qc_submit():
    """Accept stage-based QC results and insert into batch_records.

    Expected JSON body:
    {
        "batch_id": 1,
        "stage_id": 3,
        "batch_size": 50000,
        "aql_level": "1.0",
        "results": [
            {"checkpoint_id": 12, "checkpoint_name": "Hardness", "result_type": "numeric",
             "samples": ["85.2", "87.1", "83.4"]},
            {"checkpoint_id": 13, "checkpoint_name": "Appearance", "result_type": "passfail",
             "samples": ["PASS", "PASS", "PASS"]},
            ...
        ]
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    batch_id = data.get('batch_id')
    stage_id = data.get('stage_id')
    batch_size = data.get('batch_size')
    aql_level = data.get('aql_level', '')
    results = data.get('results', [])

    if not batch_id or not stage_id:
        return jsonify({'error': 'batch_id and stage_id are required'}), 400

    batch = get_batch(batch_id)
    if not batch:
        return jsonify({'error': 'Batch not found'}), 404

    batch_number = batch['batch_number']
    product_name = batch['product_name']
    tested_by = session['user']['full_name']

    saved_count = 0
    errors = []

    for r in results:
        cp_name = r.get('checkpoint_name', '')
        result_type = r.get('result_type', 'numeric')
        raw_samples = [str(v).strip() for v in r.get('samples', []) if str(v).strip()]

        if not raw_samples:
            continue  # skip unanswered checkpoints

        try:
            if result_type == 'numeric':
                numeric_vals = []
                for v in raw_samples:
                    try:
                        numeric_vals.append(float(v))
                    except ValueError:
                        pass
                if not numeric_vals:
                    continue
                mean = round(sum(numeric_vals) / len(numeric_vals), 4)
                range_val = round(max(numeric_vals) - min(numeric_vals), 4)
                # Tolerance check via stage_checkpoint tol_min / tol_max
                cp = get_checkpoint_by_id(r.get('checkpoint_id')) if r.get('checkpoint_id') else None
                tol_min = float(cp['tol_min']) if cp and cp['tol_min'] is not None else None
                tol_max = float(cp['tol_max']) if cp and cp['tol_max'] is not None else None
                # Check each bound independently so one-sided specs (e.g. "<= 5%") still validate.
                if tol_min is None and tol_max is None:
                    status = 'PASS'  # No numeric spec; informational only
                else:
                    passes_lo = (tol_min is None) or (mean >= tol_min)
                    passes_hi = (tol_max is None) or (mean <= tol_max)
                    status = 'PASS' if (passes_lo and passes_hi) else 'FAIL'
                indiv_json = json.dumps(numeric_vals)
                sample_count = len(numeric_vals)

            elif result_type == 'passfail':
                fail_count = sum(1 for v in raw_samples if v.upper() in ('FAIL', 'F', 'NO'))
                status = 'FAIL' if fail_count > 0 else 'PASS'
                mean = None
                range_val = None
                tol_min = None
                tol_max = None
                indiv_json = json.dumps(raw_samples)
                sample_count = len(raw_samples)

            else:  # text
                status = 'PASS'
                mean = None
                range_val = None
                tol_min = None
                tol_max = None
                indiv_json = json.dumps(raw_samples)
                sample_count = len(raw_samples)

            insert_batch_record(
                batch_number=batch_number,
                product_name=product_name,
                checklist_id=None,
                checkpoint=cp_name,
                individual_values=indiv_json,
                sample_count=sample_count,
                mean=mean,
                range_val=range_val,
                tol_min=tol_min,
                tol_max=tol_max,
                status=status,
                tested_by=tested_by,
                batch_id=batch_id,
                stage_id=stage_id,
                batch_size=batch_size,
                aql_level=aql_level,
            )
            saved_count += 1

        except Exception as e:
            errors.append(f'{cp_name}: {str(e)}')

    if errors:
        return jsonify({'status': 'partial', 'saved': saved_count, 'errors': errors}), 207

    return jsonify({'status': 'ok', 'saved': saved_count}), 201


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
    stages = get_all_stages()
    return render_template('internal/spc_dashboard.html', products=products, stages=stages)


@app.route('/api/spc-data')
@login_required
def api_spc_data():
    """Return SPC chart data for a product+checkpoint combination."""
    product = request.args.get('product', '')
    checkpoint = request.args.get('checkpoint', '')
    stage_id = request.args.get('stage_id', type=int)

    if not product or not checkpoint:
        return jsonify({'error': 'Product and checkpoint required'}), 400

    records = get_batch_records_for_spc(product, checkpoint, stage_id=stage_id)
    if not records:
        return jsonify({'batches': [], 'chart_type': 'variable', 'means': [], 'ranges': []}), 200

    # Detect chart type: if any row has non-null mean, treat as variables (X-bar/R).
    # Otherwise if rows have 'PASS'/'FAIL' individuals, treat as attributes (p-chart).
    has_numeric = any(r['mean'] is not None for r in records)

    batches = [r['batch_number'] for r in records]

    # ── Variables data (numeric) ────────────────────────────────────────
    if has_numeric:
        means = [r['mean'] if r['mean'] is not None else 0.0 for r in records]
        ranges = [r['range_val'] if r['range_val'] is not None else 0.0 for r in records]
        individuals = []
        for r in records:
            try:
                vals = json.loads(r['individual_values']) if r['individual_values'] else []
                individuals.append([float(v) for v in vals if isinstance(v, (int, float)) or
                                    (isinstance(v, str) and v.replace('.', '', 1).lstrip('-').isdigit())])
            except (ValueError, TypeError):
                individuals.append([])

        sample_count = records[0]['sample_count'] or 1
        tol_min = records[0]['tol_min']
        tol_max = records[0]['tol_max']

        x_double_bar = sum(means) / len(means) if means else 0
        r_bar = sum(ranges) / len(ranges) if ranges else 0

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
        n = max(1, min(sample_count, 10))
        c = spc_constants.get(n, spc_constants[5])
        ucl_xbar = round(x_double_bar + c['A2'] * r_bar, 4)
        lcl_xbar = round(x_double_bar - c['A2'] * r_bar, 4)
        ucl_r = round(c['D4'] * r_bar, 4)
        lcl_r = round(c['D3'] * r_bar, 4)

        # Flatten all individual samples into a single ordered sequence
        flat_values = []
        batch_boundaries = []  # {sample_index, label} marks where each batch starts
        for batchIdx, samples in enumerate(individuals):
            batch_boundaries.append({'sample_index': len(flat_values), 'label': batches[batchIdx]})
            flat_values.extend(samples)

        return jsonify({
            'chart_type': 'variable',
            'batches': batches,
            'means': means,
            'ranges': ranges,
            'individuals': individuals,
            'flat_values': flat_values,
            'batch_boundaries': batch_boundaries,
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

    # ── Attributes data (PASS/FAIL) — p-chart ───────────────────────────
    import math
    sample_sizes = []
    fail_counts = []
    fail_rates = []
    for r in records:
        try:
            vals = json.loads(r['individual_values']) if r['individual_values'] else []
        except (ValueError, TypeError):
            vals = []
        n = len(vals) or (r['sample_count'] or 1)
        d = sum(1 for v in vals if str(v).upper() in ('FAIL', 'F', 'NO'))
        # If row-level status is FAIL and vals is empty, count 1 fail out of 1 sample
        if not vals and (r['status'] or '').upper() == 'FAIL':
            d = 1
        sample_sizes.append(n)
        fail_counts.append(d)
        fail_rates.append(round(d / n, 4) if n else 0.0)

    total_samples = sum(sample_sizes) or 1
    total_fails = sum(fail_counts)
    p_bar = total_fails / total_samples
    n_bar = total_samples / len(sample_sizes) if sample_sizes else 1
    # Standard p-chart control limits (using average n for approximation)
    sigma = math.sqrt(p_bar * (1 - p_bar) / n_bar) if n_bar > 0 else 0
    ucl_p = min(1.0, round(p_bar + 3 * sigma, 4))
    lcl_p = max(0.0, round(p_bar - 3 * sigma, 4))

    return jsonify({
        'chart_type': 'attribute',
        'batches': batches,
        'sample_sizes': sample_sizes,
        'fail_counts': fail_counts,
        'fail_rates': fail_rates,
        'p_bar': round(p_bar, 4),
        'ucl_p': ucl_p,
        'lcl_p': lcl_p,
        'total_samples': total_samples,
        'total_fails': total_fails
    }), 200


@app.route('/api/checkpoints')
@login_required
def api_checkpoints():
    """Return checkpoints for a product, optionally filtered by stage."""
    product = request.args.get('product', '')
    stage_id = request.args.get('stage_id', type=int)
    if not product and stage_id is None:
        return jsonify([]), 200
    checkpoints = get_distinct_checkpoints(product, stage_id=stage_id)
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
        # Safe parse — individual_values may be NULL in older records
        raw_vals = r['individual_values']
        try:
            vals = json.loads(raw_vals) if raw_vals else []
        except (ValueError, TypeError):
            vals = []

        # Determine result type from the values
        if vals and all(isinstance(v, (int, float)) for v in vals):
            result_type = 'numeric'
        elif vals and all(str(v).upper() in ('PASS', 'FAIL', 'YES', 'NO', 'P', 'F') for v in vals):
            result_type = 'passfail'
        elif not vals and r['mean'] is not None:
            result_type = 'numeric'
        else:
            result_type = 'text'

        test = {
            'id': r['id'],
            'checkpoint': r['checkpoint'],
            'individual_values': vals,
            'result_type': result_type,
            'sample_count': r['sample_count'],
            'mean': r['mean'],
            'range_val': r['range_val'],
            'tol_min': r['tol_min'],
            'tol_max': r['tol_max'],
            'status': r['status'],
            'tested_by': r['tested_by'],
            'tested_at': r['tested_at'],
            'tolerance': (r['tolerance'] if 'tolerance' in r.keys() else '') or '',
            'unit':      (r['unit']      if 'unit'      in r.keys() else '') or '',
            'sample_size': (r['sample_size'] if 'sample_size' in r.keys() else '') or '',
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


def _can_edit_library():
    return 'user' in session and session['user']['role'] in ('Quality Manager', 'Admin', 'Executive')


@app.route('/portal/specs/edit/<int:checkpoint_id>', methods=['POST'])
@login_required
def edit_library_checkpoint(checkpoint_id):
    """Update one editable field on a stage checkpoint (writes audit log)."""
    if not _can_edit_library():
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 403

    field = request.form.get('field', '').strip()
    new_value = request.form.get('value', '').strip()
    reason = request.form.get('reason', '').strip()

    if field not in EDITABLE_CHECKPOINT_FIELDS:
        return jsonify({'ok': False, 'error': f"Field '{field}' not editable"}), 400

    ok, err = update_stage_checkpoint_field(
        checkpoint_id, field, new_value,
        user=session['user']['full_name'], reason=reason
    )
    if not ok:
        return jsonify({'ok': False, 'error': err}), 400
    return jsonify({'ok': True}), 200


@app.route('/portal/specs/add-custom', methods=['POST'])
@login_required
def add_custom_checkpoint():
    """Add a user-created checkpoint to an existing stage."""
    if not _can_edit_library():
        flash("Only Quality Manager / Admin can modify the library.", "danger")
        return redirect(url_for('specs'))

    try:
        stage_id = int(request.form.get('stage_id'))
    except (TypeError, ValueError):
        flash("Invalid stage.", "warning")
        return redirect(url_for('specs'))

    name = (request.form.get('checkpoint_name') or '').strip()
    if not name:
        flash("Checkpoint name is required.", "warning")
        return redirect(url_for('specs'))

    data = {
        'section': request.form.get('section', '').strip(),
        'checkpoint_no': request.form.get('checkpoint_no', '').strip() or 'C',
        'checkpoint_name': name,
        'sample_size': request.form.get('sample_size', '').strip(),
        'sample_count': request.form.get('sample_count', '1').strip() or '1',
        'instruction': request.form.get('instruction', '').strip(),
        'tolerance': request.form.get('tolerance', '').strip(),
        'unit': request.form.get('unit', '').strip(),
        'frequency': request.form.get('frequency', '').strip(),
        'defect_type': request.form.get('defect_type', '').strip(),
        'test_type': request.form.get('test_type', 'variable').strip(),
        'result_type': request.form.get('result_type', 'numeric').strip(),
        'reason': request.form.get('reason', '').strip() or 'Custom addition',
    }
    try:
        new_id = insert_custom_stage_checkpoint(stage_id, data, user=session['user']['full_name'])
        flash(f"Custom checkpoint added (id #{new_id}).", "success")
    except Exception as e:
        flash(f"Failed to add checkpoint: {e}", "danger")
    return redirect(url_for('specs'))


@app.route('/portal/specs/deactivate/<int:checkpoint_id>', methods=['POST'])
@login_required
def deactivate_checkpoint(checkpoint_id):
    """Soft-delete a checkpoint from the active library."""
    if not _can_edit_library():
        flash("Unauthorized.", "danger")
        return redirect(url_for('specs'))
    reason = request.form.get('reason', '')
    ok, err = deactivate_stage_checkpoint(
        checkpoint_id, user=session['user']['full_name'], reason=reason
    )
    flash("Checkpoint deactivated." if ok else f"Failed: {err}", "success" if ok else "danger")
    return redirect(url_for('specs'))


@app.route('/api/checkpoint/<int:checkpoint_id>/audit')
@login_required
def api_checkpoint_audit(checkpoint_id):
    """Return audit log for a checkpoint."""
    rows = get_checkpoint_audit_log(checkpoint_id)
    return jsonify([dict(r) for r in rows]), 200


@app.route('/portal/specs/export.xlsx')
@login_required
def export_library():
    """Download current active library as Excel."""
    from io import BytesIO
    from flask import send_file

    library = get_stage_library()
    rows = []
    for layer in library:
        for stage in layer['stages']:
            for cp in stage['checkpoints']:
                rows.append({
                    'Layer': layer['layer'],
                    'Stage Code': stage['stage_code'],
                    'Stage Name': stage['stage_name'],
                    'Product Form': stage.get('product_form') or '—',
                    'Checkpoint #': cp.get('checkpoint_no', ''),
                    'Checkpoint': cp.get('checkpoint_name', ''),
                    'Section': cp.get('section', ''),
                    'Sample Size': cp.get('sample_size', ''),
                    'n (samples)': cp.get('sample_count', ''),
                    'Tolerance': cp.get('tolerance', ''),
                    'Unit': cp.get('unit', ''),
                    'Tol Min': cp.get('tol_min'),
                    'Tol Max': cp.get('tol_max'),
                    'Frequency': cp.get('frequency', ''),
                    'Defect Type': cp.get('defect_type', ''),
                    'Test Type': cp.get('test_type', ''),
                    'Result Type': cp.get('result_type', ''),
                    'Source': cp.get('source', 'Excel'),
                    'Updated By': cp.get('updated_by', ''),
                    'Updated At': cp.get('updated_at', ''),
                })
    df = pd.DataFrame(rows)
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Stage Checkpoint Library', index=False)
    buf.seek(0)
    return send_file(
        buf,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='atlas_stage_checkpoint_library.xlsx'
    )


# ─── Batch Tracker ────────────────────────────────────────────────────────────

@app.route('/portal/batch-tracker')
@login_required
def batch_tracker():
    status_filter = request.args.get('status')
    product_filter = request.args.get('product_id', type=int)
    batches = get_all_batches(status=status_filter, product_id=product_filter)
    products = get_all_products()
    return render_template('internal/batch_tracker.html',
                           batches=batches, products=products,
                           status_filter=status_filter, product_filter=product_filter)


@app.route('/portal/batch-tracker/create', methods=['POST'])
@login_required
def create_batch_route():
    if session['user']['role'] not in ('Quality Manager', 'Executive', 'Admin'):
        flash("Unauthorized.", "danger")
        return redirect(url_for('batch_tracker'))
    batch_number = request.form.get('batch_number', '').strip()
    product_id = request.form.get('product_id', type=int)
    batch_size = request.form.get('batch_size', type=int)
    if not batch_number or not product_id:
        flash("Batch number and product are required.", "warning")
        return redirect(url_for('batch_tracker'))
    if get_batch_by_number(batch_number):
        flash(f"Batch {batch_number} already exists.", "warning")
        return redirect(url_for('batch_tracker'))
    create_batch(batch_number, product_id, session['user']['full_name'], batch_size)
    flash(f"Batch {batch_number} created.", "success")
    return redirect(url_for('batch_tracker'))


@app.route('/api/batch/<int:batch_id>/stages')
@login_required
def api_batch_stages(batch_id):
    batch = get_batch(batch_id)
    if not batch:
        return jsonify({'error': 'Batch not found'}), 404
    stages = get_stages_for_product(batch['product_id'])
    results = get_batch_stage_results(batch_id)
    result_map = {r['stage_id']: dict(r) for r in results}
    pipeline = []
    for s in stages:
        r = result_map.get(s['id'], {})
        pipeline.append({
            'id': s['id'],
            'stage_code': s['stage_code'],
            'stage_name': s['stage_name'],
            'layer': s['layer'],
            'sequence_order': s['sequence_order'],
            'verdict': r.get('verdict', 'NOT_STARTED'),
            'signed_by': r.get('signed_by'),
            'signed_at': r.get('signed_at'),
            'notes': r.get('notes', ''),
        })
    return jsonify({'batch_id': batch_id, 'pipeline': pipeline})


@app.route('/api/batch/<int:batch_id>/sign-stage', methods=['POST'])
@login_required
def api_sign_stage(batch_id):
    if session['user']['role'] not in ('Quality Manager', 'Admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    stage_id = data.get('stage_id')
    verdict = data.get('verdict')
    notes = data.get('notes', '')
    if not stage_id or verdict not in ('PASS', 'FAIL'):
        return jsonify({'error': 'stage_id and verdict (PASS/FAIL) required'}), 400
    if not can_start_stage(batch_id, stage_id):
        return jsonify({'error': 'Prerequisites not met — complete earlier stages first'}), 400
    insert_batch_stage_result(batch_id, stage_id, verdict,
                              signed_by=session['user']['full_name'], notes=notes)
    batch = get_batch(batch_id)
    stage = get_stage_by_id(stage_id)
    # Advance batch status
    if verdict == 'PASS':
        stages = get_stages_for_product(batch['product_id'])
        results = get_batch_stage_results(batch_id)
        passed_ids = {r['stage_id'] for r in results if r['verdict'] == 'PASS'}
        all_stage_ids = {s['id'] for s in stages}
        if all_stage_ids == passed_ids:
            update_batch_status(batch_id, 'Pending-Release', current_stage_id=stage_id)
        else:
            update_batch_status(batch_id, 'In-Progress', current_stage_id=stage_id)
    else:
        update_batch_status(batch_id, 'In-Progress', current_stage_id=stage_id)
    return jsonify({'status': 'ok', 'verdict': verdict, 'stage_code': stage['stage_code']})


@app.route('/api/batch/<int:batch_id>/release', methods=['POST'])
@login_required
def api_release_batch(batch_id):
    if session['user']['role'] not in ('Executive', 'Admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    batch = get_batch(batch_id)
    if not batch or batch['status'] != 'Pending-Release':
        return jsonify({'error': 'Batch must be in Pending-Release status'}), 400
    update_batch_status(batch_id, 'Released', released_by=session['user']['full_name'])
    return jsonify({'status': 'ok'})


@app.route('/api/batch/<int:batch_id>/link-material', methods=['POST'])
@login_required
def api_link_material(batch_id):
    if session['user']['role'] not in ('Quality Manager', 'Admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    lot_id = data.get('material_lot_id')
    qty = data.get('quantity_used')
    unit = data.get('unit', '')
    if not lot_id:
        return jsonify({'error': 'material_lot_id required'}), 400
    link_batch_material(batch_id, lot_id, qty, unit)
    return jsonify({'status': 'ok'})


# ─── Material Lots ─────────────────────────────────────────────────────────────

@app.route('/portal/material-lots')
@login_required
def material_lots():
    status_filter = request.args.get('status')
    type_filter = request.args.get('material_type')
    lots = get_all_material_lots(status=status_filter, material_type=type_filter)
    return render_template('internal/material_lots.html',
                           lots=lots, status_filter=status_filter, type_filter=type_filter)


@app.route('/portal/material-lots/create', methods=['POST'])
@login_required
def create_material_lot_route():
    if session['user']['role'] not in ('Quality Manager', 'Admin'):
        flash("Unauthorized.", "danger")
        return redirect(url_for('material_lots'))
    material_type = request.form.get('material_type')
    material_name = request.form.get('material_name', '').strip()
    lot_number = request.form.get('lot_number', '').strip()
    supplier = request.form.get('supplier', '').strip()
    received_date = request.form.get('received_date') or None
    expiry_date = request.form.get('expiry_date') or None
    quantity = request.form.get('quantity', type=float)
    unit = request.form.get('unit', '').strip()
    if not all([material_type, material_name, lot_number]):
        flash("Material type, name, and lot number are required.", "warning")
        return redirect(url_for('material_lots'))
    create_material_lot(material_type, material_name, lot_number, supplier,
                        received_date, expiry_date, quantity, unit)
    flash(f"Lot {lot_number} created and placed in Quarantine.", "success")
    return redirect(url_for('material_lots'))


@app.route('/portal/material-lots/<int:lot_id>/release', methods=['POST'])
@login_required
def release_material_lot(lot_id):
    if session['user']['role'] not in ('Quality Manager', 'Admin'):
        flash("Unauthorized.", "danger")
        return redirect(url_for('material_lots'))
    update_material_lot_status(lot_id, 'Released', released_by=session['user']['full_name'])
    flash("Material lot released.", "success")
    return redirect(url_for('material_lots'))


@app.route('/portal/material-lots/<int:lot_id>/reject', methods=['POST'])
@login_required
def reject_material_lot(lot_id):
    if session['user']['role'] not in ('Quality Manager', 'Admin'):
        flash("Unauthorized.", "danger")
        return redirect(url_for('material_lots'))
    update_material_lot_status(lot_id, 'Rejected', released_by=session['user']['full_name'])
    flash("Material lot rejected.", "warning")
    return redirect(url_for('material_lots'))


# ─── Stage-Aware QC APIs ──────────────────────────────────────────────────────

@app.route('/api/stage-checkpoints/<int:stage_id>')
@login_required
def api_stage_checkpoints(stage_id):
    checkpoints = get_checkpoints_by_stage(stage_id)
    return jsonify([dict(c) for c in checkpoints])


@app.route('/api/stages')
@login_required
def api_stages():
    product_form = request.args.get('product_form')
    layer = request.args.get('layer')
    stages = get_all_stages(layer=layer, product_form=product_form)
    return jsonify([dict(s) for s in stages])


@app.route('/api/batches-active')
@login_required
def api_batches_active():
    """Return non-released batches for QC entry dropdowns."""
    batches = get_all_batches()
    active = [dict(b) for b in batches if b['status'] not in ('Released', 'Rejected')]
    return jsonify(active)


# ─── CAPA from QC Failures ────────────────────────────────────────────────────

@app.route('/portal/capa/from-qc', methods=['POST'])
@login_required
def capa_from_qc():
    if session['user']['role'] not in ('Quality Manager', 'Admin'):
        flash("Unauthorized.", "danger")
        return redirect(url_for('capa'))
    batch_id = request.form.get('batch_id', type=int)
    stage_id = request.form.get('stage_id', type=int)
    root_cause = request.form.get('root_cause', '').strip()
    corrective = request.form.get('corrective_action', '').strip()
    preventive = request.form.get('preventive_action', '').strip()
    if not all([batch_id, stage_id, root_cause, corrective, preventive]):
        flash("All fields required.", "warning")
        return redirect(url_for('capa'))
    insert_capa_from_qc(batch_id, stage_id, root_cause, corrective, preventive,
                        session['user']['full_name'])
    flash("QC CAPA logged successfully.", "success")
    return redirect(url_for('capa'))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Enable Debug Mode so templates reload instantly and code changes auto-restart.
    app.run(debug=True, host='0.0.0.0', port=port)
