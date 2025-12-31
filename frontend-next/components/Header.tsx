'use client';

import { Box, Group, Text, Badge, ThemeIcon, Skeleton } from '@mantine/core';
import { IconFileAnalytics } from '@tabler/icons-react';
import { useBackendHealth } from '@/hooks';

export function Header() {
  const { data: health, isLoading, isError } = useBackendHealth();
  const isHealthy = !isLoading && !isError && health?.status === 'healthy';

  return (
    <Box mb="xl" pt="xs">
      <Group justify="space-between" align="center">
        <Group gap="md">
          {/* Logo mark with FON Advisors blue */}
          <ThemeIcon
            size={44}
            radius="md"
            color="fonBlue"
          >
            <IconFileAnalytics size={24} stroke={1.5} />
          </ThemeIcon>

          <Box>
            <Text
              size="xl"
              fw={700}
              c="charcoal.7"
              style={{ letterSpacing: '-0.5px', lineHeight: 1.2 }}
            >
              Proposal Writer
            </Text>
            <Text size="sm" c="charcoal.5">
              Compliance Matrix Generator
            </Text>
          </Box>
        </Group>

        {/* Status indicator */}
        {isLoading ? (
          <Skeleton height={24} width={120} radius="sm" />
        ) : (
          <Badge
            size="md"
            variant="dot"
            color={isHealthy ? 'teal' : 'red'}
          >
            {isHealthy ? 'System Operational' : 'System Offline'}
          </Badge>
        )}
      </Group>
    </Box>
  );
}
