## UI Guidelines and Best Practices

This document summarizes the UI decisions and patterns used in the Next.js frontend (`frontend-next/`) with Mantine UI components.

---

## Technology Stack

- **Framework**: Next.js 14 (App Router)
- **UI Library**: Mantine v7
- **Icons**: Tabler Icons
- **Styling**: Mantine theme + CSS variables

---

## Branding and Theme

### FON Advisors Brand Colors

The theme is defined in `frontend-next/theme/theme.ts`:

| Color | Hex | Usage |
|-------|-----|-------|
| **FON Blue** | `#1D5C96` | Primary brand color, navbar background, primary buttons |
| **Dark Grey** | `#2B2B2B` | Text color, card headers |

### Color Palettes

Both colors have full 10-shade palettes for flexibility:

**fonBlue palette:**
- `fonBlue.0` (#ecf4fc) - Light backgrounds
- `fonBlue.1` (#dceaf8) - Hover backgrounds, subtitle text on blue
- `fonBlue.6` (#1D5C96) - **Main brand color** (navbar, primary buttons)
- `fonBlue.7` (#164775) - Button hover states

**charcoal palette:**
- `charcoal.2` (#cdcdcd) - Borders, dividers
- `charcoal.5` (#7d7d7d) - Muted/secondary text
- `charcoal.6` (#626262) - **Card headers**, active nav buttons
- `charcoal.8` (#2B2B2B) - Primary text, headings

### Theme Configuration

```typescript
// theme/theme.ts
export const theme = createTheme({
  primaryColor: 'fonBlue',
  autoContrast: true,        // Automatically picks white/black text
  luminanceThreshold: 0.3,   // Threshold for contrast calculation
  // ...
});
```

---

## Navigation Bar

Located in `frontend-next/components/Navigation.tsx`.

### Styling
- **Background**: FON Blue (`fonBlue.5` / #3332FF)
- **Border**: Slightly darker blue (`fonBlue.6`)
- **Height**: 64px
- **Position**: Sticky top

### Logo
- **File**: `public/FON_Logo.png`
- **Dimensions**: 160×40px (wide format to show full logo)
- **Style**: `objectFit: 'contain'` to preserve aspect ratio
- **Subtitle**: "Proposal Writer" in light blue (`fonBlue.1`)

### Navigation Links
- **Default state**: White text on transparent background
- **Active state**: White text on charcoal background (`charcoal.6` / #626262)
- **Hover state**: Charcoal background with white text

### Mobile
- White burger menu icon
- Drawer with logo and navigation links (charcoal text on white background)

---

## Card Components

Cards use Mantine's `Card` component with custom header sections.

### Card Headers

All card headers use consistent styling:

```tsx
<Card.Section withBorder inheritPadding py="sm" bg="charcoal.6">
  <Group gap="xs">
    <IconName size={18} color="white" />
    <Text fw={600} size="sm" c="white">
      Header Title
    </Text>
  </Group>
</Card.Section>
```

- **Background**: Charcoal (`charcoal.6` / #646564)
- **Text**: White, semi-bold (600)
- **Icons**: White, 18px
- **Padding**: Inherited from card + vertical sm

### Card Body
- White background
- Charcoal border (`charcoal.2`)
- Medium shadow
- Medium border radius

### Cards in Use
| Component | Header Title |
|-----------|-------------|
| `JobForm.tsx` | "Submit New Job", "Documents" |
| `ProcessingCard.tsx` | "Processing" |
| `JobStatus.tsx` | "Job Status" |

---

## Buttons

### Primary Buttons
- **Color**: FON Blue (`fonBlue`)
- **Text**: White (auto-contrast)
- **Hover**: Slight lift + blue shadow

```tsx
<Button color="fonBlue" size="md">
  Primary Action
</Button>
```

### Light Variant
- **Background**: Light shade of the color
- **Text**: Color shade

```tsx
<Button color="fonBlue" variant="light">
  Secondary Action
</Button>
```

### Subtle Variant
Used for tertiary actions like "New Job" reset.

---

## Typography

### Font Stack
```css
font-family: var(--font-inter), -apple-system, BlinkMacSystemFont, 
             Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif;
```

### Headings
- **Color**: Charcoal (`charcoal.7`)
- **Weight**: 600 (semi-bold)
- **Sizes**: h1: 2rem, h2: 1.5rem, h3: 1.25rem

### Body Text
- **Primary**: Charcoal (`charcoal.7`)
- **Muted**: Mid-gray (`charcoal.5`)
- **Subtle**: Light gray (`charcoal.4`)

---

## Status Indicators

Defined in `frontend-next/app/globals.css`:

| Status | Border Color | Background |
|--------|-------------|------------|
| Queued | FON Blue | Light blue (#F0F0FF) |
| Running | Orange (#f59e0b) | Light orange (#fffbeb) |
| Completed | Teal (#10b981) | Light teal (#ecfdf5) |
| Failed | Red (#ef4444) | Light red (#fef2f2) |

---

## Layout

### Page Structure
- **Container**: `size="xl"` with `py="xl"` padding
- **Grid**: 7/5 column split (form left, status right) on desktop
- **Mobile**: Full-width stacked columns

### Background
- Light gray (`#F7F7F7`) with subtle dot pattern
- Dot color: `#E8E8E8`, 24px spacing

---

## CSS Variables

Global CSS variables in `frontend-next/app/globals.css`:

```css
:root {
  --fon-blue: #1D5C96;
  --fon-blue-light: #629ddd;
  --fon-blue-lighter: #ecf4fc;
  --fon-blue-dark: #164775;
  --fon-charcoal: #2B2B2B;
  --fon-charcoal-light: #464646;
  --fon-charcoal-medium: #626262;
  --fon-charcoal-lighter: #7d7d7d;
  
  --bg-primary: #F7F7F7;
  --bg-dots: #E8E8E8;
  --border-subtle: #D1D1D1;
  --text-primary: #323332;
  --text-muted: #8C8C8C;
}
```

---

## Extending the UI

### Adding a New Card

```tsx
import { Card, Text, Group } from '@mantine/core';
import { IconName } from '@tabler/icons-react';

<Card padding="lg">
  <Card.Section withBorder inheritPadding py="sm" bg="charcoal.6">
    <Group gap="xs">
      <IconName size={18} color="white" />
      <Text fw={600} size="sm" c="white">
        New Card Title
      </Text>
    </Group>
  </Card.Section>

  <Box mt="md">
    {/* Card content */}
  </Box>
</Card>
```

### Adding Navigation Links

Edit `navLinks` array in `Navigation.tsx`:

```tsx
const navLinks = [
  { href: '/submit', label: 'Submit Jobs', icon: IconFileUpload },
  { href: '/jobs', label: 'Previous Jobs', icon: IconHistory },
  { href: '/new-page', label: 'New Page', icon: IconNewIcon },
];
```

---

## File Reference

| File | Purpose |
|------|---------|
| `theme/theme.ts` | Mantine theme configuration |
| `app/globals.css` | Global styles, CSS variables |
| `components/Navigation.tsx` | Top navigation bar |
| `components/JobForm.tsx` | Job submission form cards |
| `components/ProcessingCard.tsx` | Submit button card |
| `components/JobStatus.tsx` | Job progress card |
| `public/FON_Logo.png` | Company logo (wide format) |

---

## Design Principles

1. **Brand Consistency**: FON Blue for primary actions and navigation; charcoal for structure and headers
2. **High Contrast**: White text on colored backgrounds; charcoal text on light backgrounds
3. **Visual Hierarchy**: Card headers create clear sections; subtle shadows add depth
4. **Responsive**: Mobile-first with drawer navigation and stacked layouts
5. **Accessible**: Auto-contrast ensures readable text; focus rings for keyboard navigation
