'use client';

import { Stack, Button, Group, Text, Badge, Divider, Box } from '@mantine/core';
import {
  IconDownload,
  IconFileSpreadsheet,
  IconFileText,
  IconPackage,
  IconCheck,
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
      <Divider label="Processing Complete" labelPosition="center" />

      {/* Stats */}
      <Group justify="center" gap="xl">
        <Box ta="center">
          <Text size="2rem" fw={800} c="teal">
            {results.file_count || 0}
          </Text>
          <Text size="xs" c="dimmed">
            Requirements Extracted
          </Text>
        </Box>
        <Box ta="center">
          <Badge size="xl" variant="light" color="teal" leftSection={<IconCheck size={14} />}>
            Complete
          </Badge>
        </Box>
      </Group>

      <Divider />

      {/* Download Buttons */}
      <Text size="sm" fw={600}>
        📥 Download Results
      </Text>

      <Stack gap="sm">
        {/* ZIP Download (All outputs) */}
        {results.zip_sas_url && (
          <Button
            component="a"
            href={results.zip_sas_url}
            target="_blank"
            rel="noopener noreferrer"
            leftSection={<IconPackage size={18} />}
            variant="gradient"
            gradient={{ from: 'violet', to: 'grape', deg: 90 }}
            size="lg"
            fullWidth
          >
            Download All (ZIP)
          </Button>
        )}

        <Group grow>
          {/* Compliance Matrix */}
          {results.requirements_sas_url && (
            <Button
              component="a"
              href={results.requirements_sas_url}
              target="_blank"
              rel="noopener noreferrer"
              leftSection={<IconFileSpreadsheet size={18} />}
              variant="gradient"
              gradient={{ from: 'teal', to: 'green', deg: 90 }}
              size="md"
            >
              Compliance Matrix (Excel)
            </Button>
          )}

          {/* Proposal Document */}
          {results.proposal_sas_url && (
            <Button
              component="a"
              href={results.proposal_sas_url}
              target="_blank"
              rel="noopener noreferrer"
              leftSection={<IconFileText size={18} />}
              variant="gradient"
              gradient={{ from: 'blue', to: 'cyan', deg: 90 }}
              size="md"
            >
              Proposal (Word)
            </Button>
          )}
        </Group>

        {!results.proposal_sas_url && results.requirements_sas_url && (
          <Text size="xs" c="dimmed" ta="center">
            Proposal generation was not requested or failed
          </Text>
        )}
      </Stack>

      <Divider />

      {/* New Job Button */}
      <Button
        variant="outline"
        color="gray"
        onClick={clearCurrentJob}
        leftSection={<IconDownload size={18} style={{ transform: 'rotate(180deg)' }} />}
      >
        Process New Job
      </Button>
    </Stack>
  );
}

