'use client';

import {
  Stack,
  Text,
  Paper,
  Group,
  Badge,
  ThemeIcon,
  Box,
  ScrollArea,
} from '@mantine/core';
import {
  IconClock,
  IconPlayerPlay,
  IconCheck,
  IconX,
  IconHistory,
} from '@tabler/icons-react';
import { useJobHistory } from '@/hooks';
import { JobHistoryItem } from '@/lib/types';

function getStatusIcon(status: string) {
  switch (status) {
    case 'queued':
      return <IconClock size={14} />;
    case 'running':
      return <IconPlayerPlay size={14} />;
    case 'completed':
      return <IconCheck size={14} />;
    case 'failed':
      return <IconX size={14} />;
    default:
      return <IconClock size={14} />;
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
  const { setCurrentJobId } = useJobHistory();

  return (
    <Paper
      p="sm"
      radius="md"
      withBorder
      style={{ cursor: 'pointer' }}
      onClick={() => setCurrentJobId(job.job_id)}
      className="hover-card"
    >
      <Group justify="space-between" wrap="nowrap">
        <Box style={{ minWidth: 0 }}>
          <Text size="xs" fw={600} truncate>
            {job.job_id.slice(0, 8)}...
          </Text>
          <Text size="xs" c="dimmed">
            {job.created_at}
          </Text>
        </Box>
        <Badge
          size="sm"
          variant="light"
          color={getStatusColor(job.status)}
          leftSection={getStatusIcon(job.status)}
        >
          {job.status}
        </Badge>
      </Group>
      {job.file_count && (
        <Text size="xs" c="dimmed" mt={4}>
          {job.file_count} requirements
        </Text>
      )}
    </Paper>
  );
}

export function JobHistory() {
  const { jobs } = useJobHistory();
  const recentJobs = jobs.slice(-5).reverse(); // Show last 5, newest first

  return (
    <Stack gap="sm">
      <Group gap="xs">
        <ThemeIcon size="sm" variant="light" color="cyan">
          <IconHistory size={14} />
        </ThemeIcon>
        <Text size="sm" fw={600}>
          Job History
        </Text>
      </Group>

      {recentJobs.length === 0 ? (
        <Paper p="md" radius="md" withBorder>
          <Text size="sm" c="dimmed" ta="center">
            No jobs submitted yet
          </Text>
        </Paper>
      ) : (
        <ScrollArea.Autosize mah={400}>
          <Stack gap="xs">
            {recentJobs.map((job) => (
              <JobHistoryCard key={job.job_id} job={job} />
            ))}
          </Stack>
        </ScrollArea.Autosize>
      )}
    </Stack>
  );
}

