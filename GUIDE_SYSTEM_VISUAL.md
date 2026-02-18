# AEGIS Guide System - Visual Reference

## Component Layout & Appearance

### 1. Floating Help Beacon

```
┌─────────────────────────────────────┐
│                                     │
│  AEGIS Application Content          │
│                                     │
│                                     │
│                                     │
│                      ┌─────────┐    │
│                      │  ? (48) │◄── Floating beacon
│                      │ pulsing │    (48px circle)
│                      └─────────┘    │
│                      32px from      │
│                      right & bottom │
└─────────────────────────────────────┘
```

**States:**
- Default: AEGIS Blue (#33B8FF) with glow shadow
- Hover: 10% larger, stronger glow
- Active: 95% scaled (pressed effect)
- Idle: Subtle vertical bounce animation
- Always: Pulsing ring expands every 2 seconds

### 2. Contextual Help Panel (Open)

```
┌──────────────────────────────────────────────┐
│ AEGIS Application                           │
├──────────────────────────────────────────────┤
│                          ┌─ Panel (380px) ──┐
│                          │ Dashboard      ✕  │
│                          ├────────────────────┤
│                          │ Your mission      │
│                          │ control center.   │
│                          │ See document      │
│                          │ quality at a      │
│                          │ glance...         │
│                          │                  │
│                          │ Key Actions      │
│                          │ □ Click any tile │
│                          │ □ View metrics   │
│                          │ □ Upload doc     │
│                          │                  │
│                          │ ▼ Pro Tips       │
│                          │                  │
│                          │ [Watch Demo]    │
│                          │ [Take Tour]     │
│                          └────────────────────┘
│                                   ▲
│ Slides in from right, 300ms      │
└──────────────────────────────────────────────┘
```

**Panel Structure:**
```
┌─────────────────────────────┐
│ Title ────────────────── ✕  │  Header (20px padding)
├─────────────────────────────┤
│ Description paragraph...    │  Content (20px padding)
│                             │
│ KEY ACTIONS                 │
│ □ Action 1                  │
│ □ Action 2                  │
│                             │
│ ▼ PRO TIPS (collapsed)      │
├─────────────────────────────┤
│ [Watch Demo] [Take Tour]    │  Footer (20px padding)
└─────────────────────────────┘
```

### 3. Spotlight Overlay & Tour Tooltip

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│ Dark overlay
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│ (70% opacity)
│ ░░░░░░░░░                       ░░░░░░░░░░░░░░░░░░│
│ ░░░░░░░░░┌───────────────────┐░░░░░░░░░░░░░░░░░░│
│ ░░░░░░░░░│ TARGET ELEMENT    │░░░░░░░░░░░░░░░░░░│
│ ░░░░░░░░░│ (8px padding)     │░░░░░░░░░░░░░░░░░░│
│ ░░░░░░░░░└───────────────────┘░░░░░░░░░░░░░░░░░░│
│ ░░░░░░░░░                       ░░░░░░░░░░░░░░░░░░│
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│ ◄─ SVG mask cutout
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
└──────────────────────────────────────────────────────┘
     ▲
     └─ Tooltip (positioned nearby)

         ┌──────────────────────────┐
         │ Step 1 of 8           ✕  │  Header
         ├──────────────────────────┤
         │ Start Here               │  Title
         │ Drag and drop your       │  Description
         │ document here...         │
         ├──────────────────────────┤
         │ [Skip]  •••••  [Next →]  │  Controls
         └──────────────────────────┘
```

**Spotlight Features:**
- Full-screen dark overlay (70% opacity black)
- SVG mask with smooth rectangular cutout around target
- Padding around target element (8px)
- Tooltip positions smartly (top/bottom/left/right)
- Stays within viewport with 20px padding
- Smooth 400ms transitions between steps

### 4. Getting Started Card (Landing Page)

```
┌─────────────────────────────────────────────────┐
│ 🧭 New to AEGIS?                          →    │  Animated gradient border
│    Take a 2-minute guided tour                 │  Glowing shadow
│                                                 │  Icon floats up/down
└─────────────────────────────────────────────────┘
```

**Card Details:**
```
Card Structure:
┌────────────────────────────────────────┐
│ 🧭 │ New to AEGIS?              →    │  48px height
│    │ Take a 2-minute tour             │  24px padding
├────────────────────────────────────────┤
│ Icon + Text + Arrow                    │
└────────────────────────────────────────┘

Animations:
- Icon: Float up/down (3s loop)
- Arrow: Pulse right (2s loop)
- Border: Hue rotate (8s loop)
- Glow: Pulse shadow (4s loop)
- Hover: Lift 4px up

Click behavior:
- Hides dashboard
- Starts full guided tour
- First step highlights hero upload zone
```

### 5. Tour Tooltip Details

```
┌───────────────────────────────┐
│ Step 2 of 8              ✕    │  20px padding
├───────────────────────────────┤
│ Graph View                    │  16px title
│ Visualize role               │  14px description
│ relationships and            │  1.6 line-height
│ hierarchies as an            │
│ interactive network.          │
├───────────────────────────────┤
│ [Skip Tour]                   │  Skip button spans
│           •••••               │  Progress dots (6-12px each)
│ [← Back]  [Next →]           │  Navigation buttons
└───────────────────────────────┘

Mobile layout:
┌──────────────────────────┐
│ Step 2 of 8         ✕   │
├──────────────────────────┤
│ Graph View               │
│ Visualize role           │
│ relationships...         │
├──────────────────────────┤
│ [Skip Tour]              │  Full width
│ •••••                    │
│ [← Back]  [Next →]       │  Stacked
└──────────────────────────┘
```

### 6. Modal Help Button

```
┌────────────────────────────────────┐
│ Roles Studio              ? ✕       │
├────────────────────────────────────┤
│ [Overview] [Graph] [RACI]...       │
│                                    │
│ Content area...                    │
└────────────────────────────────────┘
                    ▲
                    └─ 24px circle button
                       SVG icon inside
                       Positioned before close button
```

## Color Reference

### Light Mode
```
Beacon:        AEGIS Blue (#33B8FF) with glow
Panel bg:      White (99% opacity) with blur
Panel border:  Black @ 8% opacity
Text primary:  Dark gray (#111827)
Text secondary: Medium gray (#4b5563)
Action icons:  AEGIS Blue (#33B8FF)
Spotlight:     Black @ 70% opacity
Tooltip bg:    White (98% opacity) with blur
```

### Dark Mode
```
Beacon:        AEGIS Blue (#33B8FF) with glow (same)
Panel bg:      Dark gray (95% opacity) with blur
Panel border:  Light gray @ 10% opacity
Text primary:  Light gray (#e5e7eb)
Text secondary: Medium gray (#9ca3af)
Action icons:  AEGIS Blue (#33B8FF)
Spotlight:     Black @ 70% opacity (same)
Tooltip bg:    Dark gray (98% opacity) with blur
```

## Animation Timing

```
Beacon pulse:        2000ms loop
Beacon bounce:       2000ms loop (offset 500ms)
Panel slide:         300ms in/out
Spotlight move:      400ms
Tooltip pop:         300ms
Progress dot active: 200ms
Icon float:          3000ms
Arrow pulse:         2000ms

Easing functions:
- Panel/beacon: cubic-bezier(0.4, 0, 0.2, 1) [material decelerate]
- Spotlight: cubic-bezier(0.4, 0, 0.2, 1) [material decelerate]
- Tooltip pop: cubic-bezier(0.34, 1.56, 0.64, 1) [overshoot bounce]
- Loops: cubic-bezier(0.4, 0, 0.6, 1) [ease-in-out]
```

## Responsive Breakpoints

```
Desktop (>768px):
- Beacon: 48px diameter, 32px padding
- Panel: 380px width
- Tooltip: max 360px width
- All animations at full speed

Tablet (480px-768px):
- Beacon: 48px diameter, 24px padding
- Panel: 100% width (on right side)
- Tooltip: adjusts to fit
- Animations slightly faster

Mobile (<480px):
- Beacon: 40px diameter, 16px padding
- Panel: 100% full-screen width
- Tooltip: 100vw - 24px margin
- Button stack vertically
- Font sizes reduce slightly
```

## Z-Index Layering

```
2500 ┌────────────────────────┐ Toast notifications
2400 └────────────────────────┘
2300
2200
2100
2000 ┌────────────────────────┐ Loading overlays
1900 └────────────────────────┘
1800
1700
1600
1500 ┌────────────────────────┐ Guide beacon
1400 │ ┌────────────────────┐ │ Spotlight overlay
1450 │ │ Guide panel        │ │ Guide panel
1400 │ │                    │ │
1400 │ └────────────────────┘ │
1400 └────────────────────────┘
1300
1200
1100 ┌────────────────────────┐ Modal alerts
1000 │ ┌────────────────────┐ │ Modal dialogs
     │ │ Modal content      │ │
     │ └────────────────────┘ │
     └────────────────────────┘
```

## Size Reference

```
Beacon:
- Diameter: 48px
- Icon: 24px
- Bottom offset: 32px
- Right offset: 32px
- Box shadow: 0 4px 16px rgba(...)

Panel:
- Width: 380px
- Height: 100vh
- Header padding: 20px
- Content padding: 20px
- Footer padding: 20px
- Border: 1px left

Tooltip:
- Max width: 360px
- Padding: 20px
- Border radius: 12px
- Box shadow: 0 20px 48px rgba(...)

Help button (modal):
- Size: 24px square
- Icon: 18px
- Padding: 4px
- Border radius: 4px

Getting Started card:
- Min height: 48px
- Padding: 24px
- Border radius: 12px
- Icon size: 32px
```

## Viewport Behavior

```
┌─────────────────────────────────────────┐
│ Normal viewport (1024x768)              │
│                                         │
│ Tooltip positions relative to target:   │
│ - Centered if enough space              │
│ - Adjusted if near edges                │
│ - Always ≥20px from viewport edges      │
│                                     ? ◄─┤ Beacon
└─────────────────────────────────────────┘

On small screens:
┌─────────────────────────────┐
│ Narrow (375px)              │
│                             │
│ Tooltip:                    │
│ - Centers horizontally      │
│ - Adjusts vertical position │
│ - Respects safe area       │
│ - Never overlaps beacon    │
│ ? ◄ Beacon (reduced size)  │
└─────────────────────────────┘
```

## Interaction Flows

### Opening Help Panel
```
User clicks "?" beacon
    ↓
Panel slides in from right (300ms)
    ↓
Content populated for current section
    ↓
Lucide icons rendered
    ↓
Panel ready for interaction
```

### Starting a Tour
```
User clicks "Watch Demo" or "Take Tour"
    ↓
Panel slides out (300ms)
    ↓
Spotlight overlay appears
    ↓
First tour step renders with smooth animations
    ↓
Element scrolls into view if needed
    ↓
Tooltip appears and positions itself
    ↓
User can navigate with buttons or skip
```

### Dark Mode Toggle
```
User clicks theme button
    ↓
document.body.classList toggles 'dark-mode'
    ↓
CSS automatically adjusts colors via selectors
    ↓
Guide system components update instantly
    ↓
No JavaScript needed (pure CSS solution)
```

## Accessibility Features

```
Keyboard Navigation:
┌─────────────────────────────┐
│ Tab  → Focus beacon         │
│ Enter→ Open panel           │
│ Tab  → Focus button         │
│ Enter→ Start tour           │
│ Esc  → Close panel/tour     │
└─────────────────────────────┘

Focus Indicators:
┌─────────────────────────────┐
│ All buttons:                │
│ ┌────────────────────────┐ │
│ │ Button text (blue)    │ │  2px outline
│ └────────────────────────┘ │  Offset 2px
│                             │
└─────────────────────────────┘

Screen Reader Support:
- "Open help and guided tour" (beacon)
- "Close help panel" (close button)
- "Step 2 of 8" (counter announced)
- "Take Tour" (button label)
- "Open help for this section" (help button)
```

This visual reference shows the exact appearance, layout, and behavior of all guide system components. Refer back to these diagrams when implementing or customizing the guide system.
