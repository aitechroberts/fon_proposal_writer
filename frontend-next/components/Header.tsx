'use client';

import { Box, Group, Text, Badge, Transition } from '@mantine/core';
import { IconFileAnalytics, IconCircleCheck, IconAlertCircle } from '@tabler/icons-react';
import { useBackendHealth } from '@/hooks';

export function Header() {
  const { data: health, isLoading, isError } = useBackendHealth();
  const isHealthy = !isLoading && !isError && health?.status === 'healthy';

  return (
    <Box
      style={{
        background: 'linear-gradient(90deg, #04395E 0%, #0A2E4D 55%, #00A3E0 100%)',
        padding: '1.25rem 1.5rem',
        borderRadius: '12px',
        marginBottom: '1.5rem',
      }}
    >
      <Group justify="space-between" align="center">
        <Group gap="md">
          <Box
            style={{
              background: 'rgba(255, 255, 255, 0.95)',
              borderRadius: '10px',
              padding: '10px 14px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              boxShadow: '0 4px 14px rgba(0, 0, 0, 0.08)',
            }}
          >
            <IconFileAnalytics size={32} color="#04395E" stroke={1.8} />
          </Box>
          <Box>
            <Text
              size="xl"
              fw={800}
              c="white"
              style={{ letterSpacing: '-0.5px', lineHeight: 1.2 }}
            >
              RFP Compliance Matrix Generator
            </Text>
            <Text size="sm" c="white" opacity={0.85} mt={2}>
              Transform government RFPs into compliance matrices with AI-powered extraction
            </Text>
          </Box>
        </Group>

        <Transition mounted={!isLoading} transition="fade" duration={200}>
          {(styles) => (
            <Badge
              style={styles}
              size="lg"
              variant="filled"
              color={isHealthy ? 'teal' : 'red'}
              leftSection={
                isHealthy ? (
                  <IconCircleCheck size={14} />
                ) : (
                  <IconAlertCircle size={14} />
                )
              }
            >
              {isHealthy ? 'API Connected' : 'API Offline'}
            </Badge>
          )}
        </Transition>
      </Group>
    </Box>
  );
}

