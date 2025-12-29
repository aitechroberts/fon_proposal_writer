'use client';

import { Stack, Button, Group, Text, Badge, Divider, Box } from '@mantine/core';
import {
  IconFileSpreadsheet,
  IconFileText,
  IconPackage,
  IconCheck,
  IconRefresh,
} from '@tabler/icons-react';
import { JobResultsResponse } from '@/lib/types';
import { useJobHistory } from '@/hooks';

interface ResultsDownloadProps {
  results: JobResultsResponse;
}

export function ResultsDownload({ results }: ResultsDownloadProps) {
  const { clearCurrentJob } = useJobHistory();

  return (
    <Stack gap="md">
      <Divider
        label={
          <Badge variant="light" color="teal" leftSection={<IconCheck size={12} />}>
            Complete
          </Badge>
        }
        labelPosition="center"
      />

      {/* Stats */}
      <Box ta="center" py="xs">
        <Text className="font-mono" size="xl" fw={700} c="teal">
          {results.file_count || 0}
        </Text>
        <Text size="xs" c="dimmed">
          requirements extracted
        </Text>
      </Box>

      {/* Download Buttons */}
      <Stack gap="xs">
        {/* ZIP Download (All outputs) */}
        {results.zip_sas_url && (
          <Button
            component="a"
            href={results.zip_sas_url}
            target="_blank"
            rel="noopener noreferrer"
            leftSection={<IconPackage size={16} />}
            color="violet"
            size="sm"
            fullWidth
          >
            Download All (ZIP)
          </Button>
        )}

        <Group grow gap="xs">
          {/* Compliance Matrix */}
          {results.requirements_sas_url && (
            <Button
              component="a"
              href={results.requirements_sas_url}
              target="_blank"
              rel="noopener noreferrer"
              leftSection={<IconFileSpreadsheet size={16} />}
              color="teal"
              variant="light"
              size="xs"
            >
              Matrix
            </Button>
          )}

          {/* Proposal Document */}
          {results.proposal_sas_url && (
            <Button
              component="a"
              href={results.proposal_sas_url}
              target="_blank"
              rel="noopener noreferrer"
              leftSection={<IconFileText size={16} />}
              color="blue"
              variant="light"
              size="xs"
            >
              Proposal
            </Button>
          )}
        </Group>

        {!results.proposal_sas_url && results.requirements_sas_url && (
          <Text size="xs" c="dimmed" ta="center">
            Proposal not generated
          </Text>
        )}
      </Stack>

      <Divider />

      {/* New Job Button */}
      <Button
        variant="subtle"
        color="gray"
        size="xs"
        onClick={clearCurrentJob}
        leftSection={<IconRefresh size={14} />}
        fullWidth
      >
        New Job
      </Button>
    </Stack>
  );
}
