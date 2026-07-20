class Theme:
    """
    Unified Design Rules — White-First approach.
    80% White, 10% Black/Dark, 10% Accent/Semantic.
    All UI constants live here. Never hardcode in components.
    """
    # --- Background Layers ---
    BG = "#FFFFFF"            # App window (Base)
    SURFACE = "#FFFFFF"       # Cards, panels
    SURFACE_MUTED = "#F8FAFC" # Input fields, inactive tabs
    SIDEBAR_BG = "#FFFFFF"    # Left panel sidebar

    # --- Text ---
    FG = "#0F172A"            # Primary text — near-black
    MUTED_FG = "#94A3B8"      # Secondary / placeholder text
    CAPTION_FG = "#64748B"    # Captions / axis labels

    # --- Borders ---
    BORDER = "#E2E8F0"        # Card & input borders (Slate 200)
    BORDER_FOCUS = "#6366F1"  # Indigo 500 (Magic UI accent)

    # --- Primary Action (SEND) ---
    PRIMARY = "#0F172A"       # Black for buttons
    PRIMARY_FG = "#FFFFFF"
    PRIMARY_HOVER = "#1E293B" # Dark slate hover

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
    FONT_BRAND = ("Tahoma", 22, "bold")     # "ONE ARM" branding
    FONT_TITLE = ("Tahoma", 22, "bold")
    FONT_H1 = ("Tahoma", 14, "bold")
    FONT_H2 = ("Tahoma", 12, "bold")
    FONT_BODY = ("Tahoma", 10)
    FONT_BODY_BOLD = ("Tahoma", 10, "bold")
    FONT_SMALL = ("Tahoma", 8)
    FONT_CAPTION = ("Tahoma", 6)
    FONT_LOG = ("Tahoma", 14)
    FONT_LOG_BOLD = ("Tahoma", 14, "bold")

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
