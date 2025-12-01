import os
import io
import json
import pandas as pd
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# =============================================================================
# CONFIGURATION & PATHS
# =============================================================================
SECRET_KEY = 'change_this_to_a_random_secret_key'

# Get absolute path to ensure folders are found correctly
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Define Folder Paths
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
UPLOAD_FOLDER = os.path.join(STATIC_DIR, 'uploads')
DB_PATH = os.path.join(BASE_DIR, 'production_v30_secure.db')


# =============================================================================
# 1. TEMPLATES (Automatic Generation)
# =============================================================================
def setup_directories_and_templates():
    if not os.path.exists(TEMPLATE_DIR): os.makedirs(TEMPLATE_DIR)
    if not os.path.exists(STATIC_DIR): os.makedirs(STATIC_DIR)
    if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)

    # --- BASE.HTML ---
    with open(os.path.join(TEMPLATE_DIR, 'base.html'), 'w', encoding='utf-8') as f:
        f.write('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ca-Wire Automation</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background-color: #f3f5f9; font-family: 'Segoe UI', sans-serif; color: #2c3e50; }
        .card { border: none; border-radius: 16px; box-shadow: 0 8px 30px rgba(0,0,0,0.05); }

        /* User Theme */
        .user-nav { background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); }
        .btn-primary-custom { background-image: linear-gradient(135deg, #0f2027 0%, #2c5364 100%); border: none; color: white; padding: 12px; border-radius: 8px; }

        /* Admin Theme */
        .admin-nav { background: #212529; border-bottom: 1px solid #495057; }

        /* Gradients */
        .grad-heat { background: linear-gradient(135deg, #FF512F 0%, #DD2476 100%); color: white; }
        .grad-chem { background: linear-gradient(135deg, #4776E6 0%, #8E54E9 100%); color: white; }
        .grad-dark { background: linear-gradient(135deg, #232526 0%, #414345 100%); color: white; }
    </style>
</head>
<body>
    {% if current_user.is_authenticated %}
        {% if current_user.role == 'admin' %}
        <!-- ADMIN NAVBAR -->
        <nav class="navbar navbar-expand-lg navbar-dark admin-nav mb-5">
            <div class="container-fluid px-4">
                <a class="navbar-brand fw-bold font-monospace" href="/admin">
                    <i class="fa-solid fa-terminal me-2 text-danger"></i>ROOT<span class="text-secondary">_ACCESS</span>
                </a>
                <div class="collapse navbar-collapse">
                    <div class="navbar-nav ms-auto gap-3">
                        <span class="nav-item nav-link text-white-50"><small>SECURE SESSION</small></span>
                        <a class="nav-link text-white fw-bold" href="/logout"><i class="fa-solid fa-power-off me-1"></i> Terminate</a>
                    </div>
                </div>
            </div>
        </nav>
        {% else %}
        <!-- USER NAVBAR -->
        <nav class="navbar navbar-expand-lg navbar-dark user-nav mb-5">
            <div class="container">
                <a class="navbar-brand" href="/">Ca-Wire<span style="color:#00f2fe"> System</span></a>
                <div class="collapse navbar-collapse">
                    <div class="navbar-nav ms-auto gap-3">
                        <a class="nav-link text-white" href="{{ url_for('operator_dashboard') }}">Dashboard</a>
                        <a class="nav-link text-white" href="{{ url_for('settings') }}">Settings</a>
                        <a class="nav-link text-white" href="/history">History</a>
                        <a class="nav-link text-warning" href="/subscription">Subscription</a>
                        <a class="nav-link text-white" href="/logout">Logout</a>
                    </div>
                </div>
            </div>
        </nav>
        {% endif %}
    {% endif %}

    <div class="container pb-5">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} mb-4 shadow-sm">{{ message }}</div>
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

    # --- ADMIN LOGIN.HTML (NEW SEPARATE LOGIN) ---
    with open(os.path.join(TEMPLATE_DIR, 'admin_login.html'), 'w', encoding='utf-8') as f:
        f.write('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Restricted Access</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background-color: #121212; color: #e0e0e0; height: 100vh; display: flex; align-items: center; justify-content: center; font-family: 'Courier New', monospace; }
        .login-box { width: 100%; max-width: 400px; padding: 40px; background: #1e1e1e; border: 1px solid #333; border-radius: 8px; box-shadow: 0 0 20px rgba(0,0,0,0.5); }
        .form-control { background: #2c2c2c; border: 1px solid #444; color: #fff; }
        .form-control:focus { background: #333; border-color: #dc3545; color: #fff; box-shadow: none; }
        .btn-danger { background: #b02a37; border: none; letter-spacing: 2px; }
        .blink { animation: blinker 1s linear infinite; }
        @keyframes blinker { 50% { opacity: 0; } }
    </style>
</head>
<body>
    <div class="login-box">
        <div class="text-center mb-4">
            <i class="fa-solid fa-shield-halved fa-3x text-danger mb-3"></i>
            <h4 class="text-uppercase fw-bold text-white">Admin Console</h4>
            <p class="text-muted small"><span class="blink">_</span>SECURE CONNECTION REQUIRED</p>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-dark text-danger border-danger small p-2 text-center mb-3">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <form method="POST">
            <div class="mb-3">
                <label class="small text-muted mb-1">ADMIN ID</label>
                <input type="text" name="username" class="form-control" autocomplete="off" required>
            </div>
            <div class="mb-4">
                <label class="small text-muted mb-1">PASSPHRASE</label>
                <input type="password" name="password" class="form-control" required>
            </div>
            <button type="submit" class="btn btn-danger w-100 py-2 fw-bold">AUTHENTICATE</button>
        </form>
        <div class="text-center mt-4">
            <a href="{{ url_for('login') }}" class="text-decoration-none text-muted small"><i class="fa-solid fa-arrow-left me-1"></i> Operator Login</a>
        </div>
    </div>
</body>
</html>
        ''')

    # --- ADMIN DASHBOARD (CLEAN ENTERPRISE LAYOUT) ---
    with open(os.path.join(TEMPLATE_DIR, 'admin.html'), 'w', encoding='utf-8') as f:
        f.write('''
{% extends "base.html" %}
{% block content %}
<style>
    :root { --admin-primary: #4361ee; --admin-bg: #f8f9fa; }
    .card-clean { border: 1px solid #e0e6ed; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); border-radius: 12px; background: white; }
    .card-header-clean { background: transparent; border-bottom: 1px solid #f1f2f3; padding: 1.5rem; }
    .avatar-initials { width: 40px; height: 40px; background: #e2e6ea; color: #495057; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.9rem; }
    .status-dot { height: 8px; width: 8px; border-radius: 50%; display: inline-block; margin-right: 6px; }
    .dot-success { background-color: #1abc9c; box-shadow: 0 0 0 3px rgba(26, 188, 156, 0.2); }
    .dot-danger { background-color: #e7515a; box-shadow: 0 0 0 3px rgba(231, 81, 90, 0.2); }
    .dot-warning { background-color: #e2a03f; }
    .task-card { border-left: 4px solid var(--admin-primary); transition: 0.2s; }
    .task-card:hover { transform: translateX(5px); }
</style>

<div class="row mb-4 align-items-end">
    <div class="col">
        <h6 class="text-uppercase text-muted small fw-bold ls-1">Administration</h6>
        <h2 class="fw-bold text-dark">User Management</h2>
    </div>
    <div class="col-auto">
        <span class="badge bg-white text-dark border py-2 px-3 shadow-sm">
            <i class="fa-regular fa-calendar me-2"></i> {{ now.strftime('%B %d, %Y') }}
        </span>
    </div>
</div>

<div class="row g-4">
    <!-- LEFT: USER DIRECTORY -->
    <div class="col-lg-8">
        <div class="card-clean h-100">
            <div class="card-header-clean d-flex justify-content-between align-items-center">
                <h5 class="fw-bold m-0 text-dark">User Directory <span class="text-muted fw-normal ms-2 fs-6">({{ all_users|length }} total)</span></h5>
                <div class="d-flex gap-2">
                    <button class="btn btn-sm btn-outline-secondary"><i class="fa-solid fa-filter me-1"></i> Filter</button>
                    <button class="btn btn-sm btn-outline-primary"><i class="fa-solid fa-download me-1"></i> Export</button>
                </div>
            </div>
            <div class="table-responsive">
                <table class="table align-middle mb-0 table-hover">
                    <thead class="bg-light text-secondary small">
                        <tr>
                            <th class="ps-4 py-3 border-0 rounded-start">User Profile</th>
                            <th class="py-3 border-0">Role</th>
                            <th class="py-3 border-0">Access Status</th>
                            <th class="py-3 border-0 rounded-end text-end pe-4">Expiry</th>
                        </tr>
                    </thead>
                    <tbody class="border-top-0">
                        {% for user in all_users %}
                        <tr>
                            <td class="ps-4 py-3">
                                <div class="d-flex align-items-center">
                                    <div class="avatar-initials me-3">{{ user.username[:2].upper() }}</div>
                                    <div>
                                        <div class="fw-bold text-dark">{{ user.username }}</div>
                                        <div class="small text-muted">ID: #{{ user.id }}</div>
                                    </div>
                                </div>
                            </td>
                            <td>
                                {% if user.role == 'admin' %}
                                    <span class="badge bg-dark text-white shadow-sm">ADMIN</span>
                                {% else %}
                                    <span class="badge bg-light text-dark border">OPERATOR</span>
                                {% endif %}
                            </td>
                            <td>
                                {% if user.role == 'admin' %}
                                    <span class="text-dark fw-bold small"><span class="status-dot dot-success"></span>Permanent</span>
                                {% elif user.subscription_expiry and user.subscription_expiry > now %}
                                    <span class="text-success fw-bold small"><span class="status-dot dot-success"></span>Active</span>
                                {% else %}
                                    <span class="text-danger fw-bold small"><span class="status-dot dot-danger"></span>Expired</span>
                                {% endif %}
                            </td>
                            <td class="text-end pe-4 text-muted font-monospace small">
                                {{ user.subscription_expiry.strftime('%Y-%m-%d') if user.subscription_expiry else '--' }}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- RIGHT: ACTION PANEL & CONFIG -->
    <div class="col-lg-4">

        <!-- PENDING APPROVALS SECTION -->
        <div class="mb-4">
            <h6 class="fw-bold text-muted text-uppercase small mb-3">Action Queue <span class="badge bg-danger rounded-pill ms-1">{{ pending_users|length }}</span></h6>
            {% if pending_users %}
                {% for p_user in pending_users %}
                <div class="card-clean task-card p-3 mb-3">
                    <div class="d-flex justify-content-between mb-2">
                        <span class="fw-bold text-dark">{{ p_user.username }}</span>
                        <span class="badge bg-warning text-dark">Pending</span>
                    </div>
                    <div class="bg-light p-2 rounded mb-3 small">
                        <span class="text-muted d-block text-uppercase" style="font-size: 0.7rem;">Transaction ID / UTR</span>
                        <span class="font-monospace fw-bold text-dark">{{ p_user.submitted_utr }}</span>
                    </div>
                    <div class="row g-2">
                        <div class="col-6">
                            <form action="{{ url_for('admin_approve_payment') }}" method="POST">
                                <input type="hidden" name="user_id" value="{{ p_user.id }}">
                                <button type="submit" class="btn btn-primary w-100 btn-sm">Approve</button>
                            </form>
                        </div>
                        <div class="col-6">
                            <form action="{{ url_for('admin_reject_payment') }}" method="POST">
                                <input type="hidden" name="user_id" value="{{ p_user.id }}">
                                <button type="submit" class="btn btn-outline-danger w-100 btn-sm">Deny</button>
                            </form>
                        </div>
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <div class="card-clean p-4 text-center border-dashed">
                    <i class="fa-solid fa-clipboard-check fa-2x text-muted mb-2"></i>
                    <p class="text-muted small m-0">All tasks completed.</p>
                </div>
            {% endif %}
        </div>

        <!-- QR CONFIG SECTION -->
        <div>
            <h6 class="fw-bold text-muted text-uppercase small mb-3">System Configuration</h6>
            <div class="card-clean p-4">
                <div class="text-center mb-3">
                    <img src="{{ url_for('static', filename='uploads/upi_qr.png') }}?v={{ now.timestamp() }}" class="img-fluid rounded border p-1" style="width: 120px; height: 120px; object-fit: contain;">
                    <div class="small text-muted mt-2">Active Payment QR</div>
                </div>
                <form action="{{ url_for('admin_upload_qr') }}" method="POST" enctype="multipart/form-data">
                    <label class="form-label fw-bold small">Upload Replacement</label>
                    <input type="file" name="file" class="form-control form-control-sm mb-3" required accept="image/*">
                    <button type="submit" class="btn btn-dark w-100 btn-sm"><i class="fa-solid fa-cloud-arrow-up me-2"></i>Update System</button>
                </form>
            </div>
        </div>

    </div>
</div>
{% endblock %}
        ''')

    # --- SUBSCRIPTION.HTML ---
    with open(os.path.join(TEMPLATE_DIR, 'subscription.html'), 'w', encoding='utf-8') as f:
        f.write('''
{% extends "base.html" %} 
{% block content %} 
<div class="row justify-content-center"> 
    <div class="col-lg-5"> 
        <div class="card border-0 shadow-lg text-center overflow-hidden"> 
            <div class="card-header grad-dark p-4"> 
                <h4 class="text-white m-0">Subscription Status</h4> 
            </div> 
            <div class="card-body p-0"> 
                <div class="p-5 bg-white">
                    {% if days_left > 0 %} 
                        <!-- 1. ACTIVE PLAN -->
                        <div class="mb-4"><i class="fa-solid fa-circle-check fa-5x text-success"></i></div>
                        <h2 class="fw-bold text-dark">Active Plan</h2> 
                        <p class="text-muted">Expires on: <span class="fw-bold">{{ expiry_date }}</span></p> 
                        <div class="alert alert-success d-inline-block px-4 py-2 rounded-pill fw-bold">{{ days_left }} Days Remaining</div>
                        <div class="mt-4">
                            <a href="{{ url_for('operator_dashboard') }}" class="btn btn-dark btn-lg px-5 shadow">Go to Dashboard</a>
                        </div>

                    {% elif current_user.submitted_utr %}
                        <!-- 2. PENDING APPROVAL -->
                        <div class="mb-3"><i class="fa-solid fa-hourglass-half fa-4x text-warning pulse-btn"></i></div>
                        <h3 class="fw-bold text-warning">Verification Pending</h3>
                        <p class="text-muted mb-4">We are verifying your payment details.</p>

                        <div class="bg-light p-3 rounded border d-inline-block text-start mb-3">
                            <small class="text-uppercase text-muted fw-bold d-block mb-1">Submitted UTR / Ref ID</small>
                            <div class="font-monospace fs-5 text-dark fw-bold">{{ current_user.submitted_utr }}</div>
                        </div>
                        <p class="small text-muted">Access will be restored immediately after admin approval.</p>
                        <button class="btn btn-outline-secondary btn-sm" disabled>Waiting for Admin...</button>

                    {% else %} 
                        <!-- 3. EXPIRED / PAY NOW -->
                        <div class="mb-3"><i class="fa-solid fa-triangle-exclamation fa-4x text-danger"></i></div>
                        <h3 class="fw-bold text-danger">Plan Expired</h3> 
                        <p class="text-muted mb-4">Renew now to access the calculator.</p>

                        <div class="card bg-light border-0 rounded-4 text-start p-4 mt-3">
                            <h6 class="fw-bold text-uppercase text-secondary mb-3 small ls-1">Step 1: Scan & Pay</h6>
                            <div class="text-center bg-white p-3 rounded mb-3 border">
                                <img src="{{ url_for('static', filename='uploads/upi_qr.png') }}?v={{ now.timestamp() }}" 
                                     class="img-fluid" style="max-height: 200px;" 
                                     alt="Admin has not uploaded a QR code yet">
                                <p class="small text-muted mt-2">Scan with PhonePe / GPay / Paytm</p>
                            </div>

                            <h6 class="fw-bold text-uppercase text-secondary mb-3 small ls-1 mt-2">Step 2: Submit UTR for Verification</h6>
                            <form action="{{ url_for('subscription') }}" method="POST">
                                <div class="mb-3">
                                    <label class="form-label small fw-bold">Enter UPI Reference ID / UTR</label>
                                    <input type="text" name="utr" class="form-control" placeholder="e.g. 3245xxxxxxxx" required>
                                </div>
                                <button type="submit" class="btn btn-success w-100 py-3 fw-bold">
                                    SUBMIT FOR APPROVAL <i class="fa-solid fa-paper-plane ms-2"></i>
                                </button> 
                            </form>
                        </div>
                    {% endif %} 
                </div>
            </div> 
        </div> 
    </div> 
</div> 
{% endblock %}
        ''')

    # --- OPERATOR_DASHBOARD.HTML ---
    with open(os.path.join(TEMPLATE_DIR, 'operator_dashboard.html'), 'w', encoding='utf-8') as f:
        f.write('''
{% extends "base.html" %} 
{% block content %}
<style>
    .fade-in { animation: fadeIn 0.5s ease-in; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    .card-hover:hover { transform: translateY(-3px); transition: all 0.3s ease; box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
    .pulse-btn { animation: pulse 2s infinite; }
    @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.7); } 70% { box-shadow: 0 0 0 10px rgba(255, 255, 255, 0); } 100% { box-shadow: 0 0 0 0 rgba(255, 255, 255, 0); } }
    .form-floating > .form-control:focus ~ label { color: #DD2476; font-weight: bold; }
    .form-floating > .form-control:focus { border-color: #DD2476; box-shadow: 0 0 0 0.25rem rgba(221, 36, 118, 0.25); }
</style>

<div class="d-flex justify-content-between align-items-center mb-4 fade-in">
    <h3 class="fw-bold"><i class="fa-solid fa-industry me-2"></i>Operator Dashboard</h3>
    <a href="{{ url_for('settings') }}" class="btn btn-dark shadow-sm"><i class="fa-solid fa-gear me-2"></i>Coil Settings</a>
</div>

<div class="row g-4 fade-in">
    <div class="col-lg-8">
        <form id="calcForm" method="POST" action="{{ url_for('confirm_injection') }}">
            <div class="card shadow-sm border-0 mb-4 card-hover">
                <div class="card-header grad-heat py-3"><h5 class="m-0 fw-bold"><i class="fa-solid fa-fire me-2"></i>Heat Parameters</h5></div>
                <div class="card-body p-4">
                    <div class="row g-3">
                        <div class="col-md-6"><div class="form-floating"><input type="text" class="form-control fw-bold" id="heat_id" name="heat_id" required><label>Heat ID</label></div></div>
                        <div class="col-md-6"><div class="form-floating"><input type="text" class="form-control" id="lf_number" name="lf_number" required><label>LF Number</label></div></div>
                        <div class="col-md-4"><div class="form-floating"><input type="number" step="0.1" class="form-control" id="tonnage" name="tonnage" value="150" required><label>Tonnage</label></div></div>
                        <div class="col-md-4"><div class="form-floating"><input type="number" class="form-control" id="temp" name="temp" value="1580" required><label>Temp (°C)</label></div></div>
                        <div class="col-md-4"><div class="form-floating"><input type="number" class="form-control" id="freeboard" name="freeboard" value="400"><label>Freeboard</label></div></div>
                    </div>
                </div>
            </div>
            <div class="card shadow-sm border-0 card-hover">
                <div class="card-header grad-chem py-3"><h5 class="m-0 fw-bold"><i class="fa-solid fa-flask me-2"></i>Chemistry</h5></div>
                <div class="card-body p-4 bg-light">
                    <div class="row g-3">
                        <div class="col-md-4"><label class="small fw-bold text-muted">Al%</label><input type="number" step="0.001" class="form-control" id="al" name="al" value="0.040"></div>
                        <div class="col-md-4"><label class="small fw-bold text-muted">S%</label><input type="number" step="0.001" class="form-control" id="s" name="s" value="0.005"></div>
                        <div class="col-md-4"><label class="small fw-bold text-muted">Si%</label><input type="number" step="0.001" class="form-control" id="si" name="si_pct" value="0.200"></div>
                        <div class="col-md-6"><label class="small fw-bold text-muted">Initial P%</label><input type="number" step="0.001" class="form-control" id="p_initial" name="p_initial" value="0.012"></div>
                        <div class="col-md-6"><label class="small fw-bold text-muted">Current P%</label><input type="number" step="0.001" class="form-control" id="p_before" name="p_before" value="0.015"></div>
                        <input type="hidden" id="speed" value="120">
                        <input type="hidden" id="calculated_length_hidden" name="calculated_length_hidden" value="0">
                    </div>
                </div>
            </div>
        </form>
    </div>

    <div class="col-lg-4">
        <div class="card border-0 shadow-sm mb-4 grad-dark">
            <div class="card-body p-4">
                <div class="d-flex justify-content-between mb-2"><span class="text-white-50 small">ACTIVE COIL</span><span class="badge bg-light text-dark">{{ coil.coil_number }}</span></div>
                <h2 class="fw-bold mb-3">{{ "%.0f"|format(coil.current_length) }} <span class="fs-6 text-white-50">m left</span></h2>
                {% set pct = (coil.current_length / coil.total_length * 100) if coil.total_length > 0 else 0 %}
                <div class="progress" style="height: 6px; background: rgba(255,255,255,0.1);"><div class="progress-bar bg-success" style="width: {{ pct }}%"></div></div>
            </div>
        </div>
        <div class="card h-100 border-0 shadow-lg text-white" style="background: linear-gradient(180deg, #2C3E50 0%, #000000 100%);">
            <div class="card-body d-flex flex-column justify-content-between p-4">
                <div class="text-center py-4 rounded-4 mb-4" style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);">
                    <span class="small text-info text-uppercase fw-bold">Required Wire</span>
                    <h1 class="display-2 fw-bolder my-2"><span id="resultDisplay">0</span><span class="fs-4 text-white-50">m</span></h1>
                    <div class="badge bg-dark border border-secondary px-3 py-2"><i class="fa-regular fa-clock me-1"></i> <span id="timeDisplay">0.0 min</span></div>
                </div>
                <div class="d-grid gap-3">
                    <button type="button" class="btn btn-info fw-bold py-3 rounded-pill shadow pulse-btn" onclick="predictLength()">CALCULATE</button>
                    <button type="submit" form="calcForm" class="btn btn-success fw-bold py-3 rounded-pill shadow" id="injectBtn" disabled>CONFIRM INJECTION</button>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
    function predictLength() {
        const btn = document.querySelector('button[onclick="predictLength()"]');
        btn.innerHTML = 'Processing...';
        const data = {
            tonnage: document.getElementById('tonnage').value, freeboard: document.getElementById('freeboard').value,
            speed: document.getElementById('speed').value, temp: document.getElementById('temp').value,
            al: document.getElementById('al').value, s: document.getElementById('s').value,
            si: document.getElementById('si').value, p_initial: document.getElementById('p_initial').value,
            p_before: document.getElementById('p_before').value
        };
        fetch('/calculate_api', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data) })
        .then(res => res.json()).then(data => {
            btn.innerHTML = 'CALCULATE';
            if(data.success) {
                document.getElementById('resultDisplay').innerText = data.length_m;
                document.getElementById('timeDisplay').innerText = data.time_min + " min";
                document.getElementById('calculated_length_hidden').value = data.length_m;
                document.getElementById('injectBtn').disabled = false;
            } else { alert(data.error); if(data.redirect) window.location.href = data.redirect; }
        });
    }
</script>
{% endblock %}
        ''')

    # --- LOGIN.HTML (USER ONLY) ---
    with open(os.path.join(TEMPLATE_DIR, 'login.html'), 'w', encoding='utf-8') as f:
        f.write('''
{% extends "base.html" %} 
{% block content %} 
<div class="row justify-content-center mt-5"> 
    <div class="col-md-5"> 
        <div class="card shadow-lg border-0"> 
            <div class="card-body p-5 text-center"> 
                <h3 class="fw-bold mb-4">Operator Login</h3> 
                <form method="POST"> 
                    <div class="mb-3 text-start"> <label class="form-label">Username</label> <input type="text" name="username" class="form-control form-control-lg" required> </div> 
                    <div class="mb-4 text-start"> <label class="form-label">Password</label> <input type="password" name="password" class="form-control form-control-lg" required> </div> 
                    <button type="submit" class="btn btn-primary-custom w-100 py-3 shadow">LOGIN</button> 
                </form> 
                <div class="mt-4"> <a href="{{ url_for('signup') }}" class="text-decoration-none">Create Account</a> </div> 
                <div class="mt-3"> <a href="{{ url_for('admin_login') }}" class="small text-muted text-decoration-none"><i class="fa-solid fa-shield-halved me-1"></i>Admin Portal</a> </div>
            </div> 
        </div> 
    </div> 
</div> 
{% endblock %}
        ''')

    with open(os.path.join(TEMPLATE_DIR, 'signup.html'), 'w', encoding='utf-8') as f:
        f.write('''
{% extends "base.html" %} 
{% block content %} 
<div class="row justify-content-center mt-5"> 
    <div class="col-md-5"> 
        <div class="card shadow-lg border-0"> 
            <div class="card-body p-5 text-center"> 
                <h3 class="fw-bold mb-4">Create Account</h3> 
                <form method="POST"> 
                    <div class="mb-3 text-start"> <label class="form-label">Username</label> <input type="text" name="username" class="form-control" required> </div> 
                    <div class="mb-4 text-start"> <label class="form-label">Password</label> <input type="password" name="password" class="form-control" required> </div> 
                    <button type="submit" class="btn btn-success w-100 py-3 shadow">SIGN UP</button> 
                </form> 
                <div class="mt-4"><a href="{{ url_for('login') }}">Back to Login</a></div> 
            </div> 
        </div> 
    </div> 
</div> 
{% endblock %}
        ''')

    with open(os.path.join(TEMPLATE_DIR, 'history.html'), 'w', encoding='utf-8') as f:
        f.write('''
{% extends "base.html" %} 
{% block content %} 
<div class="card shadow-sm"> 
    <div class="card-header bg-white d-flex justify-content-between align-items-center py-3"> 
        <h5 class="m-0 fw-bold">Injection Logs</h5> 
        <div class="d-flex gap-2"> 
            <a href="{{ url_for('export_data') }}" class="btn btn-success btn-sm">Export Excel</a> 
            <form action="{{ url_for('delete_history') }}" method="POST" onsubmit="return confirm('Delete all logs?');"> 
                <button type="submit" class="btn btn-outline-danger btn-sm">Clear</button> 
            </form> 
        </div> 
    </div> 
    <div class="card-body p-0"> 
        <div class="table-responsive"> 
            <table class="table table-hover align-middle mb-0"> 
                <thead class="bg-light"> <tr> <th class="ps-4">Time</th> <th>Heat ID</th> <th>LF</th> <th>Coil</th> <th>Tonnage</th> <th>Used (m)</th> </tr> </thead> 
                <tbody> 
                    {% for log in logs %} 
                    <tr> <td class="ps-4">{{ log.timestamp.strftime('%m-%d %H:%M') }}</td> <td>{{ log.heat_id }}</td> <td>{{ log.lf_number }}</td> <td>{{ log.coil_number }}</td> <td>{{ log.heat_tonnage }}</td> <td>{{ "%.1f"|format(log.calculated_length) }}</td> </tr> 
                    {% else %} 
                    <tr><td colspan="6" class="text-center py-3">No history.</td></tr> 
                    {% endfor %} 
                </tbody> 
            </table> 
        </div> 
    </div> 
</div> 
{% endblock %}
        ''')

    with open(os.path.join(TEMPLATE_DIR, 'settings.html'), 'w', encoding='utf-8') as f:
        f.write('''
{% extends "base.html" %} 
{% block content %} 
<div class="row justify-content-center"> 
    <div class="col-lg-6"> 
        <div class="d-flex align-items-center mb-3"> 
            <a href="{{ url_for('operator_dashboard') }}" class="btn btn-outline-secondary me-3 rounded-circle" style="width:40px;height:40px;padding:0;line-height:38px;"><i class="fa-solid fa-arrow-left"></i></a> 
            <h4 class="fw-bold m-0">Coil Configuration</h4> 
        </div> 
        <div class="card shadow-lg border-0 overflow-hidden"> 
            <div class="card-header grad-dark text-white p-4"> 
                <div class="d-flex justify-content-between align-items-center"> 
                    <span>Active Coil: <strong>{{ coil.coil_number }}</strong></span> 
                    <i class="fa-solid fa-sliders"></i> 
                </div> 
            </div> 
            <div class="card-body p-4"> 
                <form method="POST"> 
                    <div class="mb-4"> 
                        <label class="form-label text-uppercase small fw-bold text-muted">New / Current Coil ID</label> 
                        <div class="input-group"> 
                            <span class="input-group-text bg-white"><i class="fa-solid fa-barcode"></i></span> 
                            <input type="text" class="form-control fw-bold" name="coil_number" value="{{ coil.coil_number }}"> 
                        </div> 
                    </div> 
                    <div class="row g-3"> 
                        <div class="col-md-6"> <label class="form-label text-muted small fw-bold">Total Length (m)</label> <input type="number" class="form-control" name="total_length" value="{{ coil.total_length }}"> </div> 
                        <div class="col-md-6"> <label class="form-label text-muted small fw-bold">Density (g/m)</label> <input type="number" step="0.1" class="form-control" name="density" value="{{ coil.density }}"> </div> 
                        <div class="col-md-6"> <label class="form-label text-muted small fw-bold">Target Recovery (%)</label> <input type="number" step="0.1" class="form-control" name="recovery_target" value="{{ coil.recovery_target }}"> </div> 
                        <div class="col-md-6"> <label class="form-label text-muted small fw-bold">Target PPM</label> <input type="number" class="form-control" name="target_ppm" value="{{ coil.target_ppm }}"> </div> 
                    </div> 
                    <hr class="my-4"> 
                    <button type="submit" class="btn btn-primary-custom w-100 py-3 fw-bold shadow"> <i class="fa-solid fa-floppy-disk me-2"></i> SAVE CONFIGURATION </button> 
                </form> 
            </div> 
        </div> 
    </div> 
</div> 
{% endblock %}
        ''')


setup_directories_and_templates()

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
# Default login view is for standard users
login_manager.login_view = 'login'


# --- MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(50), default='operator')
    subscription_expiry = db.Column(db.DateTime, nullable=True)
    submitted_utr = db.Column(db.String(100), nullable=True)


class CoilConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    coil_number = db.Column(db.String(50), default="C1")
    is_active = db.Column(db.Boolean, default=True)
    total_length = db.Column(db.Float, default=5000.0)
    current_length = db.Column(db.Float, default=5000.0)
    heats_treated = db.Column(db.Integer, default=0)
    density = db.Column(db.Float, default=68.0)
    target_ppm = db.Column(db.Float, default=30.0)
    recovery_target = db.Column(db.Float, default=20.0)


class InjectionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    heat_id = db.Column(db.String(50))
    lf_number = db.Column(db.String(20))
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


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- HELPERS ---
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


def subscription_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated: return login_manager.unauthorized()
        if current_user.role != 'admin':
            if not current_user.subscription_expiry or current_user.subscription_expiry < datetime.now():
                if request.path.startswith('/calculate_api'): return jsonify(
                    {'success': False, 'error': 'SUBSCRIPTION EXPIRED', 'redirect': '/subscription'})
                flash("Subscription expired.", "danger")
                return redirect(url_for('subscription'))
        return f(*args, **kwargs)

    return decorated_function


@app.context_processor
def inject_now():
    return {'now': datetime.now(), 'pending_count': User.query.filter(User.submitted_utr != None).count()}


@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response


# --- ROUTES ---
@app.route('/', methods=['GET'])
def index():
    if not current_user.is_authenticated: return redirect(url_for('login'))

    # Strict Redirection Logic
    if current_user.role == 'admin':
        return redirect(url_for('admin_panel'))
    else:
        # Standard users go to Subscription check or Dashboard
        if current_user.subscription_expiry and current_user.subscription_expiry > datetime.now():
            return redirect(url_for('operator_dashboard'))
        return redirect(url_for('subscription'))


# --- USER LOGIN (OPERATORS ONLY) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()

        # LOGIC: If user exists, pass matches
        if user and check_password_hash(user.password, request.form.get('password')):
            # If Admin logs in here, strictly redirect to admin panel instead of showing error
            if user.role == 'admin':
                login_user(user)
                return redirect(url_for('admin_panel'))

            login_user(user)
            return redirect(url_for('index'))

        flash('Invalid operator credentials', 'danger')
    return render_template('login.html')


# --- ADMIN LOGIN (SECURE PORTAL) ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()

        # LOGIC: Must be admin role to enter here
        if user and check_password_hash(user.password, request.form.get('password')):
            if user.role == 'admin':
                login_user(user)
                return redirect(url_for('admin_panel'))
            else:
                flash('Unauthorized. Operators use the standard login.', 'warning')
                return redirect(url_for('login'))

        flash('Authentication Failed. Incident logged.', 'dark')
    return render_template('admin_login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form.get('username')).first():
            flash('Username taken', 'danger')
        else:
            # Create NEW USER (Default: Operator)
            # Security Note: Admins cannot be created via signup form
            db.session.add(User(username=request.form.get('username'),
                                password=generate_password_hash(request.form.get('password')), role='operator'))
            db.session.commit()
            flash('Created. Login now.', 'success')
            return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# --- ADMIN PANEL (SECURE) ---
@app.route('/admin')
@login_required
def admin_panel():
    # Strict check: If a normal user tries to access /admin, kick them out
    if current_user.role != 'admin':
        abort(403)

    pending_users = User.query.filter(User.submitted_utr != None, User.submitted_utr != "").all()
    all_users = User.query.all()
    return render_template('admin.html', pending_users=pending_users, all_users=all_users, now=datetime.now())


@app.route('/admin/upload_qr', methods=['POST'])
@login_required
def admin_upload_qr():
    if current_user.role != 'admin': abort(403)
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'upi_qr.png'))
            flash('QR Code Updated!', 'success')
    return redirect(url_for('admin_panel'))


@app.route('/admin/approve_payment', methods=['POST'])
@login_required
def admin_approve_payment():
    if current_user.role != 'admin': abort(403)
    user = User.query.get(request.form.get('user_id'))
    if user:
        user.subscription_expiry = datetime.now() + timedelta(days=30)
        user.submitted_utr = None
        db.session.commit()
        flash(f'Payment Approved for {user.username}. Access granted.', 'success')
    return redirect(url_for('admin_panel'))


@app.route('/admin/reject_payment', methods=['POST'])
@login_required
def admin_reject_payment():
    if current_user.role != 'admin': abort(403)
    user = User.query.get(request.form.get('user_id'))
    if user:
        user.submitted_utr = None
        db.session.commit()
        flash(f'Payment Rejected for {user.username}.', 'danger')
    return redirect(url_for('admin_panel'))


@app.route('/subscription', methods=['GET', 'POST'])
@login_required
def subscription():
    # If admin tries to go to subscription page, send to admin panel
    if current_user.role == 'admin':
        return redirect(url_for('admin_panel'))

    # --- MANUAL APPROVAL LOGIC ---
    if request.method == 'POST':
        utr = request.form.get('utr')
        if utr:
            # ONLY save UTR. Do NOT grant time.
            current_user.submitted_utr = utr
            db.session.commit()
            flash(f"UTR {utr} Submitted. Waiting for Admin Approval.", "info")
            return redirect(url_for('subscription'))
        else:
            flash("Please enter a valid Transaction ID.", "danger")

    # --- DISPLAY LOGIC ---
    days = 0
    if current_user.subscription_expiry:
        delta = current_user.subscription_expiry - datetime.now()
        days = delta.days if delta.days > 0 else 0
    return render_template('subscription.html', days_left=days,
                           expiry_date=current_user.subscription_expiry.strftime(
                               '%Y-%m-%d') if current_user.subscription_expiry else "N/A")


@app.route('/operator_dashboard')
@login_required
@subscription_required
def operator_dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_panel'))
    return render_template('operator_dashboard.html', coil=get_active_coil())


@app.route('/calculate_api', methods=['POST'])
@login_required
@subscription_required
def calculate_api():
    d = request.json
    c = get_active_coil()
    try:
        tonnage, freeboard, speed, temp = float(d['tonnage']), float(d['freeboard']), float(d['speed']), float(
            d['temp'])
        pure_ca = (tonnage * 1000) * (c.target_ppm / 1000000)
        gross_ca = pure_ca / (c.recovery_target / 100)
        length = (gross_ca * 1000) / c.density
        if freeboard > 500: length += int((freeboard - 500) // 50) * 20
        if temp > 1600: length += int((temp - 1600) // 10) * 20
        if float(d['al']) < 0.028: length += 40
        if float(d['s']) > 0.010: length += int(round(float(d['s']) - 0.010, 5) // 0.001) * 10
        if round(float(d['p_before']) - float(d['p_initial']), 5) > 0.003: length += int(
            round(round(float(d['p_before']) - float(d['p_initial']), 5) - 0.003, 5) // 0.001) * 20
        if float(d['si']) < 0.010: length += int(round(0.010 - float(d['si']), 5) // 0.001) * 10
        return jsonify(
            {'success': True, 'length_m': round(length, 2), 'time_min': round(length / speed if speed > 0 else 0, 2)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/confirm_injection', methods=['POST'])
@login_required
@subscription_required
def confirm_injection():
    c = get_active_coil()
    l = float(request.form.get('calculated_length_hidden', 0))
    if l > 0:
        c.current_length -= l
        c.heats_treated += 1
        db.session.add(InjectionLog(heat_id=request.form.get('heat_id'), lf_number=request.form.get('lf_number'),
                                    coil_number=c.coil_number, balance_after=c.current_length,
                                    heat_tonnage=float(request.form.get('tonnage')),
                                    freeboard=float(request.form.get('freeboard', 0)), calculated_length=l,
                                    al_before=float(request.form.get('al', 0)),
                                    s_before=float(request.form.get('s', 0)),
                                    si_before=float(request.form.get('si_pct', 0)),
                                    p_before=float(request.form.get('p_before', 0)),
                                    p_initial_lf=float(request.form.get('p_initial', 0)),
                                    temp=float(request.form.get('temp', 0))))
        db.session.commit()
        flash(f"Injected {l}m", "success")
    return redirect(url_for('operator_dashboard'))


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    # Only operators or admin can access, but generally admin uses admin panel
    if request.method == 'POST':
        c_num = request.form['coil_number'].strip()
        exist = CoilConfig.query.filter_by(coil_number=c_num).first()
        CoilConfig.query.update({CoilConfig.is_active: False})
        if exist:
            exist.is_active = True
            exist.total_length = float(request.form['total_length'])
            exist.density = float(request.form['density'])
            exist.recovery_target = float(request.form['recovery_target'])
            exist.target_ppm = float(request.form['target_ppm'])
        else:
            db.session.add(
                CoilConfig(coil_number=c_num, is_active=True, total_length=float(request.form['total_length']),
                           current_length=float(request.form['total_length']), density=float(request.form['density']),
                           recovery_target=float(request.form['recovery_target']),
                           target_ppm=float(request.form['target_ppm'])))
        db.session.commit()
        flash('Settings Saved', 'success')
        return redirect(url_for('settings'))
    return render_template('settings.html', coil=get_active_coil())


@app.route('/history')
@login_required
def history():
    return render_template('history.html',
                           logs=InjectionLog.query.order_by(InjectionLog.timestamp.desc()).limit(50).all())


@app.route('/delete_history', methods=['POST'])
@login_required
def delete_history():
    db.session.query(InjectionLog).delete();
    db.session.commit()
    return redirect(url_for('history'))


@app.route('/export_data')
@login_required
def export_data():
    logs = InjectionLog.query.all()
    if not logs: return redirect(url_for('history'))
    data = [{'Time': l.timestamp, 'Heat': l.heat_id, 'Used': l.calculated_length} for l in logs]
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='openpyxl') as w: pd.DataFrame(data).to_excel(w, index=False)
    out.seek(0)
    return send_file(out, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name='logs.xlsx')


if __name__ == '__main__':
    # If admin_panel() is a separate function you defined, call it here on its own line.
    # admin_panel()

    with app.app_context():
        db.create_all()

        # Default Admin setup
        if not User.query.filter_by(username='admin').first():
            db.session.add(
                User(
                    username='admin',
                    password=generate_password_hash('admin123'),
                    role='admin'
                )
            )
            db.session.commit()
            print(">>> SYSTEM: Admin created. Login at /admin/login")
            print(">>> CREDENTIALS: admin / admin123")

    app.run(debug=True, host='0.0.0.0', port=5000)