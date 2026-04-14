import os
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv(override=True)


def normalize_database_url(raw_url: str) -> str:
    url = (raw_url or "").strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    parsed = urlsplit(url)
    if parsed.scheme not in {"postgresql", "postgresql+psycopg2"}:
        return url
    if "@" not in parsed.netloc:
        return url

    user_info, host_info = parsed.netloc.rsplit("@", 1)
    if ":" in user_info:
        username, password = user_info.split(":", 1)
    else:
        username, password = user_info, ""

    safe_user = quote(unquote(username), safe="")
    safe_pass = quote(unquote(password), safe="")
    safe_netloc = f"{safe_user}:{safe_pass}@{host_info}" if password else f"{safe_user}@{host_info}"
    return urlunsplit((parsed.scheme, safe_netloc, parsed.path, parsed.query, parsed.fragment))


def get_engine():
    database_url = normalize_database_url(os.getenv("DATABASE_URL") or "")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is required")
    return create_engine(database_url, pool_pre_ping=True)


def apply_sql_file(engine, sql_file):
    sql_content = sql_file.read_text(encoding="utf-8")
    # Execute full SQL file so PostgreSQL blocks (e.g. DO $$ ... $$) remain intact.
    raw_conn = engine.raw_connection()
    try:
        cursor = raw_conn.cursor()
        cursor.execute(sql_content)
        raw_conn.commit()
    finally:
        raw_conn.close()


def main():
    root = Path(__file__).resolve().parent
    sql_dir = root / "sql"
    sql_files = sorted(sql_dir.glob("*.sql"))
    if not sql_files:
        print("No SQL migration files found.")
        return

    engine = get_engine()
    for sql_file in sql_files:
        print(f"Applying migration: {sql_file.name}")
        apply_sql_file(engine, sql_file)
    print("Migrations applied successfully.")


if __name__ == "__main__":
    main()
