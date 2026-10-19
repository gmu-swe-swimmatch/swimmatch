"""Blueprint registration."""


def register_blueprints(app):
    from backend.routes.athlete import athlete_bp
    from backend.routes.auth import auth_bp
    from backend.routes.pages import pages_bp
    from backend.routes.schools import schools_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(athlete_bp)
    app.register_blueprint(schools_bp)
