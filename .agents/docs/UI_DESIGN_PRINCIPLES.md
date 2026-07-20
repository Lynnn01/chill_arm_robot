# UI/UX Design Principles

This document summarizes the core UI/UX design principles for **CAT CAN'T STOCKS**, drawing from **Magic UI**, **Awesome Design Systems**, and **Anthropics Frontend Design** guidelines.

## 1. Magic UI Principles
Magic UI focuses on highly polished, interactive, and visually stunning interfaces for modern applications.

*   **Minimalism & Cleanliness**: Avoid clutter. Use generous whitespace (negative space) to let elements breathe. The interface should feel weightless.
*   **High Contrast Typography**: Use stark contrasts for text hierarchy. Primary text should be bold and dark, while secondary/metadata text should be muted (e.g., slate grays) but still legible.
*   **Subtle Interactions**: Buttons and interactive elements should have smooth, subtle hover states (e.g., slightly altering the background shade or border color) rather than jarring color changes.
*   **Card-Based Grouping**: Group related data into distinct "cards" using very thin, subtle borders (e.g., `border border-foreground/10`) and no heavy drop shadows unless highlighting a primary floating element.
*   **Micro-animations**: The *feeling* of responsiveness is key. The UI should react instantly to clicks and inputs.

## 2. Awesome Design Systems Best Practices
A design system is a collection of reusable components, guided by clear standards, that can be assembled together to build any number of applications.

*   **Consistency is Key**: Reusable components must look and behave exactly the same way everywhere.
*   **Single Source of Truth**: All colors, fonts, and spacing variables must be defined in CSS Variables in `globals.css`. Never hardcode hex colors or font sizes directly in component files.
*   **Accessibility (A11y)**: Maintain high contrast ratios between background and foreground colors.
*   **Scalable Architecture**: Keep UI components isolated. One component, one responsibility.

## 3. Application to CAT CAN'T STOCKS
*   **Color Palette**: Monochrome — dark gray background (`oklch(0.18)`) + off-white text. **Only** Red/Green allowed as accent colors for P/L data.
*   **Layout**: 4px/8px grid system with consistent padding. Max width `max-w-6xl mx-auto`.
*   **Feedback**: Always provide Loading / Error / Empty states. Never leave the user staring at a blank area.

---

## 4. Anthropics Frontend Design Philosophy (Anti-Generic)
Source: [anthropics/skills — frontend-design](https://www.skills.sh/anthropics/skills/frontend-design)

*   **No Generic AI Aesthetics**: Avoid overused fonts, templated color schemes, and predictable layouts that look AI-generated.
*   **Hero is a Thesis**: Open every page with the most characteristic thing — for this portfolio app, that's **the most impactful number** (total P/L, portfolio value).
*   **Structure Encodes Information**: Use numbered labels (01, 02) only when content is actually a sequence. Dividers only when separating genuinely different content groups.
*   **Deliberate Motion**: One purposeful animation beats many scattered micro-animations. When in doubt, don't animate.
*   **Minimal = Precision**: For a minimalist vision like this project, elegance comes from perfect spacing, type hierarchy, and detail — not from adding more decoration.

> 📄 Full guidelines: [design_rules/09_anthropics_design_philosophy.md](design_rules/09_anthropics_design_philosophy.md).
