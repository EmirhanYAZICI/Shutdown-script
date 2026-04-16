import os
import sys
import subprocess
import ctypes
import tkinter as tk
from tkinter import messagebox

# --- Yardımcı Fonksiyonlar ---

def yonetici_mi():
    """Uygulamanın yönetici olarak çalışıp çalışmadığını kontrol eder."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def yonetici_olarak_baslat():
    """Uygulamayı yönetici olarak yeniden başlatır."""
    if not yonetici_mi():
        # Scripti yönetici olarak yeniden çalıştır
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{os.path.abspath(__file__)}"', None, 1
        )
        sys.exit()

# Yönetici kontrolü - yönetici değilse yönetici olarak yeniden başlat
yonetici_olarak_baslat()

# --- Global Değişkenler ---
kalan_saniye = 0
sayac_aktif = False
sayac_id = None

def kapatma_baslat():
    global kalan_saniye, sayac_aktif, sayac_id

    # Zaten bir sayaç çalışıyorsa uyar
    if sayac_aktif:
        messagebox.showwarning("Uyarı", "Zaten bir kapatma zamanlayıcısı çalışıyor!\nÖnce iptal et.")
        return

    try:
        # Input'lardan verileri alıyoruz
        saat = int(entry_saat.get() or 0)
        dakika = int(entry_dakika.get() or 0)

        # Toplam saniyeyi hesaplıyoruz
        toplam_saniye = (saat * 3600) + (dakika * 60)

        if toplam_saniye <= 0:
            messagebox.showwarning("Hata", "Lütfen geçerli bir süre gir kanka!")
            return

        kalan_saniye = toplam_saniye
        sayac_aktif = True

        # Windows'un kendi shutdown zamanlayıcısını başlat
        # Bu sayede Windows "bilgisayar kapanacak" uyarısını gösterir
        subprocess.run(
            ["shutdown", "/s", "/t", str(toplam_saniye)],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        # Giriş alanlarını devre dışı bırak
        entry_saat.config(state='disabled')
        entry_dakika.config(state='disabled')
        btn_baslat.config(state='disabled')

        # Sayaç etiketini göster
        lbl_sayac.pack(side='right', padx=10)
        lbl_sayac_baslik.pack(side='right')

        # Geri sayımı başlat (arayüzde göstermek için)
        geri_sayim_guncelle()

    except ValueError:
        messagebox.showerror("Hata", "Lütfen sadece sayı gir!")

def geri_sayim_guncelle():
    global kalan_saniye, sayac_aktif, sayac_id

    if not sayac_aktif:
        return

    if kalan_saniye <= 0:
        # Süre doldu! Windows zaten kapatacak (shutdown komutu zamanladık)
        # Ama ekstra güvenlik için yine de çalıştır
        sayac_aktif = False
        lbl_sayac.config(text="00:00:00", fg="#ff0000")
        bilgisayari_kapat()
        return

    # Kalan süreyi formatla
    saat = kalan_saniye // 3600
    dakika = (kalan_saniye % 3600) // 60
    saniye = kalan_saniye % 60
    zaman_str = f"{saat:02d}:{dakika:02d}:{saniye:02d}"

    # Renk değiştir - son 1 dakikada kırmızı, son 5 dakikada turuncu
    if kalan_saniye <= 60:
        renk = "#ff0000"  # Kırmızı
    elif kalan_saniye <= 300:
        renk = "#ff8c00"  # Turuncu
    else:
        renk = "#00ff00"  # Yeşil

    lbl_sayac.config(text=zaman_str, fg=renk)

    # Pencere başlığında da göster
    root.title(f"Otomatik Kapatıcı - {zaman_str}")

    kalan_saniye -= 1
    sayac_id = root.after(1000, geri_sayim_guncelle)

def bilgisayari_kapat():
    """PC'yi gerçekten kapatır - subprocess ile doğrudan shutdown komutu çalıştırır."""
    try:
        # subprocess.run ile doğrudan kapatma komutu - /f force close
        subprocess.run(
            ["shutdown", "/s", "/f", "/t", "0"],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    except Exception as e:
        # Yedek yöntem - os.system
        os.system("shutdown /s /f /t 0")

def kapatma_iptal():
    global sayac_aktif, sayac_id, kalan_saniye

    if not sayac_aktif:
        messagebox.showinfo("Bilgi", "Şu anda aktif bir zamanlayıcı yok.")
        return

    # Geri sayımı durdur
    sayac_aktif = False
    kalan_saniye = 0

    if sayac_id:
        root.after_cancel(sayac_id)
        sayac_id = None

    # Windows'un kendi shutdown zamanlayıcısını da iptal et (varsa)
    os.system("shutdown -a")

    # Arayüzü sıfırla
    entry_saat.config(state='normal')
    entry_dakika.config(state='normal')
    btn_baslat.config(state='normal')
    lbl_sayac.pack_forget()
    lbl_sayac_baslik.pack_forget()
    root.title("Otomatik Kapatıcı")

    messagebox.showinfo("İptal Edildi", "Kapatma zamanlayıcısı iptal edildi.")

def pencere_kapanirken():
    """Pencere kapatılırken sayacı da iptal et."""
    global sayac_aktif
    if sayac_aktif:
        cevap = messagebox.askyesno(
            "Dikkat!",
            "Kapatma zamanlayıcısı hâlâ çalışıyor!\n\n"
            "Uygulamayı kapatırsan zamanlayıcı da iptal olur.\n"
            "Çıkmak istediğine emin misin?"
        )
        if not cevap:
            return
        # Zamanlayıcıyı iptal et
        kapatma_iptal()

    root.destroy()

# --- Arayüz Tasarımı ---
root = tk.Tk()
root.title("Otomatik Kapatıcı")
root.geometry("420x300")
root.resizable(False, False)
root.configure(bg="#1e1e2e")
root.eval('tk::PlaceWindow . center')  # Pencereyi ekranın ortasında açar
root.protocol("WM_DELETE_WINDOW", pencere_kapanirken)

# --- Üst Bar (Sayaç gösterilecek yer) ---
frame_ust = tk.Frame(root, bg="#1e1e2e")
frame_ust.pack(fill='x', padx=10, pady=(5, 0))

# Sol tarafta boş alan (dengeleme)
lbl_bos = tk.Label(frame_ust, text="", bg="#1e1e2e")
lbl_bos.pack(side='left')

# Sağ üstte sayaç (başlangıçta gizli)
lbl_sayac = tk.Label(
    frame_ust,
    text="00:00:00",
    font=("Consolas", 18, "bold"),
    fg="#00ff00",
    bg="#1e1e2e"
)

lbl_sayac_baslik = tk.Label(
    frame_ust,
    text="⏱ Kalan:",
    font=("Arial", 10),
    fg="#aaaaaa",
    bg="#1e1e2e"
)

# --- Ana İçerik ---
frame_ana = tk.Frame(root, bg="#1e1e2e")
frame_ana.pack(expand=True)

# Başlık
tk.Label(
    frame_ana,
    text="⚡ Kapatma Zamanlayıcı",
    font=("Arial", 14, "bold"),
    fg="#cdd6f4",
    bg="#1e1e2e"
).pack(pady=(10, 15))

# Giriş alanları frame
frame_inputs = tk.Frame(frame_ana, bg="#1e1e2e")
frame_inputs.pack()

# Saat Girişi
tk.Label(frame_inputs, text="Saat:", font=("Arial", 10), fg="#bac2de", bg="#1e1e2e").grid(row=0, column=0, padx=5, pady=3, sticky='e')
entry_saat = tk.Entry(frame_inputs, justify='center', width=8, font=("Arial", 12),
                      bg="#313244", fg="#cdd6f4", insertbackground="#cdd6f4",
                      relief='flat', bd=5)
entry_saat.insert(0, "0")
entry_saat.grid(row=0, column=1, padx=5, pady=3)

# Dakika Girişi
tk.Label(frame_inputs, text="Dakika:", font=("Arial", 10), fg="#bac2de", bg="#1e1e2e").grid(row=1, column=0, padx=5, pady=3, sticky='e')
entry_dakika = tk.Entry(frame_inputs, justify='center', width=8, font=("Arial", 12),
                        bg="#313244", fg="#cdd6f4", insertbackground="#cdd6f4",
                        relief='flat', bd=5)
entry_dakika.insert(0, "0")
entry_dakika.grid(row=1, column=1, padx=5, pady=3)

# Butonlar Frame
frame_btn = tk.Frame(frame_ana, bg="#1e1e2e")
frame_btn.pack(pady=15)

btn_baslat = tk.Button(
    frame_btn,
    text="🚀 Zamanlayıcıyı Başlat",
    command=kapatma_baslat,
    bg="#a6e3a1", fg="#1e1e2e",
    activebackground="#94e2d5", activeforeground="#1e1e2e",
    font=("Arial", 10, "bold"),
    width=22, relief='flat', bd=0, cursor="hand2"
)
btn_baslat.pack(pady=3)

btn_iptal = tk.Button(
    frame_btn,
    text="❌ İşlemi İptal Et",
    command=kapatma_iptal,
    bg="#f38ba8", fg="#1e1e2e",
    activebackground="#eba0ac", activeforeground="#1e1e2e",
    font=("Arial", 10, "bold"),
    width=22, relief='flat', bd=0, cursor="hand2"
)
btn_iptal.pack(pady=3)

# --- Alt bilgi ---
tk.Label(
    root,
    text="Yönetici olarak çalışıyor ✔",
    font=("Arial", 8),
    fg="#585b70",
    bg="#1e1e2e"
).pack(side='bottom', pady=5)

root.mainloop()