import asyncio
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ── Configuración ──────────────────────────────────────────
TOKEN    = "8711857960:AAGDUQjeumriJnZNLK-Htbmc_lnOXnpv9rE"
CHAT_ID  = 743358609
MESSAGE  = "mandar listas"
INTERVAL = 10 * 60  # segundos
# ───────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)

bot_running = False
send_count  = 0
loop_task   = None  # referencia única al loop activo

async def send_loop(app: Application):
    global bot_running, send_count
    while bot_running:
        try:
            await app.bot.send_message(chat_id=CHAT_ID, text=MESSAGE)
            send_count += 1
            now = datetime.now().strftime("%H:%M:%S")
            logging.info(f"[{now}] Mensaje enviado #{send_count}")
        except Exception as e:
            logging.error(f"Error enviando mensaje: {e}")
        await asyncio.sleep(INTERVAL)

async def start_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global bot_running, loop_task

    if update.effective_chat.id != CHAT_ID:
        return

    if bot_running:
        await update.message.reply_text("⚠️ El bot ya está corriendo.")
        return

    # Cancelar cualquier loop residual antes de arrancar uno nuevo
    if loop_task and not loop_task.done():
        loop_task.cancel()
        try:
            await loop_task
        except asyncio.CancelledError:
            pass

    bot_running = True
    loop_task = asyncio.create_task(send_loop(ctx.application))

    await update.message.reply_text(
        "✅ Bot iniciado.\n"
        f"📨 Enviará *mandar listas* cada *10 minutos*.",
        parse_mode="Markdown"
    )

async def stop_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global bot_running, loop_task

    if update.effective_chat.id != CHAT_ID:
        return

    if not bot_running:
        await update.message.reply_text("⚠️ El bot ya estaba detenido.")
        return

    bot_running = False

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
    estado = "🟢 Activo" if bot_running else "🔴 Detenido"
    await update.message.reply_text(
        f"*Estado:* {estado}\n"
        f"*Mensajes enviados:* {send_count}\n"
        f"*Intervalo:* 10 minutos",
        parse_mode="Markdown"
    )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",  start_cmd))
    app.add_handler(CommandHandler("stop",   stop_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    logging.info("Bot escuchando...")
    app.run_polling()

if __name__ == "__main__":
    main()
