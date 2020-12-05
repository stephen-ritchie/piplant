import logging
import os

from flask import Flask
from . import __version__


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'db.sqlite')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'db.sqlite'),
    )
    app.jinja_env.globals['BUILD_VERSION'] = __version__

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    with app.app_context():
        # Configure the logger
        configure_logger(app)

        # Init the database
        from piplant.models import db
        db.init_app(app)
        db.create_all()

        # Init the auth manager
        from .auth import login_manager
        login_manager.init_app(app)

        # Register the blueprints
        register_blueprints(app)

        return app


def configure_logger(app):
    file_handler = logging.FileHandler(os.path.join(app.instance_path, "server.log"))
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    app.logger.addHandler(file_handler)


def register_blueprints(app):
    from .views.api import api
    from .views.api import __version__ as api_version
    app.register_blueprint(api, url_prefix='/api/v%s' % api_version)

    from .auth import auth
    app.register_blueprint(auth)

    from .views.home import home
    app.register_blueprint(home)

    from .views.device import device
    app.register_blueprint(device)

    from .views.user import user
    app.register_blueprint(user)

    from .views.schedule import schedule
    app.register_blueprint(schedule, url_prefix='/schedules')
