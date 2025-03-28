# -*- coding: utf-8 -*-

import datetime
from typing import Literal, List

import discord
import gspread
from discord import app_commands
from discord.ext import commands
from gspread.worksheet import Worksheet
from oauth2client.service_account import ServiceAccountCredentials

from main import SHEET_AC_URL, SHEET_CS_URL
from constant import AC_GAME_LIST, CS_GAME_LIST, CIRCLE_LIST

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

json = "shichiteibot-61a5e2d1ee27.json"
credentials = ServiceAccountCredentials.from_json_keyfile_name(json, scope)
gc = gspread.authorize(credentials)


class IR(commands.GroupCog, name="ir"):

    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    def get_sheet_url(self, category: str):
        if category == "AC":
            sheet_url = SHEET_AC_URL
        else:
            sheet_url = SHEET_CS_URL
        return sheet_url

    async def get_worksheet(
        self, interaction: discord.Interaction, sheet_url: str, game: str
    ) -> Worksheet | None:
        try:
            worksheet = gc.open_by_url(sheet_url).worksheet(game)
            return worksheet
        except gspread.exceptions.WorksheetNotFound:
            await interaction.followup.send(
                content="機種名の入力に誤りがあります", ephemeral=True
            )
            return

    def get_author_col_loc(self, song: str):
        if song == "上位":
            author_col_loc = 3
        else:
            author_col_loc = 13
        return author_col_loc

    async def game_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> List[app_commands.Choice[str]]:
        category = interaction.namespace.category
        if category == "AC":
            if current == "":
                return [
                    app_commands.Choice(name=game, value=game) for game in AC_GAME_LIST
                ]
            else:
                return [
                    app_commands.Choice(name=game, value=game)
                    for game in AC_GAME_LIST
                    if current.lower() in game.lower()
                ]
        elif category == "CS":
            if current == "":
                return [
                    app_commands.Choice(name=game, value=game) for game in CS_GAME_LIST
                ]
            else:
                return [
                    app_commands.Choice(name=game, value=game)
                    for game in CS_GAME_LIST
                    if current.lower() in game.lower()
                ]
        else:
            return []

    @app_commands.command()
    @app_commands.autocomplete(game=game_autocomplete)
    @app_commands.describe(
        circle="所属サークル",
        category="AC or CS",
        game="機種",
        song="上位 or 下位",
        difficulty="難易度 (1が最難)",
        score="スコア (計算方法は機種によって異なります)",
        result="リザルト画像\n時間と共に撮影できると良い",
    )
    async def submit(
        self,
        interaction: discord.Interaction,
        circle: Literal[tuple(CIRCLE_LIST)],
        category: Literal["AC", "CS"],
        game: str,
        song: Literal["上位", "下位"],
        difficulty: Literal[1, 2, 3, 4, 5],
        score: float,
        result: discord.Attachment,
    ):
        """Submit your IR score!"""
        await interaction.response.defer()
        sheet_url = self.get_sheet_url(category)
        img_url = result.url
        try:
            worksheet = gc.open_by_url(sheet_url).worksheet(game)
        except gspread.exceptions.WorksheetNotFound:
            await interaction.followup.send(
                content="機種名の入力に誤りがあります", ephemeral=True
            )
            return
        self.update_score(
            interaction, circle, song, difficulty, score, img_url, worksheet
        )
        self.sort_sheet(song, worksheet)
        current_rank = self.get_current_rank(
            interaction.user.display_name, song, worksheet
        )
        embed = self.submission_embed(
            user=interaction.user,
            circle=circle,
            category=category,
            game=game,
            song=song,
            difficulty=difficulty,
            score=score,
            rank=current_rank,
            img_url=img_url,
            sheet_url=sheet_url,
        )
        await interaction.followup.send(embed=embed)

    def update_score(
        self,
        interaction: discord.Interaction,
        circle: str,
        song: str,
        difficulty: int,
        score: float,
        url: str,
        worksheet: Worksheet,
    ) -> tuple[str, str, str, str] | tuple[None, None, None, None]:
        author = interaction.user.display_name
        date = interaction.created_at + datetime.timedelta(hours=9)
        date = date.strftime("%Y-%m-%d %H:%M:%S")

        author_col_loc = self.get_author_col_loc(song)

        for i in range(4, 100):
            cell_value = worksheet.cell(i, author_col_loc).value
            if cell_value is None:
                break
            if cell_value == author:
                break
        row = i

        worksheet.update_cell(row, author_col_loc, author)
        worksheet.update_cell(row, author_col_loc + 1, circle)
        worksheet.update_cell(row, author_col_loc + 2, score)
        worksheet.update_cell(row, author_col_loc + 3, difficulty)
        worksheet.update_cell(row, author_col_loc + 5, date)
        worksheet.update_cell(row, author_col_loc + 6, url)
        return

    def sort_sheet(self, song: str, worksheet: Worksheet) -> None:
        author_col_loc = self.get_author_col_loc(song)
        sort_range_alphabet_1 = chr(author_col_loc + 64)
        sort_range_alphabet_2 = chr(author_col_loc + 70)
        score_col_loc = author_col_loc + 2
        diff_col_loc = author_col_loc + 3
        point_col_loc = author_col_loc + 4
        date_col_loc = author_col_loc + 5
        data = worksheet.get
        worksheet.sort(
            (diff_col_loc, "asc"),
            (score_col_loc, "des"),
            range=f"{sort_range_alphabet_1}5:{sort_range_alphabet_2}205",
        )
        cell_list = worksheet.range(5, point_col_loc, 204, point_col_loc)
        point = 2100
        for counter, cell in enumerate(cell_list):
            if counter < 10:
                point -= 100
            else:
                point = 100
            cell.value = point
        worksheet.update_cells(cell_list)
        return

    def submission_embed(
        self,
        user: discord.Member,
        circle: str,
        category: str,
        game: str,
        song: str,
        difficulty: str,
        score: float,
        rank: str,
        img_url: str,
        sheet_url: str,
    ) -> discord.Embed:
        embed = discord.Embed(
            title="IR Submission",
            color=0xFF0000,
            description="Your score is registered!",
            url=sheet_url,
        )
        embed.set_author(
            name=f"{user.display_name} ({circle})", icon_url=user.display_avatar.url
        )
        embed.set_image(url=img_url)
        embed.add_field(name="機種", value=game)
        embed.add_field(name="部門", value=category)
        embed.add_field(name="曲", value=song)
        embed.add_field(name="難易度", value=difficulty)
        embed.add_field(name="スコア", value=f"{score}")
        embed.add_field(name="現在の順位", value=f"{rank}位")
        return embed

    def get_current_rank(self, author: str, song: str, worksheet: Worksheet) -> int:
        author_col_loc = self.get_author_col_loc(song)
        for i in range(4, 100):
            cell_value = worksheet.cell(i, author_col_loc).value
            if cell_value is None:
                break
            if cell_value == author:
                break
        row = i
        rank = row - 4
        return rank

    @app_commands.command()
    @app_commands.describe(category="AC or CS", game="機種", song="上位 or 下位")
    @app_commands.autocomplete(game=game_autocomplete)
    async def ranking(
        self,
        interaction: discord.Interaction,
        category: Literal["AC", "CS"],
        game: str,
        song: Literal["上位", "下位"],
    ):
        """Show IR ranking."""
        await interaction.response.defer()
        ranking_embed = await self.make_ranking_embed(interaction, category, game, song)
        await interaction.followup.send(embed=ranking_embed)

    async def make_ranking_embed(
        self,
        interaction: discord.Interaction,
        category: str,
        game: str,
        song: str,
    ) -> discord.Embed:
        sheet_url = self.get_sheet_url(category)
        worksheet = await self.get_worksheet(interaction, sheet_url, game)
        if worksheet is None:
            return
        ranking_embed = discord.Embed(
            title="IR Rankings",
            color=0xFF0000,
            url=sheet_url,
            description=game,
        )
        ranking_embed.set_author(
            name=self.bot.user, icon_url=self.bot.user.display_avatar.url
        )
        author_col_loc = self.get_author_col_loc(song)
        name_list = worksheet.col_values(author_col_loc)[4:]
        circle_list = worksheet.col_values(author_col_loc + 1)[4:]
        score_list = worksheet.col_values(author_col_loc + 2)[4:]
        diff_list = worksheet.col_values(author_col_loc + 3)[4:]
        ranking_text = ""
        if len(name_list) != 0:
            for i in range(len(name_list)):
                ranking_text += f"{i+1}. {name_list[i]} ({circle_list[i]}): {score_list[i]} (難易度{diff_list[i]})\n"
        ranking_embed.add_field(name="Ranking", value=ranking_text, inline=False)
        return ranking_embed


async def setup(bot: commands.Bot):
    await bot.add_cog(IR(bot))
