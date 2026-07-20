---
name: Aurelian Guide
colors:
  surface: '#fbf9f9'
  surface-dim: '#dbdad9'
  surface-bright: '#fbf9f9'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f5f3f3'
  surface-container: '#efeded'
  surface-container-high: '#e9e8e7'
  surface-container-highest: '#e4e2e2'
  on-surface: '#1b1c1c'
  on-surface-variant: '#46464a'
  inverse-surface: '#303031'
  inverse-on-surface: '#f2f0f0'
  outline: '#77767b'
  outline-variant: '#c7c6ca'
  surface-tint: '#5f5e60'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#1b1b1d'
  on-primary-container: '#858386'
  inverse-primary: '#c8c6c8'
  secondary: '#9a4605'
  on-secondary: '#ffffff'
  secondary-container: '#fe9251'
  on-secondary-container: '#6e2f00'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#1a1c1b'
  on-tertiary-container: '#838483'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e4e2e4'
  primary-fixed-dim: '#c8c6c8'
  on-primary-fixed: '#1b1b1d'
  on-primary-fixed-variant: '#474649'
  secondary-fixed: '#ffdbca'
  secondary-fixed-dim: '#ffb68e'
  on-secondary-fixed: '#331200'
  on-secondary-fixed-variant: '#763300'
  tertiary-fixed: '#e2e3e1'
  tertiary-fixed-dim: '#c6c7c5'
  on-tertiary-fixed: '#1a1c1b'
  on-tertiary-fixed-variant: '#454746'
  background: '#fbf9f9'
  on-background: '#1b1c1c'
  surface-variant: '#e4e2e2'
typography:
  display-lg:
    fontFamily: Source Han Serif
    fontSize: 48px
    fontWeight: '500'
    lineHeight: 60px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Source Han Serif
    fontSize: 32px
    fontWeight: '500'
    lineHeight: 40px
  headline-md:
    fontFamily: Source Han Serif
    fontSize: 24px
    fontWeight: '500'
    lineHeight: 32px
  body-lg:
    fontFamily: Source Han Sans
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Source Han Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-xs:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
  3xl: 64px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 64px
---

## Brand & Style

This design system is built on a philosophy of **restrained elegance** and **cultural resonance**. Designed for an AI Digital Human Tour Guide, the visual language prioritizes legibility and breathability, ensuring the technology recedes to highlight the heritage and stories being told.

The style is **Elevated Minimalism**: a blend of high-end editorial aesthetics and modern functionalism. It avoids the typical "neon-blue" AI tropes, opting instead for a warm, paper-like tactile feel. The interface utilizes high-quality whitespace, crisp 1px borders, and a sophisticated typographic hierarchy to evoke the feeling of a premium museum catalog or a boutique travel journal. 

Key attributes include:
- **Sophisticated & Intellectual:** Using serif headings to bridge the gap between history and the future.
- **Breathable:** Heavy use of whitespace to reduce cognitive load during information-heavy tours.
- **Trustworthy:** A grounded, neutral palette that feels institutional yet welcoming.

## Colors

The palette is anchored in a "Warm Gallery" aesthetic. The primary background uses a soft, off-white to reduce eye strain, while interactive elements and surfaces use pure white to create subtle organic depth without needing shadows.

- **Background (#FAFAF8):** The primary canvas, providing a warm, non-clinical feel.
- **Surface (#FFFFFF):** Used for cards, modals, and elevated containers to create a "layered paper" effect.
- **Primary Text (#1A1A1C):** A deep, near-black for maximum readability and authority.
- **Secondary/Tertiary Text (#6F6F6F / #A0A0A0):** Used for metadata, captions, and de-emphasized UI labels.
- **Accent (#E07B3C):** A warm orange used exclusively for call-to-action buttons, active AI states, and critical navigation highlights.
- **Borders (#E8E8E6):** Used for structural definition in place of shadows.

## Typography

The typography strategy employs a dual-language system that balances traditional editorial style with modern UI utility.

- **Headings (Source Han Serif):** Used for titles, section headers, and prominent narrative text. The serif adds a "cultural" weight and authority, making the AI's dialogue feel like a curated lecture.
- **Body & UI (Source Han Sans):** Used for all functional UI elements, descriptions, and lists. It provides high legibility and a clean, modern contrast to the serif headings.
- **Numbers & English (Inter):** Integrated into the Sans stack for a precise, systematic look in technical data, timestamps, and labels.

**System Note:** Maintain a 1.5x line height for body copy to ensure the "breathable" quality of the design is preserved across all text blocks.

## Layout & Spacing

The layout follows a **Fluid 12-Column Grid** on desktop and a **4-Column Grid** on mobile. The core of the system is a 4px base unit, used to maintain a strict vertical rhythm.

- **Logic:** Padding and margins should always be multiples of 8px (sm, md, lg) for primary structural elements, using 4px (xs) only for tight internal component spacing (e.g., icon-to-text).
- **Margins:** Generous outer margins (64px on desktop) are mandatory to maintain the "high-end" minimalist feel.
- **Reflow:** On mobile, components stack vertically with a minimum 16px gutter. Content cards should span the full width of the safe area.

## Elevation & Depth

This design system intentionally rejects shadows in favor of **Low-Contrast Outlines** and **Tonal Layering**.

- **Flat Hierarchy:** Depth is communicated through color contrast (White surfaces on Warm White backgrounds) rather than Z-axis simulation.
- **Borders:** Every card and interactive container must use a 1px solid border (#E8E8E6). This provides structural clarity while maintaining a light, airy aesthetic.
- **Scrims:** For modals or overlays, use a semi-transparent blur (Backdrop Filter: 8px) with a 20% opacity tint of the Primary Text color to focus attention without introducing heavy drop-shadows.

## Shapes

The shape language is controlled and systematic. It avoids hyper-roundness to maintain a professional, architectural feel, while steering clear of sharp corners to remain approachable.

- **Buttons:** 8px radius. This provides a clear interactive "pill" feel without being fully circular.
- **Cards/Containers:** 12px radius. This defines the primary content areas with a soft but structured corner.
- **Modals/Overlays:** 16px radius. Larger radii are used for the highest level of the hierarchy to signify a "takeover" state.

## Components

### Buttons
- **Primary:** Warm Orange (#E07B3C) background with Pure White text. 8px radius. No shadow.
- **Secondary:** Transparent background with 1px border (#E8E8E6). Text in Near Black (#1A1A1C).
- **Ghost:** No background or border. Used for low-priority actions (e.g., "Dismiss", "Back").

### Cards
- **Base:** Pure White (#FFFFFF) background with a 1px border (#E8E8E6). 12px corner radius.
- **Content:** Headline in Serif, Body in Sans. Padding should be at least 24px (lg) to ensure the content doesn't feel cramped.

### Input Fields
- **Default:** 1px border (#E8E8E6) with a subtle off-white background (#FAFAF8) when inactive.
- **Focus:** Border changes to Warm Orange (#E07B3C) with a 1px solid stroke. No glow or outer shadow.

### AI Interaction States
- **Thinking/Active:** Use the Warm Orange (#E07B3C) as a subtle pulse or a 2px top-border on the chat container to indicate the AI is processing information.
- **Transcript:** Use Source Han Sans Regular for the user and Source Han Serif Medium for the AI responses to visually distinguish the "Voice of Authority."

### Chips/Tags
- **Style:** 1px border, 12px text (Inter), 4px radius. Used for "Historical Era," "Architectural Style," or "Duration."