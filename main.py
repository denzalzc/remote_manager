from flask import Flask, render_template, request
import subprocess


app = Flask(__name__)

@app.route("/")
def index():
    return render_template('cli.html')

@app.route('/api/comm')
def comm():
    command = request.args.get('text')
    
    result = subprocess.run(command.split(' '), capture_output=True, text=True, encoding='utf-8')

    if result.returncode == 0:
        return result.stdout
    else:
        return result.stderr

    print("Статус:", "Успешно" if result.returncode == 0 else "Ошибка")
    print("Код возврата:", result.returncode)
    print("Вывод:\n", result.stdout)
    print("Ошибки:\n", result.stderr)

app.run(host='77.222.63.95', port=5000, debug=True)