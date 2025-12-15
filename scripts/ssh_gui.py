"""
Basit SSH GUI (Tkinter + OpenSSH)

Amaç:
- Uygulama dışından, SSH ile sunucuya bağlanmak için küçük bir araç.
- AWS EC2 "Connect" ekranındaki gibi: Instance ID, keypair, DNS ve örnek komut gösterir.

Notlar:
- Bu script sadece "bağlantı testi" yapar. Başarılı olunca "Connected" yazar.
- Paramiko KULLANMAZ. Sisteminizdeki OpenSSH istemcisini (`ssh`) kullanır.
- Private key şifreliyse (passphrase), “hızlı test” modunda bağlanamaz.
  Bu durumda interaktif terminal açarak SSH başlatır (passphrase orada girilir).

Çalıştırma:
  python scripts/ssh_gui.py
"""

from __future__ import annotations

import os
import socket
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Optional, Tuple


def _find_ssh_exe() -> str:
    """
    Sistem SSH istemcisini bulur.
    - Windows: çoğunlukla OpenSSH (ssh.exe) yüklüdür
    - Linux/macOS: `ssh` PATH üzerindedir
    """
    import shutil

    ssh_path = shutil.which("ssh")
    if ssh_path:
        return ssh_path

    # Windows fallback (bazı sistemlerde PATH yok ama dosya var)
    if os.name == "nt":
        candidate = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "System32", "OpenSSH", "ssh.exe")
        if os.path.exists(candidate):
            return candidate

    raise RuntimeError(
        "Sisteminizde 'ssh' bulunamadı.\n\n"
        "Windows için: Optional Features > OpenSSH Client kurun.\n"
        "Sonra tekrar deneyin."
    )


def _known_hosts_null_path() -> str:
    # ssh prompt/known_hosts yazımı istemiyorsak: Windows'ta NUL, Unix'te /dev/null
    return "NUL" if os.name == "nt" else "/dev/null"


def _build_ssh_cmd(
    host: str,
    port: int,
    username: str,
    key_path: str,
    *,
    remote_cmd: Optional[str] = None,
    batch_mode: bool = True,
    strict_host_key: str = "accept-new",
) -> list[str]:
    ssh = _find_ssh_exe()

    cmd: list[str] = [
        ssh,
        "-i",
        key_path,
        "-p",
        str(port),
        "-o",
        "ConnectTimeout=10",
        "-o",
        "ServerAliveInterval=10",
        "-o",
        "ServerAliveCountMax=1",
    ]

    if batch_mode:
        # Passphrase/interactive prompt'ları kapatır; şifreli key varsa burada fail eder.
        cmd += ["-o", "BatchMode=yes"]

    # İlk bağlantıda host key prompt'u istemiyoruz (GUI'yi kilitlemesin).
    # accept-new bazı eski ssh sürümlerinde yok; fail olursa fallback yapacağız.
    cmd += ["-o", f"StrictHostKeyChecking={strict_host_key}", "-o", f"UserKnownHostsFile={_known_hosts_null_path()}"]

    cmd.append(f"{username}@{host}")

    if remote_cmd:
        cmd.append(remote_cmd)

    return cmd


