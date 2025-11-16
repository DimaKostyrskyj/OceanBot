# contracts.py - ИСПРАВЛЕННЫЙ ФАЙЛ
import discord
from discord.ext import commands
from discord import ui
from utils.database import Database
from utils.config import ROLES, CHANNELS, COLORS
import datetime
import asyncio

db = Database()

class ContractCreationModal(ui.Modal, title='📋 Создание контракта'):
    def __init__(self):
        super().__init__(timeout=300)

    title_input = ui.TextInput(
        label='Название контракта',
        placeholder='Например: Дальний конвой',
        max_length=100,
        required=True
    )
    
    description = ui.TextInput(
        label='Описание контракта',
        style=discord.TextStyle.paragraph,
        placeholder='Опишите детали контракта...',
        max_length=500,
        required=False
    )
    
    time_to_complete = ui.TextInput(
        label='Время на выполнение',
        placeholder='Например: 2 часа, 30 минут, 1 день',
        max_length=50,
        required=True
    )
    
    duration = ui.TextInput(
        label='На сколько берется контракт',
        placeholder='Например: до 20:00 сегодня, до завтра, на 3 дня',
        max_length=50,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Рассчитываем время окончания (4 часа для регистрации)
            registration_ends = datetime.datetime.now() + datetime.timedelta(hours=4)
            
            # Создаем контракт в базе данных
            contract_id = await db.create_contract(
                self.title_input.value,
                self.description.value,
                self.duration.value,
                self.time_to_complete.value,
                registration_ends.isoformat(),
                0,
                interaction.user.id,
                "general"
            )
            
            if not contract_id:
                await interaction.response.send_message("❌ Ошибка при создании контракта!", ephemeral=True)
                return
            
            # Создаем embed контракта
            embed = discord.Embed(
                title=f"📋 {self.title_input.value}",
                description=self.description.value if self.description.value else "Описание отсутствует",
                color=COLORS["INFO"],
                timestamp=datetime.datetime.now()
            )
            
            embed.add_field(
                name="**⏱️ Время на выполнение:**",
                value=self.time_to_complete.value,
                inline=False
            )
            
            embed.add_field(
                name="**🕒 Длительность:**",
                value=self.duration.value,
                inline=False
            )
            
            embed.add_field(
                name="**⏰ На сколько берется:**",
                value=self.duration.value,
                inline=False
            )
            
            embed.add_field(
                name="**👤 Создал:**",
                value=interaction.user.mention,
                inline=False
            )
            
            embed.add_field(
                name="**📊 Участники:**",
                value="❌ Пока нет участников",
                inline=False
            )
            
            embed.add_field(
                name="**🟢 Статус:**",
                value="Открыта регистрация",
                inline=True
            )
            
            embed.set_footer(text=f"ID контракта: {contract_id}")
            
            # Создаем view для контракта
            view = ContractView(contract_id)
            
            # ОТПРАВЛЯЕМ КОНТРАКТ В КАНАЛ КОНТРАКТОВ
            contracts_channel = interaction.guild.get_channel(CHANNELS["CONTRACTS"])
            if contracts_channel:
                await contracts_channel.send(embed=embed, view=view)
                print(f"✅ Контракт создан в канале контрактов")
            
            await interaction.response.send_message(
                f"✅ Контракт \"{self.title_input.value}\" успешно создан в <#{CHANNELS['CONTRACTS']}>!",
                ephemeral=True
            )
            
        except Exception as e:
            print(f"❌ Ошибка при создании контракта: {e}")
            await interaction.response.send_message(
                f"❌ Ошибка при создании контракта: {str(e)}",
                ephemeral=True
            )

class CreateContractView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label='🚀 Создать контракт', style=discord.ButtonStyle.primary, custom_id='create_contract_button')
    async def create_contract(self, interaction: discord.Interaction, button: ui.Button):
        # Проверяем права
        required_role_ids = [ROLES["ORG"], ROLES["OWNER"]]
        user_role_ids = [role.id for role in interaction.user.roles]
        
        if not any(role_id in user_role_ids for role_id in required_role_ids):
            await interaction.response.send_message("❌ У вас нет прав для создания контрактов!", ephemeral=True)
            return
        
        await interaction.response.send_modal(ContractCreationModal())

