# UI/UX Design Principles

This document summarizes the core UI/UX design principles inspired by **Magic UI** and the best practices found in **Awesome Design Systems**, tailored for this project.

## 1. Magic UI Principles
Magic UI focuses on highly polished, interactive, and visually stunning interfaces for modern applications.

*   **Minimalism & Cleanliness**: Avoid clutter. Use generous whitespace (negative space) to let elements breathe. The interface should feel weightless.
*   **High Contrast Typography**: Use stark contrasts for text hierarchy. Primary text should be bold and dark, while secondary/metadata text should be muted (e.g., slate grays) but still legible.
*   **Subtle Interactions**: Buttons and interactive elements should have smooth, subtle hover states (e.g., slightly altering the background shade or border color) rather than jarring color changes.
*   **Card-Based Grouping**: Group related data into distinct "cards" using very thin, subtle borders (e.g., `1px solid #E2E8F0`) and no heavy drop shadows unless highlighting a primary floating element.
*   **Micro-animations**: While difficult in basic desktop GUI frameworks, the *feeling* of responsiveness is key. The UI should react instantly to clicks and inputs.

## 2. Awesome Design Systems Best Practices
A design system is a collection of reusable components, guided by clear standards, that can be assembled together to build any number of applications.

*   **Consistency is Key**: Reusable components must look and behave exactly the same way everywhere. A "Primary Button" in the control panel must have the exact same color, padding, and font as a "Primary Button" in the chat log.
*   **Single Source of Truth**: All colors, fonts, and spacing variables must be defined in a single central location (e.g., `app/theme.py`). Never hardcode hex colors or font sizes directly in component files.
*   **Accessibility (A11y)**: Maintain high contrast ratios between background and foreground colors.
*   **Scalable Architecture**: Keep UI components isolated. The logic for the "Dashboard" should not be tangled with the logic for the "Camera View". 

## 3. Application to ONE ARM GUI
*   **Color Palette**: 80% White background (`#FFFFFF`), 10% Black/Dark Slate for text and primary interactive elements (`#0F172A`), and 10% subtle grays or accent colors (e.g., red for danger).
*   **Layout**: Use grid layouts with consistent padding (e.g., 10px or 20px intervals).
*   **Feedback**: Always provide clear visual feedback in the UI for background processes (e.g., "Robot is moving...").
