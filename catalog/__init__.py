"""
The Flask class and Flask's Blueprint registration is placed
in the catalog module's global scope.

"""

from flask import Flask
from catalog.login.controller import bp_login
from catalog.main.controller import bp_main
from catalog.rlimiter.controller import bp_rlimit

app = Flask(__name__)

app.register_blueprint(bp_login, url_prefix="/user")
app.register_blueprint(bp_main, url_prefix="/catalog")
app.register_blueprint(bp_rlimit, url_prefix="/rlimit")

# For file upload feature
app.config["UPLOAD_FOLDER"] = "catalog/static/uploads"
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024 # Restrict file size to 1MB
