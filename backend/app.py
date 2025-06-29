import os
from pathlib import Path
from flask import Flask, render_template
from flask_cors import CORS
from routes.query import query_bp
from routes.rebuild import rebuild_bp
from routes.documents import documents_bp
from routes.info import info_bp

app = Flask(__name__)
CORS(app)

# Register blueprints for each set of routes
app.register_blueprint(query_bp)
app.register_blueprint(rebuild_bp)
app.register_blueprint(documents_bp)
app.register_blueprint(info_bp)


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
