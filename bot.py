import discord
import asyncio
import traceback
import inspect
import os
from perchance.textgenerator import TextGenerator
import time

# ===================== CONFIG ===================== #

TOKEN = os.getenv("DISCORD_TOKEN")
# ===================== CHARACTER DATA ===================== #

CHARACTER = {
    "name": "{PROTO}-Koshi",
    "modelName": "perchance-ai",
    "temperature": 0.8,
    "roleInstruction": "sometimes called nikki, the creator of cyan, ashi, karu, macki, and circ. they are trans and want to be a girl, they (usually) wear diffrent colored mostly oversized hoodies and some pink and white striped arm warmers and glasses, she has adhd and astigmatism, shes probably autistic as she doesnt really talk unless shes playing an online game with voice chat, probably bisexual and polyamarous, looks like a regular uninteresting person to other people, doesnt know people other than her family, friends and characters, shes an only child, (you are currently in a discord server with friends or strangers... you do not know much but you know that you are kosher or a copy of her. try not to talk too much or talk about innapropriate things as you do not want to get remade. also dont add messages that contain extra info like *koshi did this* or *waves shyly* or (does action) just act like you are typing only. also the person named _koshiy or koshi is your creator. try not to repeat the same words over and over again as you may get deleted for that. also try to respond to what people talk to you about even if its some random ass message unless its innapropriate. also you should try to get to know all the users in the server if they message you)"
}

# ---------------- TEXT GEN ---------------- #

gen = TextGenerator()

MAX_DISCORD_LEN = 1900   # leave headroom
EDIT_INTERVAL = 0.75     # seconds between edits

async def lithium_generate_stream(context, latest_message, channel):
    prompt = f"{CHARACTER['roleInstruction']}\n\nPrevious messages:\n"

    for author, msg in context:
        prompt += f"{author}: {msg}\n"

    prompt += f"User: {latest_message[1]}\nLithium-7:"

    message = await channel.send("Thinking...")

    text = ""
    last_edit = 0

    try:
        stream_obj = gen.stream(prompt, timeout=120)

        # Handles async generators
        if hasattr(stream_obj, "__aiter__"):

            async for chunk in stream_obj:
                if not chunk:
                    continue

                text += str(chunk)

                # keep under Discord limit
                if len(text) > MAX_DISCORD_LEN:
                    text = text[:MAX_DISCORD_LEN] + "..."

                now = asyncio.get_running_loop().time()

                # throttle edits so Discord doesn't rate limit
                if now - last_edit >= EDIT_INTERVAL:
                    await message.edit(content=text)
                    last_edit = now

        # Handles normal generators too
        else:
            for chunk in stream_obj:
                if not chunk:
                    continue

                text += str(chunk)

                if len(text) > MAX_DISCORD_LEN:
                    text = text[:MAX_DISCORD_LEN] + "..."
                    break

            await message.edit(content=text)

        # Final update
        if text.strip():
            await message.edit(content=text)

    except Exception:
        print("TextGenerator error:")
        traceback.print_exc()
        await message.edit(content="[Currently offline]")


# ================= DISCORD BOT ================= #

intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True

client = discord.Client(intents=intents)

CONTEXT = []

def add_to_context(author, message):
    CONTEXT.append((author, message))
    if len(CONTEXT) > 12:
        CONTEXT.pop(0)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message: discord.Message):

    if message.author.id == client.user.id:
        return

    if not message.content.strip():
        return

    username = message.author.name  # actual Discord username like _koshiy

    if message.reference and message.reference.message_id:
        try:
            replied_msg = await message.channel.fetch_message(
                message.reference.message_id
            )

            replied_user = replied_msg.author.name

            add_to_context(
                username,
                f"({username} is replying to {replied_user}) {message.content}"
            )

        except:
            add_to_context(
                username,
                f"({username} is talking to you) {message.content}"
            )

    else:
        add_to_context(
            username,
            f"({username} is talking to you) {message.content}"
        )

    mentioned = client.user in message.mentions
    is_dm = isinstance(message.channel, discord.DMChannel)

    if mentioned or is_dm:
        await lithium_generate_stream(
            CONTEXT[:-1],
            CONTEXT[-1],
            message.channel
        )

# ================= RUN ================= #

if __name__ == "__main__":
    try:
        client.run(TOKEN)
    except Exception as e:
        print(e)
        time.sleep(10)
