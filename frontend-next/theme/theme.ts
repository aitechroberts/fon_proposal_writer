'use client';

import { createTheme, MantineColorsTuple } from '@mantine/core';

// FON Advisors brand colors
// Primary Blue: #3332FF
// Charcoal: #323332

// Blue (#3332FF) - Primary brand color at shade 5
const fonBlue: MantineColorsTuple = [
  '#F0F0FF',  // 0 - Lightest (light backgrounds, subtle highlights)
  '#D4D4FF',  // 1 - Very light (hover backgrounds)
  '#B8B8FF',  // 2 - Light (selected states, badges)
  '#9C9CFF',  // 3 - Medium-light
  '#6766FF',  // 4 - Medium (secondary buttons)
  '#3332FF',  // 5 - MAIN BRAND COLOR (primary buttons, links)
  '#2928CC',  // 6 - Slightly darker (button hover)
  '#1F1E99',  // 7 - Dark (button active/pressed)
  '#151466',  // 8 - Very dark (dark mode accents)
  '#0A0A33',  // 9 - Darkest (dark mode text)
];

// Charcoal (#323332) - Neutral/text color at shade 7
const charcoal: MantineColorsTuple = [
  '#F7F7F7',  // 0 - Almost white (light mode backgrounds)
  '#E8E8E8',  // 1 - Very light gray (card backgrounds)
  '#D1D1D1',  // 2 - Light gray (borders, dividers)
  '#BABABA',  // 3 - Medium-light gray
  '#A3A3A3',  // 4 - Medium gray (muted text)
  '#8C8C8C',  // 5 - Mid gray (secondary text)
  '#646564',  // 6 - Dark gray
  '#323332',  // 7 - MAIN CHARCOAL (primary text, headings)
  '#232423',  // 8 - Very dark (dark mode backgrounds)
  '#141514',  // 9 - Almost black (darkest elements)
];

export const theme = createTheme({
  // Primary color (used for buttons, links, focused inputs)
  primaryColor: 'fonBlue',
  
  // Default text color
  black: '#323332',
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
    xs: '0 1px 2px 0 rgba(50, 51, 50, 0.05)',
    sm: '0 1px 3px 0 rgba(50, 51, 50, 0.1), 0 1px 2px 0 rgba(50, 51, 50, 0.06)',
    md: '0 4px 6px -1px rgba(50, 51, 50, 0.1), 0 2px 4px -1px rgba(50, 51, 50, 0.06)',
    lg: '0 10px 15px -3px rgba(50, 51, 50, 0.1), 0 4px 6px -2px rgba(50, 51, 50, 0.05)',
    xl: '0 20px 25px -5px rgba(50, 51, 50, 0.1), 0 10px 10px -5px rgba(50, 51, 50, 0.04)',
  },
  
  defaultRadius: 'md',
  
  // Semantic colors for other states
  other: {
    // Light backgrounds
    lightBackground: '#F7F7F7',
    cardBackground: '#FFFFFF',
    
    // Dark backgrounds  
    darkBackground: '#232423',
    darkCardBackground: '#323332',
    
    // Accents
    lightAccent: '#F0F0FF',
    darkAccent: '#151466',
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
