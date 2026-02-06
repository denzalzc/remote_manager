from flask import Flask, render_template, request, jsonify
from termcolor import colored
from functools import wraps
from telebot import TeleBot
import subprocess, os
import random
import string


def warn(text: str): print(colored(text, 'yellow'))
def succ(text: str): print(colored(text, 'green'))
def fatl(text: str): print(colored(text, 'red'))
def info(text: str): print(colored(text, 'blue'))

app = Flask(__name__)

ALLOWED_IPS = {
    '213.156.210.18',
}

def gen_api_key():
    fatl('CALLED')
    with open('tg_data', 'r') as tg_key_file:
        all_symbols = string.ascii_letters + string.digits
        random_key = "".join(random.choices(all_symbols, k=10))
        info(random_key)

        bot_apikey, chat_id = tg_key_file.read().strip().split('/')
        bot = TeleBot(bot_apikey)
        bot.send_message(chat_id=chat_id, text=random_key)

        return random_key
    
allowed_api_key = gen_api_key()
print(allowed_api_key)



def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')

        print(api_key, allowed_api_key)
        
        if not(api_key) or not(api_key == allowed_api_key):
            "Permission denied: Your IP is not whitelisted", 403
        if api_key == allowed_api_key:
            return f(*args, **kwargs)
    return decorated_function



def check_ip(ip):
    def ip_to_int(ip):
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return None
                
            result = 0
            for i, part in enumerate(parts):
                if not part.isdigit():
                    return None
                    
                num = int(part)
                if num < 0 or num > 255:
                    return None
                    
                shift = 24 - (i * 8)
                result += (num << shift)
            return result
        except (ValueError, IndexError):
            return None
    
    def network_address(ip_cidr):
        try:
            ip, mask_bits = ip_cidr.split('/')
            mask_bits = int(mask_bits)
            if mask_bits < 0 or mask_bits > 32:
                return None, None
                
            ip_int = ip_to_int(ip)
            if ip_int is None:
                return None, None
                
            mask = (0xFFFFFFFF << (32 - mask_bits)) & 0xFFFFFFFF
            return ip_int & mask, mask
        except (ValueError, IndexError):
            return None, None
    
    if not ip or not isinstance(ip, str):
        return False
    
    client_ip_int = ip_to_int(ip)
    if client_ip_int is None:
        return False
    
    for allowed in ALLOWED_IPS:
        if '/' in allowed:
            net_addr, mask = network_address(allowed)
            if net_addr is None or mask is None:
                continue
                
            if (client_ip_int & mask) == net_addr:
                return True
        else:
            if ip == allowed:
                return True
    
    return False

def ip_whitelist(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr
        
        if request.headers.get('X-Forwarded-For'):
            client_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            client_ip = request.headers.get('X-Real-IP')
        
        info(f"Попытка доступа от IP: {client_ip}")
        
        if not check_ip(client_ip):
            fatl(f"Отказано в доступе для IP: {client_ip}")
            if request.path.startswith('/api/'):
                return "Permission denied: Your IP is not whitelisted", 403
            else:
                return render_template('access_denied.html', ip=client_ip), 403
        
        succ(f"Разрешен доступ для IP: {client_ip}")
        return f(*args, **kwargs)
    
    return decorated_function

@app.route("/")
@ip_whitelist
def index():
    return render_template('cli.html', start_path=os.getcwd())

@app.route('/api/comm')
@ip_whitelist
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
@ip_whitelist
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
            
            files_with_type = []
            for f in files:
                full_path = os.path.join(path, f)
                if os.path.isdir(full_path):
                    files_with_type.append(f + '/') 
                else:
                    files_with_type.append(f)
            
            dirs = [f for f in files_with_type if f.endswith('/')]
            files_list = [f for f in files_with_type if not f.endswith('/')]
            
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
@ip_whitelist
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
@ip_whitelist
def editfile_open():
    filefullpath = request.args.get('filefullpath')
    if not filefullpath:
        return "Ошибка: не указан путь к файлу"
    
    try:
        if not os.path.isabs(filefullpath):
            current_dir = os.getcwd()
            filefullpath = os.path.abspath(os.path.join(current_dir, filefullpath))
        
        if not os.path.exists(filefullpath):
            return f"Ошибка: файл '{filefullpath}' не существует"
        
        if os.path.isdir(filefullpath):
            return f"Ошибка: '{filefullpath}' это папка, а не файл"
        
        with open(filefullpath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content
        
    except UnicodeDecodeError:
        return "Ошибка: файл не является текстовым (бинарный файл)"
    except Exception as e:
        return f"Ошибка открытия файла: {str(e)}"

@app.route('/api/editfile/save')
@ip_whitelist
def editfile_save():
    filefullpath = request.args.get('filefullpath')
    content = request.args.get('content')
    
    if not filefullpath or content is None:
        return "Ошибка: не указаны необходимые параметры"
    
    try:
        if not os.path.isabs(filefullpath):
            current_dir = os.getcwd()
            filefullpath = os.path.abspath(os.path.join(current_dir, filefullpath))
        
        if os.path.exists(filefullpath) and os.path.isdir(filefullpath):
            return f"Ошибка: '{filefullpath}' это папка, а не файл"
        
        with open(filefullpath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"Файл сохранен: {filefullpath}"
        
    except Exception as e:
        return f"Ошибка сохранения файла: {str(e)}"

@app.errorhandler(403)
def forbidden(e):
    return render_template('access_denied.html', ip=request.remote_addr), 403

if __name__ == '__main__':
    info(f"Allowed IPs: {ALLOWED_IPS}")
    app.run(host='77.222.63.95', port=5000, debug=True)