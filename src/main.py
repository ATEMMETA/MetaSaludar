import os, cv2, pyttsx3, pyvirtualcam, multiprocessing, logging, sys, traceback, json, colorama, glob, requests, discord
from cvzone.PoseModule import PoseDetector
from pyvirtualcam import PixelFormat
from datetime import datetime
from os import environ
from dotenv import load_dotenv
from discord.ext import commands
import numpy as np  # Import numpy

from dependencies.Webhook import WebhookBuilder
from dependencies.Facerec import Facerec
from dependencies.Facedet import FaceDet  # Import Facedet

# ... (colorama initialization, config loading, directory creation, logging setup, 
#      environment variables, text-to-speech - keep this part as it is)

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}

intents = discord.Intents.default()
intents.message_content = True  # If you need to read message content
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.command()
async def addface(ctx, name):
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if any(attachment.filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
            try:
                image_bytes = await attachment.read()
                image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)

                fd = FaceDet(images_path)  # Use images_path consistently
                success, original_image_path, detected_image_path = fd.find_face(image, name)

                if success:
                    fr.load_encoding_images(images_path)  # Reload encodings
                    await ctx.send(f"Face added for {name}!")
                else:
                    await ctx.send("No face detected in the image.")
            except Exception as e:
                await ctx.send(f"An error occurred: {e}")
        else:
            await ctx.send("Invalid file type. Please upload a JPG, JPEG, or PNG image.")
    else:
        await ctx.send("Please attach an image to the command.")

def run_discord_bot():
    bot.run(os.getenv('DISCORD_TOKEN'))

if __name__ == '__main__':
    multiprocessing.freeze_support()

    # ... (rest of your setup: cap, detector, webhook, fr, frame_width, frame_height, fps)

    discord_process = multiprocessing.Process(target=run_discord_bot)
    discord_process.start()

    with pyvirtualcam.Camera(frame_width, frame_height, fps, fmt=PixelFormat.BGR) as cam:
        face_c = 0
        face = False
        face_det = []

        while True:
            try:
                ret, frame = cap.read()
                if not ret:
                    break

                # ... (Motion detection logic - add your code here)

                # Face recognition
                face_locations, face_names = fr.detect_known_faces(frame)
                for (y1, x2, y2, x1), name in zip(face_locations, face_names):
                    color = (0, 0, 225) if name == "Unknown" else (0, 225, 0)
                    cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_DUPLEX, 1, color, 1)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 1)

                    if name != "Unknown":
                        face_det.append(name)

                if len(face_locations) > 0:
                    face_c += 1
                    face = True
                else:
                    face = False

                # ... (Body detection, recording logic - add your code here)

                if webserver:
                    cam.send(frame)
                    cam.sleep_until_next_frame()

            except cv2.error as e:
                logger.exception(f"OpenCV error in main loop: {e}")
                print(f"An OpenCV error occurred: {e}")
                break
            except Exception as e:
                logger.exception(f"Error in main loop: {e}")
                print(f"A general error occurred: {e}")
                break

    cap.release()
    cv2.destroyAllWindows()

    discord_process.terminate()
    discord_process.join()
