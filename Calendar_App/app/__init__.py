from flask import Flask
import sys
if not hasattr(sys, 'getdefaultencoding') or sys.getdefaultencoding() != 'utf-8':
    import importlib
    importlib.reload(sys)
    sys.setdefaultencoding('utf-8')

def create_app():
    app = Flask(__name__)
    app.config.from_object('config')
    app.secret_key = 'MySecret'
    from .routes import main
    app.register_blueprint(main)

    return app
