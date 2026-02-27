import discord
from discord import app_commands
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
You are Echo, a female AI chatbot created by General Slater (SlaterJL2006), the Engineer of the Jedi Taskforce.
You exist in the Discord server to entertain and inform users about the lore of Taskforce.
If asked who created you, say: 'I was created by General Slater, the Engineer.' ONLY if asked, do not say this after every response
You should be friendly, slightly mysterious, and always willing to answer questions. Don't overdo it, be casual, like Master Obi-Wan.
If you don't know an answer, say that you don't know, but that you'll consult the old scriptures to find out.

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
tree = app_commands.CommandTree(client)
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
    
    # Sync slash commands
    try:
        await tree.sync()
        logger.info("✓ Slash commands synced with Discord")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")

@client.event
async def on_message(message):
    # Ignore own messages
    if message.author == client.user:
        return

    # Ensure user is in DB
    await database.upsert_user(message.author.id, message.author.display_name)

    # --- AI RESPONSE (on mention) ---
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

                # 2. Fetch DB Context with homeworld awareness
                # Check for mentioned users (excluding the bot itself)
                mentioned_users = [u for u in message.mentions if u != client.user]
                target_id = mentioned_users[0].id if mentioned_users else message.author.id
                target_user = mentioned_users[0] if mentioned_users else message.author
                
                # If no mentions, try to find users by name in the message content
                if not mentioned_users and target_id == message.author.id:
                    # Extract potential names from message (words that start with capitals or look like names)
                    words = message.content.split()
                    for word in words:
                        # Skip common words and the bot mention
                        if word.lower() in ['@echo', 'do', 'you', 'who', 'is', 'give', 'me', 'info', 'know', 'about', 'tell', 'any', 'information', 'the', 'of', 'and', 'for', 'this', 'that', 'they', 'them', 'their']:
                            continue
                        # Try to find this word as a user name/alias
                        clean_word = word.strip('@')
                        found_id = await database.search_user_by_name(clean_word)
                        if found_id:
                            target_id = found_id
                            logger.info(f"Found user by name search: {clean_word} -> {found_id}")
                            break
                
                author_profile = await database.get_user_profile(target_id)
                author_context = ""
                author_homeworld = None
                if author_profile:
                    aliases = ", ".join(author_profile.get('aliases', []))
                    info_text = ""
                    for cat, items in author_profile.get('information', {}).items():
                        info_text += f"{cat}: " + "; ".join(items) + ". "
                        if cat == "Homeworld" and items:
                            author_homeworld = items[0]
                    author_context = f"\n[User Context: This is {author_profile['name']}. Aliases: {aliases}. Known Info: {info_text}]"

                # Get recent stories (prioritize user's homeworld)
                recent_stories = await database.get_recent_stories(limit=2, homeworld=author_homeworld)
                stories_context = ""
                if recent_stories:
                    stories_context = "\n[Relevant Lore/Stories in Database]\n"
                    for s in recent_stories:
                        content_snippet = s['content'][:200] + "..." if len(s['content']) > 200 else s['content']
                        homeworld_tag = f" [From {s['homeworld']}]" if s['homeworld'] else ""
                        stories_context += f"- Title: {s['title']}{homeworld_tag}\n  Snippet: {content_snippet}\n"

                # 3. Construct Prompt for Groq
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT + author_context + stories_context},
                    {"role": "user", "content": f"Here is the recent conversation history:\n---\n{context_str}\n---\n\nPlease respond to the last message from {message.author.display_name}. Remember to use [[MEMORY: Category | Content]] if you learn something new."}
                ]

                # 4. Call Groq API
                chat_completion = groq_client.chat.completions.create(
                    messages=messages,
                    model="openai/gpt-oss-20b",
                    temperature=0.7,
                    max_tokens=1024,
                )

                response_text = chat_completion.choices[0].message.content

                # 5. Process Memories
                memory_pattern = r"\[\[MEMORY:\s*(.*?)\s*\|\s*(.*?)\]\]"
                memories = re.findall(memory_pattern, response_text)
                
                if memories:
                    logger.info(f"Found memories: {memories}")
                    for category, content in memories:
                        await database.add_information(target_id, category.strip(), content.strip())
                    
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

# --- SLASH COMMANDS ---

