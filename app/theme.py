class Theme:
    """
    Unified Design Rules — White-First approach.
    80% White, 10% Black/Dark, 10% Accent/Semantic.
    All UI constants live here. Never hardcode in components.
    """
    # --- Background Layers ---
    BG = "#F8FAFC"            # App window — slightly off-white (Slate 50)
    SURFACE = "#FFFFFF"       # Cards, panels
    SURFACE_MUTED = "#F1F5F9" # Input fields, inactive tabs (Slate 100)
    SIDEBAR_BG = "#FFFFFF"    # Left panel sidebar

    # --- Text ---
    FG = "#0F172A"            # Primary text — near-black (Slate 900)
    MUTED_FG = "#94A3B8"      # Secondary / placeholder text (Slate 400)
    CAPTION_FG = "#64748B"    # Captions / axis labels (Slate 500)

    # --- Borders ---
    BORDER = "#E2E8F0"        # Card & input borders (Slate 200)
    BORDER_FOCUS = "#6366F1"  # Indigo 500 (Magic UI accent)

    # --- Primary Action (SEND) ---
    PRIMARY = "#1E293B"       # Dark slate
    PRIMARY_FG = "#FFFFFF"
    PRIMARY_HOVER = "#334155" # Slate 700

    # --- Danger Action (RESET) ---
    DANGER = "#EF4444"
    DANGER_HOVER = "#DC2626"
    DANGER_FG = "#FFFFFF"

    # --- Semantic ---
    ACCENT = "#6366F1"        # Indigo 500
    ACCENT_FG = "#FFFFFF"
    SUCCESS = "#22C55E"
    WARNING = "#F59E0B"

    # --- Fonts ---
    FONT_BRAND = ("Tahoma", 18, "bold")     # "ONE ARM" branding
    FONT_TITLE = ("Tahoma", 18, "bold")
    FONT_H1 = ("Tahoma", 14, "bold")
    FONT_H2 = ("Tahoma", 12, "bold")
    FONT_BODY = ("Tahoma", 12)
    FONT_BODY_BOLD = ("Tahoma", 12, "bold")
    FONT_SMALL = ("Tahoma", 10)
    FONT_CAPTION = ("Tahoma", 8)
    FONT_LOG = ("Tahoma", 12)
    FONT_LOG_BOLD = ("Tahoma", 12, "bold")

    # --- Spacing (8-pt grid) ---
    SP_XS = 4
    SP_SM = 8
    SP_MD = 16
    SP_LG = 24
    SP_XL = 32

    # --- Radius ---
    RADIUS_SM = 8
    RADIUS_MD = 12
    RADIUS_LG = 16
    RADIUS_PILL = 24

    @classmethod
    def apply_window_style(cls, root):
        root.configure(bg=cls.BG)
