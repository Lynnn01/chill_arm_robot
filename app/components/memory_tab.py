import tkinter as tk
from app.theme import Theme

class MemoryTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=Theme.BG)
        self.card = tk.Frame(self, bg=Theme.SURFACE, relief=tk.SOLID, bd=1, highlightbackground=Theme.BORDER, highlightthickness=1)
        self.card.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.memory_text = tk.Text(self.card, wrap=tk.WORD, bg=Theme.SURFACE, fg=Theme.FG, font=Theme.FONT_BODY, bd=0, relief=tk.FLAT, padx=15, pady=15)
        self.memory_text.pack(fill=tk.BOTH, expand=True, pady=10)
        self.memory_text.config(state=tk.DISABLED)
        
        self._update_memory_ui()

    def _update_memory_ui(self):
        try:
            import hardware.init as hw
            lines = ["🧠 Known Objects:\n"]
            if hw.known_objects:
                for obj, coords in hw.known_objects.items():
                    if isinstance(coords, list):
                        lines.append(f" 🔹 {obj}: [X: {coords[0]:.1f}, Y: {coords[1]:.1f}]")
                    else:
                        lines.append(f" 🔹 {obj}: {coords}")
            else:
                lines.append("   (Empty)")
            lines.append(f"\n🖐️ Gripper Status:\n")
            if hw.is_holding_object:
                lines.append(f" 🔸 Holding: {hw.current_held_object}")
            else:
                lines.append(" 🔸 Empty")
            
            self.memory_text.config(state=tk.NORMAL)
            self.memory_text.delete(1.0, tk.END)
            self.memory_text.insert(tk.END, "\n".join(lines))
            self.memory_text.config(state=tk.DISABLED)
        except Exception:
            pass
        self.after(1000, self._update_memory_ui)
