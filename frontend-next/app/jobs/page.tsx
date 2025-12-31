'use client';

import {
  Container,
  Title,
  Text,
  Box,
} from '@mantine/core';
import { JobsTable } from '@/components';

export default function PreviousJobsPage() {
  return (
    <Container size="xl" py="xl">
      {/* Page Header */}
      <Box mb="xl">
        <Title order={1} c="charcoal.7" mb="xs">
          Previous Jobs
        </Title>
        <Text c="charcoal.5" size="lg">
          View and download results from completed extraction jobs
        </Text>
      </Box>

      {/* Jobs Table */}
      <JobsTable />
    </Container>
  );
}
