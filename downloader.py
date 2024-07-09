from telethon.sync import TelegramClient
from telethon.tl.types import PeerUser, PeerChat, MessageMediaPhoto, Message
import re, os, json, time, asyncio, aiofiles
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)

class Parsing:
    def __init__(self, input_emails):
        self.api_id = ...
        self.api_hash = "..."
        self.phone = "..."
        self.channel_id = ...

        self.message_info = {email: [] for email in input_emails}
        self.client = None
        self.entity = None
        self.input_emails = input_emails

        self.message_limit = int(input("Введите кол-во читаемых строк: "))

    async def async_init(self):
        self.client = TelegramClient(self.phone, self.api_id, self.api_hash)
        await self.client.start()
        self.entity = await self.client.get_entity("...")
        self.messages = await self.client.get_messages(self.entity, limit=self.message_limit, from_user=self.entity)

    async def create_server(self):
        print("Start")
        await self.get_email()
        self.dir_creater()
        await self.text_file()

    async def get_photos(self):
        download_tasks = []
        for media in self.messages[::-1]:
            if media.media:
                download_tasks.append(self.download_media(media))
        
        await asyncio.gather(*download_tasks)

    async def get_email(self):
        current_email = None
        idx = 0
        for mail in self.messages[::-1]:
            if "Email:" in mail.message:
                current_email = re.search(r'📧 Email: ([\w\.-]+@[\w\.-]+)', mail.message).group(1)
                if current_email in self.input_emails:
                    self.message_info[current_email] = []
            if current_email in self.input_emails:
                self.message_info[current_email].append(mail.message)
                if mail.media:
                    await self.download_media_with_retry(mail, current_email, idx)
                    idx += 1
                    print(f"Photo for {current_email} saved! photo_{idx}.jpg")
        return self.message_info

    async def download_media_with_retry(self, mail, email, idx, retries=5, delay=1):
        for attempt in range(retries):
            try:
                await mail.download_media(os.path.join(str(email), f"photo_{idx}.jpg"))
                break
            except Exception as e:
                if attempt < retries - 1:
                    logger.warning(f"Error: {e}. Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Failed to download media after {retries} attempts: {e}")
                    raise

    def dir_creater(self):
        # Создание папок 
        for email in self.message_info:
            if not os.path.exists(email):
                os.makedirs(email, exist_ok=True)
                print(f"Path created: {email}")

    async def text_file(self):
        save_tasks = []
        for email, messages in self.message_info.items():
            save_tasks.append(self.save_messages(email, messages))
        await asyncio.gather(*save_tasks)

    async def save_messages(self, email, messages):
        async with aiofiles.open(os.path.join(email, "info.txt"), "w", encoding='UTF-8') as file:
            for msg in messages:
                await file.write(msg + "\n")
        print(f"[+] Messages saved for {email}")

def read_emails_from_file(file_path):
    with open(file_path, 'r') as file:
        emails = [line.strip() for line in file.readlines()]
    return emails

async def main():
    emails = read_emails_from_file("mails.txt")
    start = Parsing(emails)
    await start.async_init()
    await start.create_server()

# Run the main function
asyncio.run(main())