'use client';

import { Stack, Button, Group, Text, Badge, Divider, Box, Tooltip } from '@mantine/core';
import {
  IconFileSpreadsheet,
  IconFileText,
  IconPackage,
  IconCheck,
  IconRefresh,
  IconQuote,
} from '@tabler/icons-react';
import { JobResultsResponse } from '@/lib/types';
import { useJobHistory } from '@/hooks';

interface ResultsDownloadProps {
  results: JobResultsResponse;
}

export function ResultsDownload({ results }: ResultsDownloadProps) {
  const { clearCurrentJob } = useJobHistory();

  const hasProposals = results.clean_proposal_sas_url || results.cited_proposal_sas_url;

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
        <Text size="xs" c="charcoal.5">
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
            color="fonBlue"
            size="sm"
            fullWidth
          >
            Download All (ZIP)
          </Button>
        )}

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
            size="sm"
            fullWidth
          >
            Compliance Matrix (Excel)
          </Button>
        )}

        {/* Proposal Documents */}
        {hasProposals && (
          <Group grow gap="xs">
            {/* Clean Proposal */}
            {results.clean_proposal_sas_url && (
              <Tooltip label="Citations removed - ready for submission" withArrow>
                <Button
                  component="a"
                  href={results.clean_proposal_sas_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  leftSection={<IconFileText size={16} />}
                  color="fonBlue"
                  variant="light"
                  size="xs"
                >
                  Clean Proposal
                </Button>
              </Tooltip>
            )}

            {/* Cited Proposal */}
            {results.cited_proposal_sas_url && (
              <Tooltip label="Includes citations for reference" withArrow>
                <Button
                  component="a"
                  href={results.cited_proposal_sas_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  leftSection={<IconQuote size={16} />}
                  color="violet"
                  variant="light"
                  size="xs"
                >
                  Cited Proposal
                </Button>
              </Tooltip>
            )}
          </Group>
        )}

        {!hasProposals && results.requirements_sas_url && (
          <Text size="xs" c="charcoal.5" ta="center">
            Proposal not generated
          </Text>
        )}
      </Stack>

      <Divider />

      {/* New Job Button */}
      <Button
        variant="subtle"
        color="charcoal"
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
