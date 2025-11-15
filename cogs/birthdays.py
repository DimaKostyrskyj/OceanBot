# birthdays.py - ЗАМЕНИТЕ ВЕСЬ ФАЙЛ
import discord
from discord.ext import commands, tasks
from utils.database import Database
from utils.config import CHANNELS, COLORS
import datetime

db = Database()

class Birthdays(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.birthday_check.start()

    def cog_unload(self):
        self.birthday_check.cancel()

    @tasks.loop(hours=24)
    async def birthday_check(self):
        """Ежедневная проверка дней рождений"""
        await self.check_birthdays()

    @birthday_check.before_loop
    async def before_birthday_check(self):
        await self.bot.wait_until_ready()

    async def check_birthdays(self):
        """Проверяет дни рождения и отправляет уведомления"""
        try:
            today = datetime.datetime.now().strftime('%d.%m')
            birthdays = await db.get_all_birthdays()
            
            if not birthdays:
                return
                
            for user_data in birthdays:
                if len(user_data) < 3:
                    continue
                    
                user_id, user_name, birthday = user_data[0], user_data[1], user_data[2]
                
                # Извлекаем день и месяц из даты
                try:
                    # Обрабатываем разные форматы даты
                    if '.' in birthday:
                        bday_parts = birthday.split('.')
                        if len(bday_parts) >= 2:
                            bday_day = bday_parts[0].zfill(2)
                            bday_month = bday_parts[1].zfill(2)
                            bday_day_month = f"{bday_day}.{bday_month}"
                            
                            if bday_day_month == today:
                                await self.send_birthday_notification(user_id, user_name, birthday)
                    else:
                        print(f"⚠️ Неверный формат даты рождения: {birthday}")
                except Exception as e:
                    print(f"❌ Ошибка при проверке дня рождения: {e}")
        except Exception as e:
            print(f"❌ Ошибка в check_birthdays: {e}")

    async def send_birthday_notification(self, user_id: int, user_name: str, birthday: str):
        """Отправляет уведомление о дне рождения"""
        try:
            channel = self.bot.get_channel(CHANNELS["BIRTHDAYS"])
            if channel:
                embed = discord.Embed(
                    title="🎉 День рождения!",
                    description=f"У пользователя <@{user_id}> сегодня день рождения! 🎂",
                    color=COLORS["SUCCESS"]
                )
                embed.add_field(name="👤 Пользователь", value=user_name, inline=True)
                embed.add_field(name="📅 Дата рождения", value=birthday, inline=True)
                embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1279099585158254653.webp")
                await channel.send(embed=embed)
                print(f"✅ Уведомление о дне рождения отправлено для {user_name}")
        except Exception as e:
            print(f"❌ Ошибка отправки уведомления о дне рождения: {e}")

    @commands.hybrid_command(name="set_birthday", description="Установить дату рождения")
    async def set_birthday(self, ctx, date: str):
        """Установить дату рождения в формате ДД.ММ.ГГГГ"""
        try:
            # Проверяем формат даты
            parts = date.split('.')
            if len(parts) != 3:
                raise ValueError("Неверный формат")
                
            day, month, year = map(int, parts)
            birthday_date = datetime.date(year, month, day)
            
            # Проверяем что дата не в будущем
            if birthday_date > datetime.date.today():
                embed = discord.Embed(
                    title="❌ Ошибка",
                    description="Дата рождения не может быть в будущем!",
                    color=COLORS["ERROR"]
                )
                await ctx.send(embed=embed, ephemeral=True)
                return
            
            # Проверяем что год разумный (не старше 100 лет и не моложе 10)
            current_year = datetime.date.today().year
            if year < current_year - 100 or year > current_year - 10:
                embed = discord.Embed(
                    title="❌ Ошибка",
                    description="Пожалуйста, укажите реальную дату рождения!",
                    color=COLORS["ERROR"]
                )
                await ctx.send(embed=embed, ephemeral=True)
                return
            
            # Сохраняем в базу
            success = await db.save_birthday(ctx.author.id, str(ctx.author), date)
            
            if success:
                embed = discord.Embed(
                    title="✅ Дата рождения установлена",
                    description=f"Ваша дата рождения: **{date}**",
                    color=COLORS["SUCCESS"]
                )
                await ctx.send(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(
                    title="❌ Ошибка",
                    description="Не удалось сохранить дату рождения",
                    color=COLORS["ERROR"]
                )
                await ctx.send(embed=embed, ephemeral=True)
            
        except ValueError:
            embed = discord.Embed(
                title="❌ Ошибка",
                description="Неверный формат даты. Используйте: ДД.ММ.ГГГГ\nНапример: 15.05.1990",
                color=COLORS["ERROR"]
            )
            await ctx.send(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Ошибка",
                description=f"Произошла ошибка: {str(e)}",
                color=COLORS["ERROR"]
            )
            await ctx.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(name="birthdays", description="Показать все дни рождения")
    async def show_birthdays(self, ctx):
        """Показывает все дни рождения"""
        try:
            birthdays = await db.get_all_birthdays()
            
            if not birthdays:
                embed = discord.Embed(
                    title="📅 Дни рождения",
                    description="Пока нет сохраненных дней рождения",
                    color=COLORS["INFO"]
                )
                await ctx.send(embed=embed)
                return
            
            embed = discord.Embed(
                title="📅 Дни рождения участников",
                color=COLORS["OCEAN"]
            )
            
            # Группируем по месяцам
            birthdays_by_month = {}
            for user_data in birthdays:
                if len(user_data) < 3:
                    continue
                    
                user_id, user_name, birthday = user_data[0], user_data[1], user_data[2]
                
                try:
                    # Парсим дату для группировки по месяцам
                    day, month, year = map(int, birthday.split('.'))
                    month_name = {
                        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
                        5: "Май", 6: "Июнь", 7: "Июль", 8: "Август", 
                        9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
                    }.get(month, "Неизвестно")
                    
                    if month_name not in birthdays_by_month:
                        birthdays_by_month[month_name] = []
                    birthdays_by_month[month_name].append((user_name, birthday, user_id))
                except:
                    continue
            
            if not birthdays_by_month:
                embed.description = "Не удалось обработать дни рождения"
                await ctx.send(embed=embed)
                return
            
            for month, bdays in birthdays_by_month.items():
                bday_list = "\n".join([f"• {name} - {bday}" for name, bday, uid in bdays])
                embed.add_field(
                    name=f"🎂 {month}",
                    value=bday_list,
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"❌ Ошибка в show_birthdays: {e}")
            embed = discord.Embed(
                title="❌ Ошибка",
                description="Не удалось загрузить дни рождения",
                color=COLORS["ERROR"]
            )
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="my_birthday", description="Показать мою дату рождения")
    async def my_birthday(self, ctx):
        """Показывает дату рождения пользователя"""
        try:
            birthdays = await db.get_all_birthdays()
            user_birthday = None
            
            for bday_data in birthdays:
                if len(bday_data) > 0 and bday_data[0] == ctx.author.id:
                    user_birthday = bday_data
                    break
            
            if user_birthday and len(user_birthday) >= 3:
                _, user_name, birthday, *_ = user_birthday
                embed = discord.Embed(
                    title="🎂 Ваша дата рождения",
                    description=f"**{birthday}**",
                    color=COLORS["SUCCESS"]
                )
                await ctx.send(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(
                    title="❌ Дата рождения не установлена",
                    description="Используйте `/set_birthday ДД.ММ.ГГГГ` чтобы установить дату",
                    color=COLORS["ERROR"]
                )
                await ctx.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            print(f"❌ Ошибка в my_birthday: {e}")
            embed = discord.Embed(
                title="❌ Ошибка",
                description="Не удалось получить информацию о дне рождения",
                color=COLORS["ERROR"]
            )
            await ctx.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Birthdays(bot))