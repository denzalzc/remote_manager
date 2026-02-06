from flask import Flask, render_template, request
from termcolor import colored
import subprocess, os

def warn(text: str): print(colored(text, 'yellow'))
def succ(text: str): print(colored(text, 'green'))
def fatl(text: str): print(colored(text, 'red'))
def info(text: str): print(colored(text, 'blue'))


app = Flask(__name__)

@app.route("/")
def index():
    return render_template('cli.html', start_path=os.getcwd())

@app.route('/api/comm')
def comm():
    command = request.args.get('text')

    if command.startswith('cd '):
        try:
            new_dir = command[3:].strip()
            if not os.path.isabs(new_dir):
                current_dir = os.getcwd()
                new_dir = os.path.join(current_dir, new_dir)
            
            if os.path.isdir(new_dir):
                os.chdir(new_dir)
                return f"Каталог изменен на: {new_dir}"
            else:
                return f"Ошибка: каталог '{new_dir}' не найден"
        except Exception as e:
            return f"Ошибка выполнения cd: {str(e)}"
    
    try:
        result = subprocess.run(
            command,
            shell=True,
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

@app.route('/api/operonfiles')
def oper_on_files():
    file_full_path = request.args.get('filefullpath')
    operation = request.args.get('oper')

    info(file_full_path)
    info(operation)

    return 'kek'


app.run(host='77.222.63.95', port=5000, debug=True)