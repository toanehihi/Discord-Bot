import discord
from discord.ext import commands
import cv2
import numpy as np
from ultralytics import YOLO
from io import BytesIO

class AnimalsDetect(commands.Cog, name="animals-detection"):
    def __init__(self, bot):
        self.bot = bot
        self.model = YOLO("best.pt").to("cuda")

    @commands.command(name="detect", description="Phát hiện động vật trong ảnh")
    async def detect(self, ctx):
        if not ctx.message.attachments:
            await ctx.send("Vui lòng gửi kèm một ảnh.")
            return

        attachment = ctx.message.attachments[0]
        image_bytes = await attachment.read()

        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        results = self.model.predict(source=img, conf=0.5, verbose=False)
        annotated = results[0].plot()

        _, buffer = cv2.imencode('.jpg', annotated)
        byte_io = BytesIO(buffer)

        byte_io.seek(0)
        await ctx.send(file=discord.File(byte_io, filename="detected.jpg"))

async def setup(bot):
    await bot.add_cog(AnimalsDetect(bot))