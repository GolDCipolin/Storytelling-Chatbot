import discord
import sqlite3
from discord import app_commands
from discord.ext import tasks, commands
import random
import os
from ai import continue_story
from ai_art import generate_image


intents = discord.Intents.all()
# database stuff
database = sqlite3.connect('database.db')
cursor = database.cursor()
database.execute("CREATE TABLE IF NOT EXISTS story(story_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, story_text STRING)")
database.execute("CREATE TABLE IF NOT EXISTS story_images(image_id INTEGER PRIMARY KEY AUTOINCREMENT, story_id INTEGER, image_path TEXT, FOREIGN KEY (story_id) REFERENCES story(story_id) ON DELETE CASCADE)")

story = """Okay, buckle up, because this is the story of Antony, a real-life football wizard!
Once upon a time, in a sunny city far away in Brazil, a little boy named Antony was born. Even before he could walk properly, Antony was chasing after a football! It was his favorite toy, his best friend, and the key to his biggest dreams.

Antony grew up playing football on the dusty streets with his friends. They used their imaginations and turned ordinary spaces into amazing stadiums. A pile of rocks became the goalposts, and the squeaky sound of their worn-out ball was like the roar of a crowd!

Antony wasn't just good; he was *magical*! He had incredible skills. He could dribble the ball like it was glued to his feet, make the most amazing passes, and score goals that made everyone jump up and cheer! He even had a special trick, a super speedy spin he called the "Antony Twirl," that left defenders dizzy and confused!

He practiced hard, every single day. He knew that to become a professional footballer, he needed to be dedicated. He would train under the blazing sun, pushing himself to be better, faster, and stronger.

Soon, everyone in his town was talking about Antony, the amazing footballer. He was invited to join a famous football academy. It was a big step, but Antony was ready. He packed his bags, said goodbye to his friends and family, and promised to make them proud.

At the academy, Antony learned even more about football. He learned about teamwork, strategy, and how to be a true champion. He faced tough challenges and played against some of the best young players in the country.

He worked even harder than before, because now he was training and competing with really talented kids. Sometimes he felt tired and wanted to give up, but he remembered his dream and all the people who believed in him. So, he would dust himself off and keep practicing.

And guess what? All that hard work paid off! Antony became a star player and helped his team win many games. Soon, big football clubs from all around the world started to notice him! They saw his amazing skills, his passion, and his dedication.

One day, Antony got the call he had been dreaming of! A famous European football club wanted him to join their team! It was a dream come true! He packed his bags again, this time for an adventure across the ocean!

Now, Antony plays in big stadiums with thousands of cheering fans. He wears a special jersey with his name on the back, and he scores amazing goals. He still does his "Antony Twirl" that makes everyone gasp!

But even though he's a famous footballer now, Antony never forgets where he came from. He remembers playing on the dusty streets with his friends, dreaming big dreams. He always tries his best, not just for himself, but for all the young kids back home who are chasing their own football dreams.

And that, my friends, is the amazing story of Antony, the football wizard! He shows us that with hard work, dedication, and a little bit of magic, anything is possible! Now, go out there and chase your own dreams, just like Antony!"""



