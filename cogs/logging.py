import discord
from discord.ext import commands
from utils.config import CHANNELS, COLORS
import datetime

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def log_action(self, action: str, description: str, color: int, guild: discord.Guild, **kwargs):
        """Универсальная функция для логирования"""
        log_channel = guild.get_channel(CHANNELS["LOG_CHANNEL"])
        if not log_channel:
            return

        embed = discord.Embed(
            title=f"📝 {action}",
            description=description,
            color=color,
            timestamp=datetime.datetime.utcnow()
        )

        # Добавляем дополнительные поля
        for key, value in kwargs.items():
            if value:  # Добавляем только если значение не пустое
                embed.add_field(name=key.replace('_', ' ').title(), value=value, inline=True)

        embed.set_footer(text=f"Server: {guild.name}")
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        
        await self.log_action(
            "Сообщение удалено",
            f"Сообщение от {message.author.mention} было удалено в {message.channel.mention}",
            COLORS["ERROR"],
            message.guild,
            author=message.author.mention,
            channel=message.channel.mention,
            content=message.content or "Вложение/Embed"
        )

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return
        
        await self.log_action(
            "Сообщение изменено",
            f"Сообщение от {before.author.mention} было изменено в {before.channel.mention}",
            COLORS["WARNING"],
            before.guild,
            author=before.author.mention,
            channel=before.channel.mention,
            before=before.content[:1024] if before.content else "Вложение/Embed",
            after=after.content[:1024] if after.content else "Вложение/Embed"
        )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.log_action(
            "Участник присоединился",
            f"{member.mention} присоединился к серверу",
            COLORS["SUCCESS"],
            member.guild,
            user=member.mention,
            account_created=discord.utils.format_dt(member.created_at, 'R')
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.log_action(
            "Участник покинул сервер",
            f"{member.mention} покинул сервер",
            COLORS["ERROR"],
            member.guild,
            user=member.mention,
            joined_at=discord.utils.format_dt(member.joined_at, 'R') if member.joined_at else "Неизвестно"
        )

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # Изменение ролей
        if before.roles != after.roles:
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]

            if added_roles:
                await self.log_action(
                    "Роль добавлена",
                    f"Пользователю {after.mention} добавлены роли",
                    COLORS["SUCCESS"],
                    after.guild,
                    user=after.mention,
                    roles=", ".join([role.mention for role in added_roles])
                )

            if removed_roles:
                await self.log_action(
                    "Роль удалена",
                    f"У пользователя {after.mention} удалены роли",
                    COLORS["ERROR"],
                    after.guild,
                    user=after.mention,
                    roles=", ".join([role.mention for role in removed_roles])
                )

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel != after.channel:
            if not before.channel and after.channel:  # Вошел в голосовой
                await self.log_action(
                    "Подключение к голосовому каналу",
                    f"{member.mention} подключился к голосовому каналу",
                    COLORS["SUCCESS"],
                    member.guild,
                    user=member.mention,
                    channel=after.channel.mention
                )
            elif before.channel and not after.channel:  # Вышел из голосового
                await self.log_action(
                    "Отключение от голосового канала",
                    f"{member.mention} отключился от голосового канала",
                    COLORS["ERROR"],
                    member.guild,
                    user=member.mention,
                    channel=before.channel.mention
                )
            elif before.channel and after.channel:  # Переместился между каналами
                await self.log_action(
                    "Перемещение между голосовыми каналами",
                    f"{member.mention} переместился между голосовыми каналами",
                    COLORS["WARNING"],
                    member.guild,
                    user=member.mention,
                    from_channel=before.channel.mention,
                    to_channel=after.channel.mention
                )

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        await self.log_action(
            "Роль создана",
            f"Создана новая роль {role.mention}",
            COLORS["SUCCESS"],
            role.guild,
            role=role.mention,
            color=str(role.color)
        )

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        await self.log_action(
            "Роль удалена",
            f"Роль **{role.name}** была удалена",
            COLORS["ERROR"],
            role.guild,
            role=role.name
        )

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        if before.name != after.name:
            await self.log_action(
                "Роль переименована",
                f"Роль была переименована",
                COLORS["WARNING"],
                after.guild,
                before_name=before.name,
                after_name=after.name
            )

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        await self.log_action(
            "Канал создан",
            f"Создан новый канал {channel.mention}",
            COLORS["SUCCESS"],
            channel.guild,
            channel=channel.mention,
            type=channel.type.name
        )

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self.log_action(
            "Канал удален",
            f"Канал **{channel.name}** был удален",
            COLORS["ERROR"],
            channel.guild,
            channel=channel.name,
            type=channel.type.name
        )

async def setup(bot):
    await bot.add_cog(Logging(bot))