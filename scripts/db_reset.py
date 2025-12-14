"""beatify/scripts/db_reset.py

Amaç:
- Veritabanını analiz etmek (tablolar, satır sayıları, foreign key ilişkileri)
- Veritabanını tam resetlemek:
  - ya tüm tabloları drop ederek
  - ya tüm database'i drop + recreate ederek

GÜVENLİK:
- Varsayılan DRY-RUN modudur.
- Gerçek silme işlemleri için mutlaka `--yes` verilmelidir.

Kullanım örnekleri:

1) Analiz:
   python scripts/db_reset.py analyze

2) Tabloları drop ederek reset (database kalır):
   python scripts/db_reset.py drop-tables --yes

3) Database'i tamamen drop + recreate (en temiz reset):
   python scripts/db_reset.py drop-database --yes

4) Database'i drop + recreate + migrations'ı hemen çalıştır:
   python scripts/db_reset.py drop-database --yes --run-migrations

Notlar:
- DB bağlantı bilgileri `app.config.config.DB_CONFIG` içinden okunur.
- .env kullanıyorsan otomatik yüklenir (python-dotenv varsa).
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, List, Tuple

import mysql.connector


def _ensure_project_root_on_path() -> None:
    """
    Windows'ta script'i alt klasörden çalıştırınca `import app` bulunamayabiliyor.
    Proje kökünü sys.path'e ekleyerek bunu garanti altına alır.
    """
    here = os.path.abspath(os.path.dirname(__file__))
    root = os.path.abspath(os.path.join(here, os.pardir))
    if root not in sys.path:
        sys.path.insert(0, root)


def _configure_console_encoding() -> None:
    """
    Windows'ta varsayılan terminal encoding'i (cp1252/cp1254) Türkçe karakterlerde
    UnicodeEncodeError verebiliyor. stdout/stderr'i mümkünse UTF-8'e al.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            # Python 3.7+
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:
            pass


def _load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv()
    except Exception:
        # dotenv yoksa sorun değil
        pass


def _get_db_config() -> Dict[str, Any]:
    """DB_CONFIG'i .env yüklendikten sonra import eder."""
    _ensure_project_root_on_path()
    _load_dotenv_if_available()
    from app.config.config import DB_CONFIG

    # kopya döndür (yan etkisiz)
    return dict(DB_CONFIG)


def _connect(database: str | None) -> mysql.connector.MySQLConnection:
    cfg = _get_db_config()

    host = cfg.get("host")
    user = cfg.get("user")
    password = cfg.get("password")
    dbname = cfg.get("database")

    if database is None:
        # Server seviyesinde bağlantı (DROP DATABASE için)
        return mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            charset="utf8mb4",
        )

    # Belirli database'e bağlan
    return mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database or dbname,
        charset="utf8mb4",
    )


def _fetch_all_tables(conn: mysql.connector.MySQLConnection, dbname: str) -> List[str]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """,
        (dbname,),
    )
    rows = cur.fetchall() or []
    cur.close()
    return [r[0] for r in rows]


def _table_row_count(conn: mysql.connector.MySQLConnection, table_name: str) -> int:
    cur = conn.cursor()
    # table_name information_schema'dan geliyor; yine de backtick ile quote edelim
    cur.execute(f"SELECT COUNT(*) FROM `{table_name}`")
    (count,) = cur.fetchone()
    cur.close()
    return int(count or 0)


def _foreign_keys(conn: mysql.connector.MySQLConnection, dbname: str) -> List[Tuple[str, str, str, str]]:
    """(table, column, referenced_table, referenced_column)"""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT table_name, column_name, referenced_table_name, referenced_column_name
        FROM information_schema.key_column_usage
        WHERE table_schema = %s
          AND referenced_table_name IS NOT NULL
        ORDER BY table_name, column_name
        """,
        (dbname,),
    )
    rows = cur.fetchall() or []
    cur.close()
    return [(r[0], r[1], r[2], r[3]) for r in rows]


def cmd_analyze(args: argparse.Namespace) -> int:
    cfg = _get_db_config()
    dbname = args.database or cfg.get("database")

    if not dbname:
        raise SystemExit("DB_NAME/DB_CONFIG.database bulunamadı")

    print(f"[analyze] host={cfg.get('host')} user={cfg.get('user')} database={dbname}")

    conn = _connect(dbname)
    try:
        tables = _fetch_all_tables(conn, dbname)
        print(f"[analyze] tables ({len(tables)}): {', '.join(tables) if tables else '(none)'}")

        if tables:
            print("[analyze] row counts:")
            for t in tables:
                try:
                    c = _table_row_count(conn, t)
                except Exception as e:
                    c = -1
                    print(f"  - {t}: (count failed) {e}")
                else:
                    print(f"  - {t}: {c}")

        fks = _foreign_keys(conn, dbname)
        if fks:
            print("[analyze] foreign keys:")
            for (t, c, rt, rc) in fks:
                print(f"  - {t}.{c} -> {rt}.{rc}")
        else:
            print("[analyze] foreign keys: (none)")

        return 0
    finally:
        conn.close()


