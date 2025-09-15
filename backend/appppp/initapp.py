from flask import Flask
from route import main_bp
import os


def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.urandom(24)  # 隨機生成一個 24 位的秘鑰
    app.register_blueprint(main_bp)
    return app
     
     

if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(host='0.0.0.0', port=8000 , debug=True)
    
    



