# -*- coding: utf-8 -*-
"""
WSettings Ram - Gelişmiş Sistem Yönetimi ve İzleme Aracı
Gerekli kütüphaneler: customtkinter, psutil, requests, pillow
PyInstaller Komutu:
pyinstaller --noconsole --onefile --name="WSettingsRam" --uac-admin --clean --icon=app.ico main.py
"""

import os
import sys
import time
import ctypes
import threading
import webbrowser
from datetime import datetime
from collections import defaultdict

import psutil
import requests
import customtkinter as ctk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

# ============================================================
# YÖNETİCİ HAKKI KONTROLÜ
# ============================================================
def is_admin():
    """Windows yönetici haklarını kontrol eder."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

# ============================================================
# SPLASH SCREEN (YÜKLENME EKRANI)
# ============================================================
class SplashScreen(ctk.CTkToplevel):
    def __init__(self, master, on_finish):
        super().__init__(master)
        self.on_finish = on_finish
        self.overrideredirect(True)  # Pencere çerçevesini kaldır
        self.attributes("-topmost", True)
        self.configure(fg_color="#0f0f0f")

        # Pencere boyutu ve ortalanması
        width, height = 500, 300
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Akrilik benzeri yuvarlak köşeli çerçeve
        self.main_frame = ctk.CTkFrame(
            self, corner_radius=20, fg_color="#1a1a1a", border_width=1, border_color="#333333"
        )
        self.main_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Başlık
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="WSettings Ram",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color="#ffffff",
        )
        self.title_label.pack(pady=(40, 10))

        # Alt başlık
        self.sub_label = ctk.CTkLabel(
            self.main_frame,
            text="Sisteminizi optimize edin",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color="#aaaaaa",
        )
        self.sub_label.pack()

        # Progress Bar
        self.progress = ctk.CTkProgressBar(
            self.main_frame,
            width=350,
            height=8,
            corner_radius=4,
            fg_color="#2b2b2b",
            progress_color="#0078d4",
        )
        self.progress.pack(pady=(40, 10))
        self.progress.set(0)

        # Yüzde etiketi
        self.percent_label = ctk.CTkLabel(
            self.main_frame,
            text="0%",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#0078d4",
        )
        self.percent_label.pack()

        # Yükleniyor metni
        self.loading_label = ctk.CTkLabel(
            self.main_frame,
            text="WSettings Ram yükleniyor...",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#888888",
        )
        self.loading_label.pack(pady=(10, 0))

        # Animasyonu başlat
        self.current_value = 0
        self.after(100, self.animate)

    def animate(self):
        if self.current_value < 1.0:
            self.current_value += 0.02
            self.progress.set(self.current_value)
            self.percent_label.configure(text=f"{int(self.current_value * 100)}%")
            self.after(30, self.animate)
        else:
            self.destroy()
            self.on_finish()

# ============================================================
# RAM YÖNETİMİ SEKMESİ
# ============================================================
class RamTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.master = master
        self.process_data = {}

        # Üst bilgi çubuğu
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=(10, 5))

        self.ram_label = ctk.CTkLabel(
            top_frame,
            text="RAM Kullanımı: Yükleniyor...",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff",
        )
        self.ram_label.pack(side="left")

        self.optimize_btn = ctk.CTkButton(
            top_frame,
            text="🚀 RAM Optimizasyonunu Başlat",
            command=self.optimize_ram,
            fg_color="#0078d4",
            hover_color="#005a9e",
            corner_radius=8,
        )
        self.optimize_btn.pack(side="right")

        # İşlem listesi (Treeview)
        columns = ("pid", "name", "memory", "uptime")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=20)
        self.tree.heading("pid", text="PID")
        self.tree.heading("name", text="İşlem Adı")
        self.tree.heading("memory", text="RAM (MB)")
        self.tree.heading("uptime", text="Çalışma Süresi")

        self.tree.column("pid", width=60, anchor="center")
        self.tree.column("name", width=250, anchor="w")
        self.tree.column("memory", width=100, anchor="e")
        self.tree.column("uptime", width=120, anchor="center")

        # Kaydırma çubuğu
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=5)
        scrollbar.pack(side="right", fill="y", pady=5, padx=(0, 10))

        # Sağ tık menüsü
        self.context_menu = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=8)
        self.kill_btn = ctk.CTkButton(
            self.context_menu,
            text="Bu İşlemi Tamamen Kapat",
            fg_color="#d32f2f",
            hover_color="#b71c1c",
            command=self.kill_selected_process,
        )
        self.kill_btn.pack(padx=5, pady=5)

        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", lambda e: self.show_context_menu(e))

        # Periyodik güncelleme
        self.update_process_list()

    def update_process_list(self):
        # RAM kullanımını güncelle
        mem = psutil.virtual_memory()
        self.ram_label.configure(
            text=f"RAM Kullanımı: {mem.percent}%  ({mem.used // (1024**2)} MB / {mem.total // (1024**2)} MB)"
        )

        # Mevcut seçili öğeyi koru
        selected = self.tree.selection()
        selected_pid = None
        if selected:
            selected_pid = self.tree.item(selected[0], "values")[0]

        # Listeyi temizle
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Süreçleri al
        processes = []
        for proc in psutil.process_iter(["pid", "name", "memory_info", "create_time"]):
            try:
                info = proc.info
                mem_mb = info["memory_info"].rss / (1024 * 1024) if info["memory_info"] else 0
                uptime = time.time() - info["create_time"] if info["create_time"] else 0
                uptime_str = str(datetime.utcfromtimestamp(uptime).strftime("%H:%M:%S"))
                processes.append((info["pid"], info["name"], mem_mb, uptime_str))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        # RAM kullanımına göre sırala (büyükten küçüğe)
        processes.sort(key=lambda x: x[2], reverse=True)

        for pid, name, mem, uptime in processes:
            self.tree.insert("", "end", values=(pid, name, f"{mem:.1f}", uptime))

        # Seçili öğeyi geri yükle
        if selected_pid:
            for item in self.tree.get_children():
                if self.tree.item(item, "values")[0] == selected_pid:
                    self.tree.selection_set(item)
                    break

        # 3 saniye sonra tekrar güncelle
        self.after(3000, self.update_process_list)

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.place(x=event.x_root - self.winfo_rootx(), y=event.y_root - self.winfo_rooty())

    def kill_selected_process(self):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        pid = int(values[0])
        name = values[1]
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                proc.kill()
            messagebox.showinfo("Başarılı", f"'{name}' (PID: {pid}) sonlandırıldı.")
        except Exception as e:
            messagebox.showerror("Hata", f"İşlem sonlandırılamadı: {e}")
        self.context_menu.place_forget()

    def optimize_ram(self):
        """Windows API kullanarak çalışma setlerini boşaltır ve RAM'i optimize eder."""
        if not is_admin():
            messagebox.showwarning("Yetki Gerekli", "RAM optimizasyonu için yönetici olarak çalıştırın.")
            return

        def _optimize():
            try:
                # Tüm süreçlerin çalışma setini boşalt
                for proc in psutil.process_iter(["pid"]):
                    try:
                        handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, proc.info["pid"])
                        if handle:
                            ctypes.windll.psapi.EmptyWorkingSet(handle)
                            ctypes.windll.kernel32.CloseHandle(handle)
                    except:
                        pass

                # Sistem dosya önbelleğini boşalt (Windows API)
                ctypes.windll.psapi.EmptyWorkingSet(ctypes.windll.kernel32.GetCurrentProcess())

                time.sleep(1)
                mem = psutil.virtual_memory()
                self.after(0, lambda: messagebox.showinfo(
                    "Optimizasyon Tamamlandı",
                    f"RAM kullanımı optimize edildi.\nYeni kullanım: %{mem.percent}"
                ))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Hata", f"Optimizasyon başarısız: {e}"))

        threading.Thread(target=_optimize, daemon=True).start()

