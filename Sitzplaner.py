import tkinter as tk
from tkinter import messagebox
import random, math, requests, re, subprocess, sys, os, urllib

VERSION = "1.1"
UPDATE_URL = "https://raw.githubusercontent.com/Skorpionel/Sitzplaner/refs/heads/main/Sitzplaner.py"
EXE_UPDATE_URL = "https://github.com/Skorpionel/Sitzplaner/raw/refs/heads/main/Sitzplaner.exe"

BG         = "#1a1a1a"
CANVAS_BG  = "#212121"
TABLE_FILL = "#2e2e2e"
TABLE_OUT  = "#484848"
TABLE_SEL  = "#8f8f8f"
TEXT_COL   = "#cccccc"
NUM_COL    = "#eeeeee"
BTN_BG     = "#2a2a2a"
BTN_HOV    = "#363636"
BTN_ACT    = "#444444"
TRASH_NORM = "#3b1c1c"
TRASH_OUT  = "#884b4b"
TRASH_FIRE = "#a12424"
HEADER_BG  = "#111111"
ACCENT     = "#888888"
ACCENT2    = "#cccccc"
MUTED      = "#555555"

TW, TH    = 110, 64
SNAP_GRID = 10

def updates_überprüfen():
    try:
        antwort = requests.get(UPDATE_URL, timeout=3)
        antwort.raise_for_status()
        data = antwort.text

        m = re.search(r'VERSION\s*=\s*["\'](.+?)["\']', data)
        if not m:
            return False, None
        
        neuste_version = m.group(1)

        aktuelle = tuple(int(x) for x in VERSION.split("."))
        neueste  = tuple(int(x) for x in neuste_version.split("."))

        return neueste > aktuelle, neuste_version
    
    except requests.RequestException as e:
        print(f"Update-Prüfung fehlgeschlagen: {e}")
        return False, None
    except ValueError:
        return False, None

update, neuste_version = updates_überprüfen()
if update:
    if messagebox.askyesno("Update verfügbar",
                           f"Wollen Sie die neueste Version {neuste_version} verwenden? \nAktuell: Version {VERSION}"):
        neue_exe = os.path.join(os.path.dirname(sys.executable), f"Sitzplaner_V.{neuste_version}.exe")
        urllib.request.urlretrieve(EXE_UPDATE_URL, neue_exe)
        subprocess.Popen(["Autoupdater.exe", "Sitzplaner.exe", neue_exe])
        sys.exit()

def snap(v):
    return round(v / SNAP_GRID) * SNAP_GRID

class Tisch:
    _zähler = 1

    def __init__(self, x, y, s1=None, s2=None):
        self.x       = x
        self.y       = y
        self.winkel  = 0
        self.s1      = s1 if s1 is not None else Tisch._zähler * 2 - 1
        self.s2      = s2 if s2 is not None else Tisch._zähler * 2
        Tisch._zähler += 1
        self.canvas_ids  = []
        self.ausgewählt = False

    def ecken(self):
        cx, cy = self.x, self.y
        hw, hh = TW / 2, TH / 2
        punkte = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
        rad    = math.radians(self.winkel)
        ca, sa = math.cos(rad), math.sin(rad)
        return [(ca*px - sa*py + cx, sa*px + ca*py + cy) for px, py in punkte]

    def sitzposition(self, welcher):
        cx, cy = self.x, self.y
        rad    = math.radians(self.winkel)
        ca, sa = math.cos(rad), math.sin(rad)
        versatz = TW / 2 - 18
        lx = -versatz if welcher == 1 else versatz
        return ca*lx + cx, sa*lx + cy


