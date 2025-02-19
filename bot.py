import discord
import os
import asyncio
import logging
import sys
import traceback
import requests
import random
import colorama
import glob
import json
from discord.ext import commands
from os import environ
from dotenv import load_dotenv
from dependencies.Facedet import FaceDet

colorama.init()

# Configuration
load_dotenv()
try:
    with open("config.json", "r") as f:
        config = json.load(f)
    TOKEN = os.environ.get("TOKEN") or config["token"]
    IMAGES_PATH = config["images_path"]
    TEMP_PATH = config["temp_path"]
except FileNotFoundError:
    print("Error: config.json not found. Create it with 'token', 'images_path', and 'temp_path'.")
    sys.exit(1)
except json.JSONDecodeError:
    print("Error: Invalid JSON in config.json")
    sys.exit(1)
except KeyError as e:
    print(f"Error: Missing key {e} in config.json")
    sys.exit(1)

# Path setup
images_path = os.path.join(os.path.dirname(__file__), IMAGES_PATH)
temp_path = os.path.join(os.path.dirname(__file__), TEMP_PATH, "temp_images")

# Logger setup
logger = logging.getLogger('logger')
fh = logging.FileHandler(os.path.join(os.path.dirname(__file__), "logs/d_bot.log"))
logger.addHandler(fh)

def exc_handler(exctype, value, tb):
    logger.exception(''.join(traceback.format_exception(exctype, value, tb)))

sys.excepthook = exc_handler

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents)
bot.remove_command('help')

# Face Detection setup
facedet = FaceDet(os.path.dirname(__file__))

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

@bot.event
async def on_ready():
    print(f'Bot started successfully as {bot.user}.')
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name=random.choice(["Your camera 📷", "Your house 🏠", "Everything 🤖"]))
    )

@bot.event
async def on_message(message):
    try:
        username = str(message.author.name)
        user_message = str(message.content)
        channel = str(message.channel.name)
        print(f'{username}: {user_message} ({channel})')
        await bot.process_commands(message)
    except Exception as e:
        logger.exception(f"Error in on_message: {e}")
        await message.channel.send("An error occurred. Please try again later.")

@bot.command()
async def addface(ctx, name):
    if not name.isalnum() or "_" in name:
        await ctx.send("Invalid name. Please use alphanumeric characters and no underscores.")
        return

    faces = [os.path.splitext(os.path.basename(face))[0] for ext in ALLOWED_EXTENSIONS for face in glob.glob(os.path.join(images_path, f"*{ext}"))]

    if name in faces:
        await ctx.send(f"**{name}** is already in the database.")
        return

    if not ctx.message.attachments:
        await ctx.send("No **image** attached to command.")
        return

    attachment = ctx.message.attachments[0]
    if not any(attachment.filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
        await ctx.send("Invalid file type. Only .jpg, .jpeg, and .png are allowed.")
        return

    os.makedirs(temp_path, exist_ok=True)  # Create directory beforehand

    try:
        img_data = requests.get(attachment.url).content
        temp_file_path = os.path.join(temp_path, f"ud_{name}.jpg")

        with open(temp_file_path, "wb") as handler:
            handler.write(img_data)

        detector = facedet.findface(temp_file_path, name)

        if detector:
            await ctx.send(f"**{name}** added to database.", file=discord.File(detector[2]))
            try:
                os.remove(detector[2])
            except Exception as e:
                logger.error(f"Error removing detector output image: {e}")
        else:
            await ctx.send(f"**No face detected in image**.")

        os.remove(temp_file_path)  # Clean up temporary file
    except requests.exceptions.RequestException as e:  # Catch requests errors
        logger.exception(f"Error downloading image: {e}")
        await ctx.send("Error downloading image from attachment.")
        return  # Stop processing
    except Exception as e:
        logger.exception(f"Error in addface: {e}")
        await ctx.send(f"An error occurred: {e}")
        try:
            os.remove(temp_file_path)
        except:
            pass

@bot.command()
async def delface(ctx, name):
    faces = [os.path.splitext(os.path.basename(face))[0] for ext in ALLOWED_EXTENSIONS for face in glob.glob(os.path.join(images_path, f"*{ext}"))]

    if name in faces:
        for ext in ALLOWED_EXTENSIONS:
            file_path = os.path.join(images_path, f"{name}{ext}")
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    await ctx.send(f"**{name}** removed from database.")
                    return  # Exit after successful deletion
                except Exception as e:
                    logger.exception(f"Error deleting file: {e}")
                    await ctx.send(f"Error deleting **{name}**. Please try again.")
                    return
        await ctx.send(f"**{name}** was found but no matching file was deleted.")
    else:
        await ctx.send(f"**{name}** is not in the database.")

@bot.command()
async def listfaces(ctx):
    faces = [os.path.splitext(os.path.basename(face))[0] for ext in ALLOWED_EXTENSIONS for face in glob.glob(os.path.join(images_path, f"*{ext}"))]

    if not faces:
        await ctx.send("No faces in the database.")
        return

    message = ", ".join(faces)
    if len(faces) <= 10:  # Define a limit (e.g., 10)
        images = []
        for face in faces:
            for ext in ALLOWED_EXTENSIONS:
                image_path = os.path.join(images_path, f"{face}{ext}")
                if os.path.exists(image_path):
                    try:
                        images.append(discord.File(image_path))
                    except Exception as e:  # Catch potential errors
                        logger.exception(f"Error creating discord.File: {e}")
                        await ctx.send(f"Error displaying image for {face}.")
                        continue  # Skip to the next image
        try:
            if len(faces) > 1:
                await ctx.send(message + " (in order)", files=images)
            else:
                await ctx.send(message, files=images)
        except discord.HTTPException:
            await ctx.send(message)  # Send message only if files are too large
    else:
        await ctx.send(message)  # Just send the message if there are too many faces


@bot.command()
async def help(ctx):
    await ctx.send("**listfaces**, **delface** (name), **addface** (name) [attachment]")

async def main():
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
