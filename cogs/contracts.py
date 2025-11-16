# contracts.py - ОБНОВЛЕННЫЙ ФАЙЛ
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
        super().__init__(timeout=None)

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
    
    duration = ui.TextInput(
        label='Длительность',
        placeholder='Например: 2ч 30мин',
        max_length=50,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Рассчитываем время окончания
            expires_at = datetime.datetime.now() + datetime.timedelta(hours=4)
            
            # Создаем контракт в базе данных - УБРАТЬ contract_type
            contract_id = await db.create_contract(
                self.title_input.value,
                self.description.value,
                self.duration.value,
                expires_at.isoformat(),
                0,  # required_count
                interaction.user.id,
                "general"  # contract_type по умолчанию
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
            
            embed.add_field(name="**⏱️ Длительность:**", value=self.duration.value, inline=True)
            embed.add_field(name="**⏰ Действует до:**", value=f"<t:{int(expires_at.timestamp())}:R>", inline=True)
            embed.add_field(name="**👤 Создал:**", value=interaction.user.mention, inline=True)
            
            embed.add_field(name="**📊 Участники:**", value="❌ Пока нет участников", inline=False)
            embed.add_field(name="**🟢 Статус:**", value="Открыта регистрация", inline=True)
            
            embed.set_footer(text=f"ID контракта: {contract_id}")
            
            # Создаем view для контракта
            view = ContractView(contract_id)
            
            # Отправляем сообщение в канал контрактов
            contracts_channel = interaction.guild.get_channel(CHANNELS["CONTRACTS"])
            if contracts_channel:
                message = await contracts_channel.send(embed=embed, view=view)
                print(f"✅ Контракт создан в канале контрактов")
            
            await interaction.response.send_message(
                f"✅ Контракт \"{self.title_input.value}\" успешно создан!",
                ephemeral=True
            )
            
        except Exception as e:
            print(f"❌ Ошибка при создании контракта: {e}")
            await interaction.response.send_message(
                f"❌ Ошибка при создании контракта: {str(e)}",
                ephemeral=True
            )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Рассчитываем время окончания
            expires_at = datetime.datetime.now() + datetime.timedelta(hours=4)
            
            # Создаем контракт в базе данных
            contract_id = await db.create_contract(
                self.title_input.value,
                self.description.value,
                self.duration.value,
                expires_at.isoformat(),
                0,  # Убрали количество участников
                interaction.user.id,
                self.contract_type
            )
            
            if not contract_id:
                await interaction.response.send_message("❌ Ошибка при создании контракта!", ephemeral=True)
                return
            
            # Создаем view для контракта
            view = ContractView(contract_id, self.contract_type)
            
            # Создаем embed контракта
            embed = discord.Embed(
                title=f"📋 {self.title_input.value}",
                description=self.description.value if self.description.value else "Описание отсутствует",
                color=COLORS["INFO"],
                timestamp=datetime.datetime.now()
            )
            
            embed.add_field(name="**⏱️ Длительность:**", value=self.duration.value, inline=True)
            embed.add_field(name="**⏰ Действует до:**", value=f"<t:{int(expires_at.timestamp())}:R>", inline=True)
            
            embed.add_field(
                name="**👤 Контракт создал:**",
                value=interaction.user.mention,
                inline=False
            )
            
            embed.add_field(name="**📊 Участники:**", value="❌ Пока нет участников", inline=False)
            embed.add_field(name="**🟢 Статус:**", value="Открыта регистрация", inline=True)
            
            embed.set_footer(text=f"ID контракта: {contract_id}")
            
            # ОТПРАВЛЯЕМ ИНФОРМАЦИЮ В КАНАЛ КОНТРАКТОВ
            contracts_channel = interaction.guild.get_channel(CHANNELS["CONTRACTS"])
            if contracts_channel:
                message = await contracts_channel.send(embed=embed)
                print(f"✅ Информация о контракте отправлена в канал контрактов")
            
            # ОТПРАВЛЯЕМ КНОПКУ В КАНАЛ ЗАПУСКА КОНТРАКТОВ
            launch_channel = interaction.guild.get_channel(CHANNELS["CONTRACTS_LAUNCH"])
            if launch_channel:
                # Создаем минималистичный embed для кнопки
                launch_embed = discord.Embed(
                    title=f"🚀 {self.title_input.value}",
                    description=f"**Тип:** {'🌊 Ocean/Academy' if self.contract_type == 'general' else '📝 Контракты'}",
                    color=COLORS["INFO"]
                )
                launch_embed.set_footer(text=f"ID: {contract_id}")
                
                await launch_channel.send(embed=launch_embed, view=view)
                
                # Тегаем соответствующие роли
                if self.contract_type == "general":
                    role_mentions = f"<@&{ROLES['OCEAN_ACADEMY']}>"
                else:
                    role_mentions = f"<@&{ROLES['CONTRACTS']}>"
                
                announcement = await launch_channel.send(
                    f"{role_mentions} 🚀 **Новый контракт создан!** {interaction.user.mention} запустил контракт \"{self.title_input.value}\""
                )
                
                print(f"✅ Кнопка контракта отправлена в канал запуска")
                
                # Планируем уведомление об окончании
                async def finish_contract():
                    await asyncio.sleep(4 * 60 * 60)  # 4 часа
                    
                    try:
                        # Обновляем статус контракта
                        await db.update_contract_status(contract_id, "completed")
                        
                        # Получаем данные контракта и участников
                        contract = await db.get_contract_by_id(contract_id)
                        participants = await db.get_contract_participants(contract_id)
                        
                        # Отправляем уведомление в канал
                        participant_mentions = " ".join([f"<@{p[1]}>" for p in participants]) if participants else ""
                        
                        completed_embed = discord.Embed(
                            title="✅ Контракт завершен",
                            description=f"Контракт \"{self.title_input.value}\" завершен!",
                            color=COLORS["SUCCESS"]
                        )
                        
                        if contracts_channel:
                            await contracts_channel.send(
                                f"{participant_mentions}",
                                embed=completed_embed
                            )
                            
                    except Exception as e:
                        print(f"❌ Ошибка завершения контракта: {e}")
            
                # Запускаем задачу завершения
                asyncio.create_task(finish_contract())
            
            await interaction.response.send_message(
                f"✅ Контракт \"{self.title_input.value}\" успешно создан!\n\n"
                f"• 📋 **Информация:** <#{CHANNELS['CONTRACTS']}>\n"
                f"• 🚀 **Записаться:** <#{CHANNELS['CONTRACTS_LAUNCH']}>",
                ephemeral=True
            )
            
        except Exception as e:
            print(f"❌ Ошибка при создании контракта: {e}")
            await interaction.response.send_message(
                f"❌ Ошибка при создании контракта: {str(e)}",
                ephemeral=True
            )

class ContractTypeView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label='🌊 Ocean/Academy', style=discord.ButtonStyle.primary)
    async def general_contract(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ContractCreationModal("general"))

    @ui.button(label='📝 Контракты', style=discord.ButtonStyle.secondary)
    async def specific_contract(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ContractCreationModal("specific"))

class ContractManagementView(ui.View):
    def __init__(self, contract_id: int, parent_view: 'ContractView'):
        super().__init__(timeout=None)
        self.contract_id = contract_id
        self.parent_view = parent_view

    @ui.button(label='▶️ Начать контракт', style=discord.ButtonStyle.success)
    async def start_contract(self, interaction: discord.Interaction, button: ui.Button):
        try:
            # Закрываем регистрацию
            self.parent_view.registration_open = False
            
            # Получаем данные контракта и участников
            contract = await db.get_contract_by_id(self.contract_id)
            participants = await db.get_contract_participants(self.contract_id)
            
            if not contract:
                await interaction.response.send_message("❌ Контракт не найден!", ephemeral=True)
                return
            
            # СОЗДАЕМ ВЕТКУ ВМЕСТО ЛС
            await self.create_contract_thread(interaction, contract, participants)
            
            # Обновляем информацию в канале контрактов
            contracts_channel = interaction.guild.get_channel(CHANNELS["CONTRACTS"])
            if contracts_channel:
                # Находим сообщение с контрактом по ID
                async for message in contracts_channel.history(limit=100):
                    if message.embeds and f"ID контракта: {self.contract_id}" in message.embeds[0].footer.text:
                        embed = message.embeds[0]
                        
                        # Обновляем статус
                        for i, field in enumerate(embed.fields):
                            if "статус" in field.name.lower():
                                embed.set_field_at(
                                    i,
                                    name=field.name,
                                    value="🟡 В процессе",
                                    inline=field.inline
                                )
                                break
                        
                        await message.edit(embed=embed)
                        break
            
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
            contract_id, title, description, duration, expires_at, required_count, created_by, created_at, status, contract_type = contract
            
            # Создаем ветку в канале контрактов
            contracts_channel = interaction.guild.get_channel(CHANNELS["CONTRACTS"])
            if contracts_channel:
                # Находим сообщение с контрактом
                async for message in contracts_channel.history(limit=100):
                    if message.embeds and f"ID контракта: {self.contract_id}" in message.embeds[0].footer.text:
                        
                        # Создаем ветку
                        thread = await message.create_thread(
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
                            name="📋 Информация о контракте",
                            value=(
                                f"**Название:** {title}\n"
                                f"**Описание:** {description or 'Не указано'}\n"
                                f"**Длительность:** {duration}\n"
                                f"**Тип:** {'🌊 Ocean/Academy' if contract_type == 'general' else '📝 Контракты'}"
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
                        
                        welcome_embed.set_footer(text="Приятной игры! 🎮")
                        
                        await thread.send(
                            content=" ".join(participant_mentions) if participant_mentions else "",
                            embed=welcome_embed
                        )
                        
                        print(f"✅ Создана ветка для контракта {title}")
                        break
                        
        except Exception as e:
            print(f"❌ Ошибка создания ветки: {e}")

    @ui.button(label='⏹️ Завершить контракт', style=discord.ButtonStyle.danger)
    async def end_contract(self, interaction: discord.Interaction, button: ui.Button):
        try:
            # Закрываем регистрацию
            self.parent_view.registration_open = False
            
            # Обновляем статус в базе данных
            await db.update_contract_status(self.contract_id, "completed")
            
            # Получаем данные контракта и участников
            contract = await db.get_contract_by_id(self.contract_id)
            participants = await db.get_contract_participants(self.contract_id)
            
            # Обновляем информацию в канале контрактов
            contracts_channel = interaction.guild.get_channel(CHANNELS["CONTRACTS"])
            if contracts_channel:
                # Находим сообщение с контрактом по ID
                async for message in contracts_channel.history(limit=100):
                    if message.embeds and f"ID контракта: {self.contract_id}" in message.embeds[0].footer.text:
                        embed = message.embeds[0]
                        
                        # Обновляем статус
                        for i, field in enumerate(embed.fields):
                            if "статус" in field.name.lower():
                                embed.set_field_at(
                                    i,
                                    name=field.name,
                                    value="✅ Завершен",
                                    inline=field.inline
                                )
                                break
                        
                        await message.edit(embed=embed)
                        break
            
            participant_count = len(participants) if participants else 0
            await interaction.response.send_message(
                f"✅ Контракт завершен! Участвовало {participant_count} участников.", 
                ephemeral=True
            )
            
        except Exception as e:
            print(f"❌ Ошибка завершения контракта: {e}")
            await interaction.response.send_message(f"❌ Ошибка при завершении контракта: {str(e)}", ephemeral=True)

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
            contract_id, title, description, duration, expires_at, required_count, created_by, created_at, status, contract_type = contract
            
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
                        f"**Длительность:** {duration}"
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
            
            # Формируем список участников с ТЕГАМИ
            participant_mentions = []
            for participant in participants:
                user_id = participant[1]
                try:
                    member = interaction.guild.get_member(user_id)
                    if member:
                        participant_mentions.append(member.mention)
                except:
                    participant_mentions.append(f"<@{user_id}>")
            
            participants_text = "\n".join(participant_mentions) if participant_mentions else "❌ Пока нет участников"
            
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
        contracts_channel = ctx.guild.get_channel(CHANNELS["CONTRACTS"])
        if not contracts_channel:
            await ctx.send("❌ Канал контрактов не найден!", ephemeral=True)
            return
        
        # Очищаем предыдущие сообщения
        try:
            await contracts_channel.purge(limit=10)
            print("✅ Очищены предыдущие сообщения в канале контрактов")
        except Exception as e:
            print(f"⚠️ Не удалось очистить канал: {e}")
        
        # Создаем embed с инструкцией
        embed = discord.Embed(
            title="🚀 Система контрактов",
            description="Нажмите кнопку ниже чтобы создать новый контракт",
            color=COLORS["OCEAN"]
        )
        embed.add_field(
            name="📋 Как использовать:",
            value=(
                "1. **Создать** - нажмите кнопку ниже\n"
                "2. **Заполните** форму с названием и описанием\n" 
                "3. **Участники** записываются кнопками в контракте\n"
                "4. **Начать** - создает ветку для участников"
            ),
            inline=False
        )
        
        # ОТПРАВЛЯЕМ СООБЩЕНИЕ С ФИКСИРОВАННОЙ КНОПКОЙ
        await contracts_channel.send(embed=embed, view=CreateContractView())
        print("✅ Фиксированная кнопка создания контрактов отправлена в канал")
        
        await ctx.send("✅ Фиксированная кнопка создания контрактов установлена!", ephemeral=True)
        
    except Exception as e:
        print(f"❌ Ошибка установки кнопки: {e}")
        await ctx.send(f"❌ Ошибка при установке кнопки: {e}", ephemeral=True)

    @commands.hybrid_command(name="active_contracts", description="Показать активные контракты")
    async def active_contracts(self, ctx):
        """Показывает активные контракты"""
        try:
            contracts = await db.get_active_contracts()
            
            if not contracts:
                await ctx.send("📭 Нет активных контрактов", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="📋 Активные контракты",
                color=COLORS["INFO"]
            )
            
            for contract in contracts:
                contract_id, title, description, duration, expires_at, required_count, created_by, created_at, status, contract_type = contract
                embed.add_field(
                    name=f"#{contract_id} - {title}",
                    value=f"**Тип:** {contract_type}\n**Статус:** {status}",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Ошибка получения контрактов: {e}")
            await ctx.send("❌ Ошибка при получении контрактов", ephemeral=True)

            

async def setup(bot):
    await bot.add_cog(Contracts(bot))