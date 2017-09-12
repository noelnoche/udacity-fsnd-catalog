#!/usr/bin/env python

"""
Executes the catalog application. From the application directory run
the following command:

    python run.py

"""

from catalog import app

if __name__ == "__main__":
    app.debug = True

    # In order to use session and flash we need a secret key
    # You can generate one by opening the Python interpreter
    # and running `os` then `os.urandom(24)`
    # Be aware that if the key is too long, it could cause session errors.
    app.secret_key = "long_and_complex_key"

    # Do not use `run()` in a production setting.
    app.run(host="0.0.0.0", port=8000)
