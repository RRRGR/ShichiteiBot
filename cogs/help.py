# -*- coding: utf-8 -*-

import discord
from discord import app_commands
from discord.ext import commands


class Help(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @app_commands.command()
    async def help(self, interaction: discord.Interaction):
        """How to use the bot"""

        help_embed = discord.Embed(
            title="botの使い方",
            color=0xFF0000,
        )
        help_embed.set_author(
            name=self.bot.user, icon_url=self.bot.user.display_avatar.url
        )
        text_how_to_submit = "'/ir'とタイプすると'/ir submit'というサジェストが出現します。そのサジェストを押すと提出のための入力欄が現れるので、順に選択肢からの選択、スコア入力、リザルト画像の添付を行って送信してください。Discordをアップデートしていないとサジェストが出ない場合があります。"
        text_bug = "不具合を見つけた場合はGrGurutoに報告をお願いします。"
        help_embed.add_field(name="提出方法", value=text_how_to_submit)
        help_embed.add_field(name="不具合", value=text_bug)
        await interaction.response.send_message(embed=help_embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
