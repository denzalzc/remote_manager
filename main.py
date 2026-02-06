from flask import Flask
from flask import render_template

app = Flask(__name__)

@app.route("/")
def hello_world():
    return render_template('cli.html')


app.run(host='77.222.63.95', port=5000, debug=True)