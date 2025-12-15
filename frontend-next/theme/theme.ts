'use client';

import { createTheme, MantineColorsTuple } from '@mantine/core';

// Parker Tide brand colors
const navy: MantineColorsTuple = [
  '#e6f0f7',
  '#c4d9e8',
  '#9fc1d9',
  '#77a8c9',
  '#5490b9',
  '#3578a8',
  '#04395E', // Primary brand navy
  '#0A2E4D', // Darker variant
  '#082540',
  '#051c33',
];

const cyan: MantineColorsTuple = [
  '#E6F6FD',
  '#b8e6f7',
  '#8ad6f1',
  '#5cc6eb',
  '#2eb6e5',
  '#00A3E0', // Primary brand cyan
  '#0092ca',
  '#0080b3',
  '#006e9c',
  '#005c85',
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
    fontWeight: '700',
  },
  radius: {
    xs: '4px',
    sm: '6px',
    md: '8px',
    lg: '12px',
    xl: '16px',
  },
  shadows: {
    xs: '0 1px 3px rgba(4, 57, 94, 0.06)',
    sm: '0 2px 6px rgba(4, 57, 94, 0.08)',
    md: '0 4px 12px rgba(4, 57, 94, 0.10)',
    lg: '0 8px 24px rgba(4, 57, 94, 0.12)',
    xl: '0 16px 48px rgba(4, 57, 94, 0.15)',
  },
  defaultRadius: 'md',
  components: {
    Button: {
      defaultProps: {
        radius: 'md',
      },
      styles: {
        root: {
          fontWeight: 600,
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            transform: 'translateY(-1px)',
          },
        },
      },
    },
    Card: {
      defaultProps: {
        radius: 'lg',
        shadow: 'sm',
      },
    },
    Paper: {
      defaultProps: {
        radius: 'lg',
        shadow: 'sm',
      },
    },
    TextInput: {
      defaultProps: {
        radius: 'md',
      },
    },
    Select: {
      defaultProps: {
        radius: 'md',
      },
    },
    Progress: {
      defaultProps: {
        radius: 'xl',
        size: 'lg',
      },
    },
  },
});