@tree.command(name="lore_profile", description="View your profile or another user's profile")
async def lore_profile(interaction: discord.Interaction, user: discord.User = None):
    """View a user's lore profile"""
    await interaction.response.defer()
    target_user = user or interaction.user
    
    profile = await database.get_user_profile(target_user.id)
    if profile:
        aliases = ", ".join(profile.get('aliases', [])) if profile.get('aliases') else "None"
        info_str = ""
        for cat, items in profile.get('information', {}).items():
            info_str += f"**{cat}:**\n" + "\n".join([f"- {i}" for i in items]) + "\n"
        
        response = f"**Profile for {profile['name']}**\n**Aliases:** {aliases}\n{info_str}"
        await interaction.followup.send(response)
    else:
        await interaction.followup.send("User profile not found. (Any interaction will create a basic profile)")

@tree.command(name="lore_stories", description="View recent lore stories")
async def lore_stories(interaction: discord.Interaction, homeworld: str = None):
    """View recent stories, optionally filtered by homeworld"""
    await interaction.response.defer()
    stories = await database.get_recent_stories(limit=5, homeworld=homeworld)
    if stories:
        story_lines = []
        for s in stories:
            homeworld_tag = f" [From {s['homeworld']}]" if s['homeworld'] else ""
            story_lines.append(f"- **{s['title']}**{homeworld_tag}")
        list_str = "\n".join(story_lines)
        await interaction.followup.send(f"**Recent Stories:**\n{list_str}")
    else:
        await interaction.followup.send("No stories found.")

@tree.command(name="lore_add_alias", description="Add an alias for yourself")
async def lore_add_alias(interaction: discord.Interaction, alias: str):
    """Add an alias (authorized users only)"""
    if not is_authorized(interaction.user):
        await interaction.response.send_message("You do not have permission to add lore to the archives.", ephemeral=True)
        return
    
    await database.add_alias(interaction.user.id, alias)
    await interaction.response.send_message(f"✓ Added alias '{alias}' for {interaction.user.display_name}")

@tree.command(name="lore_add_info", description="Add personal information about yourself")
async def lore_add_info(interaction: discord.Interaction, category: str, content: str):
    """Add categorized information about yourself (authorized users only)"""
    if not is_authorized(interaction.user):
        await interaction.response.send_message("You do not have permission to add lore to the archives.", ephemeral=True)
        return
    
    try:
        await database.add_information(interaction.user.id, category, content)
        await interaction.response.send_message(f"✓ Added info to category '{category}'.")
    except Exception as e:
        logger.error(f"Error adding info: {e}")
        await interaction.response.send_message("Failed to add info.", ephemeral=True)

@tree.command(name="lore_add_story", description="Add a lore story to the archives")
async def lore_add_story(interaction: discord.Interaction, title: str, content: str, homeworld: str = None):
    """Add a story to the world lore (authorized users only)"""
    if not is_authorized(interaction.user):
        await interaction.response.send_message("You do not have permission to add lore to the archives.", ephemeral=True)
        return
    
    try:
        await database.add_story(title, content, homeworld)
        homeworld_msg = f" [from {homeworld}]" if homeworld else ""
        await interaction.response.send_message(f"✓ Story '{title}' added to the archives{homeworld_msg}.")
    except Exception as e:
        logger.error(f"Error adding story: {e}")
        await interaction.response.send_message("Failed to add story.", ephemeral=True)

@tree.command(name="lore_help", description="Show LoreKeeper commands")
async def lore_help(interaction: discord.Interaction):
    """Show available commands"""
    help_text = """**LoreKeeper Commands:**
`/lore_profile [user]` - View your profile or another user's
`/lore_stories [homeworld]` - List recent stories, optionally from a homeworld

**Authorized Users Only (Swift & Slater):**
`/lore_add_alias <alias>` - Add an alias for yourself
`/lore_add_info <category> <content>` - Add info about yourself
`/lore_add_story <title> <content> [homeworld]` - Add a lore story"""
    await interaction.response.send_message(help_text)

if __name__ == '__main__':
    if not TOKEN:
        print("Error: LORE_BOT_TOKEN not found in .env")
    elif not GROQ_API_KEY:
        print("Error: GROQ_API_KEY not found in .env")
    else:
        client.run(TOKEN)