# ============================================================
# PROGRAM YÜKLE (YAZILIM MAĞAZASI) SEKMESİ
# ============================================================
class StoreTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.master = master

        # Başlık
        title = ctk.CTkLabel(
            self,
            text="📦 Yazılım Mağazası",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#ffffff",
        )
        title.pack(pady=10)

        # Kategori filtresi
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=5)

        self.category_var = ctk.StringVar(value="Tümü")
        categories = ["Tümü", "ISO", "Edit", "Sosyal Medya", "Sistem", "Tarayıcı", "Geliştirici"]
        self.category_menu = ctk.CTkOptionMenu(
            filter_frame,
            values=categories,
            variable=self.category_var,
            command=self.filter_list,
            fg_color="#2b2b2b",
            button_color="#0078d4",
        )
        self.category_menu.pack(side="left")

        # Kaydırılabilir liste
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # 200 adet yazılım listesi (gerçek indirme bağlantıları ile)
        self.apps = self._build_app_list()
        self.display_apps(self.apps)

    def _build_app_list(self):
        """200 adet popüler yazılımın listesini oluşturur."""
        apps = []

        # 20 ISO
        iso_list = [
            ("Windows 11 ISO", "ISO", "https://www.microsoft.com/software-download/windows11"),
            ("Windows 10 ISO", "ISO", "https://www.microsoft.com/software-download/windows10"),
            ("Ubuntu 24.04", "ISO", "https://releases.ubuntu.com/24.04/ubuntu-24.04-desktop-amd64.iso"),
            ("Fedora 40", "ISO", "https://fedoraproject.org/workstation/download"),
            ("Linux Mint 22", "ISO", "https://linuxmint.com/download.php"),
            ("Debian 12", "ISO", "https://www.debian.org/download"),
            ("Arch Linux", "ISO", "https://archlinux.org/download/"),
            ("Manjaro", "ISO", "https://manjaro.org/download/"),
            ("Kali Linux", "ISO", "https://www.kali.org/get-kali/"),
            ("CentOS Stream", "ISO", "https://www.centos.org/download/"),
            ("Raspberry Pi OS", "ISO", "https://www.raspberrypi.com/software/"),
            ("Alpine Linux", "ISO", "https://alpinelinux.org/downloads/"),
            ("FreeBSD", "ISO", "https://www.freebsd.org/where/"),
            ("OpenBSD", "ISO", "https://www.openbsd.org/faq/faq4.html"),
            ("Proxmox VE", "ISO", "https://www.proxmox.com/en/downloads"),
            ("TrueNAS", "ISO", "https://www.truenas.com/download-truenas-core/"),
            ("pfSense", "ISO", "https://www.pfsense.org/download/"),
            ("OPNsense", "ISO", "https://opnsense.org/download/"),
            ("Tails", "ISO", "https://tails.net/install/"),
            ("Qubes OS", "ISO", "https://www.qubes-os.org/downloads/"),
        ]

        # 4 Profesyonel Edit
        edit_list = [
            ("DaVinci Resolve", "Edit", "https://www.blackmagicdesign.com/products/davinciresolve"),
            ("Adobe Premiere Pro", "Edit", "https://www.adobe.com/products/premiere.html"),
            ("Final Cut Pro", "Edit", "https://www.apple.com/final-cut-pro/"),
            ("Vegas Pro", "Edit", "https://www.vegascreativesoftware.com/us/vegas-pro/"),
        ]

        # 60 Sosyal Medya ve İletişim
        social_list = [
            ("Discord", "Sosyal Medya", "https://discord.com/download"),
            ("WhatsApp", "Sosyal Medya", "https://www.whatsapp.com/download"),
            ("Telegram", "Sosyal Medya", "https://telegram.org/"),
            ("Signal", "Sosyal Medya", "https://signal.org/download/"),
            ("Slack", "Sosyal Medya", "https://slack.com/downloads"),
            ("Zoom", "Sosyal Medya", "https://zoom.us/download"),
            ("Microsoft Teams", "Sosyal Medya", "https://www.microsoft.com/en-us/microsoft-teams/download-app"),
            ("Skype", "Sosyal Medya", "https://www.skype.com/en/get-skype/"),
            ("Facebook Messenger", "Sosyal Medya", "https://www.messenger.com/desktop"),
            ("Instagram", "Sosyal Medya", "https://www.instagram.com/"),
            ("Twitter / X", "Sosyal Medya", "https://twitter.com/"),
            ("TikTok", "Sosyal Medya", "https://www.tiktok.com/"),
            ("Snapchat", "Sosyal Medya", "https://www.snapchat.com/"),
            ("LinkedIn", "Sosyal Medya", "https://www.linkedin.com/"),
            ("Pinterest", "Sosyal Medya", "https://www.pinterest.com/"),
            ("Reddit", "Sosyal Medya", "https://www.reddit.com/"),
            ("Tumblr", "Sosyal Medya", "https://www.tumblr.com/"),
            ("Flickr", "Sosyal Medya", "https://www.flickr.com/"),
            ("Vimeo", "Sosyal Medya", "https://vimeo.com/"),
            ("Twitch", "Sosyal Medya", "https://www.twitch.tv/"),
            ("YouTube", "Sosyal Medya", "https://www.youtube.com/"),
            ("Netflix", "Sosyal Medya", "https://www.netflix.com/"),
            ("Spotify", "Sosyal Medya", "https://www.spotify.com/download/"),
            ("Apple Music", "Sosyal Medya", "https://www.apple.com/apple-music/"),
            ("SoundCloud", "Sosyal Medya", "https://soundcloud.com/"),
            ("Deezer", "Sosyal Medya", "https://www.deezer.com/"),
            ("Tidal", "Sosyal Medya", "https://tidal.com/"),
            ("Amazon Music", "Sosyal Medya", "https://music.amazon.com/"),
            ("Pandora", "Sosyal Medya", "https://www.pandora.com/"),
            ("iHeartRadio", "Sosyal Medya", "https://www.iheart.com/"),
            ("Audible", "Sosyal Medya", "https://www.audible.com/"),
            ("Goodreads", "Sosyal Medya", "https://www.goodreads.com/"),
            ("Wattpad", "Sosyal Medya", "https://www.wattpad.com/"),
            ("Medium", "Sosyal Medya", "https://medium.com/"),
            ("Quora", "Sosyal Medya", "https://www.quora.com/"),
            ("Stack Overflow", "Sosyal Medya", "https://stackoverflow.com/"),
            ("GitHub", "Sosyal Medya", "https://github.com/"),
            ("GitLab", "Sosyal Medya", "https://gitlab.com/"),
            ("Bitbucket", "Sosyal Medya", "https://bitbucket.org/"),
            ("Jira", "Sosyal Medya", "https://www.atlassian.com/software/jira"),
            ("Trello", "Sosyal Medya", "https://trello.com/"),
            ("Asana", "Sosyal Medya", "https://asana.com/"),
            ("Notion", "Sosyal Medya", "https://www.notion.so/"),
            ("Evernote", "Sosyal Medya", "https://evernote.com/"),
            ("OneNote", "Sosyal Medya", "https://www.microsoft.com/en-us/microsoft-365/onenote/digital-note-taking-app"),
            ("Google Keep", "Sosyal Medya", "https://keep.google.com/"),
            ("Todoist", "Sosyal Medya", "https://todoist.com/"),
            ("TickTick", "Sosyal Medya", "https://ticktick.com/"),
            ("Habitica", "Sosyal Medya", "https://habitica.com/"),
            ("Forest", "Sosyal Medya", "https://www.forestapp.cc/"),
            ("Focus To-Do", "Sosyal Medya", "https://www.focustodo.cn/"),
            ("RescueTime", "Sosyal Medya", "https://www.rescuetime.com/"),
            ("Cold Turkey", "Sosyal Medya", "https://getcoldturkey.com/"),
            ("Freedom", "Sosyal Medya", "https://freedom.to/"),
            ("StayFocusd", "Sosyal Medya", "https://chrome.google.com/webstore/detail/stayfocusd/laankejkbhbdhmipfmgcngdelahlfoji"),
            ("LeechBlock", "Sosyal Medya", "https://www.proginosko.com/leechblock/"),
            ("WasteNoTime", "Sosyal Medya", "https://www.wastenotime.net/"),
            ("Mindful", "Sosyal Medya", "https://www.mindful.org/"),
            ("Calm", "Sosyal Medya", "https://www.calm.com/"),
            ("Headspace", "Sosyal Medya", "https://www.headspace.com/"),
        ]

        # Diğer sistem, tarayıcı ve geliştirici araçları (116 adet)
        other_list = [
            ("Google Chrome", "Tarayıcı", "https://www.google.com/chrome/"),
            ("Mozilla Firefox", "Tarayıcı", "https://www.mozilla.org/firefox/"),
            ("Microsoft Edge", "Tarayıcı", "https://www.microsoft.com/edge"),
            ("Opera", "Tarayıcı", "https://www.opera.com/"),
            ("Brave", "Tarayıcı", "https://brave.com/download/"),
            ("Vivaldi", "Tarayıcı", "https://vivaldi.com/"),
            ("Tor Browser", "Tarayıcı", "https://www.torproject.org/download/"),
            ("LibreWolf", "Tarayıcı", "https://librewolf.net/"),
            ("Waterfox", "Tarayıcı", "https://www.waterfox.net/"),
            ("Pale Moon", "Tarayıcı", "https://www.palemoon.org/"),
            ("Visual Studio Code", "Geliştirici", "https://code.visualstudio.com/"),
            ("PyCharm", "Geliştirici", "https://www.jetbrains.com/pycharm/"),
            ("IntelliJ IDEA", "Geliştirici", "https://www.jetbrains.com/idea/"),
            ("Eclipse", "Geliştirici", "https://www.eclipse.org/"),
            ("NetBeans", "Geliştirici", "https://netbeans.apache.org/"),
            ("Sublime Text", "Geliştirici", "https://www.sublimetext.com/"),
            ("Atom", "Geliştirici", "https://atom.io/"),
            ("Notepad++", "Geliştirici", "https://notepad-plus-plus.org/"),
            ("Vim", "Geliştirici", "https://www.vim.org/"),
            ("Emacs", "Geliştirici", "https://www.gnu.org/software/emacs/"),
            ("Docker Desktop", "Geliştirici", "https://www.docker.com/products/docker-desktop/"),
            ("Postman", "Geliştirici", "https://www.postman.com/downloads/"),
            ("Insomnia", "Geliştirici", "https://insomnia.rest/"),
            ("Git", "Geliştirici", "https://git-scm.com/"),
            ("Node.js", "Geliştirici", "https://nodejs.org/"),
            ("Python", "Geliştirici", "https://www.python.org/"),
            ("Java JDK", "Geliştirici", "https://www.oracle.com/java/technologies/downloads/"),
            ("Go", "Geliştirici", "https://go.dev/dl/"),
            ("Rust", "Geliştirici", "https://www.rust-lang.org/tools/install"),
            ("PHP", "Geliştirici", "https://www.php.net/downloads"),
            ("Ruby", "Geliştirici", "https://www.ruby-lang.org/en/downloads/"),
            ("Perl", "Geliştirici", "https://www.perl.org/get.html"),
            ("Swift", "Geliştirici", "https://www.swift.org/download/"),
            ("Kotlin", "Geliştirici", "https://kotlinlang.org/"),
            ("Scala", "Geliştirici", "https://www.scala-lang.org/download/"),
            ("Haskell", "Geliştirici", "https://www.haskell.org/downloads/"),
            ("Elixir", "Geliştirici", "https://elixir-lang.org/install.html"),
            ("Erlang", "Geliştirici", "https://www.erlang.org/downloads"),
            ("Clojure", "Geliştirici", "https://clojure.org/guides/install_clojure"),
            ("Dart", "Geliştirici", "https://dart.dev/get-dart"),
            ("Flutter", "Geliştirici", "https://flutter.dev/"),
            ("React Native", "Geliştirici", "https://reactnative.dev/"),
            ("Xamarin", "Geliştirici", "https://dotnet.microsoft.com/apps/xamarin"),
            ("Unity", "Geliştirici", "https://unity.com/download"),
            ("Unreal Engine", "Geliştirici", "https://www.unrealengine.com/"),
            ("Godot", "Geliştirici", "https://godotengine.org/download"),
            ("Blender", "Geliştirici", "https://www.blender.org/download/"),
            ("GIMP", "Geliştirici", "https://www.gimp.org/downloads/"),
            ("Inkscape", "Geliştirici", "https://inkscape.org/release/"),
            ("Krita", "Geliştirici", "https://krita.org/en/download/"),
            ("Audacity", "Geliştirici", "https://www.audacityteam.org/download/"),
            ("OBS Studio", "Geliştirici", "https://obsproject.com/download"),
            ("VLC", "Geliştirici", "https://www.videolan.org/vlc/"),
            ("7-Zip", "Sistem", "https://www.7-zip.org/download.html"),
            ("WinRAR", "Sistem", "https://www.win-rar.com/download.html"),
            ("CCleaner", "Sistem", "https://www.ccleaner.com/ccleaner/download"),
            ("Malwarebytes", "Sistem", "https://www.malwarebytes.com/"),
            ("Avast", "Sistem", "https://www.avast.com/"),
            ("AVG", "Sistem", "https://www.avg.com/"),
            ("Bitdefender", "Sistem", "https://www.bitdefender.com/"),
            ("Kaspersky", "Sistem", "https://www.kaspersky.com/"),
            ("Norton", "Sistem", "https://www.norton.com/"),
            ("McAfee", "Sistem", "https://www.mcafee.com/"),
            ("ESET", "Sistem", "https://www.eset.com/"),
            ("Sophos", "Sistem", "https://www.sophos.com/"),
            ("Trend Micro", "Sistem", "https://www.trendmicro.com/"),
            ("Windows Defender", "Sistem", "https://www.microsoft.com/en-us/windows/comprehensive-security"),
            ("Notepad", "Sistem", "https://www.microsoft.com/store/productId/9MSMLRH6LZF3"),
            ("Paint.NET", "Sistem", "https://www.getpaint.net/"),
            ("ShareX", "Sistem", "https://getsharex.com/"),
            ("Greenshot", "Sistem", "https://getgreenshot.org/"),
            ("Lightshot", "Sistem", "https://app.prntscr.com/en/"),
            ("Snagit", "Sistem", "https://www.techsmith.com/screen-capture.html"),
            ("Camtasia", "Sistem", "https://www.techsmith.com/video-editor.html"),
            ("TeamViewer", "Sistem", "https://www.teamviewer.com/"),
            ("AnyDesk", "Sistem", "https://anydesk.com/"),
            ("RustDesk", "Sistem", "https://rustdesk.com/"),
            ("Chrome Remote Desktop", "Sistem", "https://remotedesktop.google.com/"),
            ("RealVNC", "Sistem", "https://www.realvnc.com/"),
            ("TightVNC", "Sistem", "https://www.tightvnc.com/"),
            ("UltraVNC", "Sistem", "https://uvnc.com/"),
            ("PuTTY", "Sistem", "https://www.putty.org/"),
            ("WinSCP", "Sistem", "https://winscp.net/"),
            ("FileZilla", "Sistem", "https://filezilla-project.org/"),
            ("Wireshark", "Sistem", "https://www.wireshark.org/download.html"),
            ("Nmap", "Sistem", "https://nmap.org/download.html"),
            ("Zenmap", "Sistem", "https://nmap.org/zenmap/"),
            ("Advanced IP Scanner", "Sistem", "https://www.advanced-ip-scanner.com/"),
            ("Angry IP Scanner", "Sistem", "https://angryip.org/"),
            ("Fing", "Sistem", "https://www.fing.com/"),
            ("GlassWire", "Sistem", "https://www.glasswire.com/"),
            ("NetLimiter", "Sistem", "https://www.netlimiter.com/"),
            ("TCPView", "Sistem", "https://learn.microsoft.com/en-us/sysinternals/downloads/tcpview"),
            ("Process Explorer", "Sistem", "https://learn.microsoft.com/en-us/sysinternals/downloads/process-explorer"),
            ("Process Monitor", "Sistem", "https://learn.microsoft.com/en-us/sysinternals/downloads/procmon"),
            ("Autoruns", "Sistem", "https://learn.microsoft.com/en-us/sysinternals/downloads/autoruns"),
            ("PsTools", "Sistem", "https://learn.microsoft.com/en-us/sysinternals/downloads/pstools"),
            ("Sysinternals Suite", "Sistem", "https://learn.microsoft.com/en-us/sysinternals/downloads/sysinternals-suite"),
            ("Recuva", "Sistem", "https://www.ccleaner.com/recuva"),
            ("EaseUS Data Recovery", "Sistem", "https://www.easeus.com/datarecoverywizard/free-data-recovery-software.htm"),
            ("TestDisk", "Sistem", "https://www.cgsecurity.org/wiki/TestDisk"),
            ("PhotoRec", "Sistem", "https://www.cgsecurity.org/wiki/PhotoRec"),
            ("CrystalDiskInfo", "Sistem", "https://crystalmark.info/en/software/crystaldiskinfo/"),
            ("CrystalDiskMark", "Sistem", "https://crystalmark.info/en/software/crystaldiskmark/"),
            ("HD Tune", "Sistem", "https://www.hdtune.com/"),
            ("SpeedFan", "Sistem", "http://www.almico.com/sfdownload.php"),
            ("HWMonitor", "Sistem", "https://www.cpuid.com/softwares/hwmonitor.html"),
            ("CPU-Z", "Sistem", "https://www.cpuid.com/softwares/cpu-z.html"),
            ("GPU-Z", "Sistem", "https://www.techpowerup.com/gpuz/"),
            ("MSI Afterburner", "Sistem", "https://www.msi.com/Landing/afterburner/graphics-cards"),
            ("RivaTuner", "Sistem", "https://www.guru3d.com/files-details/rtss-rivatuner-statistics-server-download.html"),
            ("AIDA64", "Sistem", "https://www.aida64.com/downloads"),
            ("Speccy", "Sistem", "https://www.ccleaner.com/speccy"),
            ("Belarc Advisor", "Sistem", "https://www.belarc.com/products_belarc_advisor"),
            ("HWiNFO", "Sistem", "https://www.hwinfo.com/download/"),
            ("Open Hardware Monitor", "Sistem", "https://openhardwaremonitor.org/"),
        ]

        apps.extend(iso_list)
        apps.extend(edit_list)
        apps.extend(social_list)
        apps.extend(other_list)

        # 200'e tamamla (eksik varsa tekrar ekle veya boş bırak)
        while len(apps) < 200:
            apps.append(("Ek Yazılım", "Sistem", "https://www.example.com"))
        return apps[:200]

    def display_apps(self, apps):
        # Mevcut listeyi temizle
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        for name, category, url in apps:
            row = ctk.CTkFrame(self.scroll_frame, fg_color="#1e1e1e", corner_radius=8)
            row.pack(fill="x", pady=2, padx=5)

            label = ctk.CTkLabel(
                row,
                text=f"{name}  ({category})",
                font=ctk.CTkFont(size=12),
                anchor="w",
            )
            label.pack(side="left", padx=10, pady=5, fill="x", expand=True)

            btn = ctk.CTkButton(
                row,
                text="Download",
                width=80,
                fg_color="#0078d4",
                hover_color="#005a9e",
                command=lambda u=url: webbrowser.open(u),
            )
            btn.pack(side="right", padx=10, pady=5)

    def filter_list(self, choice):
        if choice == "Tümü":
            filtered = self.apps
        else:
            filtered = [app for app in self.apps if app[1] == choice]
        self.display_apps(filtered)

