# applications.py - ПОЛНЫЙ ФАЙЛ
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
        placeholder='Номер военного билета...',
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
        # Сохраняем IC данные
        ic_data = {
            'nickname': self.nickname.value,
            'passport': self.passport.value,
            'phone': self.phone.value,
            'military_id': self.military_id.value,
            'experience': self.experience.value
        }
        
        # Сохраняем временные данные
        interaction.client.ic_forms[interaction.user.id] = ic_data
        
        # Отправляем временное сообщение с кнопкой для продолжения
        embed = discord.Embed(
            title="✅ Первая часть заполнена!",
            description="Нажмите кнопку ниже, чтобы продолжить заполнение OOC информации.",
            color=COLORS["SUCCESS"]
        )
        embed.set_footer(text="Ocean Bot")
        
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
            # Получаем IC данные из временного хранилища
            ic_data = interaction.client.ic_forms.get(self.user_id)
            if not ic_data:
                await interaction.response.send_message(
                    "❌ Ошибка: данные IC формы не найдены. Пожалуйста, начните заново.",
                    ephemeral=True
                )
                return
            
            # Проверяем формат даты рождения
            try:
                day, month, year = map(int, self.birthday.value.split('.'))
                birthday_date = datetime.date(year, month, day)
                
                # Проверяем что дата не в будущем
                if birthday_date > datetime.date.today():
                    await interaction.response.send_message(
                        "❌ Дата рождения не может быть в будущем!",
                        ephemeral=True
                    )
                    return
                    
                # Проверяем что год разумный
                current_year = datetime.date.today().year
                if year < current_year - 100 or year > current_year - 10:
                    await interaction.response.send_message(
                        "❌ Пожалуйста, укажите реальную дату рождения!",
                        ephemeral=True
                    )
                    return
                    
            except ValueError:
                await interaction.response.send_message(
                    "❌ Неверный формат даты рождения. Используйте: ДД.ММ.ГГГГ",
                    ephemeral=True
                )
                return
            
            # Сохраняем OOC данные
            ooc_data = {
                'name': self.name.value,
                'game_time': self.game_time.value,
                'timezone': self.timezone.value,
                'birthday': self.birthday.value,
                'about': self.about.value
            }
            
            # Сохраняем полную заявку в базу
            await db.save_application(
                interaction.user.id,
                str(interaction.user),
                ic_data,
                ooc_data
            )
            
            # СОХРАНЯЕМ ДЕНЬ РОЖДЕНИЯ В БАЗУ ДАННЫХ
            await db.save_birthday(
                interaction.user.id,
                str(interaction.user),
                self.birthday.value
            )
            
            # ОТПРАВЛЯЕМ СООБЩЕНИЕ В КАНАЛ ДНЕЙ РОЖДЕНИЙ
            await self.send_birthday_announcement(interaction, self.birthday.value)
            
            # Удаляем временные данные
            if self.user_id in interaction.client.ic_forms:
                del interaction.client.ic_forms[self.user_id]
            
            # Отправляем заявку в канал рассмотрения
            await self.send_application_to_review(interaction, ic_data, ooc_data)
            
            # Отправляем сообщение в ЛС пользователю о подаче заявки
            await self.send_application_dm(interaction.user)
            
            # Подтверждение пользователю
            success_embed = discord.Embed(
                title="✅ Заявка отправлена!",
                description="Ваша заявка успешно отправлена на рассмотрение. Ожидайте ответа в личных сообщениях.",
                color=COLORS["SUCCESS"]
            )
            success_embed.set_footer(text="Ocean Family")
            await interaction.response.send_message(embed=success_embed, ephemeral=True)
            
        except Exception as e:
            print(f"❌ Ошибка при сохранении заявки: {e}")
            await interaction.response.send_message(
                "❌ Произошла ошибка при отправке заявки. Пожалуйста, попробуйте позже.",
                ephemeral=True
            )

    async def send_birthday_announcement(self, interaction: discord.Interaction, birthday: str):
        """Отправляет минималистичное сообщение о новом дне рождения в канал ДР"""
        try:
            birthday_channel = interaction.guild.get_channel(CHANNELS["BIRTHDAYS"])
            if not birthday_channel:
                print("❌ Канал для дней рождений не найден")
                return
            
            # Парсим дату рождения
            day, month, year = map(int, birthday.split('.'))
            birthday_date = datetime.date(year, month, day)
            
            # Вычисляем возраст
            today = datetime.date.today()
            age = today.year - birthday_date.year
            
            # Корректируем возраст если день рождения еще не наступил в этом году
            if today < datetime.date(today.year, birthday_date.month, birthday_date.day):
                age -= 1
            
            next_age = age + 1
            
            # Минималистичный embed с аватаркой
            embed = discord.Embed(
                color=0x00ffff,  # Голубой цвет Ocean
                timestamp=discord.utils.utcnow()
            )
            
            # Устанавливаем аватарку пользователя как thumbnail
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            
            # Заголовок с эмодзи
            embed.title = "🎂 Новый день рождения"
            
            # Основное описание
            embed.description = (
                f"**{interaction.user.mention}**\n"
                f"`{day:02d}.{month:02d}.{year}`\n"
                f"→ **{next_age} лет**"
            )
            
            # Footer с временем
            embed.set_footer(
                text=f"Добавлено • {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}",
                icon_url=interaction.client.user.display_avatar.url
            )
            
            await birthday_channel.send(embed=embed)
            print(f"✅ Сообщение о дне рождения отправлено в канал для {interaction.user}")
            
        except Exception as e:
            print(f"❌ Ошибка отправки сообщения о дне рождения: {e}")

    async def send_application_dm(self, user):
        """Отправляет сообщение в ЛС о подаче заявки"""
        try:
            embed = discord.Embed(
                title="Вы оставили заявку",
                description="После рассмотрения Вам придет уведомление",
                color=COLORS["INFO"]
            )
            embed.set_footer(text="Ocean Bot")
            
            await user.send(embed=embed)
            print(f"✅ Уведомление о подаче заявки отправлено в ЛС для {user}")
            
        except Exception as e:
            print(f"❌ Не удалось отправить ЛС о подаче заявки: {e}")

    async def send_application_to_review(self, interaction: discord.Interaction, ic_data: dict, ooc_data: dict):
        """Отправляет заявку в канал для рассмотрения"""
        try:
            review_channel = interaction.guild.get_channel(CHANNELS["APPLICATIONS_REVIEW"])
            if not review_channel:
                print("❌ Канал для рассмотрения заявок не найден")
                return
            
            # Создаем embed заявки
            embed = discord.Embed(
                title=f"📨 Новая заявка от {interaction.user.display_name}",
                color=COLORS["OCEAN"],
                timestamp=discord.utils.utcnow()
            )
            
            # IC информация
            embed.add_field(
                name="🎮 **IC Информация**",
                value=(
                    f"**Никнейм:** {ic_data['nickname']}\n"
                    f"**Паспорт:** {ic_data['passport']}\n"
                    f"**Телефон:** {ic_data['phone']}\n"
                    f"**Военный билет:** {ic_data['military_id']}\n"
                    f"**Опыт:** {ic_data['experience']}"
                ),
                inline=False
            )
            
            # OOC информация
            embed.add_field(
                name="👤 **OOC Информация**",
                value=(
                    f"**Имя:** {ooc_data['name']}\n"
                    f"**Время в игре:** {ooc_data['game_time']}\n"
                    f"**Часовой пояс:** {ooc_data['timezone']}\n"
                    f"**Дата рождения:** {ooc_data['birthday']}\n"
                    f"**О себе:** {ooc_data['about']}"
                ),
                inline=False
            )
            
            embed.add_field(
                name="📊 **Информация о пользователе**",
                value=f"**Discord:** {interaction.user.mention}\n**ID:** {interaction.user.id}",
                inline=False
            )
            
            # Добавляем фото Ocean
            if "FAMILY_LOGO" in IMAGES:
                embed.set_image(url=IMAGES["FAMILY_LOGO"])
            embed.set_footer(text=f"Заявка #{interaction.user.id} • Ocean Family")
            
            # Создаем view для управления заявкой
            view = ApplicationReviewView(interaction.user.id, ic_data['nickname'])
            
            # Отправляем сообщение с тегами ролей Owner и REC
            role_mentions = f"<@&{ROLES['OWNER']}> <@&{ROLES['REC']}>"
            await review_channel.send(content=role_mentions, embed=embed, view=view)
            
            print(f"✅ Заявка отправлена на рассмотрение для {interaction.user}")
            
        except Exception as e:
            print(f"❌ Ошибка отправки заявки на рассмотрение: {e}")

