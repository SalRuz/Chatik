import telebot
import requests
import time

# --- НАСТРОЙКИ ---
TG_TOKEN = '8512207770:AAEKLtYEph7gleybGhF2lc7Gwq82Kj1yedM'
ADMIN_ID = 1170970828

# Настройки PythonAnywhere
PA_USERNAME = 'SalRuzO'
PA_TOKEN = '69157472762730e677177924f2fd940a21ea7f0c'
PA_DOMAIN = 'www.pythonanywhere.com'
SCRIPT_FILE = 'vk_bot.py' # Имя файла на PythonAnywhere

bot = telebot.TeleBot(TG_TOKEN)

# Базовый заголовок для авторизации
auth_headers = {'Authorization': f'Token {PA_TOKEN}'}

def start_script_on_pa():
    base_url = f'https://{PA_DOMAIN}/api/v0/user/{PA_USERNAME}/consoles/'
    
    # 1. Сначала проверяем, есть ли уже запущенные консоли, чтобы не плодить их
    # (На бесплатном тарифе лимит - 2 консоли)
    try:
        resp = requests.get(base_url, headers=auth_headers)
        consoles = resp.json()
    except Exception as e:
        return f"Ошибка соединения с API: {e}"

    console_id = None
    
    # Ищем любую живую bash-консоль
    for console in consoles:
        if console['executable'] == 'bash':
            console_id = console['id']
            break
    
    # 2. Если консоли нет, создаем новую
    if not console_id:
        try:
            resp = requests.post(base_url, headers=auth_headers, json={'executable': 'bash'})
            if resp.status_code in [200, 201]:
                data = resp.json()
                console_id = data['id']
                # Ждем пару секунд, пока консоль загрузится ("booting")
                time.sleep(2) 
            else:
                return f"Не удалось создать консоль: {resp.text}"
        except Exception as e:
             return f"Ошибка создания консоли: {e}"

    # 3. Отправляем команду запуска в эту консоль
    # Мы используем nohup, чтобы процесс жил чуть дольше, но на Free тарифе это не гарантирует вечную работу
    command = f"python3 {SCRIPT_FILE}\n" 
    
    send_url = f'{base_url}{console_id}/send_input/'
    try:
        resp = requests.post(send_url, headers=auth_headers, json={'input': command})
        if resp.status_code == 200:
            return f"✅ Команда отправлена в консоль #{console_id}!"
        else:
            return f"Ошибка отправки команды: {resp.text}"
    except Exception as e:
        return f"Ошибка запроса: {e}"

# --- Обработчики бота ---

@bot.message_handler(commands=['run'])
def run_remote(message):
    if message.from_user.id != ADMIN_ID: return
    
    bot.reply_to(message, "⏳ Подключаюсь к PythonAnywhere...")
    result = start_script_on_pa()
    bot.reply_to(message, result)

@bot.message_handler(commands=['kill'])
def kill_consoles(message):
    if message.from_user.id != ADMIN_ID: return
    
    # Эта функция убивает ВСЕ консоли, чтобы остановить бота
    base_url = f'https://{PA_DOMAIN}/api/v0/user/{PA_USERNAME}/consoles/'
    try:
        resp = requests.get(base_url, headers=auth_headers)
        consoles = resp.json()
        count = 0
        for console in consoles:
            requests.delete(f"{base_url}{console['id']}/", headers=auth_headers)
            count += 1
        bot.reply_to(message, f"💀 Убито консолей: {count}. Скрипты должны остановиться.")
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

if __name__ == '__main__':
    print("Бот-контроллер запущен...")
    bot.infinity_polling()
