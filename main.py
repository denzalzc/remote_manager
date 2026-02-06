from flask import Flask
from flask import render_template

app = Flask(__name__)

@app.route("/")
def hello_world():
    return render_template('cli.html')


app.run(debug=True)