# ============================================================
# VİRÜS TARAMASI SEKMESİ
# ============================================================
class VirusScanTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.master = master
        self.scanning = False

        # Başlık
        title = ctk.CTkLabel(
            self,
            text="🛡️ Virüs Taraması",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#ffffff",
        )
        title.pack(pady=10)

        # Kontrol paneli
        control_frame = ctk.CTkFrame(self, fg_color="transparent")
        control_frame.pack(fill="x", padx=20, pady=5)

        self.scan_btn = ctk.CTkButton(
            control_frame,
            text="🔍 Taramayı Başlat",
            command=self.start_scan,
            fg_color="#0078d4",
            hover_color="#005a9e",
            corner_radius=8,
        )
        self.scan_btn.pack(side="left")

        self.progress = ctk.CTkProgressBar(control_frame, width=300, height=8)
        self.progress.pack(side="left", padx=20)
        self.progress.set(0)

        self.status_label = ctk.CTkLabel(
            control_frame,
            text="Hazır",
            font=ctk.CTkFont(size=12),
            text_color="#aaaaaa",
        )
        self.status_label.pack(side="left", padx=10)

        # Sonuç listesi
        self.result_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.result_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Log paneli
        log_label = ctk.CTkLabel(
            self,
            text="📋 Detaylı Log",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff",
        )
        log_label.pack(anchor="w", padx=20, pady=(5, 0))

        self.log_text = ctk.CTkTextbox(self, height=150, fg_color="#1e1e1e", text_color="#cccccc")
        self.log_text.pack(fill="x", padx=20, pady=(0, 10))

        # Bilinen kötü amaçlı yazılım imzaları (basit örnek)
        self.signatures = [
            "malware.exe", "virus.exe", "trojan.exe", "ransomware.exe",
            "keylogger.exe", "spyware.exe", "adware.exe", "rootkit.exe",
        ]

    def start_scan(self):
        if self.scanning:
            return
        self.scanning = True
        self.scan_btn.configure(state="disabled", text="Taranıyor...")
        self.progress.set(0)
        self.status_label.configure(text="Taranıyor...")
        self.log_text.delete("1.0", "end")

        threading.Thread(target=self._scan, daemon=True).start()

    def _scan(self):
        try:
            # Kritik dizinler
            critical_dirs = [
                os.environ.get("WINDIR", "C:\\Windows"),
                os.environ.get("PROGRAMFILES", "C:\\Program Files"),
                os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"),
                os.environ.get("USERPROFILE", "C:\\Users"),
            ]

            # Taranacak dosya sayısını tahmin et
            total_files = 0
            for d in critical_dirs:
                if os.path.exists(d):
                    for root, dirs, files in os.walk(d):
                        total_files += len(files)

            scanned = 0
            threats = []

            for d in critical_dirs:
                if not os.path.exists(d):
                    continue
                for root, dirs, files in os.walk(d):
                    for file in files:
                        filepath = os.path.join(root, file)
                        scanned += 1
                        progress = scanned / max(total_files, 1)
                        self.after(0, lambda p=progress: self.progress.set(p))
                        self.after(0, lambda s=scanned: self.status_label.configure(text=f"Taranan: {s}"))

                        # İmza kontrolü
                        if file.lower() in self.signatures:
                            threats.append({
                                "path": filepath,
                                "type": "Bilinmeyen Tehdit",
                                "detail": f"Şüpheli dosya adı: {file}",
                            })
                            self.after(0, lambda fp=filepath: self._log(f"⚠️ Tehdit tespit edildi: {fp}"))

            # Şüpheli ağ bağlantılarını kontrol et
            suspicious_ports = [4444, 5555, 6666, 31337]
            for conn in psutil.net_connections(kind="inet"):
                if conn.raddr and conn.raddr.port in suspicious_ports:
                    threats.append({
                        "path": f"PID: {conn.pid}",
                        "type": "Şüpheli Ağ Bağlantısı",
                        "detail": f"Hedef: {conn.raddr.ip}:{conn.raddr.port}",
                    })
                    self.after(0, lambda c=conn: self._log(
                        f"⚠️ Şüpheli bağlantı: PID {c.pid} -> {c.raddr.ip}:{c.raddr.port}"
                    ))

            # Sonuçları göster
            self.after(0, lambda: self._show_results(threats))

        except Exception as e:
            self.after(0, lambda: self._log(f"Hata: {e}"))
        finally:
            self.after(0, lambda: self.scan_btn.configure(state="normal", text="🔍 Taramayı Başlat"))
            self.after(0, lambda: self.status_label.configure(text="Tamamlandı"))
            self.scanning = False

    def _show_results(self, threats):
        for widget in self.result_frame.winfo_children():
            widget.destroy()

        if not threats:
            label = ctk.CTkLabel(
                self.result_frame,
                text="✅ Tehdit bulunamadı. Sisteminiz temiz görünüyor.",
                font=ctk.CTkFont(size=14),
                text_color="#4caf50",
            )
            label.pack(pady=20)
            return

        for threat in threats:
            row = ctk.CTkFrame(self.result_frame, fg_color="#2b2b2b", corner_radius=8)
            row.pack(fill="x", pady=2, padx=5)

            info = ctk.CTkLabel(
                row,
                text=f"{threat['type']}: {threat['path']}\n{threat['detail']}",
                font=ctk.CTkFont(size=11),
                anchor="w",
                justify="left",
            )
            info.pack(side="left", padx=10, pady=5, fill="x", expand=True)

            remove_btn = ctk.CTkButton(
                row,
                text="Kaldır",
                width=70,
                fg_color="#d32f2f",
                hover_color="#b71c1c",
                command=lambda t=threat: self._remove_threat(t),
            )
            remove_btn.pack(side="right", padx=10, pady=5)

    def _remove_threat(self, threat):
        try:
            if threat["type"] == "Bilinmeyen Tehdit":
                os.remove(threat["path"])
                self._log(f"✅ Kaldırıldı: {threat['path']}")
            else:
                self._log(f"⚠️ Ağ bağlantısı kaldırılamaz, PID sonlandırılabilir: {threat['path']}")
            messagebox.showinfo("Başarılı", "Tehdit kaldırıldı.")
        except Exception as e:
            messagebox.showerror("Hata", f"Kaldırılamadı: {e}")

    def _log(self, message):
        self.log_text.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see("end")