class ContractView(ui.View):
    def __init__(self, contract_id: int):
        super().__init__(timeout=None)
        self.contract_id = contract_id
        self.registration_open = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True

    @ui.button(label='📝 Записаться', style=discord.ButtonStyle.success, custom_id='contract_join')
    async def join_contract(self, interaction: discord.Interaction, button: ui.Button):
        try:
            if not self.registration_open:
                await interaction.response.send_message("❌ Регистрация на этот контракт закрыта!", ephemeral=True)
                return
            
            # Проверяем, не записан ли уже пользователь
            participants = await db.get_contract_participants(self.contract_id)
            if any(p[1] == interaction.user.id for p in participants):
                await interaction.response.send_message("❌ Вы уже записаны на этот контракт!", ephemeral=True)
                return
            
            # Записываем пользователя
            success = await db.add_contract_participant(self.contract_id, interaction.user.id, str(interaction.user))
            
            if success:
                # Обновляем список участников
                await self.update_participants_list(interaction)
                await interaction.response.send_message("✅ Вы успешно записались на контракт!", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Ошибка при записи на контракт!", ephemeral=True)
                
        except Exception as e:
            print(f"❌ Ошибка в join_contract: {e}")
            await interaction.response.send_message("❌ Ошибка взаимодействия с контрактом", ephemeral=True)

    @ui.button(label='🚪 Выписаться', style=discord.ButtonStyle.danger, custom_id='contract_leave')
    async def leave_contract(self, interaction: discord.Interaction, button: ui.Button):
        try:
            if not self.registration_open:
                await interaction.response.send_message("❌ Регистрация на этот контракт закрыта!", ephemeral=True)
                return
            
            # Проверяем, записан ли пользователь
            participants = await db.get_contract_participants(self.contract_id)
            if not any(p[1] == interaction.user.id for p in participants):
                await interaction.response.send_message("❌ Вы не записаны на этот контракт!", ephemeral=True)
                return
            
            # Удаляем пользователя
            success = await db.remove_contract_participant(self.contract_id, interaction.user.id)
            
            if success:
                # Обновляем список участников
                await self.update_participants_list(interaction)
                await interaction.response.send_message("✅ Вы выписались из контракта!", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Ошибка при выходе из контракта!", ephemeral=True)
                
        except Exception as e:
            print(f"❌ Ошибка в leave_contract: {e}")
            await interaction.response.send_message("❌ Ошибка взаимодействия с контрактом", ephemeral=True)

    @ui.button(label='▶️ Начать', style=discord.ButtonStyle.primary, custom_id='contract_start')
    async def start_contract(self, interaction: discord.Interaction, button: ui.Button):
        try:
            # Проверяем права
            required_role_ids = [ROLES["ORG"], ROLES["OWNER"]]
            user_role_ids = [role.id for role in interaction.user.roles]
            
            if not any(role_id in user_role_ids for role_id in required_role_ids):
                await interaction.response.send_message("❌ У вас нет прав для начала контракта!", ephemeral=True)
                return
            
            # Закрываем регистрацию
            self.registration_open = False
            
            # Получаем данные контракта и участников
            contract = await db.get_contract_by_id(self.contract_id)
            participants = await db.get_contract_participants(self.contract_id)
            
            if not contract:
                await interaction.response.send_message("❌ Контракт не найден!", ephemeral=True)
                return
            
            # СОЗДАЕМ ВЕТКУ
            await self.create_contract_thread(interaction, contract, participants)
            
            # Обновляем статус в сообщении
            await self.update_contract_status(interaction, "🟡 В процессе")
            
            participant_count = len(participants) if participants else 0
            await interaction.response.send_message(
                f"✅ Контракт начат! Создана ветка для {participant_count} участников.", 
                ephemeral=True
            )
            
        except Exception as e:
            print(f"❌ Ошибка начала контракта: {e}")
            await interaction.response.send_message(f"❌ Ошибка при начале контракта: {str(e)}", ephemeral=True)

    async def create_contract_thread(self, interaction: discord.Interaction, contract, participants):
        """Создает ветку для контракта"""
        try:
            # Распаковываем данные контракта
            contract_id, title, description, duration, time_to_complete, expires_at, required_count, created_by, created_at, status, contract_type = contract
            
            # Создаем ветку в канале контрактов
            contracts_channel = interaction.guild.get_channel(CHANNELS["CONTRACTS"])
            if contracts_channel and interaction.message:
                # Создаем ветку
                thread = await interaction.message.create_thread(
                    name=f"🚀 {title}",
                    auto_archive_duration=60  # 1 час
                )
                
                # Добавляем участников в ветку
                participant_mentions = []
                for participant in participants:
                    user_id = participant[1]
                    try:
                        member = interaction.guild.get_member(user_id)
                        if member:
                            await thread.add_user(member)
                            participant_mentions.append(member.mention)
                    except Exception as e:
                        print(f"❌ Не удалось добавить участника {user_id} в ветку: {e}")
                
                # Отправляем приветственное сообщение в ветку
                welcome_embed = discord.Embed(
                    title=f"🚀 Контракт начался!",
                    description=f"Контракт **\"{title}\"** начался!",
                    color=COLORS["SUCCESS"]
                )
                
                welcome_embed.add_field(
                    name="📋 Информация",
                    value=(
                        f"**Название:** {title}\n"
                        f"**Описание:** {description or 'Не указано'}\n"
                        f"**Время на выполнение:** {time_to_complete}\n"  # Используем time_to_complete из базы
                        f"**На сколько берется:** {duration}"
                    ),
                    inline=False
                )
                
                if participant_mentions:
                    welcome_embed.add_field(
                        name="👥 Участники",
                        value="\n".join(participant_mentions),
                        inline=False
                    )
                
                welcome_embed.add_field(
                    name="⏰ Время начала",
                    value=f"<t:{int(datetime.datetime.now().timestamp())}:F>",
                    inline=True
                )
                
                await thread.send(
                    content=" ".join(participant_mentions) if participant_mentions else "",
                    embed=welcome_embed
                )
                
                print(f"✅ Создана ветка для контракта {title}")
                        
        except Exception as e:
            print(f"❌ Ошибка создания ветки: {e}")

    async def update_participants_list(self, interaction: discord.Interaction):
        """Обновляет список участников в сообщении"""
        try:
            participants = await db.get_contract_participants(self.contract_id)
            
            # Формируем список участников с ТЕГАМИ (упоминаниями)
            participant_mentions = []
            for participant in participants:
                user_id = participant[1]
                try:
                    member = interaction.guild.get_member(user_id)
                    if member:
                        participant_mentions.append(member.mention)
                except:
                    # Если не удалось получить участника, используем упоминание по ID
                    participant_mentions.append(f"<@{user_id}>")
            
            # Форматируем участников с упоминаниями
            if participant_mentions:
                participants_text = "\n".join([f"• {mention}" for mention in participant_mentions])
            else:
                participants_text = "❌ Пока нет участников"
            
            # Обновляем сообщение
            if interaction.message:
                embed = interaction.message.embeds[0]
                
                # Обновляем поле участников
                for i, field in enumerate(embed.fields):
                    if "участники" in field.name.lower():
                        embed.set_field_at(
                            i,
                            name=f"**📊 Участники:**",
                            value=participants_text,
                            inline=field.inline
                        )
                        break
                
                await interaction.message.edit(embed=embed)
                        
        except Exception as e:
            print(f"❌ Ошибка обновления списка участников: {e}")

    async def update_contract_status(self, interaction: discord.Interaction, status: str):
        """Обновляет статус контракта"""
        try:
            if interaction.message:
                embed = interaction.message.embeds[0]
                
                # Обновляем статус
                for i, field in enumerate(embed.fields):
                    if "статус" in field.name.lower():
                        embed.set_field_at(
                            i,
                            name=field.name,
                            value=status,
                            inline=field.inline
                        )
                        break
                
                await interaction.message.edit(embed=embed)
                        
        except Exception as e:
            print(f"❌ Ошибка обновления статуса: {e}")

class Contracts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # Инициализация базы данных
        await db.init_db()
        
        # РЕГИСТРИРУЕМ ФИКСИРОВАННУЮ КНОПКУ СОЗДАНИЯ КОНТРАКТОВ
        self.bot.add_view(CreateContractView())
        print("✅ Фиксированная кнопка создания контрактов зарегистрирована")
        
        # РЕГИСТРИРУЕМ ФИКСИРОВАННЫЕ КНОПКИ ДЛЯ АКТИВНЫХ КОНТРАКТОВ
        try:
            active_contracts = await db.get_active_contracts()
            print(f"🔍 Найдено {len(active_contracts)} активных контрактов для регистрации")
            
            for contract in active_contracts:
                contract_id = contract[0]
                # Регистрируем view для каждого активного контракта
                view = ContractView(contract_id)
                self.bot.add_view(view)
                print(f"✅ Зарегистрированы фиксированные кнопки для контракта #{contract_id}")
                
        except Exception as e:
            print(f"❌ Ошибка регистрации view контрактов: {e}")

    @commands.hybrid_command(name="setup_contracts", description="Установить фиксированную кнопку создания контрактов")
    @commands.has_any_role(ROLES["ORG"], ROLES["OWNER"])
    async def setup_contracts(self, ctx):
        """Установка фиксированной кнопки создания контрактов"""
        try:
            print(f"🔧 Вызвана команда setup_contracts пользователем {ctx.author}")
            
            # КНОПКА В КАНАЛЕ #начать-контракт
            start_channel = ctx.guild.get_channel(CHANNELS["CONTRACTS_START"])
            print(f"🔍 Поиск канала с ID: {CHANNELS['CONTRACTS_START']}")
            
            if not start_channel:
                print("❌ Канал не найден")
                await ctx.send("❌ Канал для начала контрактов не найден!", ephemeral=True)
                return
            
            print(f"✅ Канал найден: {start_channel.name}")
            
            # Очищаем предыдущие сообщения в канале начала
            try:
                deleted = await start_channel.purge(limit=10)
                print(f"✅ Очищено {len(deleted)} сообщений в канале начала контрактов")
            except Exception as e:
                print(f"⚠️ Не удалось очистить канал начала: {e}")
            
            # Создаем embed с инструкцией для канала начала
            embed = discord.Embed(
                title="🚀 Создание контракта",
                description="Нажмите кнопку ниже чтобы создать новый контракт",
                color=COLORS["OCEAN"]
            )
            embed.add_field(
                name="📋 Как использовать:",
                value=(
                    "1. **Нажмите** кнопку 'Создать контракт'\n"
                    "2. **Заполните** форму с названием и описанием\n" 
                    "3. **Контракт появится** в канале <#{0}>\n"
                    "4. **Участники** записываются кнопками в контракте\n"
                    "5. **Нажмите 'Начать'** для создания ветки с участниками"
                ).format(CHANNELS["CONTRACTS"]),
                inline=False
            )
            
            # ОТПРАВЛЯЕМ ФИКСИРОВАННУЮ КНОПКУ В КАНАЛ #начать-контракт
            message = await start_channel.send(embed=embed, view=CreateContractView())
            print(f"✅ Фиксированная кнопка отправлена. ID сообщения: {message.id}")
            
            await ctx.send(
                f"✅ Фиксированная кнопка установлена в <#{CHANNELS['CONTRACTS_START']}>\n"
                f"📋 Контракты будут создаваться в <#{CHANNELS['CONTRACTS']}>",
                ephemeral=True
            )
            
        except Exception as e:
            print(f"❌ Ошибка установки кнопки: {e}")
            await ctx.send(f"❌ Ошибка при установке кнопки: {e}", ephemeral=True)

    @commands.hybrid_command(name="test_contract", description="Тестовая команда для контрактов")
    async def test_contract(self, ctx):
        """Тестовая команда"""
        try:
            await ctx.send("✅ Тестовая команда работает!", ephemeral=True)
            
            # Проверяем доступ к каналам
            contracts_channel = ctx.guild.get_channel(CHANNELS["CONTRACTS"])
            start_channel = ctx.guild.get_channel(CHANNELS["CONTRACTS_START"])
            
            if contracts_channel:
                await ctx.send(f"✅ Канал контрактов найден: #{contracts_channel.name}", ephemeral=True)
            else:
                await ctx.send("❌ Канал контрактов не найден", ephemeral=True)
                
            if start_channel:
                await ctx.send(f"✅ Канал начала найден: #{start_channel.name}", ephemeral=True)
            else:
                await ctx.send("❌ Канал начала не найден", ephemeral=True)
                
        except Exception as e:
            await ctx.send(f"❌ Ошибка: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Contracts(bot))