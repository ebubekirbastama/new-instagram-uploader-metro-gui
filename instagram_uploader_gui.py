#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EBS Instagram Uploader – Metro GUI (Toplu CSV Desteği)
- Tekli: resim/video + caption
- Toplu: CSV'den (type,url,caption) çoklu yükleme
- Caption: GUI kutusundan (tekli) veya CSV'den (toplu)
- Video için processing durumunu polling ile bekler
- Ayrı thread: GUI donmaz
- İlerleme: Toplu yüklemede determinate progress bar
"""

import os
import csv
import time
import threading
import requests
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

# .env opsiyonel
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ==========================
#  Ayarları TXT'den Oku
# ==========================
def load_txt_settings(path="ayarlar.txt"):
    data = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    data[k.strip()] = v.strip()
    return data

_settings = load_txt_settings()
ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", _settings.get("access_token", ""))
IG_USER_ID   = os.getenv("IG_USER_ID", _settings.get("ig_user_id", ""))
API_VERSION  = os.getenv("IG_API_VERSION", _settings.get("api_version", "v21.0"))
POLL_INTERVAL = int(_settings.get("poll_interval", 5))
TIMEOUT       = int(_settings.get("timeout", 600))

GRAPH_BASE = f"https://graph.facebook.com/{API_VERSION}"

# ==========================
#  API Yardımcıları
# ==========================
class InstagramUploaderError(Exception):
    pass

def _request(method, url, data=None, params=None, timeout=60):
    try:
        r = requests.request(method, url, data=data, params=params, timeout=timeout)
    except requests.RequestException as e:
        raise InstagramUploaderError(f"HTTP hatası: {e}") from e
    try:
        j = r.json()
    except ValueError:
        raise InstagramUploaderError(f"API JSON dönmedi. Status={r.status_code} Text={r.text[:200]}")
    if not r.ok:
        err = j.get("error", {})
        msg = err.get("message", r.text)
        code = err.get("code", r.status_code)
        raise InstagramUploaderError(f"API hatası: code={code} message={msg}")
    return j

def create_container(media_type, media_url, caption):
    url = f"{GRAPH_BASE}/{IG_USER_ID}/media"
    data = {"access_token": ACCESS_TOKEN}
    if caption:
        data["caption"] = caption
    if media_type.lower() == "image":
        data["image_url"] = media_url
    else:
        data["media_type"] = "VIDEO"
        data["video_url"] = media_url
    j = _request("POST", url, data=data)
    return j["id"]

def publish_container(creation_id):
    url = f"{GRAPH_BASE}/{IG_USER_ID}/media_publish"
    data = {"creation_id": creation_id, "access_token": ACCESS_TOKEN}
    j = _request("POST", url, data=data)
    return j["id"]

def get_status(creation_id):
    url = f"{GRAPH_BASE}/{creation_id}"
    params = {"fields": "status_code,status", "access_token": ACCESS_TOKEN}
    j = _request("GET", url, params=params)
    return j

# ==========================
#  CSV Okuyucu (toplu iş)
# ==========================
def read_jobs_from_csv(csv_path):
    """
    CSV başlıkları: type,url,caption  (case-insensitive)
    """
    jobs = []
    if not os.path.exists(csv_path):
        raise FileNotFoundError("CSV dosyası bulunamadı.")
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        # başlıkları normalize et
        field_map = { (k or "").strip().lower(): k for k in (reader.fieldnames or []) }
        need = ["type", "url", "caption"]
        if not all(x in field_map for x in need):
            raise ValueError("CSV başlıkları 'type,url,caption' olmalı.")
        for row in reader:
            mtype = (row.get(field_map["type"]) or "").strip().lower()
            url = (row.get(field_map["url"]) or "").strip()
            cap = (row.get(field_map["caption"]) or "").strip()
            if not mtype or not url:
                continue
            if mtype not in ("image", "video"):
                continue
            jobs.append({"type": mtype, "url": url, "caption": cap})
    if not jobs:
        raise ValueError("CSV'de geçerli iş bulunamadı.")
    return jobs

# ==========================
#  GUI Uygulaması
# ==========================
class IGUploader(ttk.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        self.title("Instagram Uploader — Metro GUI (CSV Toplu)")
        self.geometry("940x680")
        self.minsize(900, 640)

        self.var_type = tk.StringVar(value="image")
        self.var_url = tk.StringVar()
        self.var_csv = tk.StringVar()
        self.var_caption_live = tk.StringVar()  # sadece tekli için sayaç göst.
        self._build_ui()

    # --- UI ---
    def _build_ui(self):
        top = ttk.Frame(self, padding=14)
        top.pack(fill=X)

        ttk.Label(top, text="Instagram Uploader", font=("Segoe UI", 18, "bold")).pack(side=LEFT)
        info = ttk.Label(top, text="* Access Token ve IG User ID ayarlar.txt’den okunur.", bootstyle=INFO)
        info.pack(side=RIGHT)

        body = ttk.PanedWindow(self, orient=HORIZONTAL)
        body.pack(fill=BOTH, expand=YES, padx=14, pady=8)

        # Sol: Tekli yükleme
        left = ttk.Labelframe(body, text="Tekli Yükleme", padding=12)
        body.add(left)

        ttk.Label(left, text="Medya Tipi").grid(row=0, column=0, sticky=W, pady=(0,6))
        type_frm = ttk.Frame(left)
        type_frm.grid(row=0, column=1, sticky=W, pady=(0,6))
        ttk.Radiobutton(type_frm, text="Resim", value="image", variable=self.var_type).pack(side=LEFT, padx=6)
        ttk.Radiobutton(type_frm, text="Video", value="video", variable=self.var_type).pack(side=LEFT, padx=6)

        ttk.Label(left, text="Medya URL").grid(row=1, column=0, sticky=W)
        url_frm = ttk.Frame(left)
        url_frm.grid(row=1, column=1, sticky=EW, pady=4)
        self.ent_url = ttk.Entry(url_frm, textvariable=self.var_url, width=46)
        self.ent_url.pack(side=LEFT, fill=X, expand=YES)
        ttk.Button(url_frm, text="Yapıştır", bootstyle=SECONDARY, command=self._paste_url).pack(side=LEFT, padx=6)

        ttk.Label(left, text="Caption").grid(row=2, column=0, sticky=NW, pady=(6,0))
        self.txt_caption = ScrolledText(left, height=6, width=52)
        self.txt_caption.grid(row=2, column=1, sticky=EW, pady=(6,0))
        self.lbl_capcount = ttk.Label(left, text="0 karakter")
        self.lbl_capcount.grid(row=3, column=1, sticky=E, pady=(2,6))
        self.txt_caption.bind("<<Modified>>", self._on_caption_change)

        self.btn_single = ttk.Button(left, text="Tekli Yükle", bootstyle=SUCCESS, command=self._start_single)
        self.btn_single.grid(row=4, column=1, sticky=E, pady=8)

        left.grid_columnconfigure(1, weight=1)

        # Sağ: Toplu yükleme
        right = ttk.Labelframe(body, text="Toplu Yükleme (CSV)", padding=12)
        body.add(right)

        ttk.Label(right, text="CSV Dosyası (type,url,caption)").grid(row=0, column=0, sticky=W)
        csv_frm = ttk.Frame(right)
        csv_frm.grid(row=0, column=1, sticky=EW, pady=4)
        self.ent_csv = ttk.Entry(csv_frm, textvariable=self.var_csv)
        self.ent_csv.pack(side=LEFT, fill=X, expand=YES)
        ttk.Button(csv_frm, text="Seç", bootstyle=SECONDARY, command=self._pick_csv).pack(side=LEFT, padx=6)

        self.btn_batch = ttk.Button(right, text="CSV'den Yüklemeyi Başlat", bootstyle=PRIMARY, command=self._start_batch)
        self.btn_batch.grid(row=1, column=1, sticky=E, pady=(6,6))

        # Progress alanı
        prog_box = ttk.Labelframe(self, text="İlerleme ve Günlük", padding=12)
        prog_box.pack(fill=BOTH, expand=YES, padx=14, pady=(0,14))

        # Toplam ilerleme (toplu için determinate)
        self.lbl_overall = ttk.Label(prog_box, text="Toplam İlerleme: 0/0")
        self.lbl_overall.pack(anchor=W)
        self.progress_overall = ttk.Progressbar(prog_box, mode="determinate", maximum=100)
        self.progress_overall.pack(fill=X, pady=6)

        # Anlık işlem (tekli veya video processing)
        self.lbl_current = ttk.Label(prog_box, text="Anlık İşlem: Bekleniyor")
        self.lbl_current.pack(anchor=W)
        self.progress_current = ttk.Progressbar(prog_box, mode="indeterminate", bootstyle=STRIPED)
        self.progress_current.pack(fill=X, pady=(0,8))

        # Log
        self.txt_log = ScrolledText(prog_box, height=14, font=("Cascadia Mono", 10))
        self.txt_log.pack(fill=BOTH, expand=YES)
        btns = ttk.Frame(prog_box)
        btns.pack(fill=X, pady=6)
        ttk.Button(btns, text="Günlüğü Temizle", bootstyle=SECONDARY, command=self._clear_log).pack(side=LEFT)
        ttk.Button(btns, text="Kopyala", bootstyle=INFO, command=self._copy_log).pack(side=LEFT, padx=6)

    # --- UI yardımcıları ---
    def _paste_url(self):
        try:
            clip = self.clipboard_get()
            self.var_url.set(clip)
        except tk.TclError:
            pass

    def _on_caption_change(self, _evt=None):
        if self.txt_caption.edit_modified():
            text = self.txt_caption.get("1.0", "end-1c")
            self.lbl_capcount.configure(text=f"{len(text)} karakter")
            self.txt_caption.edit_modified(False)

    def _clear_log(self):
        self.txt_log.delete("1.0", tk.END)

    def _copy_log(self):
        self.clipboard_clear()
        self.clipboard_append(self.txt_log.get("1.0", "end-1c"))
        messagebox.showinfo("Kopyalandı", "Günlük panoya kopyalandı.")

    def _log(self, msg):
        self.txt_log.insert(tk.END, msg + "\n")
        self.txt_log.see(tk.END)
        self.update_idletasks()

    # --- Tekli yükleme ---
    def _start_single(self):
        if not ACCESS_TOKEN or not IG_USER_ID:
            messagebox.showerror("Eksik Bilgi", "ayarlar.txt içinde Access Token ve IG User ID bulunamadı.")
            return
        url = self.var_url.get().strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            messagebox.showerror("URL Hatası", "Geçerli bir URL girin (http/https).")
            return
        mtype = self.var_type.get()
        caption = self.txt_caption.get("1.0", "end-1c").strip()

        self._log("—" * 58)
        self._log(f"[TEKLİ] Başlıyor → type={mtype} url={url}")
        self.progress_current.start(12)
        self.lbl_current.configure(text="Anlık İşlem: Yükleniyor…")

        def worker():
            try:
                media_id = self._upload_one(mtype, url, caption, idx=None, total=None)
                self._log(f"✓ Tekli yükleme tamamlandı. media_id={media_id}")
                self.after(0, lambda: messagebox.showinfo("Başarılı", f"media_id={media_id}"))
            except Exception as e:
                self._log(f"✗ Hata: {e}")
                self.after(0, lambda: messagebox.showerror("Hata", str(e)))
            finally:
                self.after(0, self.progress_current.stop)
                self.after(0, lambda: self.lbl_current.configure(text="Anlık İşlem: Bekleniyor"))

        threading.Thread(target=worker, daemon=True).start()

    # --- Toplu yükleme ---
    def _pick_csv(self):
        path = filedialog.askopenfilename(
            title="CSV seçin",
            filetypes=[("CSV", "*.csv"), ("Tümü", "*.*")]
        )
        if path:
            self.var_csv.set(path)

    def _start_batch(self):
        if not ACCESS_TOKEN or not IG_USER_ID:
            messagebox.showerror("Eksik Bilgi", "ayarlar.txt içinde Access Token ve IG User ID bulunamadı.")
            return
        csv_path = self.var_csv.get().strip()
        if not csv_path:
            messagebox.showerror("Eksik Dosya", "CSV dosyası seçin.")
            return
        try:
            jobs = read_jobs_from_csv(csv_path)
        except Exception as e:
            messagebox.showerror("CSV Hatası", str(e))
            return

        total = len(jobs)
        self.progress_overall.configure(maximum=total, value=0)
        self.lbl_overall.configure(text=f"Toplam İlerleme: 0/{total}")
        self._log("—" * 58)
        self._log(f"[TOPLU] {total} iş kuyruğa alındı. Başlıyor…")

        def worker_batch():
            ok, fail = 0, 0
            for i, job in enumerate(jobs, start=1):
                mtype = job["type"]
                url = job["url"]
                cap = job.get("caption") or ""
                self._log(f"[{i}/{total}] type={mtype} url={url}")
                self.after(0, self.progress_current.start, 12)
                self.after(0, lambda: self.lbl_current.configure(text=f"Anlık İşlem: {i}/{total} yükleniyor…"))
                try:
                    _media_id = self._upload_one(mtype, url, cap, idx=i, total=total)
                    ok += 1
                    self._log(f"  → ✓ Başarılı.")
                except Exception as e:
                    fail += 1
                    self._log(f"  → ✗ Hata: {e}")
                finally:
                    self.after(0, self.progress_current.stop)
                    self.after(0, self._bump_overall, i, total)

            self._log(f"[TOPLU] Bitti. Başarılı: {ok}, Hatalı: {fail} (Toplam: {total})")
            self.after(0, lambda: messagebox.showinfo("Toplu Yükleme",
                                                      f"Bitti.\nBaşarılı: {ok}\nHatalı: {fail}\nToplam: {total}"))
            self.after(0, lambda: self.lbl_current.configure(text="Anlık İşlem: Bekleniyor"))

        threading.Thread(target=worker_batch, daemon=True).start()

    def _bump_overall(self, i, total):
        self.progress_overall.configure(value=i)
        self.lbl_overall.configure(text=f"Toplam İlerleme: {i}/{total}")

    # --- Ortak yükleme mantığı (tekli + toplu) ---
    def _upload_one(self, media_type, url, caption, idx=None, total=None):
        # Container
        self._log("   → Container oluşturuluyor…")
        creation_id = create_container(media_type, url, caption)

        # Video ise işlem tamamlanana kadar bekle
        if media_type == "video":
            waited = 0
            self._log("   → Video işleniyor…")
            while True:
                st = get_status(creation_id)
                code = st.get("status_code")
                status_h = st.get("status")
                self._log(f"      - status_code={code} status={status_h} (geçen={waited}s)")
                if code == "FINISHED":
                    break
                if code == "ERROR":
                    raise InstagramUploaderError("Video işleme hatası")
                time.sleep(POLL_INTERVAL)
                waited += POLL_INTERVAL
                if waited >= TIMEOUT:
                    raise InstagramUploaderError("Zaman aşımı (video processing uzun sürdü)")

        # Publish
        self._log("   → Yayınlanıyor…")
        media_id = publish_container(creation_id)
        self._log(f"   → media_id={media_id}")
        return media_id

# ==========================
#  Çalıştır
# ==========================
if __name__ == "__main__":
    if not ACCESS_TOKEN or not IG_USER_ID:
        print("UYARI: ayarlar.txt içinde access_token ve ig_user_id bulunamadı (GUI içinde uyarı verilecek).")
    app = IGUploader()
    app.mainloop()
