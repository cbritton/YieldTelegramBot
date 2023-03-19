from dotenv import load_dotenv
from dataContent import DataContent
import os

load_dotenv()
fred_api_key = os.getenv('FRED_API_KEY')
telegram_bot_key = os.getenv('TELEGRAM_BOT_KEY')


# store the content in the DataContent class.
data_content = DataContent()
