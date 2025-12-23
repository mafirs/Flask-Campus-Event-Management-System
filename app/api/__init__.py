from flask import Blueprint

# úAPIİş
auth_bp = Blueprint('auth', __name__)
venues_bp = Blueprint('venues', __name__)
materials_bp = Blueprint('materials', __name__)
applications_bp = Blueprint('applications', __name__)
approvals_bp = Blueprint('approvals', __name__)
dashboard_bp = Blueprint('dashboard', __name__)

# üe@	D!WånİèŒ
from app.api import auth, venues, materials, applications, approvals, dashboard