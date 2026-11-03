def register_blueprints(app):
    from . import admin_api, auth_api, pages, public_api, students_api

    for module in (pages, auth_api, students_api, public_api, admin_api):
        app.register_blueprint(module.bp)