def run_discord_bot():
    TOKEN = ''
    intents = discord.Intents.default()
    intents.message_content = True
    client = commands.Bot(command_prefix='-', intents=intents)

    @client.event
    async def on_ready():
        print(f'{client.user} is now running!')
        try:
            synced = await client.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(e)


    # @client.tree.command(name="prompts")
    # @app_commands.describe(prompt="Give me your prompts for the story")
    # async def hello(interaction: discord.Interaction, prompt: str):
    #     await interaction.response.send_message(
    #         f"{interaction.user.mention} said: `{prompt}`\n")
    #     query = "INSERT INTO messages VALUES (?, ?)"
    #     cursor.execute(query, (prompt, interaction.user.id))
    #     database.commit()
    #     # print("Stuff got added to the database")

    @client.tree.command(name="storylist")
    async def view_stories(interaction: discord.Interaction):

        query = "SELECT story_id, story_text FROM story WHERE user_id = ?"
        cursor.execute(query, (interaction.user.id,))
        stories = cursor.fetchall()

        if not stories:
            await interaction.response.send_message("You have no saved stories.", ephemeral=True)
            return

        story_options = []
        for story_id, story_text in stories:
            preview = " ".join(story_text.split()[:10]) + "..."
            story_options.append((preview, story_id))

        class StorySelect(discord.ui.Select):
            def __init__(self):
                options = [
                    discord.SelectOption(label=preview, value=str(story_id))
                    for preview, story_id in story_options
                ]
                super().__init__(placeholder="Select a story to view or delete", options=options)

            async def callback(self, interaction: discord.Interaction):
                selected_story_id = int(self.values[0])

                query = """
                    SELECT s.story_text, si.image_path
                    FROM story s
                    LEFT JOIN story_images si ON s.story_id = si.story_id
                    WHERE s.story_id = ?
                """
                cursor.execute(query, (selected_story_id,))
                results = cursor.fetchall()

                if not results:
                    await interaction.response.send_message("Story could not found.", ephemeral=True)
                    return

                story_text = results[0][0]
                image_urls = [row[1] for row in results if row[1]]

                story_chunks = [story_text[i:i + 1900] for i in range(0, len(story_text), 1900)]

                await interaction.response.defer()
                for i, chunk in enumerate(story_chunks):
                    await interaction.followup.send(f"**Story Page {i + 1}:**\n{chunk}")

                for image_url in image_urls:
                    await interaction.followup.send(image_url)

                await interaction.followup.send("Are you sure about deleting this story?", view=DeleteStoryView(selected_story_id))

        class DeleteStoryButton(discord.ui.Button):
            def __init__(self, story_id):
                super().__init__(label="Delete Story", style=discord.ButtonStyle.danger)
                self.story_id = story_id

            async def callback(self, interaction: discord.Interaction):
                cursor.execute("DELETE FROM story WHERE story_id = ?", (self.story_id,))
                cursor.execute("DELETE FROM story_images WHERE story_id = ?", (self.story_id,))
                database.commit()

                await interaction.response.send_message("Deleted story", ephemeral=True)

        class DeleteStoryView(discord.ui.View):
            def __init__(self, story_id):
                super().__init__()
                self.add_item(DeleteStoryButton(story_id))

        class StoryView(discord.ui.View):
            def __init__(self):
                super().__init__()
                self.add_item(StorySelect())

        await interaction.response.send_message("Here are your stories. Select one to view or delete:", view=StoryView(), ephemeral=True)

    @client.tree.command(name="promptdelete")
    async def hello(interaction: discord.Interaction):

        query = "SELECT story_id, story_text FROM story WHERE user_id = ?"
        cursor.execute(query, (interaction.user.id,))
        stories = cursor.fetchall()

        if not stories:
            await interaction.response.send_message("You have no saved stories.", ephemeral=True)
            return

        story_options = []
        for story_id, story_text in stories:
            preview = " ".join(story_text.split()[:10]) + "..."
            story_options.append((preview, story_id))

        class StorySelect(discord.ui.Select):
            def __init__(self):
                options = [
                    discord.SelectOption(label=preview, value=str(story_id))
                    for preview, story_id in story_options
                ]
                super().__init__(placeholder="Select a story to view", options=options)

            async def callback(self, interaction: discord.Interaction):
                selected_story_id = int(self.values[0])

                query = """
                    SELECT s.story_text, si.image_path
                    FROM story s
                    LEFT JOIN story_images si ON s.story_id = si.story_id
                    WHERE s.story_id = ?
                """
                cursor.execute(query, (selected_story_id,))
                results = cursor.fetchall()

                if not results:
                    await interaction.response.send_message("Story cannot be found.", ephemeral=True)
                    return

                story_text = results[0][0]
                image_urls = [row[1] for row in results if row[1]]

                story_chunks = [story_text[i:i + 1900] for i in range(0, len(story_text), 1900)]

                await interaction.response.defer()
                for i, chunk in enumerate(story_chunks):
                    await interaction.followup.send(f"**Story Page {i + 1}:**\n{chunk}")

                for image_url in image_urls:
                    await interaction.followup.send(image_url)

        class StoryView(discord.ui.View):
            def __init__(self):
                super().__init__()
                self.add_item(StorySelect())

        await interaction.response.send_message("Select to view your stories:", view=StoryView(), ephemeral=True)

    @client.tree.command(name="generate")
    @app_commands.describe(prompt="Give me your prompts for the story", age="Enter target age for the story (such as 10)")
    async def hello(interaction: discord.Interaction, prompt: str, age: int = 10):
        from ai import chat_session
        from ai import model_age

        await interaction.response.defer()

        chat_session = model_age(age)
        response = chat_session.send_message(prompt)
        story_text = response.text

        story_chunks = [story_text[i:i + 1900] for i in range(0, len(story_text), 1900)]

        discord_image_urls = []

        for i, chunk in enumerate(story_chunks):
            prompt = story_text

            image_path = await generate_image(prompt)

            if image_path:
                file = discord.File(image_path, filename=f"story_image_{i + 1}.png")

                msg = await interaction.followup.send(f"**Story Page {i + 1}:**\n{chunk}", file=file)

                image_url = msg.attachments[0].url
                discord_image_urls.append(image_url)

                os.remove(image_path)
            else:
                await interaction.followup.send(f"**Story Page {i + 1}:**\n{chunk}\n Failed to generate image.")

        query = "INSERT INTO story (user_id, story_text) VALUES (?, ?)"
        cursor.execute(query, (interaction.user.id, story_text))
        story_id = cursor.lastrowid
        database.commit()

        for image_url in discord_image_urls:
            query = "INSERT INTO story_images (story_id, image_path) VALUES (?, ?)"
            cursor.execute(query, (story_id, image_url))

        database.commit()

    @client.tree.command(name="update_story")
    @app_commands.describe(additional_prompt="Describe how you want the story to continue.")
    async def continue_story(interaction: discord.Interaction, additional_prompt: str):
        from ai import continue_story
        from ai_art import generate_image

        await interaction.response.defer()

        cursor.execute("SELECT story_id, story_text FROM story WHERE user_id = ? ORDER BY story_id DESC LIMIT 1",
                       (interaction.user.id,))
        latestStory = cursor.fetchone()

        if not latestStory:
            await interaction.followup.send("Please use `/generate` first then use `/update_story`.")
            return

        latestStoryId, previousStoryText = latestStory
        fullPrompt = previousStoryText + "\n\n" + additional_prompt
        newStoryText = continue_story(interaction.user.id, fullPrompt, cursor)
        combinedStoryText = previousStoryText + " " + newStoryText
        cursor.execute("UPDATE story SET story_text = ? WHERE story_id = ?", (combinedStoryText, latestStoryId))
        database.commit()
        cursor.execute("SELECT story_text FROM story WHERE story_id = ?", (latestStoryId,))
        updated_story = cursor.fetchone()

        if updated_story is None:
            await interaction.followup.send("Error.")
            return
        story_chunks = [combinedStoryText[i:i + 1900] for i in range(0, len(combinedStoryText), 1900)]
        discord_image_urls = []

        for i, chunk in enumerate(story_chunks):
            image_path = await generate_image(chunk)

            if image_path:
                file = discord.File(image_path, filename=f"story_image_{i + 1}.png")
                msg = await interaction.followup.send(f"**Updated** Story Page {i + 1}:\n{chunk}", file=file)
                image_url = msg.attachments[0].url
                discord_image_urls.append(image_url)
                os.remove(image_path)
            else:
                await interaction.followup.send(f"**Story Page {i + 1}:**\n{chunk}\n Couldn't generate image.")
        for image_url in discord_image_urls:
            cursor.execute("INSERT INTO story_images (story_id, image_path) VALUES (?, ?)",
                           (latestStoryId, image_url))

        database.commit()

    @client.tree.command(name="help")
    async def hello(interaction: discord.Interaction):
        await interaction.response.send_message("Use `/generate` to start making your story.\nUse `/storylist` to view your previous stories.\nUse `/update_story` to update your current story **(MUST USE `/generate` FIRST)**\nTo view help `/help`")

    client.run(TOKEN)

