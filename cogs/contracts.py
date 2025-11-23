# contracts.py - УЛУЧШЕННЫЙ ДИЗАЙН КОНТРАКТОВ
import discord
from discord.ext import commands
from discord import ui
from utils.database import Database
from utils.config import ROLES, CHANNELS, COLORS
import datetime
import asyncio

db = Database()

class ContractLaunchModal(ui.Modal, title='🚀 Запуск контракта'):
    def __init__(self):
        super().__init__(timeout=300)

    title_input = ui.TextInput(
        label='Название контракта',
        placeholder='Например: Бирюзовый док',
        max_length=100,
        required=True
    )
    
    role_to_mention = ui.TextInput(
        label='Кого тегать',
        placeholder='Напишите: Ocean или Контракт',
        max_length=10,
        required=True
    )
    
    duration_and_execution = ui.TextInput(
        label='Срок действия / Длится',
        placeholder='Например: 47 часов / 2ч 30м',
        max_length=100,
        required=True
    )
    
    complete_and_chance = ui.TextInput(
        label='Выполнить за / Шанс',
        placeholder='Например: 1ч 30м / 85%',
        max_length=100,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Валидация выбора роли
            role_choice = self.role_to_mention.value.strip()
            valid_roles = ['Ocean', 'Контракт']
            
            if role_choice not in valid_roles:
                await interaction.response.send_message(
                    "❌ Неверный выбор роли! Используйте: Ocean или Контракт",
                    ephemeral=True
                )
                return
            
            # Парсим первое объединенное поле (Срок / Длится)
            duration_input = self.duration_and_execution.value
            duration_parts = [part.strip() for part in duration_input.split('/')]
            
            if len(duration_parts) != 2:
                await interaction.response.send_message(
                    "❌ Неверный формат! Используйте: Срок действия / Длится\nНапример: 47 часов / 2ч 30м",
                    ephemeral=True
                )
                return
            
            contract_duration = duration_parts[0]
            execution_time = duration_parts[1]
            
            # Парсим второе объединенное поле (Выполнить / Шанс)
            complete_input = self.complete_and_chance.value
            complete_parts = [part.strip() for part in complete_input.split('/')]
            
            if len(complete_parts) != 2:
                await interaction.response.send_message(
                    "❌ Неверный формат! Используйте: Выполнить за / Шанс\nНапример: 1ч 30м / 85%",
                    ephemeral=True
                )
                return
            
            complete_for = complete_parts[0]
            chance = complete_parts[1]
            
            # Рассчитываем время окончания (48 часов для регистрации)
            registration_ends = datetime.datetime.now() + datetime.timedelta(hours=48)
            
            # Создаем контракт в базе данных
            contract_id = await db.create_contract(
                self.title_input.value,
                f"@Ocean или Контракт\nСрок действия контракта: {contract_duration}",
                execution_time,
                complete_for,
                registration_ends.isoformat(),
                0,
                interaction.user.id,
                "general"
            )
            
            if not contract_id:
                await interaction.response.send_message("❌ Ошибка при создании контракта!", ephemeral=True)
                return
            
            # Получаем информацию о тегируемой роли
            role_mention = ""
            role_name = ""

            if role_choice == "Ocean":
                # Получаем ID обеих ролей
                academy_role_id = ROLES.get("ACADEMY")
                ocean_role_id = ROLES.get("ORG")
                
                role_mentions = []
                role_names = []
                
                # Проверяем и добавляем роль Ocean Academy
                if academy_role_id:
                    academy_role = interaction.guild.get_role(academy_role_id)
                    if academy_role:
                        role_mentions.append(academy_role.mention)
                        role_names.append(academy_role.name)
                        print(f"✅ Роль Ocean Academy найдена: {academy_role.name} (ID: {academy_role_id})")
                    else:
                        print(f"❌ Роль Ocean Academy с ID {academy_role_id} не найдена на сервере")
                else:
                    print("❌ ID роли Ocean Academy не найден в конфиге")
                
                # Проверяем и добавляем роль Ocean
                if ocean_role_id:
                    ocean_role = interaction.guild.get_role(ocean_role_id)
                    if ocean_role:
                        role_mentions.append(ocean_role.mention)
                        role_names.append(ocean_role.name)
                        print(f"✅ Роль Ocean найдена: {ocean_role.name} (ID: {ocean_role_id})")
                    else:
                        print(f"❌ Роль Ocean с ID {ocean_role_id} не найдена на сервере")
                else:
                    print("❌ ID роли Ocean не найден в конфиге")
                
                # Объединяем упоминания и названия
                role_mention = " ".join(role_mentions)
                role_name = " и ".join(role_names)
                
            elif role_choice == "Контракт":
                contract_role_id = ROLES.get("CONTRACT")
                if contract_role_id:
                    role = interaction.guild.get_role(contract_role_id)
                    if role:
                        role_mention = role.mention
                        role_name = role.name
                        print(f"✅ Роль Контракт найдена: {role.name} (ID: {contract_role_id})")
                    else:
                        print(f"❌ Роль Контракт с ID {contract_role_id} не найдена на сервере")
                else:
                    print("❌ ID роли Контракт не найден в конфиге")

            print(f"🔍 Выбранная роль: {role_choice}")
            print(f"🔍 Упоминания ролей: {role_mention}")
            print(f"🔍 Названия ролей: {role_name}")
            
            # Создаем красивый embed контракта
            embed = discord.Embed(
                color=0x2b2d31,
                timestamp=datetime.datetime.now()
            )
            
            embed.title = f"📋 {self.title_input.value}"
            
            # Основная информация
            embed.description = (
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"**👤 Создал:** {interaction.user.mention}\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
            
            # Информация о контракте
            embed.add_field(
                name="⏰ Срок действия контракта:",
                value=f"{contract_duration}",
                inline=False
            )
            
            embed.add_field(
                name="🕒 Контракт длится:",
                value=f"{execution_time}",
                inline=False
            )
            
            embed.add_field(
                name="⚡ Выполнить за:",
                value=f"{complete_for}",
                inline=False
            )
            
            embed.add_field(
                name="🎲 Шанс:",
                value=f"{chance}",
                inline=False
            )
            
            # Участники
            embed.add_field(
                name="📊 Участники:",
                value="❌ Пока нет участников",
                inline=False
            )
            
            # Статус
            embed.add_field(
                name="🟢 Статус:",
                value="✅ Открыта регистрация",
                inline=False
            )
            
            embed.set_footer(
                text=f"ID контракта: {contract_id} • Ocean Family",
                icon_url=interaction.guild.icon.url if interaction.guild.icon else None
            )
            
            # Создаем view для контракта
            view = ContractView(contract_id)
            
            # Отправляем контракт в канал
            contracts_channel = interaction.guild.get_channel(CHANNELS["CONTRACTS"])
            if contracts_channel:
                content = f"{role_mention}\n\n" if role_mention else "❌ Роль для тега не найдена\n\n"
                message = await contracts_channel.send(
                    content=content,
                    embed=embed, 
                    view=view
                )
                
                print(f"✅ Контракт создан в канале контрактов")
                print(f"✅ Content сообщения: {content}")
                
                # Создаем ветку для контракта
                try:
                    thread = await message.create_thread(
                        name=f"🚀 {self.title_input.value}",
                        auto_archive_duration=1440
                    )
                    print(f"✅ Ветка создана для контракта {self.title_input.value}")
                except Exception as e:
                    print(f"❌ Ошибка создания ветки: {e}")
                
            await interaction.response.send_message(
                f"✅ Контракт \"{self.title_input.value}\" успешно создан в <#{CHANNELS['CONTRACTS']}>!" +
                (f" Тегнута роль: **{role_name}**" if role_name else f" Тегнута роль: **{role_choice}**"),
                ephemeral=True
            )
            
        except Exception as e:
            print(f"❌ Ошибка при создании контракта: {e}")
            try:
                await interaction.response.send_message(
                    f"❌ Ошибка при создании контракта: {str(e)}",
                    ephemeral=True
                )
            except:
                await interaction.followup.send(
                    f"❌ Ошибка при создании контракта: {str(e)}",
                    ephemeral=True
                )

class LaunchContractView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label='🚀 Запустить контракт', style=discord.ButtonStyle.primary, custom_id='launch_contract_button')
    async def launch_contract(self, interaction: discord.Interaction, button: ui.Button):
        try:
            required_role_ids = [ROLES["ORG"], ROLES["OWNER"]]
            user_role_ids = [role.id for role in interaction.user.roles]
            
            if not any(role_id in user_role_ids for role_id in required_role_ids):
                await interaction.response.send_message("❌ У вас нет прав для запуска контрактов!", ephemeral=True)
                return
            
            await interaction.response.send_modal(ContractLaunchModal())
            
        except Exception as e:
            print(f"❌ Ошибка в launch_contract: {e}")
            try:
                await interaction.response.send_message("❌ Ошибка взаимодействия", ephemeral=True)
            except:
                pass

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
            
            participants = await db.get_contract_participants(self.contract_id)
            if any(p[1] == interaction.user.id for p in participants):
                await interaction.response.send_message("❌ Вы уже записаны на этот контракт!", ephemeral=True)
                return
            
            success = await db.add_contract_participant(self.contract_id, interaction.user.id, str(interaction.user))
            
            if success:
                await self.update_participants_list(interaction)
                await interaction.response.send_message("✅ Вы успешно записались на контракт!", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Ошибка при записи на контракт!", ephemeral=True)
                
        except Exception as e:
            print(f"❌ Ошибка в join_contract: {e}")
            try:
                await interaction.response.send_message("❌ Ошибка взаимодействия с контрактом", ephemeral=True)
            except:
                pass

    @ui.button(label='🚪 Выписаться', style=discord.ButtonStyle.danger, custom_id='contract_leave')
    async def leave_contract(self, interaction: discord.Interaction, button: ui.Button):
        try:
            if not self.registration_open:
                await interaction.response.send_message("❌ Регистрация на этот контракт закрыта!", ephemeral=True)
                return
            
            participants = await db.get_contract_participants(self.contract_id)
            if not any(p[1] == interaction.user.id for p in participants):
                await interaction.response.send_message("❌ Вы не записаны на этот контракт!", ephemeral=True)
                return
            
            success = await db.remove_contract_participant(self.contract_id, interaction.user.id)
            
            if success:
                await self.update_participants_list(interaction)
                await interaction.response.send_message("✅ Вы выписались из контракта!", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Ошибка при выходе из контракта!", ephemeral=True)
                
        except Exception as e:
            print(f"❌ Ошибка в leave_contract: {e}")
            try:
                await interaction.response.send_message("❌ Ошибка взаимодействия с контрактом", ephemeral=True)
            except:
                pass

    @ui.button(label='▶️ Начать контракт', style=discord.ButtonStyle.primary, custom_id='contract_start')
    async def start_contract(self, interaction: discord.Interaction, button: ui.Button):
        try:
            required_role_ids = [ROLES["ORG"], ROLES["OWNER"]]
            user_role_ids = [role.id for role in interaction.user.roles]
            
            if not any(role_id in user_role_ids for role_id in required_role_ids):
                await interaction.response.send_message("❌ У вас нет прав для начала контракта!", ephemeral=True)
                return
            
            self.registration_open = False
            
            contract = await db.get_contract_by_id(self.contract_id)
            participants = await db.get_contract_participants(self.contract_id)
            
            if not contract:
                await interaction.response.send_message("❌ Контракт не найден!", ephemeral=True)
                return
            
            # Обновляем статус
            await self.update_contract_status(interaction, "🟡 В процессе")
            
            # Создаем новый view только с кнопкой "Закончить"
            new_view = ContractFinishView(self.contract_id)
            
            # Обновляем сообщение с новым view
            if interaction.message:
                await interaction.message.edit(view=new_view)
            
            participant_count = len(participants) if participants else 0
            
            await interaction.response.send_message(
                f"✅ Контракт начат! Участников: {participant_count}",
                ephemeral=True
            )
            
        except Exception as e:
            print(f"❌ Ошибка начала контракта: {e}")
            try:
                await interaction.response.send_message(f"❌ Ошибка при начале контракта: {str(e)}", ephemeral=True)
            except:
                pass

    async def update_participants_list(self, interaction: discord.Interaction):
        """Обновляет список участников в сообщении"""
        try:
            participants = await db.get_contract_participants(self.contract_id)
            
            participant_mentions = []
            for participant in participants:
                user_id = participant[1]
                try:
                    member = interaction.guild.get_member(user_id)
                    if member:
                        participant_mentions.append(member.mention)
                except:
                    participant_mentions.append(f"<@{user_id}>")
            
            # Форматируем участников БЕЗ code blocks
            if participant_mentions:
                participants_text = " ".join(participant_mentions)
            else:
                participants_text = "❌ Пока нет участников"
            
            if interaction.message:
                embed = interaction.message.embeds[0]
                
                for i, field in enumerate(embed.fields):
                    if "участники" in field.name.lower():
                        embed.set_field_at(
                            i,
                            name="📊 Участники:",
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

class ContractFinishView(ui.View):
    """View только с кнопкой 'Закончить контракт'"""
    def __init__(self, contract_id: int):
        super().__init__(timeout=None)
        self.contract_id = contract_id

    @ui.button(label='✅ Закончить контракт', style=discord.ButtonStyle.success, custom_id='contract_finish')
    async def finish_contract(self, interaction: discord.Interaction, button: ui.Button):
        try:
            required_role_ids = [ROLES["ORG"], ROLES["OWNER"]]
            user_role_ids = [role.id for role in interaction.user.roles]
            
            if not any(role_id in user_role_ids for role_id in required_role_ids):
                await interaction.response.send_message("❌ У вас нет прав для завершения контракта!", ephemeral=True)
                return
            
            contract = await db.get_contract_by_id(self.contract_id)
            participants = await db.get_contract_participants(self.contract_id)
            
            if not contract:
                await interaction.response.send_message("❌ Контракт не найден!", ephemeral=True)
                return
            
            # Обновляем статус контракта на "Завершен"
            await db.update_contract_status(self.contract_id, "completed")
            
            # Обновляем embed
            if interaction.message and interaction.message.embeds:
                embed = interaction.message.embeds[0]
                
                for i, field in enumerate(embed.fields):
                    if "статус" in field.name.lower():
                        embed.set_field_at(
                            i,
                            name=field.name,
                            value="✅ Завершен",
                            inline=field.inline
                        )
                        break
                
                # Убираем все кнопки
                await interaction.message.edit(embed=embed, view=None)
            
            participant_count = len(participants) if participants else 0
            
            await interaction.response.send_message(
                f"✅ Контракт завершен! Участников: {participant_count}",
                ephemeral=True
            )
            
        except Exception as e:
            print(f"❌ Ошибка завершения контракта: {e}")
            try:
                await interaction.response.send_message(f"❌ Ошибка при завершении контракта: {str(e)}", ephemeral=True)
            except:
                pass

class Contracts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await db.init_db()
        
        self.bot.add_view(LaunchContractView())
        print("✅ Фиксированная кнопка запуска контрактов зарегистрирована")
        
        try:
            active_contracts = await db.get_active_contracts()
            print(f"🔍 Найдено {len(active_contracts)} активных контрактов для регистрации")
            
            for contract in active_contracts:
                contract_id = contract[0]
                view = ContractView(contract_id)
                self.bot.add_view(view)
                print(f"✅ Зарегистрированы фиксированные кнопки для контракта #{contract_id}")
            
            # Регистрируем view для завершения контрактов
            self.bot.add_view(ContractFinishView(0))
            print("✅ Зарегистрирован view для завершения контрактов")
                
        except Exception as e:
            print(f"❌ Ошибка регистрации view контрактов: {e}")

    @commands.hybrid_command(name="setup_contracts", description="Установить фиксированную кнопку запуска контрактов")
    @commands.has_any_role(ROLES["ORG"], ROLES["OWNER"])
    async def setup_contracts(self, ctx):
        """Установка фиксированной кнопки запуска контрактов"""
        try:
            print(f"🔧 Вызвана команда setup_contracts пользователем {ctx.author}")
            
            launch_channel = ctx.guild.get_channel(CHANNELS["CONTRACTS_START"])
            print(f"🔍 Поиск канала с ID: {CHANNELS['CONTRACTS_START']}")
            
            if not launch_channel:
                print("❌ Канал не найден")
                await ctx.send("❌ Канал для запуска контрактов не найден!", ephemeral=True)
                return
            
            print(f"✅ Канал найден: {launch_channel.name}")
            
            try:
                deleted = await launch_channel.purge(limit=10)
                print(f"✅ Очищено {len(deleted)} сообщений в канале запуска контрактов")
            except Exception as e:
                print(f"⚠️ Не удалось очистить канал запуска: {e}")
            
            embed = discord.Embed(
                title="🚀 Запуск контракта",
                description="Нажмите кнопку ниже чтобы запустить новый контракт",
                color=COLORS["OCEAN"]
            )
            embed.add_field(
                name="📋 Как использовать:",
                value=(
                    "1. **Нажмите** кнопку 'Запустить контракт'\n"
                    "2. **Заполните** форму с информацией о контракте\n" 
                    "3. **Контракт появится** в канале <#{0}>\n"
                    "4. **Автоматически создастся ветка** для обсуждения\n"
                    "5. **Участники** записываются кнопками в контракте\n"
                    "6. **Нажмите 'Начать контракт'** для старта\n"
                    "7. **Нет ограничения** по количеству участников!"
                ).format(CHANNELS["CONTRACTS"]),
                inline=False
            )
            
            embed.add_field(
                name="🎯 Выбор тега:",
                value=(
                    "**Ocean** - тегнуть роль Ocean Academy и Ocean\n"
                    "**Контракт** - тегнуть роль Контракт"
                ),
                inline=False
            )
            
            view = LaunchContractView()
            
            message = await launch_channel.send(embed=embed, view=view)
            print(f"✅ Фиксированная кнопка отправлена. ID сообщения: {message.id}")
            
            await ctx.send(
                f"✅ Фиксированная кнопка установлена в <#{CHANNELS['CONTRACTS_START']}>\n"
                f"📋 Контракты будут создаваться в <#{CHANNELS['CONTRACTS']}>",
                ephemeral=True
            )
            
        except Exception as e:
            print(f"❌ Ошибка установки кнопки: {e}")
            await ctx.send(f"❌ Ошибка при установке кнопки: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Contracts(bot))