class SitzplanApp:
    def __init__(self, root):
        self.root = root
        if os.path.basename(__file__).endswith(".py"):
            self.root.title(f"{os.path.basename(__file__)[:-len('.py')]} V.{VERSION}")
        elif os.path.basename(__file__).endswith(".exe"):
            self.root.title(f"{os.path.basename(__file__)[:-len('.exe')]} V.{VERSION}")
        self.root.configure(bg=BG)
        self.root.geometry("1100x720")
        self.root.minsize(800, 560)

        self.tische      = []
        self.ziehtisch   = None
        self.zieh_ox     = 0
        self.zieh_oy     = 0
        self.ausgewählt = None
        self.über_müll = False

        self._ui_aufbauen()
        self._alles_zeichnen()

    def _ui_aufbauen(self):
        leiste = tk.Frame(self.root, bg=BG, height=46)
        leiste.pack(fill="x", side="top")
        leiste.pack_propagate(False)

        def knopf(text, befehl):
            b = tk.Button(leiste, text=text, command=befehl,
                          bg=BTN_BG, fg=TEXT_COL, relief="flat",
                          font=("TkDefaultFont", 9),
                          padx=11, pady=4, cursor="hand2",
                          activebackground=BTN_ACT, activeforeground="white",
                          bd=0, highlightthickness=0)
            b.pack(side="left", padx=4, pady=8)
            b.bind("<Enter>", lambda e: b.config(bg=BTN_HOV))
            b.bind("<Leave>", lambda e: b.config(bg=BTN_BG))
            return b

        knopf("Tisch hinzufügen", self._tisch_hinzufügen)
        knopf("90 Grad drehen",   self._drehen)
        knopf("Sitze bearbeiten", self._sitze_bearbeiten)

        tk.Frame(leiste, bg=MUTED, width=1).pack(side="left", fill="y", padx=5, pady=10)

        knopf("Sitze mischen",      self._sitze_mischen)
        knopf("Alles zurücksetzen", self._zurücksetzen)

        tk.Frame(leiste, bg=BG).pack(side="left", expand=True)

        gh_btn = tk.Button(
            leiste,
            text="GitHub (Source Code)",
            command=lambda: __import__("webbrowser").open("https://github.com/Skorpionel/Sitzplaner"),
            bg=BTN_BG, fg=TEXT_COL, relief="flat",
            font=("TkDefaultFont", 9),
            padx=11, pady=4, cursor="hand2",
            activebackground=BTN_ACT, activeforeground="white",
            bd=0, highlightthickness=0
        )
        gh_btn.pack(side="right", padx=8, pady=8)
        gh_btn.bind("<Enter>", lambda e: gh_btn.config(bg=BTN_HOV))
        gh_btn.bind("<Leave>", lambda e: gh_btn.config(bg=BTN_BG))

        self.canvas = tk.Canvas(self.root, bg=CANVAS_BG, bd=0,
                                highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<ButtonPress-1>",   self._bei_klick)
        self.canvas.bind("<B1-Motion>",       self._beim_ziehen)
        self.canvas.bind("<ButtonRelease-1>", self._bei_loslassen)
        self.canvas.bind("<Double-Button-1>", self._bei_doppelklick)
        self.canvas.bind("<Configure>",       lambda e: self._alles_zeichnen())

    def _alles_zeichnen(self):
        self.canvas.delete("all")
        self._raster_zeichnen()
        for t in self.tische:
            self._tisch_zeichnen(t)
        self._müll_zeichnen()

    def _raster_zeichnen(self):
        w = self.canvas.winfo_width()  or 1100
        h = self.canvas.winfo_height() or 660
        for x in range(0, w, 40):
            self.canvas.create_line(x, 0, x, h, fill="#272727", width=1)
        for y in range(0, h, 40):
            self.canvas.create_line(0, y, w, y, fill="#272727", width=1)

    def _müll_zeichnen(self):
        mx1, my1, mx2, my2 = self._müll_rechteck()
        füllung   = TRASH_FIRE if self.über_müll else TRASH_NORM
        umrandung = TRASH_FIRE if self.über_müll else TRASH_OUT
        farbe     = "#d06080"  if self.über_müll else MUTED

        self.canvas.create_rectangle(mx1, my1, mx2, my2,
                                     fill=füllung, outline=umrandung,
                                     width=2, dash=(5, 4), tags="müll")
        self.canvas.create_text((mx1+mx2)//2, (my1+my2)//2 - 8,
                                 text="[ Löschen ]",
                                 font=("TkDefaultFont", 9, "bold"),
                                 fill=farbe, tags="müll")
        self.canvas.create_text((mx1+mx2)//2, (my1+my2)//2 + 10,
                                 text="Tisch hier ablegen",
                                 font=("TkDefaultFont", 8),
                                 fill=farbe, tags="müll")

    def _müll_rechteck(self):
        w = self.canvas.winfo_width()  or 1100
        h = self.canvas.winfo_height() or 660
        return w - 150, h - 96, w - 10, h - 10

    def _tisch_zeichnen(self, t: Tisch):
        ids   = []
        ecken = t.ecken()
        pts   = [k for p in ecken for k in p]
        rand  = TABLE_SEL if t.ausgewählt else TABLE_OUT
        lw    = 2         if t.ausgewählt else 1

        ids.append(self.canvas.create_polygon(
            *pts, fill=TABLE_FILL, outline=rand, width=lw, tags=f"t_{id(t)}"))

        ids.append(self.canvas.create_line(
            *self._mittellinie(t), fill=TABLE_OUT, width=1, tags=f"t_{id(t)}"))

        for welcher in (1, 2):
            sx, sy = t.sitzposition(welcher)
            nummer = t.s1 if welcher == 1 else t.s2
            ids.append(self.canvas.create_text(
                sx, sy, text=str(nummer),
                font=("TkDefaultFont", 11, "bold"),
                fill=NUM_COL, tags=f"t_{id(t)}"))

        t.canvas_ids = ids

    def _mittellinie(self, t):
        cx, cy = t.x, t.y
        rad    = math.radians(t.winkel)
        ca, sa = math.cos(rad), math.sin(rad)
        hh     = TH / 2
        return (ca*0 - sa*(-hh) + cx, sa*0 + ca*(-hh) + cy,
                ca*0 - sa*( hh) + cx, sa*0 + ca*( hh) + cy)

    def _tisch_bei(self, x, y):
        for t in reversed(self.tische):
            if self._punkt_in_polygon(x, y, t.ecken()):
                return t
        return None

    @staticmethod
    def _punkt_in_polygon(px, py, polygon):
        n, innen, j = len(polygon), False, len(polygon) - 1
        for i in range(n):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            if ((yi > py) != (yj > py) and
                    px < (xj - xi) * (py - yi) / (yj - yi) + xi):
                innen = not innen
            j = i
        return innen

    def _im_müll(self, x, y):
        mx1, my1, mx2, my2 = self._müll_rechteck()
        return mx1 <= x <= mx2 and my1 <= y <= my2

    def _bei_klick(self, event):
        t = self._tisch_bei(event.x, event.y)
        if t:
            self._auswählen(t)
            self.ziehtisch = t
            self.zieh_ox   = event.x - t.x
            self.zieh_oy   = event.y - t.y
        else:
            self._auswählen(None)

    def _beim_ziehen(self, event):
        if not self.ziehtisch:
            return
        self.ziehtisch.x = snap(event.x - self.zieh_ox)
        self.ziehtisch.y = snap(event.y - self.zieh_oy)
        self.über_müll = self._im_müll(event.x, event.y)
        self._alles_zeichnen()

    def _bei_loslassen(self, event):
        if self.ziehtisch and self._im_müll(event.x, event.y):
            self.tische.remove(self.ziehtisch)
            Tisch._zähler -= 1
            self.ausgewählt = None
        self.ziehtisch   = None
        self.über_müll = False
        self._alles_zeichnen()

    def _bei_doppelklick(self, event):
        t = self._tisch_bei(event.x, event.y)
        if t:
            self._auswählen(t)
            self._sitze_bearbeiten()

    def _auswählen(self, t):
        if self.ausgewählt:
            self.ausgewählt.ausgewählt = False
        self.ausgewählt = t
        if t:
            t.ausgewählt = True
        self._alles_zeichnen()

    def _tisch_hinzufügen(self):
        w  = self.canvas.winfo_width()  or 600
        h  = self.canvas.winfo_height() or 400
        cx = random.randint(120, max(130, w - 120))
        cy = random.randint(80,  max(90,  h - 120))
        t  = Tisch(cx, cy)
        self.tische.append(t)
        self._auswählen(t)

    def _drehen(self):
        if not self.ausgewählt:
            return
        self.ausgewählt.winkel = (self.ausgewählt.winkel + 90) % 360
        self._alles_zeichnen()

    def _sitze_bearbeiten(self):
        if not self.ausgewählt:
            return
        t   = self.ausgewählt
        dlg = BearbeitenDialog(self.root, t.s1, t.s2)
        self.root.wait_window(dlg.fenster)
        if dlg.ergebnis:
            t.s1, t.s2 = dlg.ergebnis
            self._alles_zeichnen()

    def _sitze_mischen(self):
        if not self.tische:
            return
        nummern = []
        for t in self.tische:
            nummern += [t.s1, t.s2]
        random.shuffle(nummern)
        for i, t in enumerate(self.tische):
            t.s1 = nummern[i * 2]
            t.s2 = nummern[i * 2 + 1]
        self._alles_zeichnen()

    def _zurücksetzen(self):
        if not self.tische:
            return
        if messagebox.askyesno("Zurücksetzen",
                               "Alle Tische löschen und neu beginnen?",
                               parent=self.root):
            self.tische.clear()
            Tisch._zähler   = 1
            self.ausgewählt = None
            self._alles_zeichnen()


class BearbeitenDialog:
    def __init__(self, elternteil, s1, s2):
        self.ergebnis = None
        f = self.fenster = tk.Toplevel(elternteil)
        f.title("Sitznummern bearbeiten")
        f.configure(bg=BG)
        f.resizable(False, False)
        f.grab_set()
        f.geometry("290x200")
        f.transient(elternteil)

        rahmen = tk.Frame(f, bg=BG)
        rahmen.pack()

        self.e1 = self._eingabezeile(rahmen, "Sitz 1:", s1, 0)
        self.e2 = self._eingabezeile(rahmen, "Sitz 2:", s2, 1)

        self.fehler = tk.Label(f, text="", font=("TkDefaultFont", 8),
                               bg=BG, fg="#d06060")
        self.fehler.pack(pady=2)

        kf = tk.Frame(f, bg=BG)
        kf.pack(pady=6)

        tk.Button(kf, text="Speichern", command=self._ok,
                  bg=ACCENT, fg="white", relief="flat",
                  font=("TkDefaultFont", 9),
                  padx=13, pady=4, cursor="hand2",
                  activebackground=BTN_ACT).pack(side="left", padx=4)

        tk.Button(kf, text="Abbrechen", command=f.destroy,
                  bg=BTN_BG, fg=TEXT_COL, relief="flat",
                  font=("TkDefaultFont", 9),
                  padx=11, pady=4, cursor="hand2",
                  activebackground=BTN_HOV).pack(side="left", padx=4)

        f.bind("<Return>", lambda e: self._ok())
        f.bind("<Escape>", lambda e: f.destroy())
        self.e1.focus_set()

    def _eingabezeile(self, rahmen, label, wert, zeile):
        tk.Label(rahmen, text=label, font=("TkDefaultFont", 9),
                 bg=BG, fg=TEXT_COL, width=7, anchor="e").grid(
                     row=zeile, column=0, padx=6, pady=4)
        e = tk.Entry(rahmen, font=("TkDefaultFont", 11, "bold"), width=7,
                     bg=BTN_BG, fg=NUM_COL, insertbackground=NUM_COL,
                     relief="flat", bd=4, justify="center")
        e.insert(0, str(wert))
        e.grid(row=zeile, column=1, padx=6, pady=4)
        return e

    def _ok(self):
        try:
            v1, v2 = int(self.e1.get()), int(self.e2.get())
            if v1 <= 0 or v2 <= 0:
                raise ValueError
        except ValueError:
            self.fehler.config(text="Hier werden nur positive ganze Zahlen akzeptiert.")
            return
        self.ergebnis = (v1, v2)
        self.fenster.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app  = SitzplanApp(root)
    root.mainloop()
