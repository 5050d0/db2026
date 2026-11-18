from datetime import datetime, timedelta, timezone
from pathlib import Path
from random import Random

DOCUMENT_COUNT = 48
RANDOM_SEED = 42
OUTPUT_FILE = Path("test_data.sql")

START = datetime(2025, 1, 1, 9, tzinfo=timezone.utc)
ROLES = ((1, "reader", 24), (2, "author", 8), (3, "moderator", 3), (4, "admin", 1))
THEMES = ("IT", "History", "Philosophy", "Databases", "Ancient history", "Python")
INFORMERS = (("Informer 1", "person"), ("Informer 2", "person"), ("MEPhI", "organization"))
STATUSES = ("approved", "revision", "rejected", "in_progress")
DOCUMENT_TYPES = ("article", "spreadsheet", "photo")


def sql_literal(value):
    if value is None:
        return "NULL"
    if isinstance(value, bytes):
        return f"decode('{value.hex()}', 'hex')"
    if isinstance(value, str):
        return "'" + value.replace("'", "''") + "'"
    return str(value)


def timestamp(days=0, hours=0, minutes=0):
    return (START + timedelta(days=days, hours=hours, minutes=minutes)).isoformat()


def ip(user_id):
    return f"192.0.2.{user_id}"


def generate_sql(document_count, seed):
    rng = Random(seed)
    sql = ["BEGIN;"]

    def insert(table_and_columns, *values):
        literals = ", ".join(map(sql_literal, values))
        sql.append(f"INSERT INTO main.{table_and_columns} VALUES ({literals});")

    safe_ip_fields = "safe_ips (user_id, ip_address, is_active, date_added)"
    users_by_role = {}
    user_id = 0
    for role, prefix, count in ROLES:
        users_by_role[role] = []
        for number in range(1, count + 1):
            user_id += 1
            users_by_role[role].append(user_id)
            insert("users (user_id, login, role_code, access_level)",
                   user_id, f"{prefix}_{number:02}", role, role - 1)
            if role in (1, 2):
                insert(safe_ip_fields, user_id, ip(user_id), True, timestamp())
            for day in (0, 3, 8):
                insert("login_history (user_id, login_ip, login_ts)",
                       user_id, ip(user_id), timestamp(days=day))
    for address, active in (("198.51.100.1", True), ("2001:db8::1", True), ("203.0.113.1", False)):
        insert(safe_ip_fields, 1, address, active, timestamp())

    authors = users_by_role[2]
    moderators = users_by_role[3]
    approved = []
    document_id = 0
    for number in range(1, document_count + 1):
        parent = None
        author = rng.choice(authors)
        document_type = DOCUMENT_TYPES[(number - 1) % len(DOCUMENT_TYPES)]
        if number == 1:
            version_count = len(STATUSES)
        elif number == 2:
            version_count = 1
        else:
            version_count = rng.randint(1, 4)
        for version in range(1, version_count + 1):
            document_id += 1
            status = STATUSES[version - 1] if number == 1 else rng.choice(STATUSES)
            moderator = None if status == "in_progress" else rng.choice(moderators)
            title = f"Учебный документ {number:03}"
            content = f"{title}, версия {version}\n".encode("utf-8")
            insert("documents (document_id, parent_version, author, moderator, date_added, "
                   "ip_address, title, document_type, content, moderation_status)",
                   document_id, parent, author, moderator, timestamp(version, number % 24),
                   ip(author), title, document_type, content, status)
            if status == "approved":
                approved.append(document_id)
            parent = document_id

            theme_count = 2 if version % 2 == 0 else 1
            for offset in range(theme_count):
                theme = THEMES[(number + version - 2 + offset) % len(THEMES)]
                sql.append(
                    "INSERT INTO main.document_themes (theme_id, document_id) VALUES "
                    f"((SELECT theme_id FROM main.themes WHERE theme_name = {sql_literal(theme)}), {document_id});"
                )
            for name, kind in rng.sample(INFORMERS, rng.randint(1, 2)):
                sql.append(
                    "INSERT INTO main.document_informers (informer_id, document_id) VALUES "
                    f"((SELECT informer_id FROM main.informers WHERE informer_name = {sql_literal(name)} "
                    f"AND informer_type = {sql_literal(kind)}), {document_id});"
                )
            other_authors = [candidate for candidate in authors if candidate != author]
            for coauthor in rng.sample(other_authors, rng.randint(0, 3)):
                insert("document_coauthors (user_id, document_id)", coauthor, document_id)


    readers = users_by_role[1]
    viewers = [viewer for viewer in range(1, user_id + 1) if viewer != readers[-1]]
    for viewer in viewers:
        for hour in range(1, rng.randint(10, 30) + 1):
            insert("view_history (document_id, user_id, date_added, user_ip)",
                   rng.choice(approved), viewer, timestamp(8, hour), ip(viewer))
    for reader in readers[:-2]:
        for favorite in rng.sample(approved, min(len(approved), rng.randint(1, 5))):
            insert("favorites (user_id, document_id, date_added)", reader, favorite, timestamp(10))


    comment_fields = ("comments (comment_id, parent_id, document_id, author_id, "
                      "addressed_id, date_added, content, ip_address)")
    comment_id = 0
    for published in approved:
        commenter, respondent = rng.sample(viewers, 2)
        insert(comment_fields, comment_id + 1, None, published, commenter, None,
               timestamp(10), "Как собрали эти данные?", ip(commenter))
        insert(comment_fields, comment_id + 2, comment_id + 1, published, respondent, commenter,
               timestamp(10, minutes=15), "Описание есть в материалах.", ip(respondent))
        comment_id += 2

    events = "block_events (blocker, blocked, is_blocked, reason, date_added)"
    for reader in readers[:4]:
        insert(events, None, reader, True, "Доступ с незнакомого IP", timestamp(12))
    for reader in readers[:2]:
        insert(events, moderators[0], reader, False, "Модератор подтвердил доступ", timestamp(13))
    insert(events, moderators[1], readers[4], True, "Ручная блокировка", timestamp(13))


    sql.append(f"ALTER TABLE main.users ALTER COLUMN user_id RESTART WITH {user_id + 1};")
    sql.append(f"ALTER TABLE main.documents ALTER COLUMN document_id RESTART WITH {document_id + 1};")
    sql.append(f"ALTER TABLE main.comments ALTER COLUMN comment_id RESTART WITH {comment_id + 1};")
    sql.append("COMMIT;")
    return "\n".join(sql) + "\n"


if __name__ == "__main__":
    OUTPUT_FILE.write_text(generate_sql(DOCUMENT_COUNT, RANDOM_SEED), encoding="utf-8")
    print(f"Тестовые данные записаны в {OUTPUT_FILE}")