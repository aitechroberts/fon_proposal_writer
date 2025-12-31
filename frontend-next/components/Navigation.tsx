'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import {
  Group,
  Box,
  Text,
  UnstyledButton,
  Container,
  Burger,
  Drawer,
  Stack,
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconFileUpload, IconHistory } from '@tabler/icons-react';

const navLinks = [
  { href: '/submit', label: 'Submit Jobs', icon: IconFileUpload },
  { href: '/jobs', label: 'Previous Jobs', icon: IconHistory },
];

export function Navigation() {
  const pathname = usePathname();
  const [opened, { toggle, close }] = useDisclosure(false);

  const NavLink = ({ href, label, icon: Icon, variant = 'dark' }: typeof navLinks[0] & { variant?: 'dark' | 'light' }) => {
    const isActive = pathname === href;
    const isDark = variant === 'dark';
    
    return (
      <Link href={href} style={{ textDecoration: 'none' }}>
        <UnstyledButton
          onClick={close}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 16px',
            borderRadius: '8px',
            backgroundColor: isActive ? 'var(--mantine-color-charcoal-6)' : 'transparent',
            color: isActive ? 'white' : (isDark ? 'white' : 'var(--mantine-color-charcoal-7)'),
            transition: 'all 0.15s ease',
            fontWeight: 500,
          }}
          className={isActive ? '' : (isDark ? 'nav-link-hover-dark' : 'nav-link-hover')}
        >
          <Icon size={18} stroke={1.5} />
          <span>{label}</span>
        </UnstyledButton>
      </Link>
    );
  };

  return (
    <Box
      component="nav"
      style={{
        backgroundColor: 'var(--mantine-color-fonBlue-6)',
        borderBottom: '1px solid var(--mantine-color-fonBlue-7)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}
    >
      <Container size="xl">
        <Group justify="space-between" h={64}>
          {/* Logo */}
          <Link href="/submit" style={{ textDecoration: 'none' }}>
            <Group gap="md">
              <Image
                src="/FON_Logo.png"
                alt="FON Advisors Logo"
                width={160}
                height={40}
                style={{ objectFit: 'contain' }}
              />
              <Text size="sm" c="fonBlue.1" fw={500} style={{ letterSpacing: '0.5px' }}>
                Proposal Writer
              </Text>
            </Group>
          </Link>

          {/* Desktop Navigation */}
          <Group gap="xs" visibleFrom="sm">
            {navLinks.map((link) => (
              <NavLink key={link.href} {...link} variant="dark" />
            ))}
          </Group>

          {/* Mobile Burger */}
          <Burger
            opened={opened}
            onClick={toggle}
            hiddenFrom="sm"
            size="sm"
            color="white"
          />
        </Group>
      </Container>

      {/* Mobile Drawer */}
      <Drawer
        opened={opened}
        onClose={close}
        title={
          <Image
            src="/FON_Logo.png"
            alt="FON Advisors Logo"
            width={140}
            height={35}
            style={{ objectFit: 'contain' }}
          />
        }
        size="xs"
        padding="md"
      >
        <Stack gap="xs" mt="md">
          {navLinks.map((link) => (
            <NavLink key={link.href} {...link} variant="light" />
          ))}
        </Stack>
      </Drawer>
    </Box>
  );
}