class ApplicationReviewView(ui.View):
    def __init__(self, user_id: int, nickname: str):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.nickname = nickname

    @ui.button(label='✅ Принять', style=discord.ButtonStyle.success, custom_id='accept_app')
    async def accept_app(self, interaction: discord.Interaction, button: ui.Button):
        # Проверяем права
        if not any(role.id in [ROLES["REC"], ROLES["OWNER"]] for role in interaction.user.roles):
            await interaction.response.send_message("❌ У вас нет прав для обработки заявок!", ephemeral=True)
            return
        
        try:
            # Выдача роли Ocean Academy
            member = interaction.guild.get_member(self.user_id)
            if member:
                academy_role = interaction.guild.get_role(ROLES["OCEAN_ACADEMY"])
                if academy_role:
                    await member.add_roles(academy_role)
                
                # Убираем роль Guest если есть
                guest_role = interaction.guild.get_role(ROLES["GUEST"])
                if guest_role and guest_role in member.roles:
                    await member.remove_roles(guest_role)
            
            # Отправляем сообщение в ЛС о принятии заявки
            await self.send_acceptance_dm(interaction)
            
            # Обновляем сообщение с заявкой
            original_embed = interaction.message.embeds[0]
            original_embed.color = COLORS["SUCCESS"]
            original_embed.title = f"✅ Заявка одобрена - {self.nickname}"
            original_embed.add_field(
                name="✅ Одобрено",
                value=f"Заявка одобрена {interaction.user.mention}",
                inline=False
            )
            
            await interaction.response.edit_message(embed=original_embed, view=None)
            
        except Exception as e:
            print(f"❌ Ошибка при принятии заявки: {e}")
            await interaction.response.send_message("❌ Произошла ошибка при обработке заявки.", ephemeral=True)

    async def send_acceptance_dm(self, interaction: discord.Interaction):
        """Отправляет сообщение в ЛС о принятии заявки"""
        try:
            user = await interaction.guild.fetch_member(self.user_id)
            
            embed = discord.Embed(
                title="Заявка в семью Ocean одобрена!",
                description=f"Заявку одобрил: {interaction.user.mention}",
                color=COLORS["SUCCESS"]
            )
            
            await user.send(embed=embed)
            print(f"✅ Уведомление о принятии заявки отправлено в ЛС для {user}")
            
        except Exception as e:
            print(f"❌ Не удалось отправить ЛС о принятии заявки: {e}")

    @ui.button(label='❌ Отклонить', style=discord.ButtonStyle.danger, custom_id='reject_app')
    async def reject_app(self, interaction: discord.Interaction, button: ui.Button):
        if not any(role.id in [ROLES["REC"], ROLES["OWNER"]] for role in interaction.user.roles):
            await interaction.response.send_message("❌ У вас нет прав для обработки заявок!", ephemeral=True)
            return
        
        try:
            # Отправляем сообщение в ЛС об отклонении
            await self.send_rejection_dm(interaction)
            
            # Обновляем сообщение с заявкой
            original_embed = interaction.message.embeds[0]
            original_embed.color = COLORS["ERROR"]
            original_embed.title = f"❌ Заявка отклонена - {self.nickname}"
            original_embed.add_field(
                name="❌ Отклонено",
                value=f"Заявка отклонена {interaction.user.mention}",
                inline=False
            )
            
            await interaction.response.edit_message(embed=original_embed, view=None)
            
        except Exception as e:
            print(f"❌ Ошибка при отклонении заявки: {e}")
            await interaction.response.send_message("❌ Произошла ошибка при обработке заявки.", ephemeral=True)

    async def send_rejection_dm(self, interaction: discord.Interaction):
        """Отправляет сообщение в ЛС об отклонении заявки"""
        try:
            user = await interaction.guild.fetch_member(self.user_id)
            
            embed = discord.Embed(
                title="Заявка в семью Ocean отклонена",
                description=f"Заявку отклонил: {interaction.user.mention}",
                color=COLORS["ERROR"]
            )
            embed.add_field(
                name="💡 Причина", 
                value="В данный момент вы не подходите под наши требования.",
                inline=False
            )
            embed.add_field(
                name="🔄 Можно ли подать снова?", 
                value="Да, через 30 дней вы можете подать заявку снова.",
                inline=True
            )
            
            await user.send(embed=embed)
            print(f"✅ Уведомление об отклонении заявки отправлено в ЛС для {user}")
            
        except Exception as e:
            print(f"❌ Не удалось отправить ЛС об отклонении заявки: {e}")

