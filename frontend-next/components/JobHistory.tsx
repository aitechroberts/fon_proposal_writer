'use client';

import {
  Stack,
  Text,
  Paper,
  Group,
  Badge,
  Box,
  ScrollArea,
} from '@mantine/core';
import {
  IconClock,
  IconPlayerPlay,
  IconCheck,
  IconX,
} from '@tabler/icons-react';
import { useJobHistory } from '@/hooks';
import { JobHistoryItem } from '@/lib/types';

function getStatusIcon(status: string) {
  switch (status) {
    case 'queued':
      return <IconClock size={12} />;
    case 'running':
      return <IconPlayerPlay size={12} />;
    case 'completed':
      return <IconCheck size={12} />;
    case 'failed':
      return <IconX size={12} />;
    default:
      return <IconClock size={12} />;
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

function JobHistoryCard({ job }: { job: JobHistoryItem }) {
  const { setCurrentJobId, currentJobId } = useJobHistory();
  const isActive = currentJobId === job.job_id;

  return (
    <Paper
      p="xs"
      radius="md"
      withBorder
      style={{
        cursor: 'pointer',
        borderColor: isActive ? 'var(--mantine-color-cyan-5)' : undefined,
        backgroundColor: isActive ? 'var(--mantine-color-cyan-0)' : undefined,
      }}
      onClick={() => setCurrentJobId(job.job_id)}
      className="hover-lift"
    >
      <Group justify="space-between" wrap="nowrap" gap="xs">
        <Box style={{ minWidth: 0, flex: 1 }}>
          <Text size="xs" fw={500} className="font-mono" truncate>
            {job.job_id.slice(0, 8)}
          </Text>
          <Text size="xs" c="dimmed" truncate>
            {job.created_at}
          </Text>
        </Box>
        <Badge
          size="xs"
          variant="dot"
          color={getStatusColor(job.status)}
        >
          {job.status}
        </Badge>
      </Group>
    </Paper>
  );
}

export function JobHistory() {
  const { jobs } = useJobHistory();
  const recentJobs = jobs.slice(-5).reverse(); // Show last 5, newest first

  if (recentJobs.length === 0) {
    return (
      <Paper p="sm" radius="md" withBorder>
        <Text size="xs" c="dimmed" ta="center">
          No jobs yet
        </Text>
      </Paper>
    );
  }

  return (
    <ScrollArea.Autosize mah={300}>
      <Stack gap="xs">
        {recentJobs.map((job) => (
          <JobHistoryCard key={job.job_id} job={job} />
        ))}
      </Stack>
    </ScrollArea.Autosize>
  );
}
