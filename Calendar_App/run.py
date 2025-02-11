from app import create_app
import sys
if not hasattr(sys, 'getdefaultencoding') or sys.getdefaultencoding() != 'utf-8':
    import importlib
    importlib.reload(sys)
    sys.setdefaultencoding('utf-8')
import os

app = create_app()
app.secret_key = 'MySecretKey'  # Définissez une clé secrète unique et secrète


if __name__ == '__main__':
    app.secret_key = 'MySecretKey' 
    app.run(debug=True)