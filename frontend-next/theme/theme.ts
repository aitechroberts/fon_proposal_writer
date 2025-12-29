'use client';

import { createTheme, MantineColorsTuple } from '@mantine/core';

// Parker Tide brand colors
const navy: MantineColorsTuple = [
  '#f0f5fa',
  '#dae4ed',
  '#b8cfe0',
  '#8eb5d0',
  '#6699bf',
  '#4080ad',
  '#04395E', // Primary brand navy [6]
  '#0A2E4D', // Darker variant [7]
  '#082540',
  '#051c33',
];

// Modernized cyan - slightly desaturated (Tailwind sky-inspired)
const cyan: MantineColorsTuple = [
  '#f0f9ff',
  '#e0f2fe',
  '#bae6fd',
  '#7dd3fc',
  '#38bdf8',
  '#0ea5e9', // Primary accent [5]
  '#0284c7',
  '#0369a1',
  '#075985',
  '#0c4a6e',
];

export const theme = createTheme({
  primaryColor: 'navy',
  colors: {
    navy,
    cyan,
  },
  fontFamily: 'var(--font-inter), -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif',
  headings: {
    fontFamily: 'var(--font-inter), -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif',
    fontWeight: '600',
  },
  radius: {
    xs: '4px',
    sm: '6px',
    md: '8px',
    lg: '10px',
    xl: '12px',
  },
  shadows: {
    xs: '0 1px 2px rgba(0, 0, 0, 0.04)',
    sm: '0 1px 3px rgba(0, 0, 0, 0.06)',
    md: '0 4px 6px rgba(0, 0, 0, 0.07)',
    lg: '0 10px 15px rgba(0, 0, 0, 0.08)',
    xl: '0 20px 25px rgba(0, 0, 0, 0.10)',
  },
  defaultRadius: 'md',
  components: {
    Button: {
      defaultProps: {
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
        shadow: 'xs',
        withBorder: true,
      },
      styles: {
        root: {
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
      },
    },
    Badge: {
      defaultProps: {
        radius: 'sm',
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
  },
});