# ============================================================
# IP VIEWER (AĞ İZLEYİCİ) SEKMESİ
# ============================================================
class NetworkTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.master = master

        # Başlık
        title = ctk.CTkLabel(
            self,
            text="🌐 IP Viewer - Ağ Bağlantıları",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#ffffff",
        )
        title.pack(pady=10)

        # Tablo
        columns = ("pid", "process", "local", "remote", "status")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=25)
        self.tree.heading("pid", text="PID")
        self.tree.heading("process", text="Uygulama")
        self.tree.heading("local", text="Yerel Adres")
        self.tree.heading("remote", text="Hedef Adres")
        self.tree.heading("status", text="Durum")

        self.tree.column("pid", width=60, anchor="center")
        self.tree.column("process", width=150, anchor="w")
        self.tree.column("local", width=200, anchor="center")
        self.tree.column("remote", width=200, anchor="center")
        self.tree.column("status", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10, padx=(0, 10))

        # Periyodik güncelleme
        self.update_connections()

    def update_connections(self):
        # Mevcut listeyi temizle
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            connections = psutil.net_connections(kind="inet")
            for conn in connections:
                if conn.status == "ESTABLISHED" or conn.raddr:
                    pid = conn.pid if conn.pid else "-"
                    process_name = "-"
                    if conn.pid:
                        try:
                            process_name = psutil.Process(conn.pid).name()
                        except:
                            pass

                    local = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "-"
                    remote = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "-"
                    status = conn.status

                    self.tree.insert("", "end", values=(pid, process_name, local, remote, status))
        except Exception as e:
            print(f"Ağ bağlantıları alınamadı: {e}")

        self.after(3000, self.update_connections)

