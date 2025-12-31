import '@mantine/core/styles.css';
import '@mantine/dropzone/styles.css';
import '@mantine/notifications/styles.css';
import './globals.css';

import { ColorSchemeScript } from '@mantine/core';
import { Inter } from 'next/font/google';
import { Providers } from './providers';
import { Navigation } from '@/components';

const inter = Inter({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '800'],
  variable: '--font-inter',
  display: 'swap',
});

export const metadata = {
  title: 'FON Advisors Proposal Writer',
  description: 'Transform government RFPs into compliance matrices with AI-powered extraction',
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <head>
        <ColorSchemeScript />
      </head>
      <body className={inter.className}>
        <Providers>
          <Navigation />
          {children}
        </Providers>
      </body>
    </html>
  );
}
