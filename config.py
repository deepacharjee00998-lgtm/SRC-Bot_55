import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
API_ID = int(os.getenv("API_ID", "123456"))
API_HASH = os.getenv("API_HASH", "YOUR_API_HASH")
ADMIN_ID = int(os.getenv("ADMIN_ID", "YOUR_ADMIN_ID"))
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://...")
UPI_ID = os.getenv("UPI_ID", "yourname@upi")
