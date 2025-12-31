'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
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

  const NavLink = ({ href, label, icon: Icon }: typeof navLinks[0]) => {
    const isActive = pathname === href;
    
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
            backgroundColor: isActive ? 'var(--mantine-color-fonBlue-5)' : 'transparent',
            color: isActive ? 'white' : 'var(--mantine-color-charcoal-7)',
            transition: 'all 0.15s ease',
            fontWeight: 500,
          }}
          className={isActive ? '' : 'nav-link-hover'}
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
        backgroundColor: 'white',
        borderBottom: '1px solid var(--mantine-color-charcoal-2)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}
    >
      <Container size="xl">
        <Group justify="space-between" h={64}>
          {/* Logo */}
          <Link href="/submit" style={{ textDecoration: 'none' }}>
            <Group gap="sm">
              <Box
                style={{
                  width: 40,
                  height: 40,
                  backgroundColor: 'var(--mantine-color-fonBlue-5)',
                  borderRadius: 8,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Text c="white" fw={700} size="lg">F</Text>
              </Box>
              <Box>
                <Text fw={700} size="lg" c="charcoal.7" style={{ lineHeight: 1.2 }}>
                  FON Advisors
                </Text>
                <Text size="xs" c="charcoal.5">
                  Proposal Writer
                </Text>
              </Box>
            </Group>
          </Link>

          {/* Desktop Navigation */}
          <Group gap="xs" visibleFrom="sm">
            {navLinks.map((link) => (
              <NavLink key={link.href} {...link} />
            ))}
          </Group>

          {/* Mobile Burger */}
          <Burger
            opened={opened}
            onClick={toggle}
            hiddenFrom="sm"
            size="sm"
            color="var(--mantine-color-charcoal-7)"
          />
        </Group>
      </Container>

      {/* Mobile Drawer */}
      <Drawer
        opened={opened}
        onClose={close}
        title={
          <Group gap="sm">
            <Box
              style={{
                width: 32,
                height: 32,
                backgroundColor: 'var(--mantine-color-fonBlue-5)',
                borderRadius: 6,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Text c="white" fw={700} size="sm">F</Text>
            </Box>
            <Text fw={700} c="charcoal.7">FON Advisors</Text>
          </Group>
        }
        size="xs"
        padding="md"
      >
        <Stack gap="xs" mt="md">
          {navLinks.map((link) => (
            <NavLink key={link.href} {...link} />
          ))}
        </Stack>
      </Drawer>
    </Box>
  );
}
