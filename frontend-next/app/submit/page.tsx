'use client';

import { useState } from 'react';
import {
  Container,
  Grid,
  Stack,
  LoadingOverlay,
  Transition,
  Alert,
  Title,
  Text,
  Box,
} from '@mantine/core';
import { IconAlertCircle } from '@tabler/icons-react';
import {
  Header,
  JobForm,
  ProcessingCard,
  JobStatus,
} from '@/components';
import { useBackendHealth, useJobHistory } from '@/hooks';

export default function SubmitJobsPage() {
  const [formData, setFormData] = useState({
    opportunityId: '',
    customFilename: '',
    useHighergov: false,
    generateProposal: true,
    useTwoStageWriter: false,
  });

  const { isLoading: healthLoading, isError: healthError } = useBackendHealth();
  const { currentJobId } = useJobHistory();

  const handleFormChange = (data: typeof formData) => {
    setFormData(data);
  };

  return (
    <Container size="xl" py="xl">
      <LoadingOverlay
        visible={healthLoading}
        overlayProps={{ blur: 2 }}
        loaderProps={{ color: 'fonBlue', type: 'bars' }}
      />

      {/* Page Header */}
      <Box mb="xl">
        <Title order={1} c="charcoal.7" mb="xs">
          Submit New Job
        </Title>
        <Text c="charcoal.5" size="lg">
          Upload RFP documents to extract requirements and generate proposals
        </Text>
      </Box>

      {/* Backend Error Alert */}
      <Transition mounted={healthError} transition="slide-down" duration={200}>
        {(styles) => (
          <Alert
            style={{ ...styles, marginBottom: '1.5rem' }}
            icon={<IconAlertCircle size={18} />}
            title="Backend Unavailable"
            color="red"
            variant="light"
          >
            Cannot connect to the backend API. Please ensure the backend service
            is running.
          </Alert>
        )}
      </Transition>

      {/* Main Content Grid */}
      <Grid gutter="lg">
        {/* Left Column - Form */}
        <Grid.Col span={{ base: 12, md: 7 }}>
          <JobForm onFormChange={handleFormChange} />
        </Grid.Col>

        {/* Right Column - Processing & Status */}
        <Grid.Col span={{ base: 12, md: 5 }}>
          <Stack gap="md">
            {!currentJobId && <ProcessingCard formData={formData} />}
            {currentJobId && <JobStatus />}
          </Stack>
        </Grid.Col>
      </Grid>
    </Container>
  );
}
