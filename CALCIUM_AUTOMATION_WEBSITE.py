import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# =============================================================================
# 1. AUTOMATIC FILE GENERATION
# =============================================================================
def setup_templates():
    if not os.path.exists('templates'):
        os.makedirs('templates')

    # --- BASE.HTML ---
    with open('templates/base.html', 'w', encoding='utf-8') as f:
        f.write('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ca-Wire Automation</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f4f6f9; }
        .card { box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: none; }
        .form-label { font-size: 0.85rem; font-weight: 700; color: #555; }
        /* logic-alert style removed as it is no longer used */
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4">
        <div class="container">
            <a class="navbar-brand" href="/">Ca-Wire Intelligent System</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link text-white" href="/">Operations</a>
                <a class="nav-link text-white" href="/history">History</a>
                <a class="nav-link text-white" href="/settings">Settings (Switch Coil)</a>
            </div>
        </div>
    </nav>
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
        ''')

    # --- INDEX.HTML (Logic Display Removed) ---
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write('''
{% extends "base.html" %}
{% block content %}
<div class="row">
    <div class="col-md-8">
        <div class="card mb-4">
            <div class="card-header bg-white fw-bold">Heat Parameters</div>
            <div class="card-body">
                <form id="calcForm" method="POST" action="{{ url_for('confirm_injection') }}">
                    <div class="row g-3">
                        <div class="col-md-4">
                            <label class="form-label">LM Tonnage</label>
                            <input type="number" step="0.1" class="form-control" id="tonnage" name="tonnage" value="150" required>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Freeboard (mm)</label>
                            <input type="number" class="form-control" id="freeboard" name="freeboard" value="400">
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Temp Before Inj (°C)</label>
                            <input type="number" class="form-control" id="temp" name="temp" value="1580" required>
                        </div>

                        <div class="col-md-4">
                            <label class="form-label">Aluminium (Al%)</label>
                            <input type="number" step="0.001" class="form-control" id="al" name="al" value="0.040">
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Sulphur (S%)</label>
                            <input type="number" step="0.001" class="form-control" id="s" name="s" value="0.005">
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Silicon (Si%)</label>
                            <input type="number" step="0.001" class="form-control" id="si" name="si_pct" value="0.200">
                        </div>

                        <div class="col-md-6">
                            <label class="form-label">Initial LF Phosphorus (P1%)</label>
                            <input type="number" step="0.001" class="form-control" id="p_initial" name="p_initial" value="0.012">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Phosphorus Before Inj (P2%)</label>
                            <input type="number" step="0.001" class="form-control" id="p_before" name="p_before" value="0.015">
                        </div>

                        <div class="col-md-12">
                            <label class="form-label">Speed of Injection (m/min)</label>
                            <input type="number" class="form-control" id="speed" value="130">
                        </div>
                        
                        <input type="hidden" id="calculated_length_hidden" name="calculated_length_hidden" value="0">
                    </div>
                </form>
            </div>
        </div>
    </div>

    <div class="col-md-4">
        <div class="card text-center h-100">
            <div class="card-header bg-white fw-bold">Intelligent Prediction</div>
            <div class="card-body">
                <div class="alert alert-light border py-2 text-start">
                    <small><strong>Active Coil:</strong> {{ coil.coil_number }}<br>
                    <strong>Target:</strong> {{ coil.target_ppm }} ppm<br>
                    <strong>Recovery:</strong> {{ coil.recovery_target }}%</small>
                </div>
                
                <button type="button" class="btn btn-primary w-100 mb-3" onclick="predictLength()">
                    PREDICT WIRE LENGTH
                </button>

                <div class="py-3 bg-light rounded mb-3 border">
                    <h6 class="text-muted">Required Length</h6>
                    <h1 class="display-4 text-primary fw-bold my-0"><span id="resultDisplay">0.00</span>m</h1>
                    <small id="timeDisplay">Time: 0.00 min</small>
                </div>

                <button type="submit" form="calcForm" class="btn btn-success w-100 btn-lg" id="injectBtn" disabled>
                    CONFIRM INJECTION
                </button>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
    function predictLength() {
        const data = {
            tonnage: document.getElementById('tonnage').value,
            freeboard: document.getElementById('freeboard').value,
            speed: document.getElementById('speed').value,
            temp: document.getElementById('temp').value,
            al: document.getElementById('al').value,
            s: document.getElementById('s').value,
            si: document.getElementById('si').value,
            p_initial: document.getElementById('p_initial').value,
            p_before: document.getElementById('p_before').value
        };
        
        fetch('/calculate_api', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if(data.success) {
                // Just update the numbers, no logic list display
                document.getElementById('resultDisplay').innerText = data.length_m;
                document.getElementById('timeDisplay').innerText = "Injection Time: " + data.time_min + " min";
                document.getElementById('calculated_length_hidden').value = data.length_m;
                document.getElementById('injectBtn').disabled = false;
            } else {
                alert("Error: " + data.error);
            }
        });
    }
</script>
{% endblock %}
        ''')

    # --- HISTORY.HTML ---
    with open('templates/history.html', 'w', encoding='utf-8') as f:
        f.write('''
{% extends "base.html" %}
{% block content %}
<div class="card mb-4">
    <div class="card-header fw-bold">Active Coil Status ({{ coil.coil_number }})</div>
    <div class="card-body">
        <div class="row text-center mb-3">
            <div class="col-md-4"><h3 class="text-primary">{{ "%.2f"|format(coil.current_length) }} m</h3><span class="text-muted">Balance Length</span></div>
            <div class="col-md-4"><h3>{{ coil.total_length }} m</h3><span class="text-muted">Total Length</span></div>
            <div class="col-md-4"><h3>{{ coil.heats_treated }}</h3><span class="text-muted">Heats Treated</span></div>
        </div>
        <div class="progress" style="height: 25px;">
            <div class="progress-bar {% if pct < 15 %}bg-danger{% else %}bg-success{% endif %}" role="progressbar" style="width: {{ pct }}%">{{ "%.1f"|format(pct) }}%</div>
        </div>
    </div>
</div>
<div class="card">
    <div class="card-header fw-bold">Injection History Log</div>
    <div class="card-body p-0">
        <div class="table-responsive">
            <table class="table table-striped table-hover mb-0" style="font-size:0.9rem;">
                <thead class="table-dark">
                    <tr><th>Time</th><th>Coil #</th><th>Tons</th><th>Used (m)</th><th>Balance (m)</th><th>Freeboard</th></tr>
                </thead>
                <tbody>
                    {% for log in logs %}
                    <tr>
                        <td>{{ log.timestamp.strftime('%m-%d %H:%M') }}</td>
                        <td class="fw-bold">{{ log.coil_number }}</td>
                        <td>{{ log.heat_tonnage }}</td>
                        <td class="text-danger fw-bold">{{ "%.1f"|format(log.calculated_length) }}</td>
                        <td class="text-success">{{ "%.1f"|format(log.balance_after) }}</td>
                        <td>{{ log.freeboard }}</td>
                    </tr>
                    {% else %}<tr><td colspan="6" class="text-center">No history found.</td></tr>{% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}
        ''')

    # --- SETTINGS.HTML ---
    with open('templates/settings.html', 'w', encoding='utf-8') as f:
        f.write('''
{% extends "base.html" %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="card">
            <div class="card-header fw-bold bg-warning text-dark">Switch or Create Coil</div>
            <div class="card-body">
                <div class="alert alert-info small">
                    <strong>Instructions:</strong> Enter a Coil Number. If it exists, the system will switch to it and load its balance. If it's new, a new coil record will be created.
                </div>
                <form method="POST">
                    <div class="mb-3 row">
                        <label class="col-sm-5 col-form-label fw-bold">COIL NUMBER (ID)</label>
                        <div class="col-sm-7"><input type="text" class="form-control border-primary fw-bold" name="coil_number" value="{{ coil.coil_number }}"></div>
                    </div>
                    
                    <h6 class="mt-4 text-muted border-bottom pb-2">Coil Parameters</h6>
                    <div class="mb-3 row">
                        <label class="col-sm-5 col-form-label">Total Length (m)</label>
                        <div class="col-sm-7"><input type="number" step="1" class="form-control" name="total_length" value="{{ coil.total_length }}"></div>
                    </div>
                    <div class="mb-3 row">
                        <label class="col-sm-5 col-form-label">Ca Density (g/m)</label>
                        <div class="col-sm-7"><input type="number" step="0.1" class="form-control" name="density" value="{{ coil.density }}"></div>
                    </div>
                    <div class="mb-3 row">
                        <label class="col-sm-5 col-form-label">Desired Recovery (%)</label>
                        <div class="col-sm-7"><input type="number" step="0.1" class="form-control" name="recovery_target" value="{{ coil.recovery_target }}"></div>
                    </div>
                    <div class="mb-3 row">
                        <label class="col-sm-5 col-form-label">Desired LF PPM</label>
                        <div class="col-sm-7"><input type="number" step="1" class="form-control" name="target_ppm" value="{{ coil.target_ppm }}"></div>
                    </div>

                    <div class="text-end"><button type="submit" class="btn btn-dark w-100">Activate / Save Coil</button></div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
        ''')

setup_templates()

# =============================================================================
# 2. APP LOGIC
# =============================================================================
# --- FIXED CONFIGURATION FOR PYTHONANYWHERE ---
app = Flask(__name__)
app.secret_key = 'secret_key_123'

# Get the absolute path of the current folder
basedir = os.path.abspath(os.path.dirname(__file__))

# Point the database to that absolute path
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'production_v9.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELS ---
class CoilConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    coil_number = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    
    total_length = db.Column(db.Float, default=5000.0)
    current_length = db.Column(db.Float, default=5000.0)
    heats_treated = db.Column(db.Integer, default=0)
    
    density = db.Column(db.Float, default=68.0)
    target_ppm = db.Column(db.Float, default=30.0)
    recovery_target = db.Column(db.Float, default=20.0)
    recovery_initial = db.Column(db.Float, default=0.0)

class InjectionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    coil_number = db.Column(db.String(50))
    balance_after = db.Column(db.Float)
    
    heat_tonnage = db.Column(db.Float)
    freeboard = db.Column(db.Float)
    calculated_length = db.Column(db.Float)
    al_before = db.Column(db.Float)
    s_before = db.Column(db.Float)
    si_before = db.Column(db.Float)
    p_before = db.Column(db.Float)
    p_initial_lf = db.Column(db.Float)
    temp = db.Column(db.Float)

def get_active_coil():
    coil = CoilConfig.query.filter_by(is_active=True).first()
    if not coil:
        any_coil = CoilConfig.query.first()
        if any_coil:
            any_coil.is_active = True
            coil = any_coil
        else:
            coil = CoilConfig(coil_number="COIL-001", is_active=True)
            db.session.add(coil)
        db.session.commit()
    return coil

# --- API CALCULATION (Rules applied in background) ---
@app.route('/calculate_api', methods=['POST'])
def calculate_api():
    data = request.json
    coil = get_active_coil()
    try:
        # Inputs
        tonnage = float(data['tonnage'])
        freeboard = float(data['freeboard'])
        speed = float(data['speed'])
        temp = float(data['temp'])
        al = float(data['al'])
        s = float(data['s'])
        si = float(data['si'])
        p_initial = float(data['p_initial'])
        p_before = float(data['p_before'])

        # 1. BASE CALCULATION (Mass Balance)
        pure_ca_kg = (tonnage * 1000.0) * (coil.target_ppm / 1000000.0)
        gross_ca_kg = pure_ca_kg / (coil.recovery_target / 100.0)
        base_length = (gross_ca_kg * 1000.0) / coil.density
        
        length_m = base_length

        # 2. RULE: FREEBOARD
        if freeboard > 500:
            steps = int((freeboard - 500) // 50)
            length_m += (steps * 20)

        # 3. RULE: TEMPERATURE
        if temp > 1600:
            steps = int((temp - 1600) // 10)
            length_m += (steps * 20)

        # 4. RULE: ALUMINIUM
        if al < 0.028:
            length_m += 40

        # 5. RULE: SULPHUR
        if s > 0.010:
            diff = round(s - 0.010, 5)
            steps = int(diff // 0.001)
            length_m += (steps * 10)

        # 6. RULE: PHOSPHORUS
        p_diff = round(p_before - p_initial, 5)
        if p_diff > 0.003:
            diff = round(p_diff - 0.003, 5)
            steps = int(diff // 0.001)
            length_m += (steps * 20)

        # 7. RULE: SILICON
        if si < 0.010:
            diff = round(0.010 - si, 5)
            steps = int(diff // 0.001)
            length_m += (steps * 10)

        time_min = length_m / speed if speed > 0 else 0

        return jsonify({
            'success': True, 
            'length_m': round(length_m, 2), 
            'time_min': round(time_min, 2)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', coil=get_active_coil())

@app.route('/confirm_injection', methods=['POST'])
def confirm_injection():
    coil = get_active_coil()
    try:
        length_used = float(request.form.get('calculated_length_hidden', 0))
        if length_used > 0:
            coil.current_length -= length_used
            coil.heats_treated += 1
            
            new_log = InjectionLog(
                coil_number = coil.coil_number,
                balance_after = coil.current_length,
                heat_tonnage=float(request.form.get('tonnage')),
                freeboard=float(request.form.get('freeboard', 0)),
                calculated_length=length_used,
                al_before=float(request.form.get('al', 0)),
                s_before=float(request.form.get('s', 0)),
                si_before=float(request.form.get('si_pct', 0)),
                p_before=float(request.form.get('p_before', 0)),
                p_initial_lf=float(request.form.get('p_initial', 0)),
                temp=float(request.form.get('temp', 0))
            )
            db.session.add(new_log)
            db.session.commit()
            flash(f"Injected {length_used}m. Coil {coil.coil_number} Balance Updated.", "success")
        else:
            flash("Error: Length was 0.", "danger")
    except ValueError:
        flash("Input Error.", "danger")
    return redirect(url_for('index'))

@app.route('/history')
def history():
    coil = get_active_coil()
    logs = InjectionLog.query.order_by(InjectionLog.timestamp.desc()).limit(50).all()
    pct = (coil.current_length / coil.total_length) * 100 if coil.total_length > 0 else 0
    return render_template('history.html', coil=coil, logs=logs, pct=pct)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    coil = get_active_coil()
    
    if request.method == 'POST':
        try:
            input_number = request.form['coil_number'].strip()
            existing_coil = CoilConfig.query.filter_by(coil_number=input_number).first()
            
            if existing_coil:
                CoilConfig.query.update({CoilConfig.is_active: False})
                existing_coil.is_active = True
                
                existing_coil.recovery_target = float(request.form['recovery_target'])
                existing_coil.target_ppm = float(request.form['target_ppm'])
                existing_coil.density = float(request.form['density'])
                
                new_total = float(request.form['total_length'])
                if new_total != existing_coil.total_length:
                     existing_coil.total_length = new_total
                     existing_coil.current_length = new_total
                     existing_coil.heats_treated = 0
                
                db.session.commit()
                flash(f'Switched to existing coil: {input_number}', 'success')
                
            else:
                CoilConfig.query.update({CoilConfig.is_active: False})
                
                new_coil = CoilConfig(
                    coil_number = input_number,
                    is_active = True,
                    total_length = float(request.form['total_length']),
                    current_length = float(request.form['total_length']),
                    density = float(request.form['density']),
                    recovery_target = float(request.form['recovery_target']),
                    target_ppm = float(request.form['target_ppm'])
                )
                db.session.add(new_coil)
                db.session.commit()
                flash(f'Created and activated new coil: {input_number}', 'success')

        except ValueError:
            flash('Error in inputs.', 'danger')
        return redirect(url_for('settings'))
        
    return render_template('settings.html', coil=coil)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("System V9 Active (Logic hidden, functionality intact).")
    app.run(debug=True, host='0.0.0.0', port=5000)