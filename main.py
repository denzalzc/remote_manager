from flask import Flask, render_template, request


app = Flask(__name__)

@app.route("/")
def index():
    return render_template('cli.html')

@app.route('/api/comm')
def comm():
    command = request.args.get('text')
    print(command)

app.run(host='77.222.63.95', port=5000, debug=True)