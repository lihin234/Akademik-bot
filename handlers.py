import html
import re
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from database import save_memory, get_memory, clear_memory
from bedrock_client import call_bedrock

async def send_chunked_message(update: Update, loading_msg, text: str):
    def format_heading(match):
        return f"🔹 <b>{match.group(1).upper()}</b>"
    text = re.sub(r'^#+\s+(.*)$', format_heading, text, flags=re.MULTILINE)
    text = re.sub(r'^\*\s+', '- ', text, flags=re.MULTILINE)
    text = html.escape(text)
    
    text = re.sub(r'```(.*?)```', r'<pre>\1</pre>', text, flags=re.DOTALL)
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)
    
    text = text.replace('—', ' - ').replace('–', ' - ')
    text = text.replace('**', '')
    
    limit = 3900
    chunks =[]
    while len(text) > limit:
        split_at = text.rfind('\n', 0, limit)
        if split_at == -1:
            split_at = limit
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()
        
    if text:
        chunks.append(text)
    
    for index, chunk in enumerate(chunks):
        try:
            if index == 0:
                await loading_msg.edit_text(chunk, parse_mode=ParseMode.HTML)
            else:
                await asyncio.sleep(0.5)
                await update.message.reply_text(chunk, parse_mode=ParseMode.HTML)
        except Exception as e:
            clean = html.unescape(chunk)
            clean = re.sub(r'<[^>]+>', '', clean)
            clean = clean.replace('**', '').replace('*', '')
            if index == 0:
                await loading_msg.edit_text(clean)
            else:
                await asyncio.sleep(0.5)
                await update.message.reply_text(clean)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        "👋 Halo! Saya adalah Bot Akademik berbasis *AWS Bedrock (Qwen 235B)*.\n\n"
        "📚 *Panduan Penggunaan:*\n"
        "• Chat langsung ke saya untuk mode Asisten Akademik Elegan.\n"
        "• `/detect <teks>` - Deteksi AI vs Manusia.\n"
        "• `/revisi <teks>` - Humanize Teks Akademik.\n"
        "• `/clear` - Menghapus riwayat memori.\n"
        "• `/start` - Menampilkan bantuan ini."
    )
    await update.message.reply_text(welcome_msg, parse_mode=ParseMode.MARKDOWN)

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    clear_memory(user_id)
    await update.message.reply_text("🧹 <b>Memori percakapan Anda telah dikosongkan!</b>", parse_mode=ParseMode.HTML)

async def detect_ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return
    user_text = " ".join(context.args)
    loading_msg = await update.message.reply_text("🔍 <i>Menganalisis Forensik Linguistik...</i>", parse_mode=ParseMode.HTML)
    
    system_prompt = "Anda Ahli Linguistik Forensik. Analisis teks ini apakah dari AI atau Manusia berdasarkan Perplexity dan Burstiness."
    messages =[{"role": "user", "content":[{"text": user_text}]}]
    response_text = call_bedrock(messages, system_prompt=system_prompt)
    await send_chunked_message(update, loading_msg, response_text)

async def revisi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return
    user_text = " ".join(context.args)
    loading_msg = await update.message.reply_text("✍️ <i>Menulis ulang dengan bahasa Akademik Elegan...</i>", parse_mode=ParseMode.HTML)
    
    system_prompt = (
        "Tugas Anda memparafrase teks input menjadi tulisan akademik yang 100% PROFESIONAL, MASUK AKAL, ENAK DIBACA, namun memiliki ritme bahasa manusia yang natural. "
        "ATURAN MUTLAK:\n"
        "1. BAHASA BAKU & LOGIS: Jangan gunakan bahasa gaul.\n"
        "2. BUANG KOSAKATA ROBOT: Ganti kata klise AI (krusial, signifikan, komprehensif) dengan padanan organik (nyata, mendasar).\n"
        "3. BURSTINESS ELEGAN: Gunakan kalimat pendek di antara penjelasan panjang.\n"
        "4. DILARANG MERANGKUM: Jangan pernah membuat paragraf penutup atau kesimpulan. Akhiri teks tepat setelah poin terakhir."
    )
    messages =[{"role": "user", "content":[{"text": user_text}]}]
    response_text = call_bedrock(messages, system_prompt=system_prompt)
    await send_chunked_message(update, loading_msg, response_text)

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_text = update.message.text
    loading_msg = await update.message.reply_text("⏳ <i>Memproses jawaban...</i>", parse_mode=ParseMode.HTML)
    
    messages = get_memory(user_id, limit=8)
    messages.append({"role": "user", "content":[{"text": user_text}]})
    
    # 🔥 PROMPT FINAL: Membunuh Paragraf Kesimpulan 🔥
    system_prompt = (
        "Anda adalah Asisten Akademik profesional sekelas Dosen. Jawablah dengan akurat, mendalam, dan ENAK DIBACA. "
        "Untuk meminimalisir deteksi AI (Turnitin/ZeroGPT), Anda WAJIB mematuhi aturan ini:\n"
        "1. LANGSUNG PADA INTI: Dilarang menggunakan basa-basi pembuka khas AI. Kalimat pertama harus langsung berupa argumen.\n"
        "2. KOSAKATA ORGANIK: Jangan gunakan kata 'krusial', 'signifikan', 'komprehensif', 'esensial'. Gunakan padanan kata akademik yang lebih membumi.\n"
        "3. ASIMETRI FORMAT: Jika materi butuh poin-poin (1,2,3), JANGAN membuat panjang tiap poin seragam. Buat ada poin yang sangat detail (3-4 kalimat) dan ada poin yang sangat singkat (1 kalimat).\n"
        "4. ANTI PARAGRAF PENUTUP: DILARANG KERAS membuat paragraf kesimpulan di akhir tulisan. Jangan pernah menggunakan kata 'Kesimpulannya', 'Intinya', atau 'Singkatnya'. Berhentilah menjelaskan tepat setelah poin materi terakhir selesai dibahas!"
    )
    
    response_text = call_bedrock(messages, system_prompt=system_prompt)
    
    if not response_text.startswith("⚠️"):
        save_memory(user_id, "user", user_text)
        save_memory(user_id, "assistant", response_text)
    
    await send_chunked_message(update, loading_msg, response_text)
