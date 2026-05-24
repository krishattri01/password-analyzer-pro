import tkinter as tk
from tkinter import ttk, messagebox
import os, datetime, sys, math, json, threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.strength_engine import StrengthEngine
from core.pattern_detector import PatternDetector
from core.generator import PasswordGenerator


# ═══════════════════════════════════════════════════════════════════════════════
#  THEME
# ═══════════════════════════════════════════════════════════════════════════════
class Theme:
    BG       = "#0A0A14"
    SURFACE  = "#12121F"
    CARD     = "#1A1A2E"
    CARD2    = "#16213E"
    BORDER   = "#2D2D50"
    ACCENT   = "#7C3AED"
    ACCENT_L = "#9D4EDD"
    TEAL     = "#06B6D4"
    GREEN    = "#10B981"
    YELLOW   = "#F59E0B"
    RED      = "#EF4444"
    ORANGE   = "#F97316"
    TEXT     = "#E2E8F0"
    DIM      = "#64748B"
    WHITE    = "#FFFFFF"

    STRENGTH_COLORS = {
        "Very Weak":   "#EF4444",
        "Weak":        "#F97316",
        "Fair":        "#F59E0B",
        "Strong":      "#10B981",
        "Very Strong": "#06B6D4",
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  REUSABLE WIDGET HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def card(parent, **kw):
    f = tk.Frame(parent, bg=Theme.CARD,
                 highlightthickness=1, highlightbackground=Theme.BORDER, **kw)
    return f

def label(parent, text, size=10, bold=False, color=None, **kw):
    return tk.Label(parent, text=text,
                    bg=parent.cget("bg"),
                    fg=color or Theme.TEXT,
                    font=("Segoe UI", size, "bold" if bold else "normal"),
                    **kw)

def btn(parent, text, command, bg=Theme.ACCENT, fg=Theme.WHITE, size=9):
    b = tk.Button(parent, text=text, command=command,
                  bg=bg, fg=fg, relief=tk.FLAT, cursor="hand2",
                  font=("Segoe UI", size, "bold"),
                  activebackground=Theme.ACCENT_L, activeforeground=Theme.WHITE,
                  bd=0, padx=12, pady=8)
    b.bind("<Enter>", lambda e: b.config(bg=_lighten(bg)))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b

def _lighten(hex_color, amt=25):
    try:
        r = min(255, int(hex_color[1:3], 16) + amt)
        g = min(255, int(hex_color[3:5], 16) + amt)
        b = min(255, int(hex_color[5:7], 16) + amt)
        return f"#{r:02x}{g:02x}{b:02x}"
    except:
        return hex_color


# ═══════════════════════════════════════════════════════════════════════════════
#  CIRCULAR SCORE GAUGE  (drawn on Canvas)
# ═══════════════════════════════════════════════════════════════════════════════
class ScoreGauge(tk.Canvas):
    SIZE = 130

    def __init__(self, parent, **kw):
        super().__init__(parent, width=self.SIZE, height=self.SIZE,
                         bg=Theme.CARD, highlightthickness=0, **kw)
        self._score = 0
        self._color = Theme.RED
        self._label = "—"
        self._anim_target = 0
        self._anim_current = 0
        self._after_id = None
        self._draw()

    def set(self, score, color, label):
        self._anim_target = score
        self._color = color
        self._label = label
        self._animate()

    def _animate(self):
        if self._after_id:
            self.after_cancel(self._after_id)
        diff = self._anim_target - self._anim_current
        if abs(diff) < 1:
            self._anim_current = self._anim_target
            self._draw()
            return
        self._anim_current += diff * 0.15
        self._draw()
        self._after_id = self.after(16, self._animate)

    def _draw(self):
        self.delete("all")
        cx, cy, r = self.SIZE // 2, self.SIZE // 2, 52
        # Background arc
        self.create_arc(cx-r, cy-r, cx+r, cy+r,
                        start=0, extent=359.9,
                        outline=Theme.BORDER, width=10, style=tk.ARC)
        # Score arc
        extent = (self._anim_current / 100) * 359.9
        if extent > 0:
            self.create_arc(cx-r, cy-r, cx+r, cy+r,
                            start=90, extent=-extent,
                            outline=self._color, width=10, style=tk.ARC)
        # Score text
        self.create_text(cx, cy - 10,
                         text=f"{int(self._anim_current)}",
                         fill=self._color,
                         font=("Segoe UI", 22, "bold"))
        self.create_text(cx, cy + 12,
                         text=self._label,
                         fill=Theme.DIM,
                         font=("Segoe UI", 8))
        self.create_text(cx, cy + 26,
                         text="/ 100",
                         fill=Theme.BORDER,
                         font=("Segoe UI", 7))


# ═══════════════════════════════════════════════════════════════════════════════
#  ANIMATED STRENGTH BAR
# ═══════════════════════════════════════════════════════════════════════════════
class StrengthBar(tk.Canvas):
    def __init__(self, parent, **kw):
        super().__init__(parent, height=12, bg=Theme.SURFACE,
                         highlightthickness=0, **kw)
        self._target = 0
        self._current = 0.0
        self._color = Theme.RED
        self._after_id = None
        self.bind("<Configure>", lambda e: self._draw())

    def set(self, score, color):
        self._target = score
        self._color = color
        self._animate()

    def _animate(self):
        if self._after_id:
            self.after_cancel(self._after_id)
        diff = self._target - self._current
        if abs(diff) < 0.5:
            self._current = self._target
            self._draw()
            return
        self._current += diff * 0.18
        self._draw()
        self._after_id = self.after(16, self._animate)

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), 12
        if w < 2:
            return
        # bg
        self.create_rectangle(0, 0, w, h, fill=Theme.CARD2, outline="")
        fw = max(0, int(w * self._current / 100))
        if fw > 0:
            self.create_rectangle(0, 0, fw, h, fill=self._color, outline="")
        # Segment dividers
        for pct in [25, 50, 75]:
            x = int(w * pct / 100)
            self.create_line(x, 0, x, h, fill=Theme.SURFACE, width=2)


