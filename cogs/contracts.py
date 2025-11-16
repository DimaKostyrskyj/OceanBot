# contracts.py - ПОЛНЫЙ ФАЙЛ С РАЗДЕЛЕНИЕМ КАНАЛОВ
import discord
from discord.ext import commands
from discord import ui
from utils.database import Database
from utils.config import ROLES, CHANNELS, COLORS
import datetime
import asyncio

db = Database()

class ContractCreationModal(ui.Modal, title='📋 Создание контракта'):
    def __init__(self, contract_type: str):
        super().__init__(timeout=300)
        self.contract_type = contract_type

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
    
    required_count = ui.TextInput(
        label='Количество участников',
        placeholder='Например: 4',
        max_length=2,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Рассчитываем время окончания
            expires_at = datetime.datetime.now() + datetime.timedelta(hours=4)
            
            # Создаем контракт в базе данных
            contract_id = await db.create_contracts(
                self.title_input.value,
                self.description.value,
                self.duration.value,
                expires_at.isoformat(),
                int(self.required_count.value),
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
            embed.add_field(name="**👥 Требуется игроков:**", value=f"{self.required_count.value}", inline=True)
            
            embed.add_field(
                name="**👤 Контракт создал:**",
                value=interaction.user.mention,
                inline=False
            )
            
            embed.add_field(name="**📊 Участники:** (0/{})".format(self.required_count.value), 
                          value="❌ Пока нет участников", inline=False)
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
                    description=f"**Тип:** {'🌊 Ocean/Academy' if self.contract_type == 'general' else '📝 Контракты'}\n**Участников:** 0/{self.required_count.value}",
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
                        
                        # Отправляем уведомления участникам
                        if contract and participants:
                            bot = interaction.client
                            contracts_cog = bot.get_cog("Contracts")
                            if contracts_cog:
                                await contracts_cog.send_contract_notification(contract, participants, "complete")
                        
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
        super().__init__(timeout=60)

    @ui.button(label='🌊 Ocean/Academy', style=discord.ButtonStyle.primary)
    async def general_contract(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ContractCreationModal("general"))

    @ui.button(label='📝 Контракты', style=discord.ButtonStyle.secondary)
    async def specific_contract(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ContractCreationModal("specific"))

class ContractManagementView(ui.View):
    def __init__(self, contract_id: int, parent_view: 'ContractView'):
        super().__init__(timeout=60)
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
            
            # Отправляем уведомления участникам
            contracts_cog = interaction.client.get_cog("Contracts")
            if contracts_cog and participants:
                await contracts_cog.send_contract_notification(contract, participants, "start")
            
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
                f"✅ Контракт начат! Уведомления отправлены {participant_count} участникам.", 
                ephemeral=True
            )
            
        except Exception as e:
            print(f"❌ Ошибка начала контракта: {e}")
            await interaction.response.send_message(f"❌ Ошибка при начале контракта: {str(e)}", ephemeral=True)

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
            
            if contract and participants:
                # Отправляем уведомления о завершении
                contracts_cog = interaction.client.get_cog("Contracts")
                if contracts_cog:
                    await contracts_cog.send_contract_notification(contract, participants, "complete")
            
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
                f"✅ Контракт завершен! Уведомления отправлены {participant_count} участникам.", 
                ephemeral=True
            )
            
        except Exception as e:
            print(f"❌ Ошибка завершения контракта: {e}")
            await interaction.response.send_message(f"❌ Ошибка при завершении контракта: {str(e)}", ephemeral=True)

    @ui.button(label='📨 Отправить уведомления', style=discord.ButtonStyle.secondary)
    async def send_notifications(self, interaction: discord.Interaction, button: ui.Button):
        try:
            # Получаем данные контракта и участников
            contract = await db.get_contract_by_id(self.contract_id)
            participants = await db.get_contract_participants(self.contract_id)
            
            if not contract:
                await interaction.response.send_message("❌ Контракт не найден!", ephemeral=True)
                return
            
            if not participants:
                await interaction.response.send_message("❌ На контракте нет участников!", ephemeral=True)
                return
            
            # Отправляем уведомления
            contracts_cog = interaction.client.get_cog("Contracts")
            if contracts_cog:
                await contracts_cog.send_contract_notification(contract, participants, "start")
                await interaction.response.send_message(
                    f"✅ Уведомления отправлены {len(participants)} участникам!", 
                    ephemeral=True
                )
            else:
                await interaction.response.send_message("❌ Ошибка: Cog Contracts не найден", ephemeral=True)
            
        except Exception as e:
            print(f"❌ Ошибка отправки уведомлений: {e}")
            await interaction.response.send_message(f"❌ Ошибка отправки уведомлений: {str(e)}", ephemeral=True)

