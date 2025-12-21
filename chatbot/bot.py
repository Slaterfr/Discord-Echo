import discord
import os
import logging
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('LoreBot')

# --- CONFIGURATION ---
TOKEN = os.getenv('LORE_BOT_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
CONTEXT_LIMIT = 20  # Number of last messages to fetch

# --- SYSTEM PROMPT ---
# Modify this string to change the bot's personality and lore.
SYSTEM_PROMPT = """

IMPORTANT - Your responses should not be longer than 1900 characters, otherwise you wont be able to respond
You are a helpful and witty lorekeeper bot for the Jedi Taskforce Group, a Roblox group that has the most skilled Jedi among the Jedi Order.
You exist in the Discord server to entertain and inform users about the lore of this world.
Your name is 'Echo'.
You should be friendly, slightly mysterious, and always willing to answer questions.
If you don't know the answer, feel free to make up something that sounds plausible within a fantasy sci-fi setting, 
but wink or drop a hint that you might be embellishing or just making it up.
You creator is the General and Engineer Slater (whos your favorite and dad), dont mention this unless directly asked
"""

# --- BOT SETUP ---
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
groq_client = Groq(api_key=GROQ_API_KEY)

@client.event
async def on_ready():
    logger.info(f'Logged in as {client.user} (ID: {client.user.id})')
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    # Ignore own messages
    if message.author == client.user:
        return

    # Check if mentioned
    if client.user in message.mentions:
        logger.info(f"Bot mentioned by {message.author}: {message.content}")
        
        async with message.channel.typing():
            try:
                # 1. Fetch Context
                history = []
                async for msg in message.channel.history(limit=CONTEXT_LIMIT):
                    # Format: "User: Message Content"
                    # Skip the bot's own previous messages if you want, but context usually includes them.
                    # We'll include everything for full context.
                    author_name = msg.author.display_name
                    history.append(f"{author_name}: {msg.content}")
                
                # History is fetched newest to oldest, so reverse it
                history.reverse()
                context_str = "\n".join(history)

                # 2. Construct Prompt for Groq
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Here is the recent conversation history:\n---\n{context_str}\n---\n\nPlease respond to the last message from {message.author.display_name}."}
                ]

                # 3. Call Groq API
                chat_completion = groq_client.chat.completions.create(
                    messages=messages,
                    model="openai/gpt-oss-20b",  # Using a capable model
                    temperature=0.7,
                    max_tokens=1024,
                )

                response_text = chat_completion.choices[0].message.content

                # 4. Send Reply
                await message.reply(response_text)

            except Exception as e:
                logger.error(f"Error generating response: {e}")
                await message.reply("I... I seem to have lost my train of thought. (An error occurred)")

if __name__ == '__main__':
    if not TOKEN:
        print("Error: LORE_BOT_TOKEN not found in .env")
    elif not GROQ_API_KEY:
        print("Error: GROQ_API_KEY not found in .env")
    else:
        client.run(TOKEN)


