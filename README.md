🇬🇧 English Version
Telegram Moderation Bot
A powerful, role-based moderation bot for Telegram groups. Designed to manage large communities with a strict hierarchy, automated filters, and detailed logging.

🌟 Key Features
3-Level Role System: Hierarchy consisting of Owner, Head Admin, and Helper.

Advanced Moderation: Ban, Kick, Mute, and Warn systems with time formatting (s, m, h, d).

Auto-Moderation:

Word Filter: Auto-delete and warn for bad words.

Anti-Link: Blocks external links and channel forwards from non-admins.

Security:

Logging: All actions are sent to a private log channel.

Lockdown: !lock mode to stop all chat activity during raids.

Social & Stats:

Stats & Top: Track user activity and top posters.

Welcome: Customizable welcome messages for new members.

Multi-language: Supports EN, RU, UA, DE.

⚡ Prerequisites
Add the bot to your group.

Promote the bot to Admin with ALL permissions (including "Add New Admins").

📚 Command List
👤 User Commands (Available to everyone)
!help — Show available commands based on your role.

!stat — Show personal stats (Join date, message count, rank).

!top — Show top-10 active users.

!report — Reply to a message to report it to admins.

🛡️ Helper (Moderator)
!kick @user — Kick user (no ban).

!ban [time] @user — Ban user. Time: 10m, 2h, 1d. Empty = Forever.

!mute [time] @user — Mute user (Max 90 days).

!warn @user — Issue a warning (3 warnings = Ban/Kick/Mute).

!unban, !unmute, !unwarn — Remove punishments.

!mdelete @user — Delete all recent messages from a user.

🎩 Head Admin
!lock / !unlock — Panic mode. Lock the chat for everyone except admins.

!banword [word] — Add a word to the blacklist.

!unbanword [word] — Remove a word from the blacklist.

!setwelcome [text] — Set the welcome message ({username} placeholder).

👑 Owner (Creator)
!setlog @channel — Set the channel for logging actions.

Full Access to all settings (Language, Limits, Punishments).

⚙️ Configuration
Access the settings menu via private message or main command to configure:

Punishment Logic: Toggle message deletion on Ban/Kick/Mute.

Warn Settings: Warn limit and result action.

Language: Switch between English, Russian, Ukrainian, German.

🇷🇺 Русская Версия
Telegram Moderation Bot
Мощный бот для модерации Telegram-чатов с разделением ролей. Создан для управления сообществами со строгой иерархией, автоматическими фильтрами и подробным логированием.

🌟 Основные возможности
3 Уровня доступа: Иерархия Создатель, Гл. Помощник и Помощник.

Продвинутая модерация: Бан, Кик, Мут и Варны с поддержкой времени (s, m, h, d).

Авто-модерация:

Фильтр слов: Авто-удаление мата/запрещенных слов + выдача варна.

Анти-ссылки: Блокировка внешних ссылок и репостов для обычных юзеров.

Безопасность:

Логирование: Отчеты о действиях отправляются в скрытый канал.

Режим Паники: Команда !lock закрывает чат для всех (кроме админов) во время рейдов.

Социальные функции:

Статистика и Топ: Личная статистика и топ-10 активных участников.

Приветствия: Настраиваемые сообщения для новых участников.

Мультиязычность: Поддержка RU, EN, UA, DE.

⚡ Установка
Добавьте бота в группу.

Назначьте бота Администратором со ВСЕМИ правами (включая право "Добавлять администраторов").

📚 Список Команд
👤 Пользователь (Доступно всем)
!help — Показать список доступных команд.

!stat — Личная статистика (Дата входа, сообщений, ранг).

!top — Топ-10 активных пользователей чата.

!report — (В ответ на сообщение) Пожаловаться админам.

🛡️ Помощник (Helper)
!kick @user — Кикнуть (удалить) из чата.

!ban [время] @user — Забанить. Время: 10m, 2h, 1d. Пустое = Навсегда.

!mute [время] @user — Замутить (Макс. 90 дней).

!warn @user — Выдать предупреждение (Лимит настраивается).

!unban, !unmute, !unwarn — Снять наказания.

!mdelete @user — Удалить сообщения пользователя.

🎩 Гл. Помощник (Head Admin)
!lock / !unlock — Закрыть/Открыть чат (для защиты от спама).

!banword [слово] — Добавить слово в черный список.

!unbanword [слово] — Убрать слово из списка.

!setwelcome [текст] — Установить приветствие (тег {username}).

👑 Создатель (Owner)
!setlog @channel — Указать канал для логов.

Полный доступ к меню настроек (Язык, Лимиты, Удаление сообщений).

⚙️ Настройки
Меню настроек позволяет изменить:

Наказания: Удалять ли сообщения при Бане/Кике (Да/Нет).

Варны: Количество варнов и тип наказания за их превышение.

Язык: Переключение между Русским, Английским, Украинским, Немецким.
