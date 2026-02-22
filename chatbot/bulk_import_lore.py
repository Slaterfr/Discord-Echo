"""
Bulk import script for user lore data
Inserts characters, aliases, titles, events, and history into the SQLite database
"""

import sqlite3
from datetime import datetime
import asyncio
import sys

# Add parent directory to path to import database module
sys.path.insert(0, '.')

DB_NAME = 'lore.db'

# User data structure
USERS_DATA = [
    {
        "discord_id": 751920066332721152,
        "username": "SlaterJL2006",
        "aliases": ["Slater"],
        "titles": ["General", "The Inventor", "The Prodigy", "The Technician", "The Engineer"],
        "homeworld": "Coruscant",
        "events": ["The Battle for Castilon", "The Invasion of Raxus Secundus", "The Last Stand of Taskforce", "The Siege on Malachor"],
        "history": "Slater was born in the Coruscant underworld. He was found and brought to the Jedi Temple by Judicii Senko. Slater had an unusual connection to the force, most people called on it only in certain situations, mainly for using it in battle. But Slater saw how many Councilors and Elders of the Order would meditate long on things, often setting aside their time just for the meditation.\n\nBut Slater had an idea, if the force can be called on whenever, why do you need to meditate to get advice from it? So, Slater began to be in a constant state of meditation while he was doing everything. Slater didn't devote any of his time into dueling skill but rather devoted himself to becoming an engineer and pilot. His dream was to build revolutionary new things to improve the Galaxy.\n\nSlater became the Padawan of Judicii, the man who brought him to the temple, Judicii was a man of convictions and very uniform. Judicii helped Slater build his connection with the force even greater than what it was. Judicii guided Slater for many years, teaching him such a deep connection to the force that even many master's don't have. After a few years under Judicii, the Council decided he was ready, and Slater was inducted into Knighthood.\n\nSlater continued to further his knowledge and kept studying, until one day he received a letter from a newly formed Division, the Jedi Taskforce. Judicii was the Co-Leader and Co-Founder of this division, so that alone was enough to peak Slaters interest. They invited Slater to lead the Taskforce technical operations team. This job would allow him to continue his research while assisting Taskforce by making them new weapons, fixing their ships, and making sure they had all of the best tech available.\n\nWhile working here, he became friends with one of Taskforce's members, Swift. While not a high-ranking member yet, Swift was still quite well known due to the fact that her Master was the Leader of Taskforce. They often talked while Slater built new prototypes and they built up a bond with each other.\n\nAnd then one day Slater noticed that Swift hadn't shown up all day while he was working. So, he began looking around, but when he couldn't find her anywhere, he called Judicii, Judi and Bob asked him a number of questions. He didn't think he knew where she could've gone, but that's when it hit him, Castilon was Swifts home, she had recently complained about the Council not doing anything to save them. So she must've gone there. Bob marshaled together the whole Taskforce for the mission, but they insisted that Slater stayed behind. But Slater would not miss out on this mission, so he showed them his newest prototype, a new type of warship specially designed for stealth, with fully integrated stealth tech. But only he knew how to fly it, so they had to let him come, finally they agreed.\n\nThey zoomed into Castilons space sector, immediately they noticed the massive Sith battleships that had already begun their invasion on Castilon. The stealth tech was working at first, but then it began to fail before they could make it to the planet. Bob yelled at him \"I THOUGHT IT WAS SUPPOSED TO KEEP US HIDDEN!?\" Slater replied \"You missed the part where its a PROTOTYPE, I never said it was tested…\" Bob went to reply but Judi cut him short \"Never mind that, just get us onto that planet in one piece, your the best pilot in the order Slater, I know you can beat the Sith fighters, so focus Slater, focus.\"\n\nSith fighters drew near, but Slater outmaneuvered them, taking out all of them with ease, all while dodging shots from the Sith battleships. Then Slater cruised them safely into the planets atmosphere."
    },
    {
        "discord_id": 1180753256473972797,
        "username": "Swifvv",
        "aliases": ["Swift", "Swifty"],
        "titles": ["Debt Collector", "Chief General"],
        "homeworld": "Castilon",
        "events": ["The Battle for Castilon", "The Invasion of Raxus Secundus", "The Gonk Inquisition", "The Temple Guard Revolt", "The Siege on Malachor"],
        "history": "Swift was born on Castilon, immediately she began to display a deep connection to the force. She was picked up and brought to the Coruscant temple by a Jedi known merely as Bob. Unbeknownst to anyone at the time, this force sensitive child would one day be of upmost importance to the galaxy and to the Jedi Order.\n\nAfter passing all of the initiation tests it became time for Swift to become a Padawan, it seemed only fitting to the Council that it be the same person who found her to be her Master, Bob. Bob was many things at this time, he was a Jedi Master, and a promising leader in the newest branch of the Jedi Order, the Jedi Taskforce, Bob himself was on track to become the next High Councilor.\n\nSwift was a Padawan during a time of great turmoil, the Jedi Order was in a large-scale war against its long-term enemy, the Sith Order. The war had spread to many parts of the galaxy, including her homeworld Castilon. The Taskforce was first introduced at the beginning of the war, and due to Swift being the padawan of the leader at the time, it only felt natural she was inducted in.\n\nWhile in Taskforce Swift went on many missions, in between missions she spent a lot of time with Slater, who had become a good friend of hers. He was the head of Taskforce's Technical Operations department, which really was just him, he essentially fixed everything for Taskforce and kept them fully equipped for missions, all while working on new prototypes.\n\nOne day, the Taskforce received word that Castilon was under attack from the Sith. But the Council would not allow them to go because Castilon was not affiliated with the Old Republic. But that wouldn't stop Swift, she knew there was people in danger, innocent lives that would be lost if unprotected. So, she gathered all her gear and tried to sneak away in the night.\n\nWhen Bob heard about her going to Castilon he immediately marshaled the Taskforce together to go to Castilon. But the co-leader of Taskforce Judicii, strongly disagreed and sided with the Council in the matter. But Bob knew as well as everyone else did that lives would be lost on Castilon if they didn't intervene, and now a Jedi would be lost as well. He was able to sway the Council, and he got right back on track with the mission. Bob and the rest of the Taskforce deployed for Castilon that night.\n\nThe Taskforce zoomed out of hyperspace and right into the sector. Immediately they noticed the massive Sith warships in orbit, they had already begun their invasion. Bob quickly initiated stealth tech on the Taskforce battleships, keeping them hidden from the Sith.\n\nBob knew the Taskforce had to move quickly if Castilon was to survive. He knew they were outnumbered and outgunned and had low odds of success, but they had one thing going for them. Castilon was completely oceans with the exception of some islands. This would actually work in their favor, because the Sith did not intend to send all their forces to one island at once, they worked with the motto of \"divide and conquer\" which happens to be amazing news for Bob.\n\nBut before they could begin fighting on the islands, they would have to land first. But something had gone wrong, the stealth systems on the Taskforce battleships was no longer fooling the Sith, they could sense Jedi nearby.\n\nTheir cover was ruined, the Sith began to fire at them immediately. Although they sustained no immediate damage thanks to the Ships shields, it wouldn't stay that way long. They had to land if they wanted to live. The Sith quickly deployed fighters to get up close with the Taskforce battleships. Taskforce only had one ship in the sector, and it wasn't exactly meant for quick action, it was meant for infiltration.\n\nBut Taskforce was made a Division for a reason, it was made to house all of the most exceptional members of the Order. And it certainly did not disappoint when it came to that. The Taskforce pilot was able to maneuver easily in the battle, taking out all of the Sith fighters, all while dodging the shots from the Sith warships.\n\nIf it weren't for that pilot, Taskforce would've met a very early end. All of Taskforce had Commander Slater, a genius mechanic and pilot to thank for saving them that day. Slater quickly initiated the boost on the engines, bringing them speedily into the planets orbit."
    },
    {
        "discord_id": 697540192126500954,
        "username": "NaySicarius",
        "aliases": ["Nay"],
        "titles": ["Chief General", "The Resilient", "The Innovator"],
        "homeworld": "Raxus Secundus",
        "events": ["The Invasion of Raxus Secundus", "Political Crisis on Raxus Secundus", "The Last Stand of Taskforce", "The Siege on Malachor"],
        "history": "Nay Sicarius was born on the planet of Raxus Secundus, a lush forest world filled with vibrant cities and lots of politics. Nay was the son of the Governor of the planet's biggest city, Raxulon. Unlike most force sensitive children, Nay's abilities remained dormant for quite a long time. Nay was 14 when the entire Galaxy was entrenched in another Galactic War between light and dark. It wasn't long before the war reached Raxus Secundus.\n\nNay was enlisted in Raxus's top school at the time; his father wanted him to become a politician like him. And had it not been for the war, Nay may have been just that. Nay was in class when it happened, it was just like any other day, and then suddenly they heard explosions all around Raxulon. Suddenly an alarm began to go off in the school, they looked out the window and noticed multiple warships entering the planet's atmosphere, the Sith Order had begun its invasion of the planet.\n\nAll of the students began to panic, the school initiated safety protocols, locking all the rooms and leaving just the window exposed, but still locked. But it didn't matter regardless. One of Nays friends called out \"Look!\" as the Raxus Military arrived, they all expected the Military to stomp out the invaders. But this was not the case, the Sith easily thwarted the Militaries attempt at helping.\n\nThe teachers reassured them that it would all be okay, they just had to be patient and wait in the room. Nay looked out of the window once more, this time he noticed a Sith gunship, and it wasn't just going any random place, it was going straight to the senate building, the place where both of his parents worked.\n\nNay realized in this moment that they were planning on getting his father as governor to relinquish the planet, putting it under the Sith order as a tributary planet. He had read of them doing the same to other planets such as Alderaan, Felucia, Mon Cala, and many others. But in all of those cases, as soon as the planets were made tributary, the old leaders were killed and replaced by Sith enforcers.\n\nBut Nay couldn't let them do that, but the room was sealed off, with only one way out, the window. So, Nay pulled out a blaster he kept on his person for safety, and he shot at the window breaking it, and then he leapt out and began heading to the senate building. His classmates and teachers yelling at him from inside as he ran off.\n\nBut the path there was anything but clear, Sith had already begun to flood the streets. He was able to sneak past most of them, but one sensed him, a Sith enforcer known as \"The Leader\". The Leader searched for Nay, and thought he finally had him, as he slowly went to check under a box. But his senses were off, Nay fired 3 shots into the enforcers back before firing one more at his head killing the Sith.\n\nNay quickly hatched a plan, he put on The Leaders uniform, a full Sith outfit fitted with a full helmet and mechanical arm fittings, he even took all his weapons. He was the exact height as the Leader, the only thing that was off was his voice, apart from that, they might as well have been twins.\n\nKeeping up his disguise as the Leader, Nay waltzed into the Senate building where he saw a masked Sith Lord talking to his father. Trying to coerce him into signing the document giving them control over the planet, they had lined up everyone who worked in the Senate building, including Nay's mother. And were threatening to kill them if his father didn't sign the document giving them control.\n\nBut his father tried to call the Sith's bluff, refusing to sign the document, but the masked Sith wasn't bluffing. He quickly figured out which one was his wife, and lifted her into the air, choking her to her death. At this moment Nay revealed himself, firing 2 shots at the Sith Lord. Nearly taking him by surprise, but the Sith Lord's senses were far superior to that of the Leader. He froze the blaster shots midair and ordered his guards to seize Nay.\n\nThen the Sith killed Nay's mother and then threatened Nay. Finally, his father caved in, consumed by grief, but unwilling to let Nay fall to the Sith also. He signed the document. Then his father pleaded for Nays life, asking that he would be allowed to live. The Sith Lord promised he wouldn't kill Nay. But the moment his father's back was turned to the Sith, the Lord said \"But I didnt say anything about letting you live.\" just then he ignited his blade through his chest, ending his father's life for good.\n\nIt was in this moment that the final straw broke inside of Nay, his powers that once layed dormant within him, now fully awakened. The necks of the Sith guards at his side were snapped in an instant. Consumed by grief Nay fired a bolt of Sith lightning right at the Lord, an extremely advanced technique, even for someone extremely trained in the force. But Nay's grief immediately conquered anything holding him back in that moment, the lightning was so powerful it flung the Lord back a good 20 feet. Nay then ran to his father's side, holding his hand, as the life left his father, he said to Nay, who now had tears streaming down his face \"Remember son, with great power, comes great responsibility.\" And with those words, he drew his last breath, and died.\n\nNay vowed to avenge his parents. And the Sith Lord rose back to his feet, his interest piqued in Nay. The Sith quickly called out to his troops \"We secured the document, there is only one thing left to do before we depart, bring me that boy.\""
    },
    {
        "discord_id": 312947830526443521,
        "username": "ForsakenedXin",
        "aliases": ["Xin", "Forsaken"],
        "titles": ["General", "Keeper", "High Councilor", "The Diplomat"],
        "homeworld": "Coruscant",
        "events": ["Political Crisis on Raxus Secundus", "Operation Peacewalker", "The Last Stand of Taskforce"],
        "history": "Xin was born on Coruscant and brought to the Temple shortly after. He became the Padawan of Michael, the Master of the Order and acting Grandmaster. Xin and Michael didn't have to much time to bond with each other as Michael was constantly busy handling affairs in the Order.\n\nBut Xin devoted himself to studying the force and increasing his dueling proficiency, he quickly became a top prospect within the Order and would soon rise even further. Michael and Xin finally went on a mission together, this was a diplomatic mission to Raxus Secundus.\n\nThe problem with Raxus was because of Nay Sicarius, who had inherited the title of Governor after his father's passing, however he was also a member of the Jedi Council and leader of the Taskforce. So, it was very hard for him to balance both, so when he stepped down from Governor a massive seat of power needed to be filled, Nay called for help from the rest of the Council in advising the senate of Raxus's next choice for Governor.\n\nBut Raxus had many political parties, each going after the spot. The Council decided who they believed the best candidate was, but they had 0 success in convincing the other political parties to vote for their candidate. So, Xin gave it a shot, everyone doubted Xins ability to coerce them, as not even Michael could get these parties to budge in their decision. But Xin's charisma was unmatched, and he convinced 3 parties to back their candidate, making their candidate have the vast majority of the Raxus Senate backing him.\n\nThanks to Xin, the political affairs on Raxus were resolved and a trustworthy governor selected. Xin was knighted after they returned to Coruscant and his fame grew even more. Xin was offered high ranks within Temple Guards, Lorekeepers, and Taskforce. Xin accepted the offers from Lorekeepers and Taskforce but declined that of TG."
    }
]

