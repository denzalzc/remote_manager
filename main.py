from flask import Flask
from flask import render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template('cli.html')

@app.route('/api/ls')
def ls():
    return 0

app.run(host='77.222.63.95', port=5000, debug=True)