class ContinueToOOCView(ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id

    @ui.button(label='📝 Продолжить заполнение', style=discord.ButtonStyle.primary, emoji='➡️')
    async def continue_button(self, interaction: discord.Interaction, button: ui.Button):
        # Проверяем что пользователь тот же
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Эта кнопка не для вас!", ephemeral=True)
            return
        
        # Открываем OOC форму
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
        # Регистрируем персистентные view
        self.bot.add_view(ApplyButtonView())
        self.bot.add_view(ApplicationReviewView(0, ""))
        print("✅ Views зарегистрированы")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Выдача роли Guest и приветствие"""
        try:
            # Выдаем роль Guest
            guest_role = member.guild.get_role(ROLES["GUEST"])
            if guest_role:
                await member.add_roles(guest_role)
                print(f"✅ Выдана роль Guest пользователю {member}")
            
            # Отправляем приветственное сообщение
            await self.send_welcome_message(member)
            
        except Exception as e:
            print(f"❌ Ошибка при приветствии пользователя: {e}")

    async def send_welcome_message(self, member):
        """Отправляет приветственное сообщение в канал"""
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
                
                # Добавляем фото если есть
                if "WELCOME_BANNER" in IMAGES:
                    embed.set_image(url=IMAGES["WELCOME_BANNER"])
                
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text="Ocean Family")
                
                await welcome_channel.send(embed=embed)
                print(f"✅ Приветственное сообщение отправлено для {member}")
                
        except Exception as e:
            print(f"❌ Ошибка отправки приветственного сообщения: {e}")

    @commands.command(name="setup_apply")
    @commands.has_any_role(ROLES["REC"], ROLES["OWNER"])
    async def setup_apply(self, ctx):
        """Установить сообщение с формой для вступления"""
        try:
            applications_channel = ctx.guild.get_channel(CHANNELS["APPLICATIONS"])
            if not applications_channel:
                await ctx.send("❌ Канал для заявок не найден!", delete_after=10)
                return
            
            # Очищаем предыдущие сообщения
            try:
                await applications_channel.purge(limit=10)
            except:
                pass
            
            # Основное сообщение с фото и текстом
            embed_main = discord.Embed(color=0x2b2d31)
            
            # Добавляем фото если есть
            if "WELCOME_BANNER" in IMAGES:
                embed_main.set_image(url=IMAGES["WELCOME_BANNER"])
            
            # Добавляем текст под фото
            embed_main.add_field(
                name="",
                value="**Форма для вступления**\n\nНажмите на кнопку ниже, чтобы заполнить форму.",
                inline=False
            )
            
            # Отправляем сообщения
            await applications_channel.send(embed=embed_main)
            await applications_channel.send(view=ApplyButtonView())
            
            # Сообщение с названием семьи
            embed_family = discord.Embed(
                description="**Ocean FamQ**",
                color=0x2b2d31
            )
            await applications_channel.send(embed=embed_family)
            
            await ctx.send("✅ Форма для вступления установлена!", delete_after=10)
            
        except Exception as e:
            print(f"❌ Ошибка установки формы: {e}")
            await ctx.send(f"❌ Ошибка при установке формы: {e}", delete_after=10)

    @commands.command(name="test_form")
    @commands.has_any_role(ROLES["REC"], ROLES["OWNER"])
    async def test_form(self, ctx):
        """Тестирование формы заявки"""
        try:
            await ctx.send("Открываю тестовую форму...", delete_after=10)
            modal = ICForm()
            await ctx.send_modal(modal)
        except Exception as e:
            print(f"❌ Ошибка тестирования формы: {e}")
            await ctx.send("❌ Ошибка при открытии формы!", delete_after=10)

    @commands.command(name="test_welcome")
    @commands.has_any_role(ROLES["REC"], ROLES["OWNER"])
    async def test_welcome(self, ctx):
        """Тестирование приветственного сообщения"""
        try:
            await self.send_welcome_message(ctx.author)
            await ctx.send("✅ Тестовое приветственное сообщение отправлено!", delete_after=10)
        except Exception as e:
            print(f"❌ Ошибка отправки приветственного сообщения: {e}")
            await ctx.send("❌ Ошибка при отправке сообщения!", delete_after=10)

async def setup(bot):
    await bot.add_cog(Applications(bot))