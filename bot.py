import asyncio
import logging
import os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ── Configuración ──────────────────────────────────────────
TOKEN    = "8711857960:AAGDUQjeumriJnZNLK-Htbmc_lnOXnpv9rE"
CHAT_ID  = 743358609
MESSAGE  = "mandar listas"
INTERVAL = 10 * 60  # segundos
STATE_FILE = "/tmp/bot_state.txt"
# ───────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)

send_count = 0
loop_task  = None

def save_state(running: bool):
    with open(STATE_FILE, "w") as f:
        f.write("1" if running else "0")

def load_state() -> bool:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return f.read().strip() == "1"
    return False

def is_running() -> bool:
    return load_state()

async def send_loop(app: Application):
    global send_count
    while is_running():
        try:
            await app.bot.send_message(chat_id=CHAT_ID, text=MESSAGE)
            send_count += 1
            logging.info(f"Mensaje enviado #{send_count}")
        except Exception as e:
            logging.error(f"Error: {e}")
        # Esperar en trozos para poder frenar rápido
        for _ in range(INTERVAL):
            if not is_running():
                return
            await asyncio.sleep(1)

async def start_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global loop_task

    if update.effective_chat.id != CHAT_ID:
        return

    if is_running():
        await update.message.reply_text("⚠️ El bot ya está corriendo.")
        return

    # Cancelar loop residual si existe
    if loop_task and not loop_task.done():
        loop_task.cancel()
        try:
            await loop_task
        except asyncio.CancelledError:
            pass

    save_state(True)
    loop_task = asyncio.create_task(send_loop(ctx.application))

    await update.message.reply_text(
        "✅ Bot iniciado.\n"
        "📨 Enviará *mandar listas* cada *10 minutos*.",
        parse_mode="Markdown"
    )

async def stop_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global loop_task

    if update.effective_chat.id != CHAT_ID:
        return

    if not is_running():
        await update.message.reply_text("⚠️ El bot ya estaba detenido.")
        return

    save_state(False)

    if loop_task and not loop_task.done():
        loop_task.cancel()
        try:
            await loop_task
        except asyncio.CancelledError:
            pass

    await update.message.reply_text(
        f"🛑 Bot detenido.\n📊 Mensajes enviados: *{send_count}*",
        parse_mode="Markdown"
    )

async def status_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != CHAT_ID:
        return
    estado = "🟢 Activo" if is_running() else "🔴 Detenido"
    await update.message.reply_text(
        f"*Estado:* {estado}\n"
        f"*Mensajes enviados:* {send_count}\n"
        f"*Intervalo:* 10 minutos",
        parse_mode="Markdown"
    )

async def post_init(app: Application):
    """Al arrancar, retomar el loop si estaba activo antes del reinicio."""
    global loop_task
    if is_running():
        logging.info("Retomando loop activo tras reinicio...")
        loop_task = asyncio.create_task(send_loop(app))

def main():
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start",  start_cmd))
    app.add_handler(CommandHandler("stop",   stop_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    logging.info("Bot escuchando...")
    app.run_polling()

if __name__ == "__main__":
    main()
