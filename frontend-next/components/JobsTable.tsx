'use client';

import { useState } from 'react';
import {
  Table,
  Text,
  TextInput,
  Group,
  ActionIcon,
  Tooltip,
  Badge,
  Pagination,
  Paper,
  Skeleton,
  Stack,
  Box,
  Center,
} from '@mantine/core';
import {
  IconSearch,
  IconDownload,
  IconFileSpreadsheet,
  IconFileText,
  IconFileZip,
} from '@tabler/icons-react';
import { useJobs } from '@/hooks';

interface Job {
  id: string;
  job_name: string;
  created_at: string;
  completed_at: string | null;
  requirements_sas_url: string | null;
  clean_proposal_sas_url: string | null;
  cited_proposal_sas_url: string | null;
  zip_sas_url: string | null;
  file_count: number;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function DownloadButton({
  url,
  icon: Icon,
  label,
  color,
}: {
  url: string | null;
  icon: typeof IconDownload;
  label: string;
  color: string;
}) {
  if (!url) return null;

  return (
    <Tooltip label={label} withArrow>
      <ActionIcon
        component="a"
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        variant="light"
        color={color}
        size="md"
      >
        <Icon size={16} />
      </ActionIcon>
    </Tooltip>
  );
}

export function JobsTable() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const limit = 20;

  const { data, isLoading, isError } = useJobs({
    page,
    limit,
    search: search || undefined,
    sortBy: 'created_at',
    sortOrder: 'desc',
  });

  if (isLoading) {
    return (
      <Paper p="md" withBorder>
        <Stack gap="md">
          <Skeleton height={40} />
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} height={60} />
          ))}
        </Stack>
      </Paper>
    );
  }

  if (isError) {
    return (
      <Paper p="xl" withBorder>
        <Center>
          <Text c="red">Failed to load jobs. Please try again.</Text>
        </Center>
      </Paper>
    );
  }

  const jobs = data?.jobs || [];
  const totalPages = data?.total_pages || 0;

  return (
    <Stack gap="md">
      {/* Search */}
      <TextInput
        placeholder="Search by job name..."
        leftSection={<IconSearch size={16} color="var(--mantine-color-charcoal-5)" />}
        value={search}
        onChange={(e) => {
          setSearch(e.target.value);
          setPage(1);
        }}
        style={{ maxWidth: 400 }}
      />

      {/* Table */}
      <Paper withBorder style={{ overflow: 'hidden' }}>
        <Table striped highlightOnHover>
          <Table.Thead style={{ backgroundColor: 'var(--mantine-color-charcoal-0)' }}>
            <Table.Tr>
              <Table.Th>Job Name</Table.Th>
              <Table.Th>Date</Table.Th>
              <Table.Th style={{ textAlign: 'center' }}>Requirements</Table.Th>
              <Table.Th style={{ textAlign: 'right' }}>Downloads</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {jobs.length === 0 ? (
              <Table.Tr>
                <Table.Td colSpan={4}>
                  <Center py="xl">
                    <Text c="charcoal.5">
                      {search ? 'No jobs found matching your search.' : 'No completed jobs yet.'}
                    </Text>
                  </Center>
                </Table.Td>
              </Table.Tr>
            ) : (
              jobs.map((job: Job) => (
                <Table.Tr key={job.id}>
                  <Table.Td>
                    <Box>
                      <Text fw={500} size="sm" c="charcoal.7">
                        {job.job_name}
                      </Text>
                      <Text size="xs" c="charcoal.4" className="font-mono">
                        {job.id.substring(0, 8)}...
                      </Text>
                    </Box>
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm" c="charcoal.6">{formatDate(job.created_at)}</Text>
                  </Table.Td>
                  <Table.Td style={{ textAlign: 'center' }}>
                    <Badge variant="light" color="fonBlue">
                      {job.file_count}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Group gap="xs" justify="flex-end">
                      <DownloadButton
                        url={job.requirements_sas_url}
                        icon={IconFileSpreadsheet}
                        label="Download Matrix (Excel)"
                        color="teal"
                      />
                      <DownloadButton
                        url={job.clean_proposal_sas_url}
                        icon={IconFileText}
                        label="Download Clean Proposal"
                        color="fonBlue"
                      />
                      <DownloadButton
                        url={job.cited_proposal_sas_url}
                        icon={IconFileText}
                        label="Download Cited Proposal"
                        color="violet"
                      />
                      <DownloadButton
                        url={job.zip_sas_url}
                        icon={IconFileZip}
                        label="Download All (ZIP)"
                        color="orange"
                      />
                    </Group>
                  </Table.Td>
                </Table.Tr>
              ))
            )}
          </Table.Tbody>
        </Table>
      </Paper>

      {/* Pagination */}
      {totalPages > 1 && (
        <Center>
          <Pagination
            total={totalPages}
            value={page}
            onChange={setPage}
            color="fonBlue"
          />
        </Center>
      )}
    </Stack>
  );
}
