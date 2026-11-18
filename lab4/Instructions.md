1. Запустите кластер postgresql и создайте пользователя и базу данных
2. Подключитесь в БД
3. Выполните команды из main.sql
4. Выполните команды из initialize.sql
5. Выполните команды из test_data.sql (предварительно сгенерировав его через generate_data.py)
Для выполнения команд в psql в windows выполните
``` psql
\encoding UTF8
\set ON_ERROR_STOP on
\i 'C:/Users/Kirill/db2026/lab4/ИмяФайла.sql'
```