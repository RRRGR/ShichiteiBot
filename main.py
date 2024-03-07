# -*- coding: utf-8 -*-

from os import getenv

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = getenv("TOKEN")
# AU_CHAT_ID = int(getenv("AU_CHAT_ID"))
SHEET_AC_URL = getenv("SHEET_AC_URL")
SHEET_CS_URL = getenv("SHEET_CS_URL")


INITIAL_EXTENSIONS = [
    "cogs.IR",
    "cogs.help",
]


class ShichiteiBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            help_command=None,
            intents=discord.Intents.all(),
        )

    async def setup_hook(self):
        for cog in INITIAL_EXTENSIONS:
            await self.load_extension(cog)
        await self.tree.sync()

    async def on_ready(self):
        await self.change_presence(activity=discord.Game(name="使い方は'/helpから'"))


if __name__ == "__main__":
    ShichiteiBot().run(TOKEN)
