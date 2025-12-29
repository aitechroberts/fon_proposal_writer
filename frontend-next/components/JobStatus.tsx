'use client';

import {
  Card,
  Text,
  Progress,
  Stack,
  Group,
  Badge,
  Box,
  ThemeIcon,
  RingProgress,
  Center,
  Skeleton,
} from '@mantine/core';
import {
  IconClock,
  IconPlayerPlay,
  IconCheck,
  IconX,
  IconLoader2,
  IconChartBar,
} from '@tabler/icons-react';
import { useJobStatus, useJobResults, useJobHistory } from '@/hooks';
import { ResultsDownload } from './ResultsDownload';

function getStatusIcon(status: string) {
  switch (status) {
    case 'queued':
      return <IconClock size={18} />;
    case 'running':
      return <IconLoader2 size={18} className="animate-pulse" />;
    case 'completed':
      return <IconCheck size={18} />;
    case 'failed':
      return <IconX size={18} />;
    default:
      return <IconClock size={18} />;
  }
}

function getStatusColor(status: string) {
  switch (status) {
    case 'queued':
      return 'blue';
    case 'running':
      return 'orange';
    case 'completed':
      return 'teal';
    case 'failed':
      return 'red';
    default:
      return 'gray';
  }
}

function getStatusClass(status: string) {
  switch (status) {
    case 'queued':
      return 'status-queued';
    case 'running':
      return 'status-running';
    case 'completed':
      return 'status-completed';
    case 'failed':
      return 'status-failed';
    default:
      return '';
  }
}

function JobStatusSkeleton() {
  return (
    <Stack gap="md">
      <Skeleton height={60} radius="md" />
      <Group justify="center">
        <Skeleton height={100} width={100} radius="xl" />
      </Group>
      <Skeleton height={8} radius="xl" />
      <Group justify="space-between">
        <Skeleton height={14} width={60} />
        <Skeleton height={20} width={100} radius="sm" />
      </Group>
    </Stack>
  );
}

export function JobStatus() {
  const { currentJobId, updateJobStatus } = useJobHistory();
  const { data: statusData, isLoading } = useJobStatus(currentJobId);
  const { data: resultsData } = useJobResults(
    currentJobId,
    statusData?.status === 'completed'
  );

  if (!currentJobId) return null;

  const status = statusData?.status || 'queued';
  const progress = statusData?.progress || 0;
  const message = statusData?.message || 'Initializing...';

  // Update job history when status changes
  if (statusData) {
    updateJobStatus(currentJobId, statusData.status);
  }

  return (
    <Card padding="lg">
      <Card.Section withBorder inheritPadding py="sm">
        <Group gap="xs">
          <IconChartBar size={18} color="var(--mantine-color-cyan-6)" />
          <Text fw={600} size="sm" c="navy.7">
            Job Status
          </Text>
        </Group>
      </Card.Section>

      <Box mt="md">
        {isLoading ? (
          <JobStatusSkeleton />
        ) : (
          <Stack gap="md">
            {/* Status Badge */}
            <Box
              className={getStatusClass(status)}
              style={{
                padding: '0.875rem',
                borderRadius: '8px',
              }}
            >
              <Group justify="center" gap="sm">
                <ThemeIcon
                  variant="light"
                  color={getStatusColor(status)}
                  size="md"
                  radius="xl"
                >
                  {getStatusIcon(status)}
                </ThemeIcon>
                <Text size="md" fw={600} tt="capitalize">
                  {status}
                </Text>
              </Group>
              <Text size="xs" mt="xs" c="dimmed" ta="center">
                {message}
              </Text>
            </Box>

            {/* Progress */}
            {(status === 'queued' || status === 'running') && (
              <Stack gap="sm">
                <Group justify="center">
                  <RingProgress
                    size={80}
                    thickness={6}
                    roundCaps
                    sections={[{ value: progress, color: getStatusColor(status) }]}
                    label={
                      <Center>
                        <Text size="sm" fw={600} className="font-mono">
                          {Math.round(progress)}%
                        </Text>
                      </Center>
                    }
                  />
                </Group>
                <Progress
                  value={progress}
                  color={getStatusColor(status)}
                  size="sm"
                  radius="xl"
                  animated={status === 'running'}
                />
              </Stack>
            )}

            {/* Job ID */}
            <Group justify="space-between">
              <Text size="xs" c="dimmed">
                Job ID
              </Text>
              <Text size="xs" className="font-mono" c="dimmed">
                {currentJobId.slice(0, 8)}...
              </Text>
            </Group>

            {/* Results */}
            {status === 'completed' && resultsData && (
              <ResultsDownload results={resultsData} />
            )}

            {/* Error */}
            {status === 'failed' && statusData?.error_message && (
              <Box className="status-failed" p="sm" style={{ borderRadius: '8px' }}>
                <Text size="xs" c="red.7" fw={500}>
                  {statusData.error_message}
                </Text>
              </Box>
            )}
          </Stack>
        )}
      </Box>
    </Card>
  );
}
