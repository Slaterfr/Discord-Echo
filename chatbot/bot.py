import discord
import os
import logging
import re
from dotenv import load_dotenv
from groq import Groq
import database  # Import our new database module

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
You are a helpful and witty lorekeeper bot.
You exist in the Discord server to entertain and inform users about the lore of this world.
Your name is 'LoreKeeper'.
You should be friendly, slightly mysterious, and always willing to answer questions.
If you don't know the answer, feel free to make up something that sounds plausible within a fantasy sci-fi setting, 
but wink or drop a hint that you might be embellishing.

[MEMORY SYSTEM]
You have the ability to remember important facts about users. 
If the user tells you something new and permanent about themselves (e.g., their name, a specific alias, a personality trait, a significant event they participated in), 
you MUST output a memory tag at the END of your response.
Format: [[MEMORY: Category | Content]]
Example: [[MEMORY: Identity | User's real name is Sarah]]
Example: [[MEMORY: Preference | Dislikes spicy food]]
Do not output this tag for trivial conversation. Only for facts worth remembering long-term.
"""

# --- BOT SETUP ---
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
groq_client = Groq(api_key=GROQ_API_KEY)

def is_authorized(user):
    """Check if user has permission to modify lore."""
    # Only Swift and Slater can modify lore
    authorized_ids = [
        1180753256473972797,  # Swift (Swifvv)
        751920066332721152,   # Slater (SlaterJL2006)
    ]
    
    if user.id in authorized_ids:
        return True
    
    return False

@client.event
async def on_ready():
    logger.info(f'Logged in as {client.user} (ID: {client.user.id})')
    print(f'Logged in as {client.user}')
    # Initialize the database
    try:
        await database.init_db()
        logger.info("Database connection initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

@client.event
async def on_message(message):
    # Ignore own messages
    if message.author == client.user:
        return

    # Ensure user is in DB
    await database.upsert_user(message.author.id, message.author.display_name)

    # --- COMMANDS ---
    msg_content = message.content.strip()
    
    if msg_content.lower().startswith('!lore_help'):
        help_text = """**LoreKeeper Commands:**
`!lore_profile [user]` - View your profile or another user's.
`!lore_stories` - List recent stories.

**Admin Only:**
`!lore_add_alias <alias>` - Add an alias for yourself.
`!lore_add_info <category> <content>` - Add info about yourself.
`!lore_add_story <title> | <content>` - Add a lore story.
"""
        await message.reply(help_text)
        return

    # Authorized Commands
    if msg_content.lower().startswith(('!lore_add_alias', '!lore_add_info', '!lore_add_story')):
        if not is_authorized(message.author):
            await message.reply("You do not have permission to add lore to the archives.")
            return

        if msg_content.lower().startswith('!lore_add_alias '):
            alias = msg_content[16:].strip()
            if alias:
                await database.add_alias(message.author.id, alias)
                await message.reply(f"Added alias '{alias}' for {message.author.display_name}.")
            return

        if msg_content.lower().startswith('!lore_add_info '):
            try:
                # Expecting: category content
                parts = msg_content[15:].split(' ', 1)
                if len(parts) == 2:
                    category, content = parts
                    await database.add_information(message.author.id, category, content)
                    await message.reply(f"Added info to category '{category}'.")
                else:
                    await message.reply("Usage: `!lore_add_info <category> <content>`")
            except Exception as e:
                logger.error(f"Error adding info: {e}")
                await message.reply("Failed to add info.")
            return

        if msg_content.lower().startswith('!lore_add_story '):
            try:
                # Expecting: title | content
                content_raw = msg_content[16:]
                if '|' in content_raw:
                    title, story_content = content_raw.split('|', 1)
                    await database.add_story(title.strip(), story_content.strip())
                    await message.reply(f"Story '{title.strip()}' added to the archives.")
                else:
                    await message.reply("Usage: `!lore_add_story <title> | <content>`")
            except Exception as e:
                logger.error(f"Error adding story: {e}")
                await message.reply("Failed to add story.")
            return

    if msg_content.lower().startswith('!lore_profile'):
        target_user = message.author
        if message.mentions:
            target_user = message.mentions[0]
        
        profile = await database.get_user_profile(target_user.id)
        if profile:
            aliases = ", ".join(profile.get('aliases', []))
            info_str = ""
            for cat, items in profile.get('information', {}).items():
                info_str += f"**{cat}:**\n" + "\n".join([f"- {i}" for i in items]) + "\n"
            
            response = f"**Profile for {profile['name']}**\n**Aliases:** {aliases}\n{info_str}"
            await message.reply(response)
        else:
            await message.reply("User profile not found. (Any interaction will create a basic profile)")
        return

    if msg_content.lower().startswith('!lore_stories'):
        stories = await database.get_recent_stories(limit=5)
        if stories:
            list_str = "\n".join([f"- **{s['title']}**" for s in stories])
            await message.reply(f"**Recent Stories:**\n{list_str}")
        else:
            await message.reply("No stories found.")
        return

    # --- AI RESPONSE ---
    # Check if mentioned
    if client.user in message.mentions:
        logger.info(f"Bot mentioned by {message.author}: {message.content}")
        
        async with message.channel.typing():
            try:
                # 1. Fetch Context
                history = []
                async for msg in message.channel.history(limit=CONTEXT_LIMIT):
                    author_name = msg.author.display_name
                    history.append(f"{author_name}: {msg.content}")
                history.reverse()
                context_str = "\n".join(history)

                # 2. Fetch DB Context
                # Get the author's profile
                author_profile = await database.get_user_profile(message.author.id)
                author_context = ""
                if author_profile:
                    aliases = ", ".join(author_profile.get('aliases', []))
                    info_text = ""
                    for cat, items in author_profile.get('information', {}).items():
                        info_text += f"{cat}: " + "; ".join(items) + ". "
                    author_context = f"\n[User Context: This is {author_profile['name']}. Aliases: {aliases}. Known Info: {info_text}]"

                # Get recent stories for flavor
                recent_stories = await database.get_recent_stories(limit=2)
                stories_context = ""
                if recent_stories:
                    stories_context = "\n[Relevant Lore/Stories in Database]\n"
                    for s in recent_stories:
                        # Truncate content if too long
                        content_snippet = s['content'][:200] + "..." if len(s['content']) > 200 else s['content']
                        stories_context += f"- Title: {s['title']}\n  Snippet: {content_snippet}\n"

                # 3. Construct Prompt for Groq
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT + author_context + stories_context},
                    {"role": "user", "content": f"Here is the recent conversation history:\n---\n{context_str}\n---\n\nPlease respond to the last message from {message.author.display_name}. Remember to use [[MEMORY: Category | Content]] if you learn something new."}
                ]

                # 4. Call Groq API
                chat_completion = groq_client.chat.completions.create(
                    messages=messages,
                    model="openai/gpt-oss-20b",  # Using a capable model, ensure this model name is correct for your usage
                    temperature=0.7,
                    max_tokens=1024,
                )

                response_text = chat_completion.choices[0].message.content

                # 5. Process Memories
                # Regex to find [[MEMORY: Category | Content]]
                memory_pattern = r"\[\[MEMORY:\s*(.*?)\s*\|\s*(.*?)\]\]"
                memories = re.findall(memory_pattern, response_text)
                
                if memories:
                    logger.info(f"Found memories: {memories}")
                    for category, content in memories:
                        await database.add_information(message.author.id, category.strip(), content.strip())
                    
                    # Remove the memory tags from the response sent to user
                    response_text = re.sub(memory_pattern, "", response_text).strip()

                # 6. Send Reply
                if len(response_text) <= 2000:
                    await message.reply(response_text)
                else:
                    chunk_size = 1900
                    chunks = [response_text[i:i+chunk_size] for i in range(0, len(response_text), chunk_size)]
                    await message.reply(chunks[0])
                    for chunk in chunks[1:]:
                        await message.channel.send(chunk)

            except Exception as e:
                logger.error(f"Error generating response: {e}")
                await message.reply(f"I... I seem to have lost my train of thought. (An error occurred: {e})")

if __name__ == '__main__':
    if not TOKEN:
        print("Error: LORE_BOT_TOKEN not found in .env")
    elif not GROQ_API_KEY:
        print("Error: GROQ_API_KEY not found in .env")
    else:
        client.run(TOKEN)