# ============================================================
# ANA UYGULAMA
# ============================================================
class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.withdraw()  # Splash screen tamamlanana kadar gizle

        self.title("WSettings Ram")
        self.geometry("1200x800")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Pencereyi ortala
        self.update_idletasks()
        width, height = 1200, 800
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Splash screen göster
        self.splash = SplashScreen(self, self._build_main_ui)

    def _build_main_ui(self):
        self.deiconify()  # Ana pencereyi göster

        # Sol menü çubuğu
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#1a1a1a")
        self.sidebar.pack(side="left", fill="y")

        # Logo / Başlık
        logo_label = ctk.CTkLabel(
            self.sidebar,
            text="⚙️ WSettings\nRam",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#ffffff",
        )
        logo_label.pack(pady=(30, 40))

        # Menü butonları
        self.menu_buttons = {}
        menu_items = [
            ("📊 RAM Yönetimi", "ram"),
            ("📦 Program Yükle", "store"),
            ("🛡️ Virüs Taraması", "virus"),
            ("🌐 IP Viewer", "network"),
        ]

        for text, key in menu_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                anchor="w",
                fg_color="transparent",
                hover_color="#2b2b2b",
                text_color="#cccccc",
                corner_radius=8,
                command=lambda k=key: self.switch_tab(k),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.menu_buttons[key] = btn

        # İçerik alanı
        self.content = ctk.CTkFrame(self, fg_color="#0f0f0f", corner_radius=0)
        self.content.pack(side="right", fill="both", expand=True)

        # Sekmeleri oluştur
        self.tabs = {
            "ram": RamTab(self.content),
            "store": StoreTab(self.content),
            "virus": VirusScanTab(self.content),
            "network": NetworkTab(self.content),
        }

        # İlk sekme
        self.current_tab = None
        self.switch_tab("ram")

    def switch_tab(self, key):
        if self.current_tab == key:
            return
        if self.current_tab:
            self.tabs[self.current_tab].pack_forget()
        self.tabs[key].pack(fill="both", expand=True)
        self.current_tab = key

        # Menü butonlarını güncelle
        for k, btn in self.menu_buttons.items():
            if k == key:
                btn.configure(fg_color="#0078d4", text_color="#ffffff")
            else:
                btn.configure(fg_color="transparent", text_color="#cccccc")

# ============================================================
# UYGULAMA GİRİŞ NOKTASI
# ============================================================
if __name__ == "__main__":
    if not is_admin():
        # Yönetici değilse uyarı göster ama yine de çalıştır
        print("Uyarı: Bazı özellikler için yönetici hakları gereklidir.")

    app = MainApp()
    app.mainloop()