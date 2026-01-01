import telebot
import requests
import time

# --- ВАШИ НАСТРОЙКИ ---
TG_TOKEN = '8512207770:AAEKLtYEph7gleybGhF2lc7Gwq82Kj1yedM'
ADMIN_ID = 1170970828
PA_USERNAME = 'SalRuzO'
PA_TOKEN = '69157472762730e677177924f2fd940a21ea7f0c'
SCRIPT_FILE = 'vk_bot.py' 

# --- НАСТРОЙКИ ПРОКСИ УБРАНЫ (Т.к. вы запускаете с ПК) ---

bot = telebot.TeleBot(TG_TOKEN)

# Заголовки для API PythonAnywhere
auth_headers = {'Authorization': f'Token {PA_TOKEN}'}
PA_DOMAIN = 'www.pythonanywhere.com'
base_url = f'https://{PA_DOMAIN}/api/v0/user/{PA_USERNAME}/consoles/'

def start_script_on_pa():
    # 1. Проверяем запущенные консоли
    try:
        resp = requests.get(base_url, headers=auth_headers, timeout=10)
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
                time.sleep(3) # Ждем загрузку консоли
            else:
                return f"Не удалось создать консоль: {resp.text}"
        except Exception as e:
             return f"Ошибка создания консоли: {e}"

    # 3. Отправляем команду запуска
    # Используем nohup, чтобы попытаться отвязать процесс (но на Free тарифе гарантий нет)
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
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "Нет доступа.")
        return
    
    bot.reply_to(message, "⏳ Подключаюсь к PythonAnywhere...")
    result = start_script_on_pa()
    bot.reply_to(message, result)

@bot.message_handler(commands=['kill'])
def kill_consoles(message):
    if message.from_user.id != ADMIN_ID: return
    
    try:
        resp = requests.get(base_url, headers=auth_headers)
        consoles = resp.json()
        count = 0
        for console in consoles:
            cid = console['id']
            requests.delete(f"{base_url}{cid}/", headers=auth_headers)
            count += 1
        bot.reply_to(message, f"💀 Убито консолей: {count}. Скрипты должны остановиться.")
    except Exception as e:
        bot.reply_to(message, f"Ошибка при удалении: {e}")

if __name__ == '__main__':
    print("Бот запущен на вашем компьютере.")
    bot.infinity_polling()
