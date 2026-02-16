"""
AEGIS Route Blueprints
======================
v4.7.0: Route modules split from monolithic app.py for maintainability.

Each module defines a Flask Blueprint with logically grouped routes.
All blueprints are registered in register_all_blueprints().
"""
from flask import Blueprint

# Import individual blueprints
from routes.core_routes import core_bp
from routes.review_routes import review_bp
from routes.config_routes import config_bp
from routes.roles_routes import roles_bp
from routes.scan_history_routes import scan_bp
from routes.jobs_routes import jobs_bp
from routes.data_routes import data_bp


def register_all_blueprints(app):
    """Register all route blueprints with the Flask app.

    Called from app.py during initialization to wire up all route modules.
    Blueprints use no url_prefix since routes were originally defined on app directly.
    """
    app.register_blueprint(core_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(config_bp)
    app.register_blueprint(roles_bp)
    app.register_blueprint(scan_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(data_bp)
