"""
app/components/memory_tab.py — Robot memory viewer
"""
import tkinter as tk
from app.theme import Theme


class MemoryTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=Theme.SIDEBAR_BG)

        # Header
        hdr = tk.Frame(self, bg=Theme.SIDEBAR_BG)
        hdr.pack(fill=tk.X, padx=Theme.SP_MD, pady=(Theme.SP_MD, Theme.SP_SM))
        tk.Label(hdr, text="Agent Memory", font=Theme.FONT_H1,
                 bg=Theme.SIDEBAR_BG, fg=Theme.FG).pack(side=tk.LEFT)

        # Card
        card = tk.Frame(self, bg=Theme.SURFACE,
                        highlightbackground=Theme.BORDER, highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True,
                  padx=Theme.SP_MD, pady=(0, Theme.SP_MD))

        self.memory_text = tk.Text(card, wrap=tk.WORD,
                                   bg=Theme.SURFACE, fg=Theme.FG,
                                   font=Theme.FONT_BODY,
                                   bd=0, relief=tk.FLAT,
                                   padx=Theme.SP_MD, pady=Theme.SP_MD)
        self.memory_text.pack(fill=tk.BOTH, expand=True)
        self.memory_text.config(state=tk.DISABLED)

        self._update()

    def _update(self):
        try:
            import hardware.init as hw
            lines = ["🧠  Known Objects\n" + "─" * 24]
            if hw.known_objects:
                for obj, coords in hw.known_objects.items():
                    if isinstance(coords, list):
                        lines.append(f"  • {obj}: X={coords[0]:.1f}  Y={coords[1]:.1f}")
                    else:
                        lines.append(f"  • {obj}: {coords}")
            else:
                lines.append("  (Empty)")

            lines += ["", "🖐️  Gripper Status\n" + "─" * 24]
            if hw.is_holding_object:
                lines.append(f"  Holding: {hw.current_held_object}")
            else:
                lines.append("  Empty")

            self.memory_text.config(state=tk.NORMAL)
            self.memory_text.delete(1.0, tk.END)
            self.memory_text.insert(tk.END, "\n".join(lines))
            self.memory_text.config(state=tk.DISABLED)
        except Exception:
            pass
        self.after(1000, self._update)