def bulk_insert_users():
    """Insert all users and their associated data into the database"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    inserted_count = 0
    
    for user_data in USERS_DATA:
        discord_id = user_data["discord_id"]
        username = user_data["username"]
        
        try:
            # Insert or update user
            cursor.execute('''
                INSERT OR REPLACE INTO users (discord_id, name, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (discord_id, username))
            
            # Insert aliases
            for alias in user_data["aliases"]:
                cursor.execute('''
                    INSERT INTO user_aliases (user_id, alias)
                    VALUES (?, ?)
                ''', (discord_id, alias))
            
            # Insert titles
            for title in user_data["titles"]:
                cursor.execute('''
                    INSERT INTO information (user_id, category, content, created_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (discord_id, "Titles", title))
            
            # Insert homeworld
            if user_data["homeworld"]:
                cursor.execute('''
                    INSERT INTO information (user_id, category, content, created_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (discord_id, "Homeworld", user_data["homeworld"]))
            
            # Insert events
            for event in user_data["events"]:
                cursor.execute('''
                    INSERT INTO information (user_id, category, content, created_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (discord_id, "Events", event))
            
            # Insert history
            if user_data["history"]:
                cursor.execute('''
                    INSERT INTO information (user_id, category, content, created_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (discord_id, "History", user_data["history"]))
            
            inserted_count += 1
            print(f"✓ Successfully inserted {username} (ID: {discord_id})")
            
        except Exception as e:
            print(f"✗ Error inserting {username}: {e}")
            conn.rollback()
            continue
    
    conn.commit()
    conn.close()
    
    print(f"\n{'='*50}")
    print(f"Bulk import complete!")
    print(f"Successfully inserted {inserted_count} users")
    print(f"{'='*50}")

async def init_db():
    """Initialize the database schema"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Table: users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            discord_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table: user_aliases
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_aliases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            alias TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (discord_id)
        )
    ''')

    # Table: information
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS information (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (discord_id)
        )
    ''')

    # Table: stories
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ Database schema initialized")

if __name__ == "__main__":
    # Initialize database first
    asyncio.run(init_db())
    # Then insert the data
    bulk_insert_users()
