"""
QuickFind Modern Tkinter UI
Custom-rendered modern dark HUD with real application PNG icons,
rounded card highlights, category pills, smooth slide animation, and elevated typography.
"""

import os
import sys
import tkinter as tk
from typing import Optional, List, Dict
from config import (
    APP_NAME, SEARCH_BAR_WIDTH, COLOR_BG_BAR, COLOR_BG_BAR_BORDER,
    COLOR_BG_RESULTS, COLOR_ACCENT, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_ITEM_SELECTED, COLOR_ITEM_HOVER
)
from services.search_engine import SearchEngine, SearchResult
from core.app_launcher import AppLauncher
from storage.settings import SettingsManager


class TkResultCard(tk.Frame):
    """Custom-rendered result card with icon, title, subtitle, and launch pill."""

    def __init__(self, parent, result: SearchResult, on_click, on_hover):
        super().__init__(parent, bg="#12151c", cursor="hand2")
        self.result = result
        self.on_click = on_click
        self.on_hover = on_hover
        self._is_selected = False
        self._photo = None

        self.config(highlightthickness=0, padx=10, pady=6)

        # 1. Left Accent Bar (indicator for selected item)
        self.accent_bar = tk.Frame(self, width=3, bg="#12151c")
        self.accent_bar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # 2. Application Icon
        self.icon_label = tk.Label(self, bg="#12151c")
        self._load_icon()
        self.icon_label.pack(side=tk.LEFT, padx=(0, 12))

        # 3. Text Column (Title + Path)
        self.text_frame = tk.Frame(self, bg="#12151c")
        self.text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Title Row (App Name + Tag Badge)
        self.title_row = tk.Frame(self.text_frame, bg="#12151c")
        self.title_row.pack(fill=tk.X, anchor=tk.W)

        self.title_label = tk.Label(
            self.title_row,
            text=result.app.name,
            font=("Segoe UI", 12, "bold"),
            fg="#ffffff",
            bg="#12151c"
        )
        self.title_label.pack(side=tk.LEFT, anchor=tk.W)

        # Tag Badge (APP / SYSTEM / TOOL)
        tag_text = (result.app.source or "app").upper()
        self.tag_label = tk.Label(
            self.title_row,
            text=f" {tag_text} ",
            font=("Segoe UI", 8, "bold"),
            fg="#94a3b8",
            bg="#1e2433",
            relief=tk.FLAT
        )
        self.tag_label.pack(side=tk.LEFT, padx=(8, 0))

        # Subtitle (Path)
        sub_text = result.app.target_path
        if len(sub_text) > 55:
            sub_text = "..." + sub_text[-52:]

        self.sub_label = tk.Label(
            self.text_frame,
            text=sub_text,
            font=("Segoe UI", 9),
            fg="#717d91",
            bg="#12151c",
            anchor=tk.W
        )
        self.sub_label.pack(fill=tk.X, anchor=tk.W, pady=(2, 0))

        # 4. Right Enter Pill
        self.enter_pill = tk.Label(
            self,
            text=" ↵ Enter ",
            font=("Segoe UI", 9, "bold"),
            fg=COLOR_ACCENT,
            bg="#162633",
            relief=tk.FLAT,
            padx=4,
            pady=2
        )
        self.enter_pill.pack(side=tk.RIGHT, padx=(0, 4))

        # Bind events for all child widgets
        for w in (self, self.accent_bar, self.icon_label, self.text_frame,
                  self.title_row, self.title_label, self.tag_label, self.sub_label, self.enter_pill):
            w.bind("<Button-1>", lambda e: self.on_click(self.result))
            w.bind("<Enter>", lambda e: self.on_hover(self))

    def _load_icon(self):
        """Load extracted PNG icon into Tk PhotoImage."""
        png_path = self.result.app.icon_path
        if png_path and os.path.exists(png_path):
            try:
                self._photo = tk.PhotoImage(file=png_path)
                self.icon_label.config(image=self._photo)
                return
            except Exception:
                pass

        # Fallback text icon
        initial = (self.result.app.name[:1] if self.result.app.name else "A").upper()
        self.icon_label.config(
            text=f" {initial} ",
            font=("Segoe UI", 13, "bold"),
            fg=COLOR_ACCENT,
            bg="#1c2436",
            width=3,
            height=1
        )

    def set_selected(self, selected: bool):
        """Update visual styling for selection state."""
        self._is_selected = selected
        bg_color = "#1c2230" if selected else "#12151c"
        accent_color = COLOR_ACCENT if selected else "#12151c"
        pill_bg = "#183244" if selected else "#162633"

        self.config(bg=bg_color)
        self.accent_bar.config(bg=accent_color)
        self.text_frame.config(bg=bg_color)
        self.title_row.config(bg=bg_color)
        self.title_label.config(bg=bg_color, fg="#ffffff" if selected else "#f1f5f9")
        self.sub_label.config(bg=bg_color, fg="#94a3b8" if selected else "#717d91")
        self.icon_label.config(bg=bg_color)
        self.enter_pill.config(bg=pill_bg, fg=COLOR_ACCENT)


