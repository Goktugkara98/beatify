"""
MySQL / Amazon RDS Bağlantı Test Aracı (Tkinter)

Amaç:
- Amazon RDS (MySQL) gibi bir veritabanına bağlantıyı hızlıca test etmek.
- Host/endpoint, port, kullanıcı adı, şifre ve (opsiyonel) veritabanı adı ile bağlanır.
- Başarılı olursa basit bir `SELECT 1` sorgusu çalıştırır ve server versiyonunu gösterir.

Güvenlik Notu:
- Şifreyi bu dosyaya hardcode ETMEYİN.
- Bu araca şifreyi GUI üzerinden girin.

Çalıştırma:
  python scripts/db_connection_test_gui.py
"""

from __future__ import annotations

import socket
import threading
import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox, ttk
from typing import Optional

import mysql.connector


@dataclass(frozen=True)
class DbInputs:
    host: str
    port: int
    user: str
    password: str
    database: Optional[str]


def _validate_inputs(host: str, port_str: str, user: str, password: str, database: str) -> DbInputs:
    host = host.strip()
    if not host:
        raise ValueError("Endpoint/Host boş olamaz.")

    try:
        port = int(port_str.strip() or "3306")
    except ValueError:
        raise ValueError("Port sayısal olmalı.")

    if not (1 <= port <= 65535):
        raise ValueError("Port 1-65535 aralığında olmalı.")

    user = user.strip()
    if not user:
        raise ValueError("Kullanıcı adı boş olamaz.")

    # password boş olabilir (bazı kurulumlarda), ama genelde olmaz.
    password = password

    db = database.strip()
    database_opt = db if db else None

    return DbInputs(host=host, port=port, user=user, password=password, database=database_opt)


def _test_db_connection(inputs: DbInputs, connect_timeout: int = 8) -> str:
    config: dict[str, object] = {
        "host": inputs.host,
        "port": inputs.port,
        "user": inputs.user,
        "password": inputs.password,
        "connection_timeout": connect_timeout,
    }

    if inputs.database:
        config["database"] = inputs.database

    # Bağlan ve basit sorgu çalıştır
    conn = mysql.connector.connect(**config)  # type: ignore[arg-type]
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT 1")
            _ = cur.fetchone()
        finally:
            cur.close()

        server_ver = getattr(conn, "get_server_info", None)
        ver_str = server_ver() if callable(server_ver) else "unknown"

        # DNS/host çözümleme bilgisi
        try:
            resolved = socket.gethostbyname(inputs.host)
        except Exception:
            resolved = "(resolve edilemedi)"

        db_str = inputs.database or "(database seçilmedi)"
        return (
            "Bağlantı başarılı.\n"
            f"Host: {inputs.host} ({resolved})\n"
            f"Port: {inputs.port}\n"
            f"User: {inputs.user}\n"
            f"Database: {db_str}\n"
            f"Server version: {ver_str}"
        )
    finally:
        conn.close()


class DbConnectionTestGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title("Beatify - RDS/MySQL Bağlantı Testi")
        self.geometry("860x440")
        self.minsize(860, 440)

        # Varsayılanlar (AWS RDS endpoint örneği)
        self.var_host = tk.StringVar(value="beatify.cebgyygakiik.us-east-1.rds.amazonaws.com")
        self.var_port = tk.StringVar(value="3306")
        self.var_user = tk.StringVar(value="admin")
        self.var_password = tk.StringVar(value="")
        self.var_database = tk.StringVar(value="")

        self.var_status = tk.StringVar(value="Idle")
        self.var_result = tk.StringVar(value="")

        self.btn_test: ttk.Button

        self._build_ui()

    def _build_ui(self) -> None:
        pad = {"padx": 10, "pady": 6}

        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True, padx=12, pady=12)

        # Host
        ttk.Label(frm, text="RDS Endpoint / Host:").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.var_host).grid(row=0, column=1, sticky="ew", **pad)

        # Port
        ttk.Label(frm, text="Port:").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.var_port, width=10).grid(row=1, column=1, sticky="w", **pad)

        # User
        ttk.Label(frm, text="User:").grid(row=2, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.var_user, width=24).grid(row=2, column=1, sticky="w", **pad)

        # Password
        ttk.Label(frm, text="Password:").grid(row=3, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.var_password, show="*").grid(row=3, column=1, sticky="ew", **pad)

        # Database (optional)
        ttk.Label(frm, text="Database (opsiyonel):").grid(row=4, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.var_database).grid(row=4, column=1, sticky="ew", **pad)

        # Buttons
        btns = ttk.Frame(frm)
        btns.grid(row=5, column=1, sticky="w", **pad)
        self.btn_test = ttk.Button(btns, text="Bağlantıyı Test Et", command=self._on_test_clicked)
        self.btn_test.pack(side="left")
        ttk.Button(btns, text="Şifreyi Temizle", command=lambda: self.var_password.set("")).pack(side="left", padx=(8, 0))

        # Info (AWS chmod benzeri not)
        hint = (
            "Not: Şifreyi koda yazmayın; buradan girin.\n"
            "RDS Security Group inbound kuralında 3306 portu, sizin IP’nize izin vermeli.\n"
            "Ayrıca DB subnet/public erişim ayarları doğru olmalı."
        )
        ttk.Label(frm, text=hint, wraplength=740, justify="left").grid(row=6, column=0, columnspan=2, sticky="w", **pad)

        sep = ttk.Separator(frm, orient="horizontal")
        sep.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(10, 10))

        ttk.Label(frm, text="Durum:").grid(row=8, column=0, sticky="w", **pad)
        ttk.Label(frm, textvariable=self.var_status).grid(row=8, column=1, sticky="w", **pad)

        ttk.Label(frm, text="Sonuç:").grid(row=9, column=0, sticky="nw", **pad)
        result = ttk.Label(frm, textvariable=self.var_result, wraplength=740, justify="left")
        result.grid(row=9, column=1, sticky="w", **pad)

        frm.columnconfigure(1, weight=1)

    def _set_busy(self, busy: bool) -> None:
        self.btn_test.configure(state="disabled" if busy else "normal")

    def _on_test_clicked(self) -> None:
        try:
            inputs = _validate_inputs(
                host=self.var_host.get(),
                port_str=self.var_port.get(),
                user=self.var_user.get(),
                password=self.var_password.get(),
                database=self.var_database.get(),
            )
        except Exception as e:
            messagebox.showerror("Hata", str(e))
            return

        self.var_status.set("Connecting...")
        self.var_result.set("")
        self._set_busy(True)

        def worker() -> None:
            try:
                info = _test_db_connection(inputs)
                self.after(0, lambda: self._ui_success(info))
            except mysql.connector.Error as e:
                msg = f"MySQL error: {e}"
                self.after(0, lambda m=msg: self._ui_error(m))
            except Exception as e:
                msg = str(e)
                self.after(0, lambda m=msg: self._ui_error(m))

        threading.Thread(target=worker, daemon=True).start()

    def _ui_success(self, info: str) -> None:
        self.var_status.set("Connected")
        self.var_result.set(info)
        self._set_busy(False)

    def _ui_error(self, msg: str) -> None:
        self.var_status.set("Error")
        self.var_result.set(msg)
        self._set_busy(False)
        messagebox.showerror("Bağlantı Hatası", msg)


def main() -> None:
    app = DbConnectionTestGui()
    app.mainloop()


if __name__ == "__main__":
    main()
