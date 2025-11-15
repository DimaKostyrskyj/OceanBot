# main.py - ЗАМЕНИТЕ ВЕСЬ ФАЙЛ
import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
from utils.database import Database

# Загружаем переменные из .env файла
load_dotenv()

# Настройки бота
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents, help_command=None)
db = Database()

@bot.event
async def on_ready():
    print(f'🌊 Ocean Bot {bot.user} успешно запущен!')
    print(f'📊 Подключен к {len(bot.guilds)} серверам:')
    
    for guild in bot.guilds:
        print(f'   - {guild.name} (ID: {guild.id})')
    
    # Инициализация базы данных
    try:
        await db.init_db()
        print("✅ База данных инициализирована")
    except Exception as e:
        print(f"❌ Ошибка инициализации базы данных: {e}")
    
    # Небольшая задержка для стабилизации
    await asyncio.sleep(2)
    
    # Загрузка модулей
    loaded_cogs = 0
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f'✅ Загружен модуль: {filename[:-3]}')
                loaded_cogs += 1
            except Exception as e:
                print(f'❌ Ошибка загрузки {filename}: {e}')
    
    print(f'📦 Всего загружено модулей: {loaded_cogs}')
    
    # Синхронизация команд
    try:
        synced = await bot.tree.sync()
        print(f'✅ Синхронизировано {len(synced)} команд:')
        for cmd in synced:
            print(f'   - /{cmd.name}')
    except Exception as e:
        print(f'❌ Ошибка синхронизации команд: {e}')
    
    # Дополнительная задержка для регистрации view
    await asyncio.sleep(1)
    print("✅ Все view зарегистрированы")
    
    # Устанавливаем статус бота
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="Ocean Family 🌊"
        ),
        status=discord.Status.online
    )
    
    print("🎉 Бот полностью готов к работе!")

@bot.event
async def on_guild_join(guild):
    """При подключении к новому серверу"""
    print(f'✅ Бот добавлен на сервер: {guild.name} (ID: {guild.id})')
    
    # Ищем канал для отправки приветственного сообщения
    system_channel = guild.system_channel
    if system_channel and system_channel.permissions_for(guild.me).send_messages:
        embed = discord.Embed(
            title="🌊 Ocean Bot подключен!",
            description="Спасибо за добавление бота Ocean Family!",
            color=0x00ffff
        )
        embed.add_field(
            name="📝 Основные команды:",
            value="• `/setup_apply` - Настроить форму для вступления\n• `/create_contract` - Создать контракт",
            inline=False
        )
        embed.add_field(
            name="⚙️ Настройка:",
            value="Не забудьте настроить ID ролей и каналов в config.py",
            inline=False
        )
        embed.set_footer(text="Ocean Family")
        
        await system_channel.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    """Обработка ошибок команд"""
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ У вас недостаточно прав для выполнения этой команды.", ephemeral=True)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Не хватает аргумента: {error.param.name}", ephemeral=True)
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Неверный аргумент команды.", ephemeral=True)
    else:
        print(f"❌ Необработанная ошибка команды: {error}")
        await ctx.send("❌ Произошла ошибка при выполнении команды.", ephemeral=True)

@bot.hybrid_command(name="ping", description="Проверить задержку бота")
async def ping(ctx):
    """Проверка пинга бота"""
    latency = round(bot.latency * 1000)
    
    embed = discord.Embed(
        title="🏓 Понг!",
        description=f"Задержка бота: **{latency}мс**",
        color=0x00ff00
    )
    
    await ctx.send(embed=embed)

@bot.hybrid_command(name="bot_info", description="Информация о боте")
async def bot_info(ctx):
    """Информация о боте"""
    embed = discord.Embed(
        title="🌊 Ocean Bot Information",
        color=0x00ffff
    )
    
    embed.add_field(name="👑 Владелец", value="Ocean Family", inline=True)
    embed.add_field(name="📚 Версия", value="1.0.0", inline=True)
    embed.add_field(name="🏓 Задержка", value=f"{round(bot.latency * 1000)}мс", inline=True)
    
    embed.add_field(
        name="📊 Статистика",
        value=f"**Серверов:** {len(bot.guilds)}\n**Пользователей:** {len(bot.users)}",
        inline=False
    )
    
    embed.add_field(
        name="🛠️ Функции",
        value="• Система заявок\n• Контракты\n• Дни рождения\n• Логирование\n• Приветствия",
        inline=False
    )
    
    embed.set_footer(text="Ocean Family Bot")
    
    await ctx.send(embed=embed)

@bot.hybrid_command(name="reload", description="Перезагрузить модули бота (только для владельцев)")
@commands.is_owner()
async def reload(ctx):
    """Перезагрузка модулей бота"""
    reloaded = 0
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.reload_extension(f"cogs.{filename[:-3]}")
                reloaded += 1
            except Exception as e:
                await ctx.send(f"❌ Ошибка перезагрузки {filename}: {e}", ephemeral=True)
                return
    
    embed = discord.Embed(
        title="✅ Перезагрузка завершена",
        description=f"Успешно перезагружено {reloaded} модулей",
        color=0x00ff00
    )
    await ctx.send(embed=embed)

@bot.hybrid_command(name="clear_data", description="Очистить все данные (только для владельцев)")
@commands.is_owner()
async def clear_data(ctx):
    """Очистка всех данных (для тестирования)"""
    try:
        await db.clear_applications()
        await db.clear_birthdays()
        await db.clear_contracts()
        
        embed = discord.Embed(
            title="✅ Данные очищены",
            description="Все данные базы данных были очищены",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Ошибка очистки",
            description=f"Ошибка: {e}",
            color=0xff0000
        )
        await ctx.send(embed=embed)

async def main():
    """Основная функция запуска бота"""
    try:
        # ИСПРАВЛЕННЫЙ ТОКЕН - используем правильный формат
        token = "MTQyNTUxNDcyNTA2MzY1NTUyOA.GHpfeg.LsAyHjdcrz0dYGbW9-_zrFHCEnlqboUKc9aFpg"
        if not token:
            print("❌ Ошибка: Токен не найден.")
            return
        
        print("🚀 Запуск Ocean Bot...")
        await bot.start(token)
        
    except KeyboardInterrupt:
        print("\n🛑 Остановка бота...")
        await bot.close()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())