class ContractView(ui.View):
    def __init__(self, contract_id: int, contract_type: str):
        super().__init__(timeout=None)
        self.contract_id = contract_id
        self.contract_type = contract_type
        self.registration_open = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Проверяет, можно ли обработать взаимодействие"""
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
                # Обновляем информацию в обоих каналах
                await self.update_contract_channels(interaction)
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
                # Обновляем информацию в обоих каналах
                await self.update_contract_channels(interaction)
                await interaction.response.send_message("✅ Вы выписались из контракта!", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Ошибка при выходе из контракта!", ephemeral=True)
                
        except Exception as e:
            print(f"❌ Ошибка в leave_contract: {e}")
            await interaction.response.send_message("❌ Ошибка взаимодействия с контрактом", ephemeral=True)

    @ui.button(label='⚙️ Управление', style=discord.ButtonStyle.primary, custom_id='contract_manage')
    async def manage_contract(self, interaction: discord.Interaction, button: ui.Button):
        try:
            # Проверяем права
            required_role_ids = [ROLES["ORG"], ROLES["OWNER"]]
            user_role_ids = [role.id for role in interaction.user.roles]
            
            if not any(role_id in user_role_ids for role_id in required_role_ids):
                await interaction.response.send_message("❌ У вас нет прав для управления контрактами!", ephemeral=True)
                return
            
            # Создаем меню управления
            embed = discord.Embed(
                title="⚙️ Управление контрактом",
                description="Выберите действие для управления контрактом",
                color=COLORS["WARNING"]
            )
            
            view = ContractManagementView(self.contract_id, self)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            print(f"❌ Ошибка в manage_contract: {e}")
            await interaction.response.send_message("❌ Ошибка взаимодействия", ephemeral=True)

    async def update_contract_channels(self, interaction: discord.Interaction):
        """Обновляет информацию о контракте в обоих каналах"""
        try:
            participants = await db.get_contract_participants(self.contract_id)
            contract = await db.get_contract_by_id(self.contract_id)
            
            if not contract:
                return
                
            contract_id, title, description, duration, expires_at, required_count, created_by, created_at, status, contract_type = contract
            
            current_count = len(participants)
            participants_text = "\n".join([f"👤 {p[2]}" for p in participants]) if participants else "❌ Пока нет участников"
            
            # Обновляем канал контрактов (полная информация)
            contracts_channel = interaction.guild.get_channel(CHANNELS["CONTRACTS"])
            if contracts_channel:
                async for message in contracts_channel.history(limit=100):
                    if message.embeds and f"ID контракта: {self.contract_id}" in message.embeds[0].footer.text:
                        embed = message.embeds[0]
                        
                        # Обновляем поле участников
                        for i, field in enumerate(embed.fields):
                            if "участники" in field.name.lower():
                                embed.set_field_at(
                                    i,
                                    name=f"**Участники:** ({current_count}/{required_count})",
                                    value=participants_text,
                                    inline=field.inline
                                )
                                break
                        
                        await message.edit(embed=embed)
                        break
            
            # Обновляем канал запуска (минималистичная информация)
            launch_channel = interaction.guild.get_channel(CHANNELS["CONTRACTS_LAUNCH"])
            if launch_channel:
                async for message in launch_channel.history(limit=100):
                    if message.embeds and f"ID: {self.contract_id}" in message.embeds[0].footer.text:
                        embed = message.embeds[0]
                        
                        # Обновляем количество участников
                        embed.description = f"**Тип:** {'🌊 Ocean/Academy' if contract_type == 'general' else '📝 Контракты'}\n**Участников:** {current_count}/{required_count}"
                        
                        await message.edit(embed=embed)
                        break
                        
        except Exception as e:
            print(f"❌ Ошибка обновления каналов контракта: {e}")

class Contracts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_contract_notification(self, contract_data, participants, notification_type="start"):
        """Отправляет уведомления участникам контракта"""
        try:
            contract_id, title, description, duration, expires_at, required_count, created_by, created_at, status, contract_type = contract_data
            
            for participant in participants:
                user_id = participant[1]  # user_id из базы данных
                user = self.bot.get_user(user_id)
                
                if user:
                    try:
                        if notification_type == "start":
                            embed = discord.Embed(
                                title="🚀 Контракт начался!",
                                description=f"Контракт **\"{title}\"** начался!",
                                color=COLORS["SUCCESS"],
                                timestamp=datetime.datetime.now()
                            )
                            
                            embed.add_field(
                                name="📋 Информация о контракте",
                                value=(
                                    f"**Название:** {title}\n"
                                    f"**Описание:** {description or 'Не указано'}\n"
                                    f"**Длительность:** {duration}\n"
                                    f"**Тип:** {'🌊 Ocean/Academy' if contract_type == 'general' else '📝 Контракты'}"
                                ),
                                inline=False
                            )
                            
                            embed.add_field(
                                name="👥 Участники",
                                value="\n".join([f"• {p[2]}" for p in participants]),
                                inline=False
                            )
                            
                            embed.add_field(
                                name="⏰ Время начала",
                                value=f"<t:{int(datetime.datetime.now().timestamp())}:F>",
                                inline=True
                            )
                            
                            embed.set_footer(text="Приятной игры! 🎮")
                            
                            message_content = (
                                "Вы записались на контракт\n"
                                "Контракт начался - удачи в выполнении!\n\n"
                                "**Ocean Bot**"
                            )
                            
                            await user.send(content=message_content, embed=embed)
                            print(f"✅ Уведомление отправлено пользователю {user.name}")
                            
                        elif notification_type == "complete":
                            embed = discord.Embed(
                                title="✅ Контракт завершен!",
                                description=f"Контракт **\"{title}\"** завершен!",
                                color=COLORS["INFO"],
                                timestamp=datetime.datetime.now()
                            )
                            
                            embed.add_field(
                                name="🎉 Благодарность",
                                value="Спасибо за участие в контракте!",
                                inline=False
                            )
                            
                            embed.set_footer(text="Ocean Bot")
                            
                            await user.send(embed=embed)
                            print(f"✅ Уведомление о завершении отправлено пользователю {user.name}")
                            
                    except discord.Forbidden:
                        print(f"❌ Не удалось отправить ЛС пользователю {user.name} (закрытые ЛС)")
                    except Exception as e:
                        print(f"❌ Ошибка отправки ЛС пользователю {user.name}: {e}")
                else:
                    print(f"⚠️ Пользователь с ID {user_id} не найден (возможно, не в кэше)")
                    
        except Exception as e:
            print(f"❌ Ошибка отправки уведомлений: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        # Инициализируем базу данных
        await db.init_db()
        
        # Регистрируем персистентные view для активных контрактов
        try:
            active_contracts = await db.get_active_contracts()
            print(f"🔍 Найдено {len(active_contracts)} активных контрактов")
            
            for contract in active_contracts:
                contract_id, title, description, duration, expires_at, required_count, created_by, created_at, status, contract_type = contract
                
                view = ContractView(contract_id, contract_type)
                self.bot.add_view(view)
                print(f"✅ Зарегистрирован view для контракта #{contract_id} - '{title}'")
                
        except Exception as e:
            print(f"❌ Ошибка регистрации view контрактов: {e}")

    @commands.hybrid_command(name="create_contract", description="Создать новый контракт")
    @commands.has_any_role(ROLES["ORG"], ROLES["OWNER"])
    async def create_contract(self, ctx):
        """Создание нового контракта"""
        try:
            embed = discord.Embed(
                title="🚀 Создание контракта",
                description="Выберите тип контракта:",
                color=COLORS["INFO"]
            )
            embed.add_field(
                name="🌊 Ocean/Academy",
                value="Для всех участников Ocean и Academy",
                inline=True
            )
            embed.add_field(
                name="📝 Контракты", 
                value="Только для участников с ролью Контракты",
                inline=True
            )
            
            view = ContractTypeView()
            await ctx.send(embed=embed, view=view)
            
        except Exception as e:
            print(f"❌ Ошибка в create_contract: {e}")
            await ctx.send(f"❌ Ошибка при создании контракта: {e}", ephemeral=True)

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
                    value=f"**Тип:** {contract_type}\n**Участников:** {required_count}\n**Статус:** {status}",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Ошибка получения контрактов: {e}")
            await ctx.send("❌ Ошибка при получении контрактов", ephemeral=True)

    @commands.hybrid_command(name="contract_stats", description="Показать статистику контрактов")
    async def contract_stats(self, ctx):
        """Показывает статистику контрактов"""
        try:
            stats = await db.get_database_stats()
            
            embed = discord.Embed(
                title="📊 Статистика контрактов",
                color=COLORS["INFO"]
            )
            
            embed.add_field(
                name="Активные контракты",
                value=stats.get('active_contracts', 0),
                inline=True
            )
            
            embed.add_field(
                name="Всего участников",
                value=stats.get('contract_participants', 0),
                inline=True
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Ошибка получения статистики: {e}")
            await ctx.send("❌ Ошибка при получении статистики", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Contracts(bot))