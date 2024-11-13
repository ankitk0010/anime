from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import requests
from PIL import Image, ImageEnhance
from io import BytesIO
import logging

# Enable logging for better debug information
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Preprocess the image
def preprocess_image(image_path):
    img = Image.open(image_path)
    if img.mode != "RGB":
        img = img.convert("RGB")
    
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(2.0)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)

    img = img.resize((img.width // 2, img.height // 2), Image.LANCZOS)
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    buffer.seek(0)
    return buffer

# Search for anime episode
def search_anime_episode(image_buffer, min_similarity=0.75):
    url = "https://api.trace.moe/search"
    files = {"image": image_buffer}
    response = requests.post(url, files=files)
    
    if response.status_code == 200:
        data = response.json()
        if "result" in data and isinstance(data["result"], list) and data["result"]:
            for result in data["result"]:
                similarity = result.get("similarity", 0)
                if similarity >= min_similarity:
                    # Ensure 'anilist' is a dictionary, otherwise fallback to filename
                    if isinstance(result.get("anilist"), dict):
                        anime_title = result["anilist"].get("title", {}).get("native", result.get("filename", "Unknown Title"))
                    else:
                        anime_title = result.get("filename", "Unknown Title")

                    episode = result.get("episode", "Unknown")
                    similarity = round(similarity * 100, 2)
                    timestamp = result.get("from", 0)
                    timestamp_formatted = f"{int(timestamp // 60)}:{int(timestamp % 60)}"
                    
                    return f"Anime Title: {anime_title}\nEpisode: {episode}\nSimilarity: {similarity}%\nTimestamp: {timestamp_formatted}"
        return "No match found with high enough similarity."
    else:
        return f"Error: {response.status_code} {response.text}"

# Handle /start command
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Send me an anime screenshot, and I'll try to identify it!")
    logger.info("Bot started and /start command triggered.")

# Handle image messages
async def handle_image(update: Update, context: CallbackContext):
    # Show typing status while processing
    await update.message.reply_text("Processing the image... please wait.")
    await update.message.chat.send_action("typing")
    
    photo = update.message.photo[-1]
    photo_file = await photo.get_file()
    
    # Create a BytesIO object to store the downloaded image
    image_buffer = BytesIO()
    await photo_file.download_to_memory(out=image_buffer)
    image_buffer.seek(0)
    
    result_text = search_anime_episode(image_buffer)
    await update.message.reply_text(result_text)
    await update.message.chat.send_action("typing", action="cancel")  # End typing action

# Main function to start the bot
def main():
    application = Application.builder().token("7618127846:AAEAuY8l3aZx_7416Al_PMufcO_aP1zgmbo").build()

    # Log when the bot starts
    logger.info("Bot started.")
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    
    application.run_polling()

# Run the bot
if __name__ == "__main__":
    main()
