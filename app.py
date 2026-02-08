# ✨ Spark to Fire 🔥 – Learning board (Kanban)
# Run: python app.py
# Requires: Python 3.11+, pip install customtkinter
# Data: data.json in the same folder (created on first run)
# Repo: spark-to-fire

import customtkinter as ctk
from storage import load_data, save_data
from logic import (
    apply_decay,
    create_item,
    delete_item,
    move_to_in_progress,
    move_to_discarded,
    move_to_completed,
    update_last_accessed,
    update_item,
    ITEM_TYPES,
)
try:
    from PIL import Image
    from emoji_assets import get_emoji_path
except ImportError:
    Image = None
    get_emoji_path = lambda c: ""

# --- Theme (softer colors; Envisioned/Spark visible on neutral background) ---
APPEARANCE = "light"
BG = "#E8F4FD"
COL_COLORS = {
    "envisioned": "#B2EBF2",   # aqua blue (spark emoji stands out)
    "in_progress": "#B9F6CA",  # mint green
    "discarded": "#FCE4EC",    # soft pink/red, lower saturation
    "completed": "#FFE0B2",    # soft orange (Fire)
}
CARD_BG = "#FFFFFF"
TEXT_COLOR = "#1A1A2E"
BTN_PRIMARY = "#B39DDB"        # softer purple
BTN_SUCCESS = "#00E676"
BTN_DISCARD = "#EF9A9A"       # softer red, lower saturation
TITLE_MAX_LEN = 80             # max characters for task title (input limit)
TITLE_DISPLAY_LEN = 50        # max characters shown on card (keeps date/delete visible)

# --- Emojis & column display names (use font Segoe UI Emoji for colorful emojis) ---
COLUMN_EMOJI = {
    "envisioned": "✨",
    "in_progress": "🌱",   # hourglass (fire 🔥 reserved for completed/Fire)
    "discarded": "🗑️",
    "completed": "🔥",
}
COLUMN_DISPLAY = {
    "envisioned": "Spark",
    "in_progress": "In Progress",
    "discarded": "Discarded",
    "completed": "Fire",
}
TYPE_EMOJI = {
    "tutorial": "📺",
    "course": "🎓",
    "book": "📚",
    "article": "📝",
    "project": "🛠️",
    "idea": "💡",
    "other": "📌",
}
WINDOW_TITLE = "✨ Spark to Fire 🔥"
ADD_SPARK_LABEL = "✨ Add Spark"


def _type_label(t: str) -> str:
    return f"{TYPE_EMOJI.get(t, '📌')} {t}"


def _first10(val):
    return (val or "")[:10] if val else ""

def _date_value(item: dict) -> str:
    """Return just the date value for the card (file-system style under column header)."""
    s = item.get("status") or ""
    if s == "envisioned":
        return _first10(item.get("date_added")) or "—"
    if s == "in_progress":
        return _first10(item.get("last_accessed_at") or item.get("moved_to_in_progress_at")) or "—"
    if s == "discarded":
        return _first10(item.get("discarded_at")) or "—"
    if s == "completed":
        return _first10(item.get("completed_at")) or "—"
    return _first10(item.get("date_added")) or "—"

def _date_display(item: dict) -> str:
    """Return label and value for the card date (used where no column header)."""
    s = item.get("status") or ""
    v = _date_value(item)
    if s == "envisioned":
        return f"Added: {v}"
    if s == "in_progress":
        return f"Last accessed: {v}"
    if s == "discarded":
        return f"Discarded: {v}"
    if s == "completed":
        return f"Completed: {v}"
    return f"Added: {v}"


def _emoji_image(app_self, char: str, size: int = 20):
    """Return a CTkImage for the emoji (colored via Twemoji PNG), or None if unavailable."""
    if Image is None:
        return None
    key = (char, size)
    if key not in app_self._emoji_img_cache:
        path = get_emoji_path(char)
        if path:
            try:
                pil_img = Image.open(path).convert("RGBA")
                pil_img = pil_img.resize((size, size), Image.Resampling.LANCZOS)
                app_self._emoji_img_cache[key] = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(size, size))
            except Exception:
                app_self._emoji_img_cache[key] = None
        else:
            app_self._emoji_img_cache[key] = None
    return app_self._emoji_img_cache.get(key)


class SparkToFireApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode(APPEARANCE)
        self.title("Spark to Fire")  # Plain text in OS title bar (no black emoji)
        self.geometry("1200x700")
        self.configure(fg_color=BG)

        self.data = load_data()
        apply_decay(self.data)
        self._emoji_img_cache = {}  # (char, size) -> CTkImage, so colored emojis stay visible
        self._title_anim_frame = 0  # 0 or 1 for pulse

        # Title banner centred: only the emojis animate (spark + fire pulse); text stays static
        title_outer = ctk.CTkFrame(self, fg_color="transparent")
        title_outer.pack(fill="x", pady=(10, 4))
        title_banner = ctk.CTkFrame(title_outer, fg_color="transparent")
        title_banner.pack(anchor="center")
        self._spark_small = _emoji_image(self, "✨", 24)
        self._spark_big = _emoji_image(self, "✨", 30)
        self._fire_small = _emoji_image(self, "🔥", 24)
        self._fire_big = _emoji_image(self, "🔥", 30)
        # Fixed-size boxes so only the emoji pulses and layout doesn't shift
        spark_box = ctk.CTkFrame(title_banner, fg_color="transparent", width=40, height=40)
        spark_box.pack(side="left", padx=(0, 4))
        spark_box.pack_propagate(False)
        self._title_spark_lbl = ctk.CTkLabel(spark_box, text="", image=self._spark_small or self._spark_big, fg_color="transparent")
        self._title_spark_lbl.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(title_banner, text="Spark to Fire", text_color=TEXT_COLOR, font=ctk.CTkFont(family="Candara", size=32, weight="bold")).pack(side="left", padx=16)
        fire_box = ctk.CTkFrame(title_banner, fg_color="transparent", width=40, height=40)
        fire_box.pack(side="left", padx=(0, 4))
        fire_box.pack_propagate(False)
        self._title_fire_lbl = ctk.CTkLabel(fire_box, text="", image=self._fire_small or self._fire_big, fg_color="transparent")
        self._title_fire_lbl.place(relx=0.5, rely=0.5, anchor="center")
        if self._spark_small and self._spark_big and self._fire_small and self._fire_big:
            self._animate_title_banner()

        # Top bar
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=8)
        add_spark_img = _emoji_image(self, "✨", 20)
        if add_spark_img:
            self.add_btn = ctk.CTkButton(top, text=" Add Spark", image=add_spark_img, fg_color=BTN_PRIMARY, text_color="white", command=self.open_add_spark_modal, font=ctk.CTkFont(size=13))
        else:
            self.add_btn = ctk.CTkButton(top, text=ADD_SPARK_LABEL, fg_color=BTN_PRIMARY, text_color="white", command=self.open_add_spark_modal)
        self.add_btn.pack(side="left")

        # Layout: top row = Envisioned (larger) + In Progress (smaller); bottom row = Discarded + Completed (smaller)
        cols_frame = ctk.CTkFrame(self, fg_color="transparent")
        cols_frame.pack(fill="both", expand=True, padx=8, pady=4)
        cols_frame.grid_columnconfigure(0, weight=3)   # Envisioned wider
        cols_frame.grid_columnconfigure(1, weight=2)   # In Progress
        cols_frame.grid_rowconfigure(0, weight=1)
        cols_frame.grid_rowconfigure(1, weight=1)      # Equal row height so all columns show scrollbars consistently
        self.column_frames = {}
        self.scroll_frames = {}
        order = [("envisioned", 0, 0), ("in_progress", 0, 1), ("discarded", 1, 0), ("completed", 1, 1)]
        for status, row, col in order:
            color = COL_COLORS.get(status, CARD_BG)
            col_f = ctk.CTkFrame(cols_frame, fg_color=color, corner_radius=8)
            col_f.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
            col_f.grid_columnconfigure(0, weight=1)
            col_f.grid_rowconfigure(0, weight=0)
            col_f.grid_rowconfigure(1, weight=1)
            # Row 0: column title only (Spark, In Progress, ...)
            title_row = ctk.CTkFrame(col_f, fg_color="transparent")
            title_row.grid(row=0, column=0, sticky="w", padx=4, pady=(4, 0))
            emoji_char = COLUMN_EMOJI.get(status, "")
            img = _emoji_image(self, emoji_char, 20)
            if img:
                ctk.CTkLabel(title_row, text="", image=img, padx=0, pady=0).pack(side="left", padx=(0, 4))
            ctk.CTkLabel(title_row, text=COLUMN_DISPLAY.get(status, status), text_color=TEXT_COLOR, font=ctk.CTkFont(size=14, weight="bold"), padx=0, pady=0).pack(side="left")
            # Row 1: scroll — "Title" / "Date added" header is added inside scroll in refresh_board (first child)
            scroll = ctk.CTkScrollableFrame(col_f, fg_color="transparent")
            scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))
            self.column_frames[status] = col_f
            self.scroll_frames[status] = scroll
        # Footer: collected fires count (colored 🔥 per completed item)
        self.footer = ctk.CTkFrame(self, fg_color="transparent")
        self.footer.pack(fill="x", padx=12, pady=8)
        ctk.CTkLabel(self.footer, text="Collected fires: ", text_color=TEXT_COLOR, font=ctk.CTkFont(size=13)).pack(side="left")
        self.fires_imgs_frame = ctk.CTkFrame(self.footer, fg_color="transparent")
        self.fires_imgs_frame.pack(side="left")
        self.refresh_board()

    def refresh_board(self):
        self.data = load_data()
        COL_HEADERS = {
            "envisioned": ("Title", "Date added"),
            "in_progress": ("Title", "Last accessed"),
            "discarded": ("Title", "Discarded"),
            "completed": ("Title", "Completed"),
        }
        for status, scroll in self.scroll_frames.items():
            for w in scroll.winfo_children():
                w.destroy()
            # First child: header row (Title left, date right); grid so no centering; no border
            head_left, head_right = COL_HEADERS.get(status, ("Title", "Date"))
            header_row = ctk.CTkFrame(scroll, fg_color="transparent", border_width=0, corner_radius=0)
            header_row.pack(side="top", fill="x", pady=(0, 2))
            header_row.grid_columnconfigure(0, weight=0)   # Title: natural width
            header_row.grid_columnconfigure(1, weight=1)    # stretch middle
            header_row.grid_columnconfigure(2, weight=0)   # date: natural width
            lbl_title = ctk.CTkLabel(header_row, text=head_left, text_color=TEXT_COLOR, font=ctk.CTkFont(size=11, weight="bold"), padx=0, pady=0, anchor="w", fg_color="transparent")
            lbl_title.grid(row=0, column=0, sticky="w", padx=(10, 8))
            lbl_date = ctk.CTkLabel(header_row, text=head_right, text_color=TEXT_COLOR, font=ctk.CTkFont(size=11, weight="bold"), padx=0, pady=0, anchor="e", fg_color="transparent")
            lbl_date.grid(row=0, column=2, sticky="e", padx=(8, 4))
        completed_count = sum(1 for i in self.data.get("items", []) if i.get("status") == "completed")
        for w in self.fires_imgs_frame.winfo_children():
            w.destroy()
        fire_img = _emoji_image(self, "🔥", 20)
        if fire_img and completed_count > 0:
            for _ in range(completed_count):
                ctk.CTkLabel(self.fires_imgs_frame, text="", image=fire_img).pack(side="left", padx=1)
        elif not fire_img:
            ctk.CTkLabel(self.fires_imgs_frame, text="🔥" * completed_count if completed_count else "—", text_color=TEXT_COLOR, font=ctk.CTkFont(size=14)).pack(side="left")
        else:
            ctk.CTkLabel(self.fires_imgs_frame, text="—", text_color=TEXT_COLOR, font=ctk.CTkFont(size=14)).pack(side="left")

        for item in self.data.get("items", []):
            status = item.get("status") or "envisioned"
            if status not in self.scroll_frames:
                continue
            scroll = self.scroll_frames[status]
            card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=6, border_width=1, border_color="#E0E0E0")
            card.pack(fill="x", pady=2, padx=2)
            # One line per card: title (expand) | type | date | delete
            item_id = item.get("id")
            raw_title = item.get("title") or "Untitled"
            display_title = (raw_title[:TITLE_DISPLAY_LEN] + "…") if len(raw_title) > TITLE_DISPLAY_LEN else raw_title
            title_lbl = ctk.CTkLabel(card, text=display_title, text_color=TEXT_COLOR, anchor="w", font=ctk.CTkFont(weight="bold"))
            title_lbl.pack(side="left", fill="x", expand=True, padx=(8, 4), pady=6)
            type_key = item.get("type") or "other"
            type_emoji = TYPE_EMOJI.get(type_key, "📌")
            type_img = _emoji_image(self, type_emoji, 16)
            type_frame = ctk.CTkFrame(card, fg_color="transparent")
            type_frame.pack(side="left", padx=4, pady=6)
            if type_img:
                ctk.CTkLabel(type_frame, text="", image=type_img).pack(side="left", padx=(0, 2))
            ctk.CTkLabel(type_frame, text=type_key, text_color=TEXT_COLOR, font=ctk.CTkFont(size=12)).pack(side="left")
            date_lbl = ctk.CTkLabel(card, text=_date_value(item), text_color=TEXT_COLOR, font=ctk.CTkFont(size=11))
            date_lbl.pack(side="left", padx=4, pady=6)
            for w in (card, title_lbl, type_frame, date_lbl):
                w.bind("<Button-1>", lambda e, iid=item_id: self.on_card_click(iid))
            del_img = _emoji_image(self, "🗑️", 18)
            if del_img:
                del_btn = ctk.CTkButton(card, text="", image=del_img, width=32, fg_color=BTN_DISCARD, command=lambda iid=item_id: self.on_delete_item(iid))
            else:
                del_btn = ctk.CTkButton(card, text="🗑️", width=28, fg_color=BTN_DISCARD, text_color="white", command=lambda iid=item_id: self.on_delete_item(iid))
            del_btn.pack(side="right", padx=4, pady=4)
            for child in type_frame.winfo_children():
                child.bind("<Button-1>", lambda e, iid=item_id: self.on_card_click(iid))

    def on_card_click(self, item_id: str):
        update_last_accessed(self.data, item_id)
        self.open_detail_view(item_id)

    def on_delete_item(self, item_id: str):
        delete_item(self.data, item_id)
        self.refresh_board()

    def _animate_title_banner(self):
        """Pulse spark and fire emojis in the title banner (sparking / flaming effect)."""
        try:
            self._title_anim_frame = 1 - self._title_anim_frame
            if self._title_anim_frame == 0:
                self._title_spark_lbl.configure(image=self._spark_small)
                self._title_fire_lbl.configure(image=self._fire_small)
            else:
                self._title_spark_lbl.configure(image=self._spark_big)
                self._title_fire_lbl.configure(image=self._fire_big)
        except Exception:
            pass
        self.after(420, self._animate_title_banner)

    def open_add_spark_modal(self):
        # Add Spark modal: everything in one line – title, type, Save, Cancel
        modal = ctk.CTkToplevel(self)
        modal.title(ADD_SPARK_LABEL)
        modal.geometry("720x56")
        modal.transient(self)
        modal.grab_set()
        row = ctk.CTkFrame(modal, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=12)
        title_entry = ctk.CTkEntry(row, width=320, placeholder_text="Learning idea title")
        title_entry.pack(side="left", padx=(0, 8))
        def _limit_title_len(*_):
            s = title_entry.get() or ""
            if len(s) > TITLE_MAX_LEN:
                title_entry.delete(TITLE_MAX_LEN, "end")
        title_entry.bind("<KeyRelease>", _limit_title_len)
        type_var = ctk.StringVar(value=f"{TYPE_EMOJI.get('idea', '')} idea")
        type_menu = ctk.CTkOptionMenu(row, variable=type_var, values=[f"{TYPE_EMOJI.get(t, '')} {t}" for t in ITEM_TYPES], width=140)
        type_menu.pack(side="left", padx=(0, 8))
        def get_type_key():
            raw = type_var.get()
            for t in ITEM_TYPES:
                if f"{TYPE_EMOJI.get(t, '')} {t}" == raw or t in raw:
                    return t
            return "other"
        def on_save():
            title = (title_entry.get() or "").strip()[:TITLE_MAX_LEN]
            if not title:
                return
            create_item(self.data, title, get_type_key())
            modal.destroy()
            self.refresh_board()
        def on_cancel():
            modal.destroy()
        ctk.CTkButton(row, text="💾 Save", fg_color=BTN_PRIMARY, text_color=TEXT_COLOR, command=on_save).pack(side="left", padx=(0, 6))
        ctk.CTkButton(row, text="Cancel", fg_color="gray75", text_color=TEXT_COLOR, command=on_cancel).pack(side="left")

    def open_detail_view(self, item_id: str):
        # Detail view: update_last_accessed on click; Mark Completed, Discard, Move to In Progress
        item = next((i for i in self.data.get("items", []) if i.get("id") == item_id), None)
        if not item:
            return
        top = ctk.CTkToplevel(self)
        top.title(f"{item.get('title', '')[:40]} – Detail")
        top.geometry("520x580")
        top.transient(self)
        # Scrollable area so takeaways/notes have room and can grow
        scroll = ctk.CTkScrollableFrame(top, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=12)
        f = ctk.CTkFrame(scroll, fg_color="transparent")
        f.pack(fill="both", expand=True)
        ctk.CTkLabel(f, text=item.get("title") or "Untitled", text_color=TEXT_COLOR, font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(f, text=_type_label(item.get("type") or "other"), text_color=TEXT_COLOR).pack(anchor="w", pady=2)
        ctk.CTkLabel(f, text=f"Status: {item.get('status', '')}", text_color=TEXT_COLOR).pack(anchor="w", pady=2)
        ctk.CTkLabel(f, text=f"Added: {(item.get('date_added') or '')[:10]}", text_color=TEXT_COLOR).pack(anchor="w", pady=2)
        if item.get("moved_to_in_progress_at"):
            ctk.CTkLabel(f, text=f"In progress since: {(item.get('moved_to_in_progress_at') or '')[:10]}", text_color=TEXT_COLOR).pack(anchor="w", pady=2)
        if item.get("last_accessed_at"):
            ctk.CTkLabel(f, text=f"Last accessed: {(item.get('last_accessed_at') or '')[:10]}", text_color=TEXT_COLOR).pack(anchor="w", pady=2)
        if item.get("discarded_at"):
            ctk.CTkLabel(f, text=f"Discarded: {(item.get('discarded_at') or '')[:10]}", text_color=TEXT_COLOR).pack(anchor="w", pady=2)
        if item.get("completed_at"):
            ctk.CTkLabel(f, text=f"Completed: {(item.get('completed_at') or '')[:10]}", text_color=TEXT_COLOR).pack(anchor="w", pady=2)

        status = item.get("status") or "envisioned"
        actions = ctk.CTkFrame(f, fg_color="transparent")
        actions.pack(fill="x", pady=12)
        if status == "in_progress":
            ctk.CTkButton(actions, text="✅ Mark Completed", fg_color=BTN_SUCCESS, text_color=TEXT_COLOR, command=lambda: self._detail_done(top, item_id, "completed")).pack(side="left", padx=(0, 8))
            ctk.CTkButton(actions, text="🗑️ Discard", fg_color=BTN_DISCARD, text_color=TEXT_COLOR, command=lambda: self._detail_done(top, item_id, "discarded")).pack(side="left")
        elif status == "envisioned":
            ctk.CTkButton(actions, text="⏳ Move to In Progress", fg_color=BTN_PRIMARY, text_color=TEXT_COLOR, command=lambda: self._detail_done(top, item_id, "in_progress")).pack(side="left")
        elif status == "discarded":
            ctk.CTkButton(actions, text="⏳ Move to In Progress", fg_color=BTN_PRIMARY, text_color=TEXT_COLOR, command=lambda: self._detail_done(top, item_id, "in_progress")).pack(side="left")

        ctk.CTkButton(actions, text="🗑️ Delete", fg_color=BTN_DISCARD, text_color=TEXT_COLOR, command=lambda: self._detail_delete(top, item_id)).pack(side="left", padx=(12, 0))

        if status == "completed":
            # Editable takeaways and learning_notes; height grows with content
            def _textbox_height(lines, min_h=100, max_h=340, line_h=22):
                return min(max_h, max(min_h, lines * line_h + 20))
            takeaways_content = (item.get("takeaways") or "").splitlines() or [""]
            notes_content = (item.get("learning_notes") or "").splitlines() or [""]
            takeaways_h = _textbox_height(len(takeaways_content))
            notes_h = _textbox_height(len(notes_content))
            ctk.CTkLabel(f, text="Takeaways:", text_color=TEXT_COLOR).pack(anchor="w", pady=(8, 2))
            takeaways_txt = ctk.CTkTextbox(f, height=takeaways_h, fg_color=CARD_BG)
            takeaways_txt.pack(fill="x", pady=(0, 6))
            takeaways_txt.insert("1.0", item.get("takeaways") or "")
            ctk.CTkLabel(f, text="Learning notes:", text_color=TEXT_COLOR).pack(anchor="w", pady=(4, 2))
            notes_txt = ctk.CTkTextbox(f, height=notes_h, fg_color=CARD_BG)
            notes_txt.pack(fill="x", pady=(0, 8))
            notes_txt.insert("1.0", item.get("learning_notes") or "")
            def _resize_textbox(tb, min_h=100, max_h=340):
                try:
                    text = tb.get("1.0", "end")
                    lines = len(text.splitlines()) if text.strip() else 1
                    new_h = min(max_h, max(min_h, lines * 22 + 20))
                    tb.configure(height=new_h)
                except Exception:
                    pass
            takeaways_txt.bind("<KeyRelease>", lambda e: _resize_textbox(takeaways_txt))
            notes_txt.bind("<KeyRelease>", lambda e: _resize_textbox(notes_txt))
            def save_completed():
                update_item(self.data, item_id, takeaways=takeaways_txt.get("1.0", "end").strip(), learning_notes=notes_txt.get("1.0", "end").strip())
                top.destroy()
                self.refresh_board()
            ctk.CTkButton(actions, text="💾 Save", fg_color=BTN_PRIMARY, text_color=TEXT_COLOR, command=save_completed).pack(side="left")

        ctk.CTkButton(f, text="Close", fg_color="gray75", text_color=TEXT_COLOR, command=top.destroy).pack(anchor="w", pady=(8, 0))

    def _detail_done(self, toplevel, item_id: str, target: str):
        if target == "completed":
            move_to_completed(self.data, item_id)
        elif target == "discarded":
            move_to_discarded(self.data, item_id)
        elif target == "in_progress":
            move_to_in_progress(self.data, item_id)
        toplevel.destroy()
        self.refresh_board()

    def _detail_delete(self, toplevel, item_id: str):
        delete_item(self.data, item_id)
        toplevel.destroy()
        self.refresh_board()


def main():
    app = SparkToFireApp()
    app.mainloop()


if __name__ == "__main__":
    main()
