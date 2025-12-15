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
} from '@mantine/core';
import {
  IconClock,
  IconPlayerPlay,
  IconCheck,
  IconX,
  IconLoader2,
} from '@tabler/icons-react';
import { useJobStatus, useJobResults, useJobHistory } from '@/hooks';
import { ResultsDownload } from './ResultsDownload';

function getStatusIcon(status: string) {
  switch (status) {
    case 'queued':
      return <IconClock size={20} />;
    case 'running':
      return <IconLoader2 size={20} className="animate-pulse" />;
    case 'completed':
      return <IconCheck size={20} />;
    case 'failed':
      return <IconX size={20} />;
    default:
      return <IconClock size={20} />;
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
    <Card shadow="sm" radius="lg" withBorder>
      <Box
        style={{
          background: 'linear-gradient(90deg, #04395E 0%, #0A2E4D 55%, #00A3E0 100%)',
          margin: '-1rem -1rem 1rem -1rem',
          padding: '0.9rem 1.15rem',
          borderRadius: '12px 12px 0 0',
        }}
      >
        <Text c="white" fw={800} size="lg">
          📊 Job Status
        </Text>
      </Box>

      <Stack gap="md">
        {/* Status Badge */}
        <Box
          className={getStatusClass(status)}
          style={{
            padding: '1rem',
            borderRadius: '8px',
            textAlign: 'center',
          }}
        >
          <Group justify="center" gap="sm">
            <ThemeIcon
              variant="light"
              color={getStatusColor(status)}
              size="lg"
              radius="xl"
            >
              {getStatusIcon(status)}
            </ThemeIcon>
            <Text size="lg" fw={700} tt="uppercase">
              {status}
            </Text>
          </Group>
          <Text size="sm" mt="xs" c="dimmed">
            {message}
          </Text>
        </Box>

        {/* Progress */}
        {(status === 'queued' || status === 'running') && (
          <Stack gap="xs">
            <Group justify="center">
              <RingProgress
                size={100}
                thickness={8}
                roundCaps
                sections={[{ value: progress, color: getStatusColor(status) }]}
                label={
                  <Center>
                    <Text size="lg" fw={700}>
                      {Math.round(progress)}%
                    </Text>
                  </Center>
                }
              />
            </Group>
            <Progress
              value={progress}
              color={getStatusColor(status)}
              size="lg"
              radius="xl"
              animated={status === 'running'}
            />
          </Stack>
        )}

        {/* Job ID */}
        <Group justify="space-between">
          <Text size="sm" c="dimmed">
            Job ID:
          </Text>
          <Badge variant="light" color="gray">
            {currentJobId.slice(0, 8)}...
          </Badge>
        </Group>

        {/* Results */}
        {status === 'completed' && resultsData && (
          <ResultsDownload results={resultsData} />
        )}

        {/* Error */}
        {status === 'failed' && statusData?.error_message && (
          <Box
            style={{
              background: '#ffebee',
              padding: '1rem',
              borderRadius: '8px',
              borderLeft: '4px solid #f44336',
            }}
          >
            <Text size="sm" c="red" fw={500}>
              Error: {statusData.error_message}
            </Text>
          </Box>
        )}
      </Stack>
    </Card>
  );
}