def _run_ssh_test(host: str, port: int, username: str, key_path: str) -> Tuple[bool, str]:
    """
    Non-interactive bağlantı testi yapar.
    Şifreli key / passphrase gerekiyorsa BatchMode nedeniyle başarısız olur.
    """
    # Cross-platform basit doğrulama: echo
    test_cmd = "echo beatify_ssh_ok"
    cmd = _build_ssh_cmd(host, port, username, key_path, remote_cmd=test_cmd, batch_mode=True, strict_host_key="accept-new")

    try:
        cp = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
    except subprocess.TimeoutExpired:
        return False, "Timeout: SSH bağlantısı zaman aşımına uğradı."

    out = (cp.stdout or "").strip()
    err = (cp.stderr or "").strip()

    # "Permanently added ..." host-key mesajını hata metninden ayıkla (gerçek hatayı görmek için)
    if err:
        filtered_lines: list[str] = []
        for line in err.splitlines():
            lower = line.lower()
            if "permanently added" in lower and "known hosts" in lower:
                continue
            if lower.startswith("warning: permanently added"):
                continue
            filtered_lines.append(line)
        err = "\n".join(filtered_lines).strip()

    if cp.returncode == 0:
        return True, out or "Connected"

    # Bazı ssh sürümlerinde accept-new yok; fallback ile tekrar dene
    if "Bad configuration option" in err and "accept-new" in err:
        cmd2 = _build_ssh_cmd(host, port, username, key_path, remote_cmd=test_cmd, batch_mode=True, strict_host_key="no")
        try:
            cp2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=12)
        except subprocess.TimeoutExpired:
            return False, "Timeout: SSH bağlantısı zaman aşımına uğradı."

        out2 = (cp2.stdout or "").strip()
        err2 = (cp2.stderr or "").strip()
        if cp2.returncode == 0:
            return True, out2 or "Connected"
        return False, err2 or out2 or f"SSH exit code: {cp2.returncode}"

    # Passphrase gerekiyorsa genelde stderr içinde belirtir
    if "Enter passphrase" in err or "passphrase" in err.lower():
        return False, "Private key şifreli (passphrase gerekiyor). Interaktif bağlantı açın."

    return False, err or out or f"SSH exit code: {cp.returncode}"


def _open_interactive_ssh(host: str, port: int, username: str, key_path: str) -> None:
    """
    Interaktif SSH oturumu için terminal açar.

    Windows'ta varsayılan olarak CMD açar (kullanıcı alışkanlığı için).
    """
    ssh = _find_ssh_exe()
    base = f'"{ssh}" -i "{key_path}" -p {port} {username}@{host}'

    if os.name == "nt":
        # Yeni bir CMD penceresi aç; kullanıcı passphrase/password prompt görebilsin.
        #
        # Önemli:
        # - subprocess arg listesi kullanırsak, Python iç tırnakları \" şeklinde escape eder.
        # - cmd.exe bunu literal görür ve `"C:\...\ssh.exe"` yerine `\"C:\...\ssh.exe\"` çalıştırmaya kalkar.
        # - Bu yüzden Windows'ta TEK STRING komut satırı kullanıyoruz.
        try:
            cmdline = f'cmd.exe /k ""{ssh}" -i "{key_path}" -p {port} {username}@{host}""'
            subprocess.Popen(cmdline, creationflags=subprocess.CREATE_NEW_CONSOLE)  # type: ignore[arg-type,attr-defined]
        except Exception as e:
            raise RuntimeError(f"Terminal açılamadı: {e}") from e
        return

    # Diğer OS'lerde terminal açma farklı; en azından kullanıcıya komutu verelim.
    raise RuntimeError(
        "Bu sistemde interaktif terminal açma otomatik ayarlanmadı.\n\n"
        f"Lütfen terminalde şu komutu çalıştırın:\n{base}"
    )


def _connect_ssh(
    host: str,
    port: int,
    username: str,
    key_path: str,
    timeout: float = 10.0,
) -> Tuple[None, str]:
    """
    Paramiko yerine sistem ssh ile bağlantı testi yapar.
    Başarılı olursa (None, info) döndürür.
    """
    ok, info = _run_ssh_test(host, port, username, key_path)
    if ok:
        return None, info
    raise RuntimeError(info)


class SSHGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Beatify - SSH GUI (EC2 Connect)")
        self.geometry("820x420")
        self.minsize(820, 420)

        self._connected: bool = False

        # Varsayılanlar
        self.var_instance_id = tk.StringVar(value="")
        self.var_host = tk.StringVar(value="")
        self.var_port = tk.StringVar(value="22")
        # EC2'lerde çoğunlukla root ile giriş kapalıdır. Yaygın kullanıcı: ec2-user / ubuntu.
        self.var_user = tk.StringVar(value="ubuntu")
        self.var_key = tk.StringVar(value="")
        self.var_cmd = tk.StringVar(value="")
        self.var_chmod = tk.StringVar(value="")
        self.var_status = tk.StringVar(value="Idle")
        self.var_last_info = tk.StringVar(value="")

        self._build_ui()
        self._update_cmd_preview()

    def _build_ui(self) -> None:
        pad = {"padx": 10, "pady": 6}

        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True, padx=12, pady=12)

        # Instance ID (bilgi amaçlı)
        ttk.Label(frm, text="Bulut sunucusu kimliği (Instance ID):").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.var_instance_id).grid(row=0, column=1, sticky="ew", **pad)

        # Host
        ttk.Label(frm, text="Genel DNS / IP:").grid(row=1, column=0, sticky="w", **pad)
        host_entry = ttk.Entry(frm, textvariable=self.var_host)
        host_entry.grid(row=1, column=1, sticky="ew", **pad)

        # Port
        ttk.Label(frm, text="Port:").grid(row=2, column=0, sticky="w", **pad)
        port_entry = ttk.Entry(frm, textvariable=self.var_port, width=10)
        port_entry.grid(row=2, column=1, sticky="w", **pad)

        # Username
        ttk.Label(frm, text="Kullanıcı adı (User):").grid(row=3, column=0, sticky="w", **pad)
        user_row = ttk.Frame(frm)
        user_row.grid(row=3, column=1, sticky="w", **pad)
        user_entry = ttk.Entry(user_row, textvariable=self.var_user, width=24)
        user_entry.pack(side="left")
        ttk.Label(user_row, text="(Ubuntu: ubuntu, Amazon Linux: ec2-user)").pack(side="left", padx=(10, 0))

        # Key file
        ttk.Label(frm, text="Özel anahtar dosyası (Keypair .pem):").grid(row=4, column=0, sticky="w", **pad)
        key_row = ttk.Frame(frm)
        key_row.grid(row=4, column=1, sticky="ew", **pad)
        key_entry = ttk.Entry(key_row, textvariable=self.var_key)
        key_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(key_row, text="Seç...", command=self._pick_key).pack(side="left", padx=(8, 0))

        # chmod 400 (Linux/mac için)
        ttk.Label(frm, text="chmod (Linux/mac için, gerekirse):").grid(row=5, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.var_chmod, state="readonly").grid(row=5, column=1, sticky="ew", **pad)

        # SSH command preview + copy
        ttk.Label(frm, text="Örnek komut:").grid(row=6, column=0, sticky="w", **pad)
        cmd_row = ttk.Frame(frm)
        cmd_row.grid(row=6, column=1, sticky="ew", **pad)
        cmd_entry = ttk.Entry(cmd_row, textvariable=self.var_cmd, state="readonly")
        cmd_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(cmd_row, text="Kopyala", command=self._copy_cmd).pack(side="left", padx=(8, 0))

        # Buttons
        btns = ttk.Frame(frm)
        btns.grid(row=7, column=1, sticky="w", **pad)
        self.btn_connect = ttk.Button(btns, text="Bağlan (Hızlı Test)", command=self._on_connect_clicked)
        self.btn_connect.pack(side="left")
        self.btn_open_terminal = ttk.Button(btns, text="SSH istemcisi aç (CMD)", command=self._on_open_terminal_clicked)
        self.btn_open_terminal.pack(side="left", padx=(8, 0))
        self.btn_disconnect = ttk.Button(btns, text="Bağlantıyı Kes", command=self._disconnect, state="disabled")
        self.btn_disconnect.pack(side="left", padx=(8, 0))

        # Status
        sep = ttk.Separator(frm, orient="horizontal")
        sep.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(10, 10))

        ttk.Label(frm, text="Durum:").grid(row=9, column=0, sticky="w", **pad)
        ttk.Label(frm, textvariable=self.var_status).grid(row=9, column=1, sticky="w", **pad)

        ttk.Label(frm, text="Bilgi:").grid(row=10, column=0, sticky="w", **pad)
        info = ttk.Label(frm, textvariable=self.var_last_info, wraplength=700, justify="left")
        info.grid(row=10, column=1, sticky="w", **pad)

        frm.columnconfigure(1, weight=1)

        # canlı güncelleme
        for v in (self.var_instance_id, self.var_host, self.var_port, self.var_user, self.var_key):
            v.trace_add("write", lambda *_: self._update_cmd_preview())

    def _pick_key(self) -> None:
        path = filedialog.askopenfilename(
            title="Private key dosyası seç",
            filetypes=[
                ("Private key", "*.pem *.key *.ppk *"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.var_key.set(path)
            self._update_cmd_preview()

    def _update_cmd_preview(self) -> None:
        host = self.var_host.get().strip() or "<host>"
        user = self.var_user.get().strip() or "<user>"
        port = self.var_port.get().strip() or "22"
        key = self.var_key.get().strip() or "<key.pem>"
        ssh = "ssh"

        # AWS örneği: port 22 ise -p yazma
        if port == "22":
            self.var_cmd.set(f'{ssh} -i "{key}" {user}@{host}')
        else:
            self.var_cmd.set(f'{ssh} -i "{key}" -p {port} {user}@{host}')

        # chmod notu
        key_for_chmod = os.path.basename(key) if key and key != "<key.pem>" else "beatify_keypair.pem"
        if os.name == "nt":
            self.var_chmod.set('Windows: chmod gerekmez (Linux/mac/WSL: chmod 400 "key.pem")')
        else:
            self.var_chmod.set(f'chmod 400 "{key_for_chmod}"')

    def _copy_cmd(self) -> None:
        cmd = self.var_cmd.get()
        if not cmd:
            return
        self.clipboard_clear()
        self.clipboard_append(cmd)
        self.var_last_info.set("Komut panoya kopyalandı.")

    def _validate_inputs(self) -> Tuple[str, int, str, str]:
        host = self.var_host.get().strip()
        if not host:
            raise ValueError("Host/IP boş olamaz.")

        try:
            port = int(self.var_port.get().strip())
        except ValueError:
            raise ValueError("Port sayısal olmalı.")
        if not (1 <= port <= 65535):
            raise ValueError("Port 1-65535 aralığında olmalı.")

        username = self.var_user.get().strip()
        if not username:
            raise ValueError("Username boş olamaz.")

        key_path = self.var_key.get().strip()
        if not key_path:
            raise ValueError("Private key dosyası seçmelisiniz.")
        if not os.path.exists(key_path):
            raise ValueError("Private key dosyası bulunamadı.")

        return host, port, username, key_path

    def _on_connect_clicked(self) -> None:
        if self._connected:
            messagebox.showinfo("Bilgi", "Zaten bağlısınız.")
            return

        try:
            host, port, username, key_path = self._validate_inputs()
        except Exception as e:
            messagebox.showerror("Hata", str(e))
            return

        # Passphrase sor (opsiyonel): anahtar şifreliyse ilk denemede hata alıp tekrar soracağız.
        self._set_busy(True)
        self.var_status.set("Connecting...")
        self.var_last_info.set("")

        def worker() -> None:
            try:
                _, banner = _connect_ssh(host, port, username, key_path)
                self._connected = True
                self._ui_success(banner)
                return
            except (socket.error, TimeoutError) as e:
                self._ui_error(str(e))
                return
            except Exception as e:
                self._ui_error(str(e))
                return

        threading.Thread(target=worker, daemon=True).start()

    def _on_open_terminal_clicked(self) -> None:
        try:
            host, port, username, key_path = self._validate_inputs()
        except Exception as e:
            messagebox.showerror("Hata", str(e))
            return

        try:
            _open_interactive_ssh(host, port, username, key_path)
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def _disconnect(self) -> None:
        self._connected = False
        self.var_status.set("Disconnected")
        self.var_last_info.set("")
        self._set_busy(False, connected=False)

    def _ui_success(self, info: str) -> None:
        def update() -> None:
            self.var_status.set("Connected")
            self.var_last_info.set(info)
            self._set_busy(False, connected=True)

        self.after(0, update)

    def _ui_error(self, msg: str) -> None:
        def update() -> None:
            self.var_status.set("Error")
            self.var_last_info.set(msg)
            self._set_busy(False, connected=False)
            messagebox.showerror("Bağlantı Hatası", msg)

        self.after(0, update)

    def _set_busy(self, busy: bool, connected: bool = False) -> None:
        if busy:
            self.btn_connect.configure(state="disabled")
            self.btn_disconnect.configure(state="disabled")
        else:
            self.btn_connect.configure(state="disabled" if connected else "normal")
            self.btn_disconnect.configure(state="normal" if connected else "disabled")


def main() -> None:
    app = SSHGui()
    app.mainloop()


if __name__ == "__main__":
    main()