def cmd_drop_tables(args: argparse.Namespace) -> int:
    cfg = _get_db_config()
    dbname = args.database or cfg.get("database")

    if not dbname:
        raise SystemExit("DB_NAME/DB_CONFIG.database bulunamadı")

    conn = _connect(dbname)
    try:
        tables = _fetch_all_tables(conn, dbname)
        print(f"[drop-tables] target database={dbname}")
        print(f"[drop-tables] tables to drop ({len(tables)}): {', '.join(tables) if tables else '(none)'}")

        if not args.yes:
            print("[drop-tables] DRY-RUN. Gerçek silme için --yes ekleyin.")
            return 0

        if not tables:
            print("[drop-tables] Hiç tablo yok, işlem yok.")
            return 0

        cur = conn.cursor()
        try:
            cur.execute("SET FOREIGN_KEY_CHECKS=0")
            for t in tables:
                cur.execute(f"DROP TABLE IF EXISTS `{t}`")
            cur.execute("SET FOREIGN_KEY_CHECKS=1")
            conn.commit()
        finally:
            cur.close()

        print("[drop-tables] OK. Tüm tablolar drop edildi.")
        return 0
    finally:
        conn.close()


def cmd_drop_database(args: argparse.Namespace) -> int:
    cfg = _get_db_config()
    dbname = args.database or cfg.get("database")

    if not dbname:
        raise SystemExit("DB_NAME/DB_CONFIG.database bulunamadı")

    print(f"[drop-database] target database={dbname}")

    if not args.yes:
        print("[drop-database] DRY-RUN. Gerçek silme için --yes ekleyin.")
        return 0

    # 1) DROP + CREATE
    conn = _connect(None)
    try:
        cur = conn.cursor()
        try:
            cur.execute(f"DROP DATABASE IF EXISTS `{dbname}`")
            cur.execute(
                f"CREATE DATABASE `{dbname}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            conn.commit()
        finally:
            cur.close()
    finally:
        conn.close()

    print("[drop-database] OK. Database yeniden oluşturuldu.")

    # 2) migrations (opsiyonel)
    if args.run_migrations:
        print("[drop-database] running migrations...")
        from app.database.migrations_repository import MigrationsRepository

        MigrationsRepository().create_all_tables()
        print("[drop-database] OK. Tablolar oluşturuldu.")

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Beatify MySQL DB analyze/reset utility")
    p.add_argument(
        "--database",
        default=None,
        help="Hedef veritabanı adı (varsayılan: app.config.config.DB_CONFIG['database'])",
    )

    sub = p.add_subparsers(dest="command", required=True)

    p_analyze = sub.add_parser("analyze", help="Tabloları, row count ve FK'leri yazdırır")
    p_analyze.set_defaults(func=cmd_analyze)

    p_drop_tables = sub.add_parser("drop-tables", help="Database'i silmeden tüm tabloları drop eder")
    p_drop_tables.add_argument("--yes", action="store_true", help="Gerçekten sil")
    p_drop_tables.set_defaults(func=cmd_drop_tables)

    p_drop_db = sub.add_parser("drop-database", help="Database'i tamamen drop + recreate eder")
    p_drop_db.add_argument("--yes", action="store_true", help="Gerçekten sil")
    p_drop_db.add_argument(
        "--run-migrations",
        action="store_true",
        help="Recreate sonrası migrations'ı hemen çalıştır",
    )
    p_drop_db.set_defaults(func=cmd_drop_database)

    return p


def main() -> int:
    _configure_console_encoding()
    parser = build_parser()
    # Komut verilmediyse yardım menüsü göster (argparse error basmasın)
    if len(sys.argv) <= 1:
        parser.print_help()
        return 0

    args = parser.parse_args()

    # ekstra güvenlik: prod ortamda yanlışlıkla çalıştırmayı azalt
    if args.command in {"drop-tables", "drop-database"} and args.yes:
        env_guard = os.environ.get("BEATIFY_ALLOW_DB_RESET")
        if env_guard not in {"1", "true", "TRUE", "yes", "YES"}:
            print(
                "[safety] Silme işlemleri için ek güvenlik istendi.\n"
                "         PowerShell'de önce şu env'i ver:  $env:BEATIFY_ALLOW_DB_RESET=1\n"
                "         Sonra komutu tekrar çalıştır."
            )
            return 2

    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
