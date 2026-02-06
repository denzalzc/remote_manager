from flask import Flask, render_template, request, jsonify
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
    if not command:
        return "Ошибка: пустая команда"
    
    if command.startswith('cd '):
        try:
            new_dir = command[3:].strip()
            current_dir = os.getcwd()
            

            if new_dir == "~":
                new_dir = os.path.expanduser("~")
            elif new_dir.startswith("~/"):
                new_dir = os.path.expanduser(new_dir)
            

            if os.path.isabs(new_dir):
                target_dir = os.path.abspath(new_dir)
            else:
                target_dir = os.path.abspath(os.path.join(current_dir, new_dir))
            

            target_dir = os.path.normpath(target_dir)

            if os.path.isdir(target_dir):
                os.chdir(target_dir)
                return f"Каталог изменен на: {os.getcwd()}"
            else:
                return f"Ошибка: каталог '{target_dir}' не найден"
                
        except Exception as e:
            return f"Ошибка выполнения cd: {str(e)}"
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True, 
            text=True, 
            encoding='utf-8',
            cwd=os.getcwd()
        )
        
        if result.returncode == 0:
            return result.stdout if result.stdout else "Команда выполнена (нет вывода)"
        else:
            return f"Ошибка (код: {result.returncode}): {result.stderr}"
            
    except Exception as e:
        return f"Ошибка выполнения: {str(e)}"

@app.route('/api/chdir')
def chdir():
    path = request.args.get('text')
    if not path:
        path = os.getcwd()
    
    try:
        if path == "~":
            path = os.path.expanduser("~")
        elif path.startswith("~/"):
            path = os.path.expanduser(path)
        
        if not os.path.isabs(path):
            current_dir = os.getcwd()
            path = os.path.abspath(os.path.join(current_dir, path))
        
        path = os.path.normpath(path)
        
        if os.path.isdir(path):
            os.chdir(path)
            files = os.listdir(path)
            
            dirs = [f for f in files if os.path.isdir(os.path.join(path, f))]
            files_list = [f for f in files if os.path.isfile(os.path.join(path, f))]
            
            sorted_files = sorted(dirs) + sorted(files_list)
            
            return jsonify({
                "current_path": os.getcwd(),
                "files": sorted_files
            })
        else:
            return jsonify({
                "error": f"Каталог '{path}' не найден",
                "current_path": os.getcwd(),
                "files": []
            })
            
    except Exception as e:
        return jsonify({
            "error": str(e),
            "current_path": os.getcwd(),
            "files": []
        })

@app.route('/api/operonfiles')
def operonfiles():
    filefullpath = request.args.get('filefullpath')
    operation = request.args.get('oper')
    newname = request.args.get('newname')
    
    try:
        if not os.path.isabs(filefullpath):
            current_dir = os.getcwd()
            filefullpath = os.path.abspath(os.path.join(current_dir, filefullpath))
        
        if operation == 'delete':
            if os.path.exists(filefullpath):
                if os.path.isdir(filefullpath):
                    os.rmdir(filefullpath)
                else:
                    os.remove(filefullpath)
                return f"Удалено: {filefullpath}"
            else:
                return f"Ошибка: файл или папка не существует"
                
        elif operation == 'rename':
            if newname:
                dir_path = os.path.dirname(filefullpath)
                new_fullpath = os.path.abspath(os.path.join(dir_path, newname))
                
                if os.path.exists(filefullpath):
                    os.rename(filefullpath, new_fullpath)
                    return f"Переименовано: {filefullpath} -> {new_fullpath}"
                else:
                    return f"Ошибка: файл или папка не существует"
            else:
                return "Ошибка: не указано новое имя"
                
        elif operation == 'mkdir':
            if os.path.exists(filefullpath):
                return f"Ошибка: папка уже существует"
            os.makedirs(filefullpath, exist_ok=True)
            return f"Создана папка: {filefullpath}"
            
        else:
            return f"Ошибка: неизвестная операция '{operation}'"
            
    except Exception as e:
        return f"Ошибка выполнения операции: {str(e)}"
    
@app.route('/api/editfile/open')
def editfile_open():
    filefullpath = request.args.get('filefullpath')
    if not filefullpath:
        return "Ошибка: не указан путь к файлу"
    
    try:
        # Получаем абсолютный путь
        if not os.path.isabs(filefullpath):
            current_dir = os.getcwd()
            filefullpath = os.path.abspath(os.path.join(current_dir, filefullpath))
        
        # Проверяем существует ли файл
        if not os.path.exists(filefullpath):
            return f"Ошибка: файл '{filefullpath}' не существует"
        
        # Проверяем что это файл, а не папка
        if os.path.isdir(filefullpath):
            return f"Ошибка: '{filefullpath}' это папка, а не файл"
        
        # Читаем содержимое файла
        with open(filefullpath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content
        
    except UnicodeDecodeError:
        return "Ошибка: файл не является текстовым (бинарный файл)"
    except Exception as e:
        return f"Ошибка открытия файла: {str(e)}"

@app.route('/api/editfile/save')
def editfile_save():
    filefullpath = request.args.get('filefullpath')
    content = request.args.get('content')
    
    if not filefullpath or content is None:
        return "Ошибка: не указаны необходимые параметры"
    
    try:
        # Получаем абсолютный путь
        if not os.path.isabs(filefullpath):
            current_dir = os.getcwd()
            filefullpath = os.path.abspath(os.path.join(current_dir, filefullpath))
        
        # Проверяем существует ли файл (если нет - создаем)
        if os.path.exists(filefullpath) and os.path.isdir(filefullpath):
            return f"Ошибка: '{filefullpath}' это папка, а не файл"
        
        # Сохраняем содержимое файла
        with open(filefullpath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"Файл сохранен: {filefullpath}"
        
    except Exception as e:
        return f"Ошибка сохранения файла: {str(e)}"

app.run(host='77.222.63.95', port=5000, debug=True)