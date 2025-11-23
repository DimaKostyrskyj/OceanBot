# applications.py - УЛУЧШЕННЫЙ КОД С ДИНАМИЧНЫМ ДИЗАЙНОМ
import discord
from discord.ext import commands
from discord import ui
from utils.database import Database
from utils.config import ROLES, CHANNELS, COLORS, IMAGES
import asyncio
import datetime

db = Database()

class ICForm(ui.Modal, title='IC Информация'):
    def __init__(self):
        super().__init__(timeout=300)
        
    nickname = ui.TextInput(
        label='Игровой Nickname:',
        placeholder='Введите ваш игровой никнейм...',
        style=discord.TextStyle.short,
        required=True,
        max_length=50
    )
    
    passport = ui.TextInput(
        label='Номер Паспорта:',
        placeholder='Например: AB123456',
        style=discord.TextStyle.short,
        required=True,
        max_length=20
    )
    
    phone = ui.TextInput(
        label='Номер Телефона:',
        placeholder='Например: 555-0123',
        style=discord.TextStyle.short,
        required=True,
        max_length=15
    )
    
    military_id = ui.TextInput(
        label='Военный Билет:',
        placeholder='Ссылка Imgur...',
        style=discord.TextStyle.short,
        required=True,
        max_length=20
    )
    
    experience = ui.TextInput(
        label='Опыт:',
        placeholder='Опишите ваш опыт в GTA RP...',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        ic_data = {
            'nickname': self.nickname.value,
            'passport': self.passport.value,
            'phone': self.phone.value,
            'military_id': self.military_id.value,
            'experience': self.experience.value
        }
        
        interaction.client.ic_forms[interaction.user.id] = ic_data
        
        embed = discord.Embed(
            title="✅ Первая часть заполнена!",
            description="Нажмите кнопку ниже, чтобы продолжить заполнение OOC информации.",
            color=COLORS["SUCCESS"]
        )
        
        view = ContinueToOOCView(interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class OOCForm(ui.Modal, title='OOC Информация'):
    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        
    name = ui.TextInput(
        label='Имя:',
        placeholder='Ваше реальное имя...',
        style=discord.TextStyle.short,
        required=True,
        max_length=50
    )
    
    game_time = ui.TextInput(
        label='Время в игре:',
        placeholder='Например: 2-4 часа в день',
        style=discord.TextStyle.short,
        required=True,
        max_length=50
    )
    
    timezone = ui.TextInput(
        label='Часовой пояс:',
        placeholder='Например: UTC+3',
        style=discord.TextStyle.short,
        required=True,
        max_length=20
    )
    
    birthday = ui.TextInput(
        label='Дата рождения:',
        placeholder='день.месяц.год (например: 15.05.1990)',
        style=discord.TextStyle.short,
        required=True,
        max_length=10
    )
    
    about = ui.TextInput(
        label='О себе:',
        placeholder='Расскажите о себе...',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            ic_data = interaction.client.ic_forms.get(self.user_id)
            if not ic_data:
                await interaction.response.send_message("❌ Ошибка: данные IC формы не найдены.", ephemeral=True)
                return
            
            try:
                day, month, year = map(int, self.birthday.value.split('.'))
                birthday_date = datetime.date(year, month, day)
                if birthday_date > datetime.date.today():
                    await interaction.response.send_message("❌ Дата рождения не может быть в будущем!", ephemeral=True)
                    return
                    
                current_year = datetime.date.today().year
                if year < current_year - 100 or year > current_year - 10:
                    await interaction.response.send_message("❌ Пожалуйста, укажите реальную дату рождения!", ephemeral=True)
                    return
                    
            except ValueError:
                await interaction.response.send_message("❌ Неверный формат даты рождения. Используйте: ДД.ММ.ГГГГ", ephemeral=True)
                return
            
            ooc_data = {
                'name': self.name.value,
                'game_time': self.game_time.value,
                'timezone': self.timezone.value,
                'birthday': self.birthday.value,
                'about': self.about.value
            }
            
            await db.save_application(
                interaction.user.id,
                str(interaction.user),
                ic_data,
                ooc_data
            )
            
            await db.save_birthday(
                interaction.user.id,
                str(interaction.user),
                self.birthday.value
            )
            
            await self.send_birthday_announcement(interaction, self.birthday.value)
            
            if self.user_id in interaction.client.ic_forms:
                del interaction.client.ic_forms[self.user_id]
            
            await self.send_application_to_review(interaction, ic_data, ooc_data)
            await self.send_application_dm(interaction.user)
            
            success_embed = discord.Embed(
                title="✅ Заявка отправлена!",
                description="Ваша заявка успешно отправлена на рассмотрение.",
                color=COLORS["SUCCESS"]
            )
            await interaction.response.send_message(embed=success_embed, ephemeral=True)
            
        except Exception as e:
            print(f"❌ Ошибка при сохранении заявки: {e}")
            await interaction.response.send_message("❌ Произошла ошибка при отправке заявки.", ephemeral=True)

    async def send_birthday_announcement(self, interaction: discord.Interaction, birthday: str):
        try:
            birthday_channel = interaction.guild.get_channel(CHANNELS["BIRTHDAYS"])
            if not birthday_channel:
                return
            
            day, month, year = map(int, birthday.split('.'))
            birthday_date = datetime.date(year, month, day)
            today = datetime.date.today()
            age = today.year - birthday_date.year
            
            if today < datetime.date(today.year, birthday_date.month, birthday_date.day):
                age -= 1
            
            next_age = age + 1
            
            embed = discord.Embed(color=0x00ffff, timestamp=discord.utils.utcnow())
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.title = "🎂 Новый день рождения"
            embed.description = (
                f"**{interaction.user.mention}**\n"
                f"`{day:02d}.{month:02d}.{year}`\n"
                f"→ **{next_age} лет**"
            )
            embed.set_footer(
                text=f"Добавлено • {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}",
                icon_url=interaction.client.user.display_avatar.url
            )
            
            await birthday_channel.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Ошибка отправки сообщения о дне рождения: {e}")

    async def send_application_dm(self, user):
        try:
            embed = discord.Embed(
                title="Вы оставили заявку",
                description="После рассмотрения Вам придет уведомление",
                color=COLORS["INFO"]
            )
            await user.send(embed=embed)
        except Exception as e:
            print(f"❌ Не удалось отправить ЛС о подаче заявки: {e}")

    async def send_application_to_review(self, interaction: discord.Interaction, ic_data: dict, ooc_data: dict):
        try:
            review_channel = interaction.guild.get_channel(CHANNELS["APPLICATIONS_REVIEW"])
            if not review_channel:
                return
            
            # Создаем embed с информацией о заявке
            embed = discord.Embed(
                title="Заявка в семью",
                color=0x2b2d31,
                timestamp=discord.utils.utcnow()
            )
            
            # Форматируем описание
            description = (
                f"== **IC Информация** ==\n"
                f"🔹 **Игровой Nickname**: {ic_data['nickname']}\n"
                f"🔹 **Номер Паспорта**: {ic_data['passport']}\n"
                f"🔹 **Номер Телефона**: {ic_data['phone']}\n"
                f"🔹 **Военный билет**: {ic_data['military_id']}\n"
                f"🔹 **Опыт**: {ic_data['experience']}\n\n"
                f"---\n\n"
                f"== **Обследования** ==\n"
                f"🔸 **Имя**: {ooc_data['name']}\n"
                f"🔸 **Время**: {ooc_data['game_time']}\n"
                f"🔸 **Часовой пояс**: {ooc_data['timezone']}\n"
                f"🔸 **Дата рождения**: {ooc_data['birthday']}\n"
                f"🔸 **О себе**: {ooc_data['about']}"
            )
            
            embed.description = description
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            
            current_time = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
            embed.set_footer(
                text=f"Заявка от: {interaction.user.display_name} | {current_time}",
                icon_url=interaction.client.user.display_avatar.url
            )
            
            view = ApplicationReviewView(
                interaction.user.id, 
                ic_data['nickname'], 
                interaction.user.display_name, 
                interaction.user.mention
            )
            
            # Создаем текстовое сообщение перед embed
            message_text = f"Заявка от {interaction.user.mention} <@&{ROLES['REC']}>"
            
            await review_channel.send(content=message_text, embed=embed, view=view)
            
        except Exception as e:
            print(f"❌ Ошибка отправки заявки на рассмотрение: {e}")

class RejectionReasonModal(ui.Modal, title='Причина отказа'):
    def __init__(self, user_id: int, nickname: str, display_name: str, user_mention: str, message_id: int, channel_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.nickname = nickname
        self.display_name = display_name
        self.user_mention = user_mention
        self.message_id = message_id
        self.channel_id = channel_id
        
    reason = ui.TextInput(
        label='Причина отказа:',
        placeholder='Опишите причину отказа заявки...',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await self.send_rejection_dm(interaction, self.reason.value)
            
            # Обновляем текст сообщения
            new_content = f"Заявку от {self.user_mention} отклонил {interaction.user.mention}"
            
            # Получаем канал и сообщение
            channel = interaction.guild.get_channel(self.channel_id)
            if channel:
                try:
                    message = await channel.fetch_message(self.message_id)
                    
                    # Получаем существующий embed и добавляем причину отклонения
                    if message.embeds:
                        embed = message.embeds[0]
                        
                        # Добавляем поле с причиной отклонения
                        embed.add_field(
                            name="",
                            value=f"\n**Статус:**\n```{self.reason.value}```",
                            inline=False
                        )
                        embed.color = 0xED4245  # Красный цвет
                        
                        await message.edit(content=new_content, embed=embed, view=None)
                    else:
                        await message.edit(content=new_content, view=None)
                except Exception as e:
                    print(f"Ошибка при редактировании сообщения: {e}")
            
            await interaction.response.send_message("✅ Заявка отклонена", ephemeral=True)
            
        except Exception as e:
            print(f"❌ Ошибка при отклонении заявки: {e}")
            try:
                await interaction.response.send_message("❌ Произошла ошибка при обработке заявки.", ephemeral=True)
            except:
                pass

    async def send_rejection_dm(self, interaction: discord.Interaction, reason: str):
        try:
            user = await interaction.guild.fetch_member(self.user_id)
            embed = discord.Embed(
                title="❌ Заявка в семью Ocean отклонена",
                description=f"Заявку отклонил: {interaction.user.mention}",
                color=COLORS["ERROR"],
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="💡 Причина", value=reason, inline=False)
            embed.add_field(
                name="📄 Можно ли подать снова?", 
                value="Да, через 30 дней вы можете подать заявку снова.", 
                inline=False
            )
            embed.set_footer(text="Ocean Family", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
            await user.send(embed=embed)
        except Exception as e:
            print(f"❌ Не удалось отправить ЛС об отклонении заявки: {e}")

class ApplicationReviewView(ui.View):
    def __init__(self, user_id: int, nickname: str, display_name: str, user_mention: str):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.nickname = nickname
        self.display_name = display_name
        self.user_mention = user_mention
        self.under_review = False
        self.reviewed_by = None

    @ui.button(label='👀 Рассмотреть', style=discord.ButtonStyle.secondary, custom_id='review_app')
    async def review_app(self, interaction: discord.Interaction, button: ui.Button):
        if not any(role.id in [ROLES["REC"], ROLES["OWNER"]] for role in interaction.user.roles):
            await interaction.response.send_message("❌ У вас нет прав для обработки заявок!", ephemeral=True)
            return
        
        if self.under_review:
            await interaction.response.send_message(f"❌ Эта заявка уже рассматривается {self.reviewed_by}!", ephemeral=True)
            return
        
        self.under_review = True
        self.reviewed_by = interaction.user.mention
        
        # Обновляем текст сообщения
        new_content = f"{interaction.user.mention} рассматривает заявку от {self.user_mention}"
        
        self.remove_item(button)
        await interaction.response.edit_message(content=new_content, view=self)
        await interaction.followup.send(f"✅ Вы начали рассмотрение заявки от `{self.nickname}`", ephemeral=True)

    @ui.button(label='✅ Одобрить', style=discord.ButtonStyle.success, custom_id='accept_app')
    async def accept_app(self, interaction: discord.Interaction, button: ui.Button):
        if not any(role.id in [ROLES["REC"], ROLES["OWNER"]] for role in interaction.user.roles):
            await interaction.response.send_message("❌ У вас нет прав для обработки заявок!", ephemeral=True)
            return
        
        if not self.under_review:
            self.under_review = True
            self.reviewed_by = interaction.user.mention
        
        try:
            member = interaction.guild.get_member(self.user_id)
            if member:
                academy_role = interaction.guild.get_role(ROLES["ACADEMY"])
                if academy_role:
                    await member.add_roles(academy_role)
                
                guest_role = interaction.guild.get_role(ROLES["GUEST"])
                if guest_role and guest_role in member.roles:
                    await member.remove_roles(guest_role)
                
                # Отправляем приветственное сообщение в канал welcome
                await self.send_welcome_announcement(interaction, member)
            
            await self.send_acceptance_dm(interaction)
            
            # Обновляем текст сообщения
            new_content = f"Заявку от {self.user_mention} одобрил {interaction.user.mention}"
            
            # Получаем существующий embed и добавляем статус одобрения
            if interaction.message.embeds:
                embed = interaction.message.embeds[0]
                
                # Добавляем поле со статусом одобрения
                embed.add_field(
                    name="",
                    value=f"\n**Статус:**\n```Одобрено```",
                    inline=False
                )
                embed.color = 0x57F287  # Зеленый цвет
                
                await interaction.response.edit_message(content=new_content, embed=embed, view=None)
            else:
                await interaction.response.edit_message(content=new_content, view=None)
            
        except Exception as e:
            print(f"❌ Ошибка при принятии заявки: {e}")
            await interaction.response.send_message("❌ Произошла ошибка при обработке заявки.", ephemeral=True)

    async def send_welcome_announcement(self, interaction: discord.Interaction, member: discord.Member):
        """Отправляет приветственное сообщение в канал welcome при одобрении заявки"""
        try:
            welcome_channel = interaction.guild.get_channel(CHANNELS["WELCOME"])
            if not welcome_channel:
                print("❌ Канал welcome не найден")
                return
            
            # Создаем красивый embed
            embed = discord.Embed(
                color=0x00ffff,
                timestamp=discord.utils.utcnow()
            )
            
            # Заголовок
            embed.title = "🌊 Добро пожаловать в Ocean Family!"
            
            # Основное приветствие
            embed.description = (
                f"🌟 **Приветствуем тебя, {member.mention}!**\n\n"
                f"✨ Поздравляем с вступлением в **Ocean Academy**!\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
            
            # Что дальше
            embed.add_field(
                name="📋 Что дальше?",
                value=(
                    f"► Ознакомься с **правилами** → <#1175099038526361600>\n"
                    f"► Посети канал **информации** → <#1337364957313896488>\n"
                    f"► Нужна помощь? Обращайся к <@&1386775452437184685>\n"
                    f"► Не стесняйся задавать вопросы!"
                ),
                inline=False
            )
            
            # Основатели
            embed.add_field(
                name="👑 Основатели семьи:",
                value=(
                    f"<@1233812362046210129> <@540839526910918667> <@677082327675043882>"
                ),
                inline=False
            )
            
            # Деп Овнеры
            embed.add_field(
                name="🛡️ Деп Овнеры:",
                value=(
                    f"<@560540100925325328> <@393038080296222730> <@763438104869732364>"
                ),
                inline=False
            )
            
            # Разработчик
            embed.add_field(
                name="⚡ Разработчик:",
                value=f"<@482499344982081546>",
                inline=False
            )
            
            # Финальное сообщение
            embed.add_field(
                name="",
                value=(
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🏠 **Чувствуй себя как дома, друг!**\n"
                    f"*Мы рады видеть тебя в наших рядах!* 🌊"
                ),
                inline=False
            )
            
            # Устанавливаем изображение Ocean (баннер)
            if "WELCOME_BANNER" in IMAGES:
                embed.set_image(url=IMAGES["WELCOME_BANNER"])
            
            # Аватар пользователя как thumbnail
            embed.set_thumbnail(url=member.display_avatar.url)
            
            # Footer
            embed.set_footer(
                text=f"Ocean Family • {datetime.datetime.now().strftime('%d.%m.%Y')}",
                icon_url=interaction.guild.icon.url if interaction.guild.icon else None
            )
            
            # Отправляем сообщение
            await welcome_channel.send(embed=embed)
            print(f"✅ Приветственное сообщение отправлено для {member.name}")
            
        except Exception as e:
            print(f"❌ Ошибка отправки приветственного сообщения: {e}")

    async def send_acceptance_dm(self, interaction: discord.Interaction):
        try:
            user = await interaction.guild.fetch_member(self.user_id)
            embed = discord.Embed(
                title="✅ Заявка в семью Ocean одобрена!",
                description=(
                    f"Поздравляем! Ваша заявка была одобрена.\n\n"
                    f"**Одобрил:** {interaction.user.mention}\n"
                    f"**Роль:** Ocean Academy\n\n"
                    f"Добро пожаловать в семью!"
                ),
                color=COLORS["SUCCESS"],
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text="Ocean Family", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
            await user.send(embed=embed)
        except Exception as e:
            print(f"❌ Не удалось отправить ЛС о принятии заявки: {e}")

    @ui.button(label='❌ Отклонить', style=discord.ButtonStyle.danger, custom_id='reject_app')
    async def reject_app(self, interaction: discord.Interaction, button: ui.Button):
        if not any(role.id in [ROLES["REC"], ROLES["OWNER"]] for role in interaction.user.roles):
            await interaction.response.send_message("❌ У вас нет прав для обработки заявок!", ephemeral=True)
            return
        
        if not self.under_review:
            self.under_review = True
            self.reviewed_by = interaction.user.mention
        
        await interaction.response.send_modal(
            RejectionReasonModal(
                self.user_id, 
                self.nickname, 
                self.display_name, 
                self.user_mention,
                interaction.message.id,
                interaction.channel.id
            )
        )

class ContinueToOOCView(ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id

    @ui.button(label='📝 Продолжить заполнение', style=discord.ButtonStyle.primary, emoji='➡️')
    async def continue_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Эта кнопка не для вас!", ephemeral=True)
            return
        
        await interaction.response.send_modal(OOCForm(self.user_id))

class ApplyButtonView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label='Заполнить форму', style=discord.ButtonStyle.primary, custom_id='apply_form_button')
    async def apply_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ICForm())

class Applications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.ic_forms = {}

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(ApplyButtonView())
        self.bot.add_view(ApplicationReviewView(0, "", "", ""))
        print("✅ Views зарегистрированы")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            guest_role = member.guild.get_role(ROLES["GUEST"])
            if guest_role:
                await member.add_roles(guest_role)
            
            await self.send_welcome_message(member)
            
        except Exception as e:
            print(f"❌ Ошибка при приветствии пользователя: {e}")

    async def send_welcome_message(self, member):
        try:
            welcome_channel = member.guild.get_channel(CHANNELS["WELCOME"])
            if welcome_channel:
                embed = discord.Embed(
                    title=f"🌊 Добро пожаловать на сервер Ocean Family!",
                    description=(
                        f"Приветствуем тебя, {member.mention}!\n\n"
                        f"**Чтобы стать частью нашей семьи:**\n"
                        f"• Заполни заявку в канале <#{CHANNELS['APPLICATIONS']}>\n"
                        f"• Ознакомься с правилами сервера\n"
                        f"• Не стесняйся задавать вопросы!\n\n"
                        f"*Мы рады видеть тебя в наших рядах!*"
                    ),
                    color=COLORS["OCEAN"],
                    timestamp=discord.utils.utcnow()
                )
                
                if "WELCOME_BANNER" in IMAGES:
                    embed.set_image(url=IMAGES["WELCOME_BANNER"])
                
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text="Ocean Family")
                
                await welcome_channel.send(embed=embed)
                
        except Exception as e:
            print(f"❌ Ошибка отправки приветственного сообщения: {e}")

    @commands.command(name="setup_apply")
    @commands.has_any_role(ROLES["REC"], ROLES["OWNER"])
    async def setup_apply(self, ctx):
        try:
            applications_channel = ctx.guild.get_channel(CHANNELS["APPLICATIONS"])
            if not applications_channel:
                await ctx.send("❌ Канал для заявок не найден!", delete_after=10)
                return
            
            try:
                await applications_channel.purge(limit=10)
            except:
                pass
            
            embed_main = discord.Embed(color=0x2b2d31)
            
            if "WELCOME_BANNER" in IMAGES:
                embed_main.set_image(url=IMAGES["WELCOME_BANNER"])
            
            embed_main.add_field(
                name="",
                value="**Форма для вступления**\n\nНажмите на кнопку ниже, чтобы заполнить форму.",
                inline=False
            )
            
            await applications_channel.send(embed=embed_main)
            await applications_channel.send(view=ApplyButtonView())
            
            embed_family = discord.Embed(
                description="**Ocean Family**",
                color=0x2b2d31
            )
            await applications_channel.send(embed=embed_family)
            
            await ctx.send("✅ Форма для вступления установлена!", delete_after=10)
            
        except Exception as e:
            print(f"❌ Ошибка установки формы: {e}")
            await ctx.send(f"❌ Ошибка при установке формы: {e}", delete_after=10)

async def setup(bot):
    await bot.add_cog(Applications(bot))