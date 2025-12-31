'use client';

import { createTheme, MantineColorsTuple } from '@mantine/core';

// FON Advisors brand colors (sampled from logo)
// Primary Blue: #1D5C96 (at index 6)
// Dark Grey: #2B2B2B (at index 8)

// Blue (#1D5C96) - Primary brand color at shade 6
const fonBlue: MantineColorsTuple = [
  '#ecf4fc',  // 0 - Very light tint (backgrounds)
  '#dceaf8',  // 1 - Very light (hover backgrounds)
  '#bdd8f2',  // 2 - Light (selected states, badges)
  '#9cc4eb',  // 3 - Medium-light
  '#7eb1e5',  // 4 - Medium
  '#629ddd',  // 5 - Medium-dark
  '#1D5C96',  // 6 - BRAND BASE COLOR (primary buttons, links, navbar)
  '#164775',  // 7 - Darker shade (button hover)
  '#0f3254',  // 8 - Dark (button active/pressed)
  '#081e33',  // 9 - Darkest (dark mode text)
];

// Dark Grey (#2B2B2B) - Neutral/text color at shade 8
const charcoal: MantineColorsTuple = [
  '#f3f3f3',  // 0 - Light grey background
  '#e7e7e7',  // 1 - Very light gray (card backgrounds)
  '#cdcdcd',  // 2 - Light gray (borders, dividers)
  '#b2b2b2',  // 3 - Medium-light gray
  '#989898',  // 4 - Medium gray (muted text)
  '#7d7d7d',  // 5 - Mid gray (secondary text)
  '#626262',  // 6 - Dark gray (nav buttons)
  '#464646',  // 7 - Darker gray
  '#2B2B2B',  // 8 - BRAND BASE COLOR (primary text, headings)
  '#1a1a1a',  // 9 - Almost black (darkest elements)
];

export const theme = createTheme({
  // Primary color (used for buttons, links, focused inputs)
  primaryColor: 'fonBlue',
  
  // Default text color
  black: '#2B2B2B',
  white: '#FFFFFF',
  
  colors: {
    fonBlue,
    charcoal,
  },
  
  // Ensure good contrast
  autoContrast: true,
  luminanceThreshold: 0.3,
  
  fontFamily: 'var(--font-inter), -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif',
  fontFamilyMonospace: 'Monaco, Courier, monospace',
  
  headings: {
    fontFamily: 'var(--font-inter), -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif',
    fontWeight: '600',
    sizes: {
      h1: { fontSize: '2rem', lineHeight: '1.2' },
      h2: { fontSize: '1.5rem', lineHeight: '1.3' },
      h3: { fontSize: '1.25rem', lineHeight: '1.4' },
    },
  },
  
  radius: {
    xs: '4px',
    sm: '6px',
    md: '8px',
    lg: '10px',
    xl: '12px',
  },
  
  // Custom shadows using charcoal for a warmer feel
  shadows: {
    xs: '0 1px 2px 0 rgba(43, 43, 43, 0.05)',
    sm: '0 1px 3px 0 rgba(43, 43, 43, 0.1), 0 1px 2px 0 rgba(43, 43, 43, 0.06)',
    md: '0 4px 6px -1px rgba(43, 43, 43, 0.1), 0 2px 4px -1px rgba(43, 43, 43, 0.06)',
    lg: '0 10px 15px -3px rgba(43, 43, 43, 0.1), 0 4px 6px -2px rgba(43, 43, 43, 0.05)',
    xl: '0 20px 25px -5px rgba(43, 43, 43, 0.1), 0 10px 10px -5px rgba(43, 43, 43, 0.04)',
  },
  
  defaultRadius: 'md',
  
  // Semantic colors for other states
  other: {
    // Light backgrounds
    lightBackground: '#f3f3f3',
    cardBackground: '#FFFFFF',
    
    // Dark backgrounds  
    darkBackground: '#2B2B2B',
    darkCardBackground: '#464646',
    
    // Accents
    lightAccent: '#ecf4fc',
    darkAccent: '#0f3254',
  },
  
  components: {
    Button: {
      defaultProps: {
        color: 'fonBlue',
        radius: 'md',
      },
      styles: {
        root: {
          fontWeight: 500,
          transition: 'all 0.15s ease',
        },
      },
    },
    
    Card: {
      defaultProps: {
        radius: 'md',
        shadow: 'sm',
        withBorder: true,
      },
      styles: {
        root: {
          backgroundColor: 'white',
          borderColor: 'var(--mantine-color-charcoal-2)',
          transition: 'box-shadow 0.15s ease, transform 0.15s ease',
        },
      },
    },
    
    Paper: {
      defaultProps: {
        radius: 'md',
        shadow: 'xs',
      },
      styles: {
        root: {
          transition: 'box-shadow 0.15s ease',
        },
      },
    },
    
    Title: {
      styles: {
        root: {
          color: 'var(--mantine-color-charcoal-7)',
        },
      },
    },
    
    TextInput: {
      defaultProps: {
        radius: 'md',
        variant: 'filled',
      },
      styles: {
        input: {
          transition: 'border-color 0.15s ease, background-color 0.15s ease',
        },
      },
    },
    
    Select: {
      defaultProps: {
        radius: 'md',
        variant: 'filled',
      },
    },
    
    Textarea: {
      defaultProps: {
        radius: 'md',
        variant: 'filled',
      },
    },
    
    Progress: {
      defaultProps: {
        radius: 'xl',
        size: 'md',
        color: 'fonBlue',
      },
    },
    
    Badge: {
      defaultProps: {
        radius: 'sm',
        variant: 'light',
      },
      styles: {
        root: {
          fontWeight: 500,
          textTransform: 'none',
        },
      },
    },
    
    NavLink: {
      styles: {
        root: {
          borderRadius: 'var(--mantine-radius-md)',
          transition: 'background-color 0.15s ease',
        },
      },
    },
    
    Skeleton: {
      defaultProps: {
        radius: 'md',
      },
    },
    
    ActionIcon: {
      styles: {
        root: {
          transition: 'all 0.15s ease',
        },
      },
    },
    
    Switch: {
      styles: {
        track: {
          transition: 'background-color 0.15s ease',
        },
      },
    },
    
    Pagination: {
      defaultProps: {
        color: 'fonBlue',
      },
    },
    
    Table: {
      styles: {
        th: {
          color: 'var(--mantine-color-charcoal-7)',
          fontWeight: 600,
        },
      },
    },
  },
});