# @client.tree.command(name="test")
    # async def hello(interaction: discord.Interaction):
    #     await interaction.response.defer()
    #
    #     story_chunks = [story[i:i + 1900] for i in range(0, len(story), 1900)]
    #
    #     discord_image_urls = []
    #
    #     for i, chunk in enumerate(story_chunks):
    #         prompt = story
    #
    #         image_path = await generate_image(prompt)
    #
    #         if image_path:
    #             file = discord.File(image_path, filename=f"story_image_{i + 1}.png")
    #
    #             msg = await interaction.followup.send(f"**Story Page {i + 1}:**\n{chunk}", file=file)
    #
    #             image_url = msg.attachments[0].url
    #             discord_image_urls.append(image_url)
    #
    #             os.remove(image_path)
    #         else:
    #             await interaction.followup.send(f"**Story Page {i + 1}:**\n{chunk}\n Failed to generate image.")
    #
    #     query = "INSERT INTO story (user_id, story_text) VALUES (?, ?)"
    #     cursor.execute(query, (interaction.user.id, story))
    #     story_id = cursor.lastrowid
    #     database.commit()
    #
    #     for image_url in discord_image_urls:
    #         query = "INSERT INTO story_images (story_id, image_path) VALUES (?, ?)"
    #         cursor.execute(query, (story_id, image_url))
    #
    #     database.commit()