# ═══════════════════════════════════════════════════════════════════════════════
#  HISTORY LOG ENTRY
# ═══════════════════════════════════════════════════════════════════════════════
class HistoryEntry:
    def __init__(self, password, score, label, crack_time):
        self.masked    = "●" * len(password)
        self.length    = len(password)
        self.score     = score
        self.label     = label
        self.crack_time = crack_time
        self.time      = datetime.datetime.now().strftime("%H:%M:%S")
        self.color     = Theme.STRENGTH_COLORS.get(label, Theme.DIM)


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN APP
# ═══════════════════════════════════════════════════════════════════════════════
class PasswordAnalyzerApp:

    def __init__(self, root: tk.Tk):
        self.root      = root
        self.engine    = StrengthEngine()
        self.detector  = PatternDetector()
        self.generator = PasswordGenerator()
        self._show_pw  = False
        self._history  = []
        self._dot_on   = True
        self._tips = [
            "💡 Use a passphrase for easy-to-remember strong passwords",
            "💡 Never reuse passwords across different accounts",
            "💡 Enable 2FA wherever possible — even strong passwords can leak",
            "💡 A 16+ char password with mixed types takes centuries to crack",
            "💡 Password managers are safer than memorizing passwords",
            "💡 Avoid using birthdays, names, or dictionary words",
            "💡 Change passwords immediately if a data breach is suspected",
        ]
        self._tip_idx = 0

        self._setup_window()
        self._build_ui()
        self._rotate_tip()
        self._pulse_dot()
        self._run_analysis("")

    # ── Window ────────────────────────────────────────────────────────
    def _setup_window(self):
        self.root.title("🔐 Password Analyzer Pro — Pinnacle Labs")
        W, H = 1060, 800
        self.root.geometry(f"{W}x{H}")
        self.root.minsize(900, 720)
        self.root.configure(bg=Theme.BG)
        self.root.resizable(True, True)
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth()  - W) // 2
        y = (self.root.winfo_screenheight() - H) // 2
        self.root.geometry(f"{W}x{H}+{x}+{y}")

    # ── UI Shell ──────────────────────────────────────────────────────
    def _build_ui(self):
        self._build_header()
        body = tk.Frame(self.root, bg=Theme.BG)
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=(12, 0))
        self._build_left(body)
        self._build_right(body)
        self._build_footer()

    # ── HEADER ────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self.root, bg=Theme.CARD2, height=66)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        # Logo block
        logo_f = tk.Frame(hdr, bg=Theme.ACCENT, width=8)
        logo_f.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(hdr, text="  🔐 Password Analyzer Pro",
                 bg=Theme.CARD2, fg=Theme.WHITE,
                 font=("Segoe UI", 16, "bold")).pack(side=tk.LEFT, padx=(16,0), pady=8)
        tk.Label(hdr, text="Pinnacle Labs  |  Cybersecurity Internship",
                 bg=Theme.CARD2, fg=Theme.DIM,
                 font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=14, pady=(20,0))

        # Right side
        right_hdr = tk.Frame(hdr, bg=Theme.CARD2)
        right_hdr.pack(side=tk.RIGHT, padx=20)

        self.dot_lbl = tk.Label(right_hdr, text="● LIVE",
                                bg=Theme.CARD2, fg=Theme.GREEN,
                                font=("Segoe UI", 8, "bold"))
        self.dot_lbl.pack(anchor=tk.E)

        self.tip_lbl = tk.Label(right_hdr, text="",
                                bg=Theme.CARD2, fg=Theme.DIM,
                                font=("Segoe UI", 8), wraplength=280, justify=tk.RIGHT)
        self.tip_lbl.pack(anchor=tk.E)

    def _pulse_dot(self):
        self._dot_on = not self._dot_on
        self.dot_lbl.config(fg=Theme.GREEN if self._dot_on else "#064E3B")
        self.root.after(700, self._pulse_dot)

    def _rotate_tip(self):
        self.tip_lbl.config(text=self._tips[self._tip_idx % len(self._tips)])
        self._tip_idx += 1
        self.root.after(5000, self._rotate_tip)

    # ── LEFT COLUMN ───────────────────────────────────────────────────
    def _build_left(self, parent):
        left = tk.Frame(parent, bg=Theme.BG)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self._build_input_card(left)
        self._build_gauge_row(left)
        self._build_strength_bar_card(left)
        self._build_checks_card(left)

    # Input card
    def _build_input_card(self, parent):
        c = card(parent)
        c.pack(fill=tk.X, pady=(0, 10))

        inner = tk.Frame(c, bg=Theme.CARD)
        inner.pack(fill=tk.X, padx=16, pady=14)

        label(inner, "ENTER PASSWORD", 8, bold=True, color=Theme.DIM).pack(anchor=tk.W)

        row = tk.Frame(inner, bg=Theme.CARD)
        row.pack(fill=tk.X, pady=(6, 0))

        self.pw_var = tk.StringVar()
        self.pw_var.trace_add("write", self._on_type)

        self.pw_entry = tk.Entry(row, textvariable=self.pw_var, show="●",
                                 font=("Consolas", 15), bg=Theme.SURFACE,
                                 fg=Theme.WHITE, insertbackground=Theme.ACCENT,
                                 relief=tk.FLAT, bd=0,
                                 highlightthickness=2,
                                 highlightbackground=Theme.BORDER,
                                 highlightcolor=Theme.ACCENT)
        self.pw_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=11, ipadx=12)
        self.pw_entry.focus()
        self.pw_entry.bind("<FocusIn>",  lambda e: self.pw_entry.config(highlightbackground=Theme.ACCENT))
        self.pw_entry.bind("<FocusOut>", lambda e: self.pw_entry.config(highlightbackground=Theme.BORDER))

        self._show_toggle_btn = btn(row, "👁", self._toggle_visibility,
                                    bg=Theme.CARD2, fg=Theme.DIM, size=10)
        self._show_toggle_btn.pack(side=tk.LEFT, padx=(6,0), ipady=11, ipadx=8)

        for text, cmd, bg, fg in [
            ("⚡ Generate",   self._generate_password, Theme.ACCENT,  Theme.WHITE),
            ("🎲 Passphrase", self._gen_memorable,     Theme.CARD2,   Theme.TEAL),
            ("💾 Export",     self._export_report,     Theme.CARD2,   Theme.GREEN),
            ("🗑 Clear",      self._clear,              Theme.CARD2,   Theme.RED),
        ]:
            btn(row, text, cmd, bg=bg, fg=fg).pack(side=tk.LEFT, padx=(6,0), ipady=11)

        # Entropy progress inline
        ep_row = tk.Frame(inner, bg=Theme.CARD)
        ep_row.pack(fill=tk.X, pady=(10,0))
        label(ep_row, "Entropy:", 8, color=Theme.DIM).pack(side=tk.LEFT)
        self.entropy_bar = StrengthBar(ep_row)
        self.entropy_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8,8))
        self.entropy_lbl = label(ep_row, "0 bits", 8, color=Theme.DIM)
        self.entropy_lbl.pack(side=tk.LEFT)

    # Gauge row
    def _build_gauge_row(self, parent):
        row = tk.Frame(parent, bg=Theme.BG)
        row.pack(fill=tk.X, pady=(0, 10))

        # Score gauge
        gc = card(row)
        gc.pack(side=tk.LEFT, padx=(0, 10), ipadx=6, ipady=6)
        label(gc, "SCORE", 8, bold=True, color=Theme.DIM).pack(pady=(8,0))
        self.gauge = ScoreGauge(gc)
        self.gauge.pack(padx=14, pady=(4,10))

        # Stat cards
        stats_f = tk.Frame(row, bg=Theme.BG)
        stats_f.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.stat_vars = {}
        stats = [
            ("Strength",   "—", Theme.ACCENT),
            ("Length",     "—", Theme.TEAL),
            ("Crack Time", "—", Theme.RED),
            ("Char Pool",  "—", Theme.YELLOW),
        ]
        for i, (name, default, color) in enumerate(stats):
            r, c2 = divmod(i, 2)
            sc = card(stats_f)
            sc.grid(row=r, column=c2, sticky=tk.NSEW,
                    padx=(0,6) if c2==0 else 0,
                    pady=(0,6) if r==0 else 0,
                    ipadx=8, ipady=10)
            stats_f.columnconfigure(c2, weight=1)
            stats_f.rowconfigure(r, weight=1)

            label(sc, name, 8, color=Theme.DIM).pack()
            var = tk.StringVar(value=default)
            self.stat_vars[name] = var
            lbl = tk.Label(sc, textvariable=var, bg=Theme.CARD, fg=color,
                           font=("Segoe UI", 11, "bold"))
            lbl.pack()

    # Strength bar card
    def _build_strength_bar_card(self, parent):
        c = card(parent)
        c.pack(fill=tk.X, pady=(0, 10))
        inner = tk.Frame(c, bg=Theme.CARD)
        inner.pack(fill=tk.X, padx=16, pady=12)

        top = tk.Frame(inner, bg=Theme.CARD)
        top.pack(fill=tk.X)
        label(top, "STRENGTH METER", 8, bold=True, color=Theme.DIM).pack(side=tk.LEFT)
        self.bar_pct = label(top, "0%", 8, bold=True, color=Theme.DIM)
        self.bar_pct.pack(side=tk.RIGHT)

        self.strength_bar = StrengthBar(inner)
        self.strength_bar.pack(fill=tk.X, pady=(6,0))

        # Segment labels
        seg = tk.Frame(inner, bg=Theme.CARD)
        seg.pack(fill=tk.X, pady=(4,0))
        for txt, anchor in [("Weak","w"),("Fair","center"),("Strong","e")]:
            tk.Label(seg, text=txt, bg=Theme.CARD, fg=Theme.BORDER,
                     font=("Segoe UI", 7)).pack(side=tk.LEFT, expand=True, anchor=anchor)

    # Character checks card
    def _build_checks_card(self, parent):
        c = card(parent)
        c.pack(fill=tk.X, pady=(0, 10))
        inner = tk.Frame(c, bg=Theme.CARD)
        inner.pack(fill=tk.BOTH, padx=16, pady=12)
        label(inner, "CHARACTER ANALYSIS", 8, bold=True, color=Theme.DIM).pack(anchor=tk.W, pady=(0,8))
        self.checks_frame = tk.Frame(inner, bg=Theme.CARD)
        self.checks_frame.pack(fill=tk.X)

    # ── RIGHT COLUMN ──────────────────────────────────────────────────
    def _build_right(self, parent):
        right = tk.Frame(parent, bg=Theme.BG, width=340)
        right.pack(side=tk.LEFT, fill=tk.BOTH)
        right.pack_propagate(False)

        self._build_tabs(right)

    def _build_tabs(self, parent):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("P.TNotebook", background=Theme.BG, borderwidth=0)
        style.configure("P.TNotebook.Tab",
                        background=Theme.CARD2, foreground=Theme.DIM,
                        font=("Segoe UI", 8, "bold"), padding=[10, 6])
        style.map("P.TNotebook.Tab",
                  background=[("selected", Theme.ACCENT)],
                  foreground=[("selected", Theme.WHITE)])

        self.nb = ttk.Notebook(parent, style="P.TNotebook")
        self.nb.pack(fill=tk.BOTH, expand=True)

        self._build_tab_issues()
        self._build_tab_generator()
        self._build_tab_history()
        self._build_tab_tips()

    # TAB: Issues
    def _build_tab_issues(self):
        tab = tk.Frame(self.nb, bg=Theme.CARD)
        self.nb.add(tab, text=" ⚠ Issues ")

        # Weaknesses
        wf = tk.Frame(tab, bg=Theme.CARD)
        wf.pack(fill=tk.X, padx=12, pady=(12,0))
        label(wf, "WEAKNESSES", 8, bold=True, color=Theme.RED).pack(anchor=tk.W)
        self.weak_text = tk.Text(wf, bg=Theme.SURFACE, fg=Theme.RED,
                                 font=("Segoe UI", 9), relief=tk.FLAT,
                                 state=tk.DISABLED, wrap=tk.WORD,
                                 highlightthickness=0, height=7,
                                 padx=8, pady=8, spacing1=3)
        self.weak_text.pack(fill=tk.X, pady=(6,0))

        # Recommendations
        rf = tk.Frame(tab, bg=Theme.CARD)
        rf.pack(fill=tk.BOTH, expand=True, padx=12, pady=(12,12))
        label(rf, "RECOMMENDATIONS", 8, bold=True, color=Theme.GREEN).pack(anchor=tk.W)
        self.rec_text = tk.Text(rf, bg=Theme.SURFACE, fg=Theme.GREEN,
                                font=("Segoe UI", 9), relief=tk.FLAT,
                                state=tk.DISABLED, wrap=tk.WORD,
                                highlightthickness=0,
                                padx=8, pady=8, spacing1=3)
        self.rec_text.pack(fill=tk.BOTH, expand=True, pady=(6,0))

    # TAB: Generator
    def _build_tab_generator(self):
        tab = tk.Frame(self.nb, bg=Theme.CARD)
        self.nb.add(tab, text=" ⚡ Generator ")

        inner = tk.Frame(tab, bg=Theme.CARD)
        inner.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)

        # Length
        label(inner, "LENGTH", 8, bold=True, color=Theme.DIM).pack(anchor=tk.W)
        lrow = tk.Frame(inner, bg=Theme.CARD)
        lrow.pack(fill=tk.X, pady=(4,12))
        self.len_var = tk.IntVar(value=16)
        self.len_disp = label(lrow, "16", 13, bold=True, color=Theme.ACCENT)
        self.len_disp.pack(side=tk.RIGHT)
        tk.Scale(lrow, from_=8, to=40, orient=tk.HORIZONTAL,
                 variable=self.len_var, bg=Theme.CARD, fg=Theme.WHITE,
                 troughcolor=Theme.SURFACE, activebackground=Theme.ACCENT,
                 highlightthickness=0, bd=0, showvalue=False,
                 command=lambda v: self.len_disp.config(text=v)
                 ).pack(fill=tk.X, expand=True, side=tk.LEFT)

        # Options
        label(inner, "INCLUDE", 8, bold=True, color=Theme.DIM).pack(anchor=tk.W)
        self.opt_lower   = tk.BooleanVar(value=True)
        self.opt_upper   = tk.BooleanVar(value=True)
        self.opt_digits  = tk.BooleanVar(value=True)
        self.opt_special = tk.BooleanVar(value=True)

        for txt, var in [("Lowercase a–z", self.opt_lower),
                         ("Uppercase A–Z", self.opt_upper),
                         ("Numbers 0–9",   self.opt_digits),
                         ("Symbols !@#$",  self.opt_special)]:
            tk.Checkbutton(inner, text=txt, variable=var,
                           bg=Theme.CARD, fg=Theme.TEXT,
                           selectcolor=Theme.ACCENT,
                           activebackground=Theme.CARD,
                           font=("Segoe UI", 9), anchor=tk.W
                           ).pack(fill=tk.X, pady=2)

        # Buttons
        brow = tk.Frame(inner, bg=Theme.CARD)
        brow.pack(fill=tk.X, pady=(10,0))
        btn(brow, "⚡ Random Password", self._generate_custom,
            bg=Theme.ACCENT).pack(fill=tk.X, pady=(0,6))
        btn(brow, "🎲 Memorable Passphrase", self._gen_memorable,
            bg=Theme.CARD2, fg=Theme.TEAL).pack(fill=tk.X)

        # Result
        label(inner, "RESULT", 8, bold=True, color=Theme.DIM).pack(anchor=tk.W, pady=(14,4))
        res_row = tk.Frame(inner, bg=Theme.CARD)
        res_row.pack(fill=tk.X)
        self.gen_result = tk.Entry(res_row, font=("Consolas", 10),
                                   bg=Theme.SURFACE, fg=Theme.GREEN,
                                   relief=tk.FLAT, bd=0,
                                   highlightthickness=1,
                                   highlightbackground=Theme.BORDER,
                                   state="readonly")
        self.gen_result.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, ipadx=8)
        btn(res_row, "Use ➜", self._copy_and_use,
            bg=Theme.GREEN, fg=Theme.WHITE, size=8
            ).pack(side=tk.LEFT, padx=(6,0), ipady=8)

    # TAB: History
    def _build_tab_history(self):
        tab = tk.Frame(self.nb, bg=Theme.CARD)
        self.nb.add(tab, text=" 📜 History ")

        top = tk.Frame(tab, bg=Theme.CARD)
        top.pack(fill=tk.X, padx=12, pady=(10,0))
        label(top, "ANALYSIS HISTORY", 8, bold=True, color=Theme.DIM).pack(side=tk.LEFT, anchor=tk.W)
        btn(top, "🗑 Clear", self._clear_history,
            bg=Theme.CARD2, fg=Theme.RED, size=8).pack(side=tk.RIGHT)

        self.hist_frame = tk.Frame(tab, bg=Theme.CARD)
        self.hist_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        self.hist_canvas = tk.Canvas(self.hist_frame, bg=Theme.CARD,
                                     highlightthickness=0)
        scroll = tk.Scrollbar(self.hist_frame, orient=tk.VERTICAL,
                              command=self.hist_canvas.yview)
        self.hist_inner = tk.Frame(self.hist_canvas, bg=Theme.CARD)

        self.hist_inner.bind("<Configure>",
            lambda e: self.hist_canvas.configure(
                scrollregion=self.hist_canvas.bbox("all")))

        self.hist_canvas.create_window((0, 0), window=self.hist_inner, anchor="nw")
        self.hist_canvas.configure(yscrollcommand=scroll.set)

        self.hist_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # TAB: Tips
    def _build_tab_tips(self):
        tab = tk.Frame(self.nb, bg=Theme.CARD)
        self.nb.add(tab, text=" 💡 Tips ")

        inner = tk.Frame(tab, bg=Theme.CARD)
        inner.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)

        label(inner, "SECURITY BEST PRACTICES", 9, bold=True, color=Theme.ACCENT).pack(anchor=tk.W, pady=(0,10))

        tips = [
            ("🔑", "Use 16+ characters", "Longer passwords are exponentially harder to crack"),
            ("🔀", "Mix character types", "Combining uppercase, lowercase, numbers & symbols drastically increases entropy"),
            ("🚫", "No personal info", "Avoid names, birthdays, or any info that can be guessed"),
            ("🔁", "Never reuse passwords", "A breach on one site puts all accounts at risk"),
            ("🗄️", "Use a password manager", "Tools like Bitwarden or 1Password remember passwords securely"),
            ("📲", "Enable 2FA", "Two-factor authentication stops attackers even with your password"),
            ("🔔", "Check for breaches", "Use HaveIBeenPwned.com to check if your email was in a data breach"),
        ]

        for icon, title, desc in tips:
            tf = tk.Frame(inner, bg=Theme.SURFACE,
                          highlightthickness=1, highlightbackground=Theme.BORDER)
            tf.pack(fill=tk.X, pady=(0, 8))

            tk.Label(tf, text=icon, bg=Theme.SURFACE,
                     font=("Segoe UI", 14)).grid(row=0, column=0, rowspan=2,
                                                  padx=(10,8), pady=8)
            tk.Label(tf, text=title, bg=Theme.SURFACE, fg=Theme.WHITE,
                     font=("Segoe UI", 9, "bold"), anchor=tk.W
                     ).grid(row=0, column=1, sticky=tk.W, pady=(8,0))
            tk.Label(tf, text=desc, bg=Theme.SURFACE, fg=Theme.DIM,
                     font=("Segoe UI", 8), anchor=tk.W, wraplength=260, justify=tk.LEFT
                     ).grid(row=1, column=1, sticky=tk.W, pady=(0,8))

    # ── Footer ────────────────────────────────────────────────────────
    def _build_footer(self):
        foot = tk.Frame(self.root, bg=Theme.CARD2, height=28)
        foot.pack(fill=tk.X, side=tk.BOTTOM)
        foot.pack_propagate(False)
        tk.Label(foot,
                 text="Pinnacle Labs Cybersecurity Internship  •  Password Analyzer Pro  •  Built with Python & Tkinter",
                 bg=Theme.CARD2, fg=Theme.DIM,
                 font=("Segoe UI", 7)).pack(pady=6)

    # ── Handlers ──────────────────────────────────────────────────────
    def _on_type(self, *args):
        self._run_analysis(self.pw_var.get())

    def _toggle_visibility(self):
        self._show_pw = not self._show_pw
        self.pw_entry.config(show="" if self._show_pw else "●")
        self._show_toggle_btn.config(text="🙈" if self._show_pw else "👁")

    def _generate_password(self):
        self._set_password(self.generator.generate(length=18))

    def _generate_custom(self):
        pw = self.generator.generate(
            length=self.len_var.get(),
            use_lower=self.opt_lower.get(),
            use_upper=self.opt_upper.get(),
            use_digits=self.opt_digits.get(),
            use_special=self.opt_special.get())
        self.gen_result.config(state=tk.NORMAL)
        self.gen_result.delete(0, tk.END)
        self.gen_result.insert(0, pw)
        self.gen_result.config(state="readonly")

    def _gen_memorable(self):
        self._set_password(self.generator.generate_memorable())

    def _copy_and_use(self):
        pw = self.gen_result.get()
        if pw:
            self._set_password(pw)
            self.nb.select(0)

    def _set_password(self, pw):
        self.pw_var.set(pw)
        self.pw_entry.config(show="")
        self._show_pw = True
        self._show_toggle_btn.config(text="🙈")

    def _clear(self):
        self.pw_var.set("")
        self.pw_entry.config(show="●")
        self._show_pw = False
        self._show_toggle_btn.config(text="👁")

    def _clear_history(self):
        self._history.clear()
        self._refresh_history()

    # ── Analysis ──────────────────────────────────────────────────────
    def _run_analysis(self, password: str):
        result   = self.engine.analyze(password)
        patterns = self.detector.analyze(password)

        self._update_gauge(result)
        self._update_stats(result)
        self._update_bars(result)
        self._update_checks(result["char_checks"])
        self._update_text(self.weak_text, patterns["weaknesses"],
                          "✅  No weaknesses detected!")
        self._update_text(self.rec_text, patterns["recommendations"], "")
        self._update_history(password, result)
        self._update_tab_badge(patterns["weaknesses"])

    def _update_gauge(self, r):
        color = Theme.STRENGTH_COLORS.get(r["label"], Theme.DIM)
        self.gauge.set(r["score"], color, r["label"])

    def _update_stats(self, r):
        self.stat_vars["Strength"].set(r["label"])
        self.stat_vars["Length"].set(f"{r['length']} chars")
        self.stat_vars["Crack Time"].set(r["crack_time"])
        self.stat_vars["Char Pool"].set(f"{r['char_pool']} chars")

    def _update_bars(self, r):
        color = Theme.STRENGTH_COLORS.get(r["label"], Theme.DIM)
        self.strength_bar.set(r["score"], color)
        self.bar_pct.config(text=f"{r['score']}%", fg=color)
        # Entropy bar (max ~128 bits = 100%)
        e_pct = min(100, int(r["entropy"] / 128 * 100))
        e_color = Theme.GREEN if e_pct > 60 else (Theme.YELLOW if e_pct > 30 else Theme.RED)
        self.entropy_bar.set(e_pct, e_color)
        self.entropy_lbl.config(text=f"{r['entropy']} bits", fg=e_color)

    def _update_checks(self, checks):
        for w in self.checks_frame.winfo_children():
            w.destroy()
        cols = 2
        for i, (name, passed) in enumerate(checks.items()):
            r, c = divmod(i, cols)
            f = tk.Frame(self.checks_frame, bg=Theme.SURFACE,
                         highlightthickness=1,
                         highlightbackground=Theme.GREEN if passed else Theme.RED)
            f.grid(row=r, column=c, sticky=tk.EW,
                   padx=(0,4) if c==0 else 0, pady=(0,4),
                   ipadx=6, ipady=6)
            self.checks_frame.columnconfigure(c, weight=1)
            icon  = "✅" if passed else "❌"
            color = Theme.GREEN if passed else Theme.RED
            tk.Label(f, text=f"{icon}", bg=Theme.SURFACE, fg=color,
                     font=("Segoe UI", 10)).pack()
            tk.Label(f, text=name, bg=Theme.SURFACE, fg=Theme.DIM,
                     font=("Segoe UI", 7), wraplength=100).pack()

    def _update_text(self, widget, items, empty_msg):
        widget.config(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, ("\n\n".join(items)) if items else empty_msg)
        widget.config(state=tk.DISABLED)

    def _update_history(self, password, result):
        if not password:
            return
        if (self._history and
                self._history[-1].masked == "●" * len(password) and
                self._history[-1].score == result["score"]):
            return
        self._history.append(
            HistoryEntry(password, result["score"], result["label"], result["crack_time"]))
        if len(self._history) > 20:
            self._history.pop(0)
        self._refresh_history()

    def _refresh_history(self):
        for w in self.hist_inner.winfo_children():
            w.destroy()
        for entry in reversed(self._history):
            f = tk.Frame(self.hist_inner, bg=Theme.SURFACE,
                         highlightthickness=1, highlightbackground=Theme.BORDER)
            f.pack(fill=tk.X, pady=(0,4))
            top = tk.Frame(f, bg=Theme.SURFACE)
            top.pack(fill=tk.X, padx=8, pady=(6,2))
            tk.Label(top, text=entry.masked[:24],
                     bg=Theme.SURFACE, fg=Theme.DIM,
                     font=("Consolas", 8)).pack(side=tk.LEFT)
            tk.Label(top, text=entry.time,
                     bg=Theme.SURFACE, fg=Theme.BORDER,
                     font=("Segoe UI", 7)).pack(side=tk.RIGHT)
            bot = tk.Frame(f, bg=Theme.SURFACE)
            bot.pack(fill=tk.X, padx=8, pady=(0,6))
            tk.Label(bot, text=entry.label,
                     bg=Theme.SURFACE, fg=entry.color,
                     font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT)
            tk.Label(bot, text=f"{entry.score}/100  •  {entry.length} chars  •  {entry.crack_time}",
                     bg=Theme.SURFACE, fg=Theme.DIM,
                     font=("Segoe UI", 7)).pack(side=tk.LEFT, padx=8)

    def _update_tab_badge(self, weaknesses):
        count = len(weaknesses)
        self.nb.tab(0, text=f" ⚠ Issues ({count}) " if count else " ✅ Issues ")

    # ── Export ────────────────────────────────────────────────────────
    def _export_report(self):
        password = self.pw_var.get()
        if not password:
            messagebox.showwarning("No Password", "Please enter a password first.")
            return

        result   = self.engine.analyze(password)
        patterns = self.detector.analyze(password)

        base_dir    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        reports_dir = os.path.join(base_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)

        ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(reports_dir, f"report_{ts}.txt")

        lines = [
            "=" * 60,
            "   PASSWORD ANALYSIS REPORT",
            "   Pinnacle Labs Cybersecurity Internship",
            "=" * 60,
            f"",
            f"Generated  : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Password   : {'●' * len(password)}  ({len(password)} characters)",
            f"",
            f"STRENGTH   : {result['label']}",
            f"SCORE      : {result['score']} / 100",
            f"ENTROPY    : {result['entropy']} bits",
            f"CHAR POOL  : {result['char_pool']} possible characters",
            f"CRACK TIME : {result['crack_time']}  (@ 1 billion guesses/sec)",
            f"",
            "-" * 60,
            "CHARACTER CHECKS:",
        ]
        for name, passed in result["char_checks"].items():
            lines.append(f"  {'[PASS]' if passed else '[FAIL]'}  {name}")

        lines += ["", "-" * 60, "WEAKNESSES DETECTED:"]
        if patterns["weaknesses"]:
            for w in patterns["weaknesses"]:
                lines.append(f"  {w}")
        else:
            lines.append("  None — password passed all checks.")

        lines += ["", "-" * 60, "RECOMMENDATIONS:"]
        for r in patterns["recommendations"]:
            lines.append(f"  {r}")

        lines += [
            "", "=" * 60,
            "  Generated by Password Analyzer Pro",
            "  Pinnacle Labs Cybersecurity Internship Project",
            "=" * 60,
        ]

        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        messagebox.showinfo("✅ Report Exported!",
                            f"Report saved successfully!\n\n📁 Location:\n{filename}")