class TkSearchWindow:
    """Modern dark HUD launcher using custom Tkinter cards and slide animation."""

    def __init__(
        self,
        search_engine: SearchEngine,
        app_launcher: AppLauncher,
        settings: SettingsManager
    ):
        self.search_engine = search_engine
        self.app_launcher = app_launcher
        self.settings = settings

        self.root = tk.Tk()
        self._current_results: List[SearchResult] = []
        self._card_widgets: List[TkResultCard] = []
        self._selected_index = 0
        self._is_visible = False
        self._target_y = 50

        self._init_window()
        self._build_ui()

    def _init_window(self) -> None:
        """Configure frameless top-level window with dark styling."""
        self.root.title(APP_NAME)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#080a0e")

        self.root.bind("<Escape>", lambda e: self.hide())
        self.root.bind("<Down>", self._on_key_down)
        self.root.bind("<Up>", self._on_key_up)
        self.root.bind("<Return>", self._on_key_enter)
        self.root.bind("<FocusOut>", self._on_focus_out)

    def _build_ui(self) -> None:
        """Construct glassmorphic outer container and search input."""
        # Glassmorphic outer border (cyan glow outline)
        self.glow_border = tk.Frame(self.root, bg="#202838", padx=1, pady=1)
        self.glow_border.pack(fill=tk.BOTH, expand=True)

        self.inner_container = tk.Frame(self.glow_border, bg="#10131a", highlightthickness=1, highlightbackground="#2a3346")
        self.inner_container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # 1. Top Search Bar Frame
        self.bar_frame = tk.Frame(self.inner_container, bg="#141822", height=60)
        self.bar_frame.pack(fill=tk.X, padx=14, pady=10)

        # Cyan Search Icon
        self.search_icon = tk.Label(self.bar_frame, text="🔍", font=("Segoe UI", 14), bg="#141822", fg=COLOR_ACCENT)
        self.search_icon.pack(side=tk.LEFT, padx=(4, 12))

        # Search Entry Field
        self.entry_var = tk.StringVar()
        self.entry_var.trace_add("write", lambda *args: self._on_query_changed())
        self.entry = tk.Entry(
            self.bar_frame,
            textvariable=self.entry_var,
            font=("Segoe UI", 15, "bold"),
            bg="#141822",
            fg="#ffffff",
            insertbackground=COLOR_ACCENT,
            bd=0,
            highlightthickness=0
        )
        self.entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Shortcut Hint Badge (Ctrl+F | ESC)
        hk = self.settings.get("global_shortcut", "Ctrl+F")
        self.badge_lbl = tk.Label(
            self.bar_frame,
            text=f" {hk} | ESC ",
            font=("Segoe UI", 9, "bold"),
            bg="#212736",
            fg="#94a3b8",
            padx=8,
            pady=3,
            relief=tk.FLAT
        )
        self.badge_lbl.pack(side=tk.RIGHT, padx=(6, 4))

        # 2. Results Scrollable Cards Container
        self.results_frame = tk.Frame(self.inner_container, bg="#0d0f15")
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 8))

    def show(self) -> None:
        """Display floating launcher with smooth slide-down animation."""
        if self._is_visible:
            self.entry.select_range(0, tk.END)
            self.entry.focus_set()
            return

        self._is_visible = True
        self._update_results(self.entry_var.get())

        sw = self.root.winfo_screenwidth()
        w = SEARCH_BAR_WIDTH
        h = self._calculate_height()
        x = (sw - w) // 2

        self.root.geometry(f"{w}x{h}+{x}+{self._target_y - 25}")
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.entry.focus_set()
        self.entry.select_range(0, tk.END)

        # Slide-down interpolation
        self._animate_slide(0, 8, self._target_y - 25, self._target_y, x, w, h)

    def _animate_slide(self, step: int, total: int, start_y: int, end_y: int, x: int, w: int, h: int) -> None:
        if step > total or not self._is_visible:
            self.root.geometry(f"{w}x{h}+{x}+{end_y}")
            return

        t = step / float(total)
        ease = 1.0 - (1.0 - t) ** 3
        cur_y = int(start_y + (end_y - start_y) * ease)

        self.root.geometry(f"{w}x{h}+{x}+{cur_y}")
        self.root.after(14, lambda: self._animate_slide(step + 1, total, start_y, end_y, x, w, h))

    def hide(self) -> None:
        self._is_visible = False
        self.root.withdraw()

    def toggle(self) -> None:
        if self._is_visible:
            self.hide()
        else:
            self.show()

    def _calculate_height(self) -> int:
        if not self._current_results:
            return 80
        return min(520, 86 + (len(self._current_results) * 60))

    def _on_query_changed(self) -> None:
        self._update_results(self.entry_var.get())

    def _update_results(self, query: str) -> None:
        """Query search engine and rebuild card list."""
        max_res = self.settings.get("max_visible_results", 6)
        prioritize_recent = self.settings.get("prioritize_recent", True)
        results = self.search_engine.search(query, max_results=max_res, prioritize_recent=prioritize_recent)
        self._current_results = results

        # Clear existing card widgets
        for c in self._card_widgets:
            c.destroy()
        self._card_widgets.clear()

        # Build cards
        for idx, r in enumerate(results):
            card = TkResultCard(
                self.results_frame,
                r,
                on_click=self._on_card_clicked,
                on_hover=self._on_card_hovered
            )
            card.pack(fill=tk.X, pady=2)
            self._card_widgets.append(card)

        if self._card_widgets:
            self._selected_index = 0
            self._card_widgets[0].set_selected(True)

        if self._is_visible:
            sw = self.root.winfo_screenwidth()
            w = SEARCH_BAR_WIDTH
            h = self._calculate_height()
            x = (sw - w) // 2
            self.root.geometry(f"{w}x{h}+{x}+{self._target_y}")

    def _on_card_clicked(self, result: SearchResult) -> None:
        self.hide()
        self.app_launcher.launch(
            target_path=result.app.target_path,
            arguments=result.app.arguments,
            working_dir=result.app.working_dir,
            app_id=result.app.id
        )

    def _on_card_hovered(self, card: TkResultCard) -> None:
        for idx, c in enumerate(self._card_widgets):
            if c == card:
                self._selected_index = idx
                c.set_selected(True)
            else:
                c.set_selected(False)

    def _on_key_down(self, event) -> None:
        if not self._card_widgets:
            return
        self._card_widgets[self._selected_index].set_selected(False)
        self._selected_index = (self._selected_index + 1) % len(self._card_widgets)
        self._card_widgets[self._selected_index].set_selected(True)

    def _on_key_up(self, event) -> None:
        if not self._card_widgets:
            return
        self._card_widgets[self._selected_index].set_selected(False)
        self._selected_index = (self._selected_index - 1 + len(self._card_widgets)) % len(self._card_widgets)
        self._card_widgets[self._selected_index].set_selected(True)

    def _on_key_enter(self, event) -> None:
        if 0 <= self._selected_index < len(self._current_results):
            res = self._current_results[self._selected_index]
            self.hide()
            self.app_launcher.launch(
                target_path=res.app.target_path,
                arguments=res.app.arguments,
                working_dir=res.app.working_dir,
                app_id=res.app.id
            )

    def _on_focus_out(self, event) -> None:
        if self.settings.get("hide_on_blur", True):
            self.root.after(140, self._check_focus)

    def _check_focus(self) -> None:
        focused = self.root.focus_get()
        if focused is None and self._is_visible:
            self.hide()
