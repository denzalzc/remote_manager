from flask import Flask, render_template, request
import subprocess, os


app = Flask(__name__)

@app.route("/")
def index():
    return render_template('cli.html', start_path=os.getcwd())

@app.route('/api/comm')
def comm():
    command = request.args.get('text')
    
    try:
        result = subprocess.run(
            command.split(' '), 
            capture_output=True, 
            text=True, 
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            return result.stdout if result.stdout else "Команда выполнена (нет вывода)"
        else:
            return f"Ошибка (код: {result.returncode}): {result.stderr}"
            
    except FileNotFoundError as e:
        cmd_name = command.split(' ')[0] if command else "Unknown"
        return f"Ошибка: команда '{cmd_name}' не найдена"
    except Exception as e:
        return f"Ошибка выполнения: {str(e)}"

@app.route('/api/chdir')
def chdir():
    dir_path = request.args.get('text')

    return os.listdir(dir_path)


app.run(host='77.222.63.95', port=5000, debug=True)