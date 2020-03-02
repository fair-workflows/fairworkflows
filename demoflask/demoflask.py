# -*- coding: utf-8 -*-"""Documentation about the DemoFlask module."""


from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return "{'message': 'Hello World!'}"
