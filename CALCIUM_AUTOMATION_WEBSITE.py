import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

def setup_templates():
    if not os.path.exists(TEMPLATE_DIR):
        os.makedirs(TEMPLATE_DIR)

    # --- BASE.HTML (Added Google Fonts, FontAwesome, and Custom CSS) ---
    with open(os.path.join(TEMPLATE_DIR, 'base.html'), 'w', encoding='utf-8') as f:
        f.write('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ca-Wire Intelligent System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
    
    <style>
        :root {
            --primary-grad: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); /* Steel Dark */
            --accent-grad: linear-gradient(to right, #4facfe 0%, #00f2fe 100%); /* Cyan/Blue */
            --card-bg: #ffffff;
            --bg-color: #f3f5f9;
        }
        body { 
            background-color: var(--bg-color); 
            font-family: 'Inter', sans-serif; 
            color: #2c3e50;
        }
        
        /* Navigation */
        .navbar {
            background: var(--primary-grad) !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            padding: 1rem 0;
        }
        .navbar-brand {
            font-weight: 800;
            letter-spacing: 1px;
            font-size: 1.5rem;
        }
        .nav-link {
            font-weight: 500;
            transition: color 0.3s;
        }
        .nav-link:hover { color: #00f2fe !important; }

        /* Cards */
        .card { 
            border: none; 
            border-radius: 16px; 
            box-shadow: 0 8px 30px rgba(0,0,0,0.05); 
            transition: transform 0.2s;
            overflow: hidden;
        }
        .card-header {
            background: white;
            border-bottom: 2px solid #f0f0f0;
            padding: 1.2rem;
            font-weight: 700;
            color: #444;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .card-header i { color: #2c5364; }

        /* Form Controls */
        .form-label { 
            font-size: 0.8rem; 
            text-transform: uppercase; 
            letter-spacing: 0.5px; 
            font-weight: 700; 
            color: #7f8c8d; 
            margin-bottom: 5px;
        }
        .form-control {
            border-radius: 8px;
            border: 1px solid #dee2e6;
            padding: 10px 15px;
            font-weight: 600;
            color: #2c3e50;
            transition: all 0.3s;
        }
        .form-control:focus {
            box-shadow: 0 0 0 4px rgba(79, 172, 254, 0.15);
            border-color: #4facfe;
        }
        .input-group-text {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            color: #6c757d;
        }

        /* Buttons */
        .btn-primary-custom {
            background-image: var(--primary-grad);
            border: none;
            color: white;
            font-weight: 600;
            padding: 12px;
            border-radius: 8px;
            transition: opacity 0.3s;
        }
        .btn-primary-custom:hover { opacity: 0.9; color: white; }

        .btn-accent {
            background-image: var(--accent-grad);
            border: none;
            color: white;
            font-weight: 700;
            box-shadow: 0 4px 15px rgba(0, 242, 254, 0.3);
        }
        .btn-accent:hover { transform: translateY(-2px); color: white; }
        .btn-accent:disabled { background: #ccc; box-shadow: none; transform: none; }

        /* Alerts & Logic */
        .logic-alert { font-size: 0.8rem; color: #dc3545; margin-bottom: 2px; font-weight: bold; }
        .result-box {
            background: linear-gradient(135deg, #ffffff 0%, #f1f8ff 100%);
            border: 1px solid #e1e8ed;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark mb-5">
        <div class="container">
            <a class="navbar-brand" href="/"><i class="fa-solid fa-industry me-2"></i> Ca-Wire<span style="color:#00f2fe">AI</span></a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <div class="navbar-nav ms-auto gap-3">
                    <a class="nav-link text-white" href="/"><i class="fa-solid fa-calculator me-1"></i> Operations</a>
                    <a class="nav-link text-white" href="/history"><i class="fa-solid fa-clock-rotate-left me-1"></i> History</a>
                    <a class="nav-link text-white" href="/settings"><i class="fa-solid fa-gears me-1"></i> Settings</a>
                </div>
            </div>
        </div>
    </nav>

    <div class="container pb-5">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} shadow-sm rounded-3 border-0 d-flex align-items-center mb-4">
                        {% if category == 'success' %}
                            <i class="fa-solid fa-circle-check fs-4 me-3 text-success"></i>
                        {% else %}
                            <i class="fa-solid fa-circle-exclamation fs-4 me-3 text-danger"></i>
                        {% endif %}
                        <div>{{ message }}</div>
                    </div>
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

    # --- INDEX.HTML (Modern Forms & Dashboard Cards) ---
    with open(os.path.join(TEMPLATE_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write('''
{% extends "base.html" %}
{% block content %}
<div class="row g-4">
    <div class="col-lg-8">
        <div class="card h-100">
            <div class="card-header">
                <i class="fa-solid fa-sliders"></i> Heat Parameters
            </div>
            <div class="card-body p-4">
                <form id="calcForm" method="POST" action="{{ url_for('confirm_injection') }}">
                    <h6 class="text-primary fw-bold mb-3 border-bottom pb-2"><i class="fa-solid fa-fire me-2"></i>Furnace Conditions</h6>
                    <div class="row g-3 mb-4">
                        <div class="col-md-4">
                            <label class="form-label">Heat Tonnage</label>
                            <div class="input-group">
                                <span class="input-group-text"><i class="fa-solid fa-weight-hanging"></i></span>
                                <input type="number" step="0.1" class="form-control" id="tonnage" name="tonnage" value="150" required>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Freeboard (mm)</label>
                            <div class="input-group">
                                <span class="input-group-text"><i class="fa-solid fa-ruler-vertical"></i></span>
                                <input type="number" class="form-control" id="freeboard" name="freeboard" value="400">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Temperature (°C)</label>
                            <div class="input-group">
                                <span class="input-group-text"><i class="fa-solid fa-temperature-high text-danger"></i></span>
                                <input type="number" class="form-control" id="temp" name="temp" value="1580" required>
                            </div>
                        </div>
                    </div>

                    <h6 class="text-primary fw-bold mb-3 border-bottom pb-2"><i class="fa-solid fa-flask me-2"></i>Chemistry (Lab)</h6>
                    <div class="row g-3 mb-4">
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
                            <label class="form-label">Initial LF Phos (P1%)</label>
                            <input type="number" step="0.001" class="form-control" id="p_initial" name="p_initial" value="0.012">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Phos Before Inj (P2%)</label>
                            <input type="number" step="0.001" class="form-control" id="p_before" name="p_before" value="0.015">
                        </div>
                    </div>

                    <div class="row g-3">
                         <div class="col-md-12">
                            <label class="form-label">Injection Speed (m/min)</label>
                            <div class="input-group">
                                <span class="input-group-text"><i class="fa-solid fa-gauge-high"></i></span>
                                <input type="number" class="form-control" id="speed" value="120">
                            </div>
                        </div>
                    </div>
                    
                    <input type="hidden" id="calculated_length_hidden" name="calculated_length_hidden" value="0">
                </form>
            </div>
        </div>
    </div>

    <div class="col-lg-4">
        <div class="card h-100 border-0 bg-dark text-white" style="background: var(--primary-grad);">
            <div class="card-body d-flex flex-column justify-content-between p-4">
                
                <div>
                    <h5 class="fw-bold mb-4"><i class="fa-solid fa-microchip me-2" style="color:#00f2fe"></i>Intelligent Prediction</h5>
                    
                    <div class="p-3 rounded-3 mb-4" style="background: rgba(255,255,255,0.1); backdrop-filter: blur(5px);">
                        <div class="d-flex justify-content-between mb-2">
                            <span class="small text-white-50">Active Coil</span>
                            <span class="fw-bold text-white">{{ coil.coil_number }}</span>
                        </div>
                        <div class="d-flex justify-content-between mb-2">
                            <span class="small text-white-50">Target PPM</span>
                            <span class="fw-bold text-info">{{ coil.target_ppm }}</span>
                        </div>
                        <div class="d-flex justify-content-between">
                            <span class="small text-white-50">Exp. Recovery</span>
                            <span class="fw-bold text-success">{{ coil.recovery_target }}%</span>
                        </div>
                    </div>

                    <button type="button" class="btn btn-light w-100 py-3 fw-bold shadow-lg mb-4" onclick="predictLength()">
                        <i class="fa-solid fa-wand-magic-sparkles me-2 text-primary"></i> CALCULATE
                    </button>
                </div>

                <div class="text-center py-4 rounded-4 mb-4" style="background: rgba(0,0,0,0.2);">
                    <h6 class="text-info text-uppercase letter-spacing-2">Required Wire</h6>
                    <h1 class="display-3 fw-bolder my-1 text-white"><span id="resultDisplay">0.00</span><span class="fs-4">m</span></h1>
                    <div class="badge bg-secondary mt-2 px-3 py-2" id="timeDisplay"><i class="fa-regular fa-clock me-1"></i> 0.00 min</div>
                </div>

                <button type="submit" form="calcForm" class="btn btn-accent w-100 py-3 fs-5 rounded-pill" id="injectBtn" disabled>
                    CONFIRM & INJECT <i class="fa-solid fa-arrow-right ms-2"></i>
                </button>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
    function predictLength() {
        const btn = document.querySelector('button[onclick="predictLength()"]');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
        
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
            btn.innerHTML = originalText;
            if(data.success) {
                // Animate Numbers
                document.getElementById('resultDisplay').innerText = data.length_m;
                document.getElementById('timeDisplay').innerHTML = '<i class="fa-regular fa-clock me-1"></i> ' + data.time_min + " min";
                document.getElementById('calculated_length_hidden').value = data.length_m;
                
                const injectBtn = document.getElementById('injectBtn');
                injectBtn.disabled = false;
                injectBtn.classList.add('animate__animated', 'animate__pulse');
            } else {
                alert("Error: " + data.error);
            }
        })
        .catch(err => {
            btn.innerHTML = originalText;
            console.error(err);
        });
    }
</script>
{% endblock %}
        ''')

    # --- HISTORY.HTML (Visual Progress Bars & Badges) ---
    with open(os.path.join(TEMPLATE_DIR, 'history.html'), 'w', encoding='utf-8') as f:
        f.write('''
{% extends "base.html" %}
{% block content %}
<div class="row mb-4">
    <div class="col-12">
        <div class="card text-white overflow-hidden" style="background: var(--primary-grad);">
            <div class="card-body p-4 position-relative">
                <i class="fa-solid fa-ring position-absolute" style="font-size: 150px; opacity: 0.05; right: -20px; top: -20px;"></i>
                <div class="row align-items-center">
                    <div class="col-md-6">
                        <h6 class="text-info text-uppercase">Active Coil</h6>
                        <h2 class="fw-bold">{{ coil.coil_number }}</h2>
                    </div>
                    <div class="col-md-6 text-end">
                        <h6 class="text-white-50">Remaining Balance</h6>
                        <h1 class="display-4 fw-bold">{{ "%.0f"|format(coil.current_length) }} <span class="fs-5">m</span></h1>
                    </div>
                </div>
                
                <div class="mt-4">
                    <div class="d-flex justify-content-between small mb-1">
                        <span>Usage Progress</span>
                        <span>{{ "%.1f"|format(pct) }}% Remaining</span>
                    </div>
                    <div class="progress bg-secondary bg-opacity-25" style="height: 10px;">
                        <div class="progress-bar {% if pct < 15 %}bg-danger{% else %}bg-info{% endif %}" 
                             role="progressbar" 
                             style="width: {{ pct }}%"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="card">
    <div class="card-header bg-white">
        <i class="fa-solid fa-list-ul"></i> Recent Injection Logs
    </div>
    <div class="card-body p-0">
        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0">
                <thead class="bg-light">
                    <tr class="text-uppercase small text-muted">
                        <th class="ps-4">Timestamp</th>
                        <th>Coil ID</th>
                        <th>Heat (T)</th>
                        <th>Injected</th>
                        <th>Balance</th>
                        <th>Params</th>
                    </tr>
                </thead>
                <tbody class="border-top-0">
                    {% for log in logs %}
                    <tr>
                        <td class="ps-4 fw-bold text-secondary">{{ log.timestamp.strftime('%m-%d %H:%M') }}</td>
                        <td><span class="badge bg-light text-dark border">{{ log.coil_number }}</span></td>
                        <td>{{ log.heat_tonnage }}</td>
                        <td>
                            <span class="text-danger fw-bold"><i class="fa-solid fa-arrow-down-long small me-1"></i>{{ "%.1f"|format(log.calculated_length) }} m</span>
                        </td>
                        <td class="text-success fw-bold">{{ "%.1f"|format(log.balance_after) }} m</td>
                        <td>
                            <small class="text-muted d-block">Freeboard: {{ log.freeboard }}</small>
                            <small class="text-muted">Temp: {{ log.temp }}</small>
                        </td>
                    </tr>
                    {% else %}
                    <tr><td colspan="6" class="text-center py-5 text-muted">No history found.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}
        ''')

    # --- SETTINGS.HTML (Cleaner Layout) ---
    with open(os.path.join(TEMPLATE_DIR, 'settings.html'), 'w', encoding='utf-8') as f:
        f.write('''
{% extends "base.html" %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-lg-8">
        <div class="card">
            <div class="card-header bg-warning bg-opacity-10 text-warning-emphasis border-warning border-opacity-25">
                <i class="fa-solid fa-right-left"></i> Switch or Create Coil
            </div>
            <div class="card-body p-4">
                <div class="alert alert-light border shadow-sm mb-4">
                    <div class="d-flex">
                        <i class="fa-solid fa-circle-info text-primary mt-1 me-3"></i>
                        <small class="text-muted">Enter a Coil Number. If it exists in the database, the system will switch to it. If it is new, a new record will be created.</small>
                    </div>
                </div>

                <form method="POST">
                    <div class="mb-4">
                        <label class="form-label text-dark">COIL IDENTIFIER (ID)</label>
                        <div class="input-group input-group-lg">
                            <span class="input-group-text bg-white"><i class="fa-solid fa-barcode"></i></span>
                            <input type="text" class="form-control fw-bold text-primary" name="coil_number" value="{{ coil.coil_number }}" placeholder="e.g. CA-2023-X1">
                        </div>
                    </div>
                    
                    <h6 class="text-uppercase text-muted small fw-bold mb-3 mt-4">Configuration Parameters</h6>
                    <div class="row g-3">
                        <div class="col-md-6">
                            <label class="form-label">Total Length (m)</label>
                            <input type="number" step="1" class="form-control" name="total_length" value="{{ coil.total_length }}">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Ca Density (g/m)</label>
                            <input type="number" step="0.1" class="form-control" name="density" value="{{ coil.density }}">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Target Recovery (%)</label>
                            <input type="number" step="0.1" class="form-control" name="recovery_target" value="{{ coil.recovery_target }}">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Target LF PPM</label>
                            <input type="number" step="1" class="form-control" name="target_ppm" value="{{ coil.target_ppm }}">
                        </div>
                    </div>

                    <div class="mt-5">
                        <button type="submit" class="btn btn-primary-custom w-100 py-3 fs-5">
                            <i class="fa-solid fa-check-circle me-2"></i> Save & Activate Coil
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
        ''')

setup_templates()

app = Flask(__name__)
app.secret_key = 'secret_key_123'

# Database Setup
db_path = os.path.join(BASE_DIR, 'production_v10.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
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

# --- API CALCULATION ---
@app.route('/calculate_api', methods=['POST'])
def calculate_api():
    data = request.json
    coil = get_active_coil()
    try:
        tonnage = float(data['tonnage'])
        freeboard = float(data['freeboard'])
        speed = float(data['speed'])
        temp = float(data['temp'])
        al = float(data['al'])
        s = float(data['s'])
        si = float(data['si'])
        p_initial = float(data['p_initial'])
        p_before = float(data['p_before'])

        # 1. Mass Balance
        pure_ca_kg = (tonnage * 1000.0) * (coil.target_ppm / 1000000.0)
        gross_ca_kg = pure_ca_kg / (coil.recovery_target / 100.0)
        base_length = (gross_ca_kg * 1000.0) / coil.density
        length_m = base_length

        # 2. Rules
        if freeboard > 500:
            length_m += int((freeboard - 500) // 50) * 20
        if temp > 1600:
            length_m += int((temp - 1600) // 10) * 20
        if al < 0.028:
            length_m += 40
        if s > 0.010:
            length_m += int(round(s - 0.010, 5) // 0.001) * 10
        if round(p_before - p_initial, 5) > 0.003:
            length_m += int(round(round(p_before - p_initial, 5) - 0.003, 5) // 0.001) * 20
        if si < 0.010:
            length_m += int(round(0.010 - si, 5) // 0.001) * 10

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
            flash(f"Success! Injected {length_used}m. Coil Balance Updated.", "success")
        else:
            flash("Error: Calculated length was 0.", "danger")
    except ValueError:
        flash("Input Error: Check your numbers.", "danger")
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
                flash(f'Active Coil Switched to: {input_number}', 'success')
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
                flash(f'New Coil Created & Activated: {input_number}', 'success')
        except ValueError:
            flash('Error in inputs. Please check numbers.', 'danger')
        return redirect(url_for('settings'))
    return render_template('settings.html', coil=coil)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("System V10 (Visual Upgrade) Active.")
    app.run(debug=True, host='0.0.0.0', port=5000)