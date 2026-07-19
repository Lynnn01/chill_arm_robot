class Theme:
    """
    Shadcn-UI inspired minimalist theme configuration.
    80% White, 10% Black, 10% Subtle Accents.
    """
    BG = "#FFFFFF"            # Main white background
    FG = "#0F172A"            # Near black for primary text
    MUTED_FG = "#64748B"      # Slate 500 for secondary text
    BORDER = "#E2E8F0"        # Slate 200 for borders
    SURFACE = "#FFFFFF"       # White for cards/panels (relies on borders)
    SURFACE_MUTED = "#F8FAFC" # Slate 50 for subtle active states/inputs
    PRIMARY = "#0F172A"       # Black for primary buttons/accents
    PRIMARY_FG = "#FFFFFF"    # White text on primary buttons
    PRIMARY_HOVER = "#334155" # Slate 700 for hover state
    DANGER = "#EF4444"        # Red for danger actions
    DANGER_HOVER = "#DC2626"
    
    # Fonts
    FONT_TITLE = ("Tahoma", 24, "bold")
    FONT_H1 = ("Tahoma", 16, "bold")
    FONT_H2 = ("Tahoma", 14, "bold")
    FONT_BODY = ("Tahoma", 12)
    FONT_BODY_BOLD = ("Tahoma", 12, "bold")
    FONT_SMALL = ("Tahoma", 10)
    FONT_LOG = ("Tahoma", 16)
    FONT_LOG_BOLD = ("Tahoma", 16, "bold")
    
    @classmethod
    def apply_window_style(cls, root):
        root.configure(bg=cls.BG)
