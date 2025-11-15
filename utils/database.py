# database.py - ЗАМЕНИТЕ ВЕСЬ ФАЙЛ
import aiosqlite
import datetime
from typing import List, Dict, Optional, Tuple, Any
import os

class Database:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Используем абсолютный путь в текущей директории
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            db_path = os.path.join(parent_dir, "ocean_bot.db")
        self.db_path = db_path
        print(f"📁 Путь к базе данных: {self.db_path}")

    async def init_db(self):
        """Инициализация базы данных с правильной структурой"""
        try:
            print(f"🔄 Инициализация базы данных по пути: {self.db_path}")
            
            # Проверяем доступность пути
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                print(f"✅ Создана директория: {db_dir}")
            
            async with aiosqlite.connect(self.db_path) as db:
                # Включаем поддержку внешних ключей
                await db.execute("PRAGMA foreign_keys = ON")
                
                # Таблица заявок
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS applications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        user_name TEXT NOT NULL,
                        ic_nickname TEXT NOT NULL,
                        ic_passport TEXT NOT NULL,
                        ic_phone TEXT NOT NULL,
                        ic_military_id TEXT NOT NULL,
                        ic_experience TEXT NOT NULL,
                        ooc_name TEXT NOT NULL,
                        ooc_game_time TEXT NOT NULL,
                        ooc_timezone TEXT NOT NULL,
                        ooc_birthday TEXT NOT NULL,
                        ooc_about TEXT NOT NULL,
                        status TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        processed_by INTEGER,
                        processed_at TIMESTAMP
                    )
                ''')

                # Таблица дней рождений
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS birthdays (
                        user_id INTEGER PRIMARY KEY,
                        user_name TEXT NOT NULL,
                        birthday TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Таблица контрактов
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS contracts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        description TEXT,
                        duration TEXT NOT NULL,
                        expires_at TIMESTAMP NOT NULL,
                        required_count INTEGER NOT NULL,
                        created_by INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'active',
                        contract_type TEXT NOT NULL
                    )
                ''')

                # Таблица участников контрактов
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS contract_participants (
                        contract_id INTEGER,
                        user_id INTEGER,
                        user_name TEXT,
                        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (contract_id, user_id),
                        FOREIGN KEY (contract_id) REFERENCES contracts (id) ON DELETE CASCADE
                    )
                ''')

                await db.commit()
                print("✅ Таблицы базы данных созданы/проверены")
                return True
                
        except Exception as e:
            print(f"❌ Ошибка инициализации базы данных: {e}")
            return False

    # ========== МЕТОДЫ ДЛЯ ЗАЯВОК ==========

    async def save_application(self, user_id: int, user_name: str, ic_data: dict, ooc_data: dict):
        """Сохраняет заявку в базу данных"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA foreign_keys = ON")
                await db.execute('''
                    INSERT INTO applications 
                    (user_id, user_name, ic_nickname, ic_passport, ic_phone, ic_military_id, ic_experience,
                     ooc_name, ooc_game_time, ooc_timezone, ooc_birthday, ooc_about)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, user_name,
                    ic_data['nickname'], ic_data['passport'], ic_data['phone'], 
                    ic_data['military_id'], ic_data['experience'],
                    ooc_data['name'], ooc_data['game_time'], ooc_data['timezone'],
                    ooc_data['birthday'], ooc_data['about']
                ))
                await db.commit()
                print(f"✅ Заявка сохранена для пользователя {user_name}")
                return True
        except Exception as e:
            print(f"❌ Ошибка сохранения заявки: {e}")
            return False

    async def get_pending_applications(self):
        """Получает все pending заявки"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('SELECT * FROM applications WHERE status = "pending" ORDER BY created_at DESC')
                results = await cursor.fetchall()
                return results
        except Exception as e:
            print(f"❌ Ошибка получения заявок: {e}")
            return []

    async def get_application_by_user(self, user_id: int):
        """Получает заявку по ID пользователя"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('SELECT * FROM applications WHERE user_id = ?', (user_id,))
                return await cursor.fetchone()
        except Exception as e:
            print(f"❌ Ошибка получения заявки пользователя: {e}")
            return None

    async def update_application_status(self, application_id: int, status: str, processed_by: int):
        """Обновляет статус заявки"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    UPDATE applications 
                    SET status = ?, processed_by = ?, processed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, processed_by, application_id))
                await db.commit()
                print(f"✅ Статус заявки #{application_id} изменен на {status}")
                return True
        except Exception as e:
            print(f"❌ Ошибка обновления статуса заявки: {e}")
            return False

    async def get_all_applications(self):
        """Получает все заявки"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('SELECT * FROM applications ORDER BY created_at DESC')
                return await cursor.fetchall()
        except Exception as e:
            print(f"❌ Ошибка получения всех заявок: {e}")
            return []

    # ========== МЕТОДЫ ДЛЯ ДНЕЙ РОЖДЕНИЙ ==========

    async def save_birthday(self, user_id: int, user_name: str, birthday: str):
        """Сохраняет день рождения"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA foreign_keys = ON")
                await db.execute('''
                    INSERT OR REPLACE INTO birthdays (user_id, user_name, birthday)
                    VALUES (?, ?, ?)
                ''', (user_id, user_name, birthday))
                await db.commit()
                print(f"✅ День рождения сохранен для {user_name}")
                return True
        except Exception as e:
            print(f"❌ Ошибка сохранения дня рождения: {e}")
            return False

    async def get_today_birthdays(self):
        """Получает дни рождения на сегодня"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    SELECT * FROM birthdays 
                    WHERE strftime('%m-%d', birthday) = strftime('%m-%d', 'now')
                ''')
                return await cursor.fetchall()
        except Exception as e:
            print(f"❌ Ошибка получения дней рождений: {e}")
            return []

    async def get_all_birthdays(self):
        """Получает все дни рождения"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('SELECT * FROM birthdays ORDER BY birthday')
                return await cursor.fetchall()
        except Exception as e:
            print(f"❌ Ошибка получения всех дней рождений: {e}")
            return []

    # ========== МЕТОДЫ ДЛЯ КОНТРАКТОВ ==========

    async def create_contract(self, title: str, description: str, duration: str, expires_at: str,
                            required_count: int, created_by: int, contract_type: str) -> Optional[int]:
        """Создает новый контракт"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA foreign_keys = ON")
                cursor = await db.execute('''
                    INSERT INTO contracts 
                    (title, description, duration, expires_at, required_count, created_by, contract_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (title, description, duration, expires_at, required_count, created_by, contract_type))
                await db.commit()
                contract_id = cursor.lastrowid
                print(f"✅ Контракт создан: {title} (ID: {contract_id})")
                return contract_id
        except Exception as e:
            print(f"❌ Ошибка создания контракта: {e}")
            return None

    async def get_contract_participants(self, contract_id: int) -> List[Tuple]:
        """Получает всех участников контракта"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA foreign_keys = ON")
                cursor = await db.execute(
                    'SELECT * FROM contract_participants WHERE contract_id = ?', 
                    (contract_id,)
                )
                return await cursor.fetchall()
        except Exception as e:
            print(f"❌ Ошибка получения участников контракта: {e}")
            return []

    async def add_contract_participant(self, contract_id: int, user_id: int, username: str) -> bool:
        """Добавляет участника в контракт"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA foreign_keys = ON")
                await db.execute('''
                    INSERT OR IGNORE INTO contract_participants (contract_id, user_id, user_name) 
                    VALUES (?, ?, ?)
                ''', (contract_id, user_id, username))
                await db.commit()
                return True
        except Exception as e:
            print(f"❌ Ошибка добавления участника: {e}")
            return False

    async def remove_contract_participant(self, contract_id: int, user_id: int) -> bool:
        """Удаляет участника из контракта"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA foreign_keys = ON")
                await db.execute(
                    'DELETE FROM contract_participants WHERE contract_id = ? AND user_id = ?', 
                    (contract_id, user_id)
                )
                await db.commit()
                return True
        except Exception as e:
            print(f"❌ Ошибка удаления участника: {e}")
            return False

    async def get_contract_by_id(self, contract_id: int) -> Optional[Tuple]:
        """Получает контракт по ID"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA foreign_keys = ON")
                cursor = await db.execute(
                    'SELECT * FROM contracts WHERE id = ?', 
                    (contract_id,)
                )
                return await cursor.fetchone()
        except Exception as e:
            print(f"❌ Ошибка получения контракта: {e}")
            return None

    async def update_contract_status(self, contract_id: int, status: str) -> bool:
        """Обновляет статус контракта"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA foreign_keys = ON")
                await db.execute(
                    'UPDATE contracts SET status = ? WHERE id = ?', 
                    (status, contract_id)
                )
                await db.commit()
                return True
        except Exception as e:
            print(f"❌ Ошибка обновления статуса контракта: {e}")
            return False

    async def get_active_contracts(self) -> List[Tuple]:
        """Получает активные контракты"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA foreign_keys = ON")
                cursor = await db.execute('SELECT * FROM contracts WHERE status = "active"')
                return await cursor.fetchall()
        except Exception as e:
            print(f"❌ Ошибка получения активных контрактов: {e}")
            return []

    async def get_contracts_by_creator(self, user_id: int) -> List[Tuple]:
        """Получает контракты созданные пользователем"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA foreign_keys = ON")
                cursor = await db.execute(
                    'SELECT * FROM contracts WHERE created_by = ? ORDER BY created_at DESC', 
                    (user_id,)
                )
                return await cursor.fetchall()
        except Exception as e:
            print(f"❌ Ошибка получения контрактов пользователя: {e}")
            return []

    async def delete_contract(self, contract_id: int) -> bool:
        """Удаляет контракт и всех его участников"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA foreign_keys = ON")
                # Удаляем участников
                await db.execute('DELETE FROM contract_participants WHERE contract_id = ?', (contract_id,))
                # Удаляем контракт
                await db.execute('DELETE FROM contracts WHERE id = ?', (contract_id,))
                await db.commit()
                return True
        except Exception as e:
            print(f"❌ Ошибка удаления контракта: {e}")
            return False

    # ========== МЕТОДЫ ДЛЯ ОЧИСТКИ ДАННЫХ ==========

    async def clear_applications(self):
        """Очищает таблицу заявок"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA foreign_keys = ON")
                await db.execute('DELETE FROM applications')
                await db.commit()
                print("✅ Таблица заявок очищена")
                return True
        except Exception as e:
            print(f"❌ Ошибка очистки заявок: {e}")
            return False

    async def clear_birthdays(self):
        """Очищает таблицу дней рождений"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA foreign_keys = ON")
                await db.execute('DELETE FROM birthdays')
                await db.commit()
                print("✅ Таблица дней рождений очищена")
                return True
        except Exception as e:
            print(f"❌ Ошибка очистки дней рождений: {e}")
            return False

    async def clear_contracts(self):
        """Очищает таблицы контрактов"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA foreign_keys = ON")
                await db.execute('DELETE FROM contract_participants')
                await db.execute('DELETE FROM contracts')
                await db.commit()
                print("✅ Таблицы контрактов очищены")
                return True
        except Exception as e:
            print(f"❌ Ошибка очистки контрактов: {e}")
            return False

    async def reset_database(self):
        """Полный сброс базы данных"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA foreign_keys = ON")
                await db.execute('DROP TABLE IF EXISTS applications')
                await db.execute('DROP TABLE IF EXISTS birthdays')
                await db.execute('DROP TABLE IF EXISTS contracts')
                await db.execute('DROP TABLE IF EXISTS contract_participants')
                await db.commit()
                
                await self.init_db()
                print("✅ База данных полностью пересоздана")
                return True
        except Exception as e:
            print(f"❌ Ошибка сброса базы данных: {e}")
            return False

    async def get_database_stats(self) -> Dict[str, int]:
        """Получает статистику базы данных"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA foreign_keys = ON")
                stats = {}
                
                cursor = await db.execute('SELECT COUNT(*) FROM applications')
                stats['applications'] = (await cursor.fetchone())[0]
                
                cursor = await db.execute('SELECT COUNT(*) FROM applications WHERE status = "pending"')
                stats['pending_applications'] = (await cursor.fetchone())[0]
                
                cursor = await db.execute('SELECT COUNT(*) FROM birthdays')
                stats['birthdays'] = (await cursor.fetchone())[0]
                
                cursor = await db.execute('SELECT COUNT(*) FROM contracts WHERE status = "active"')
                stats['active_contracts'] = (await cursor.fetchone())[0]
                
                cursor = await db.execute('SELECT COUNT(*) FROM contract_participants')
                stats['contract_participants'] = (await cursor.fetchone())[0]
                
                return stats
        except Exception as e:
            print(f"❌ Ошибка получения статистики: {e}")
            return {}