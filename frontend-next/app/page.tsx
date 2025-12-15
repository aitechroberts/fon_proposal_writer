'use client';

import { useState } from 'react';
import {
  AppShell,
  Container,
  Grid,
  Stack,
  Paper,
  LoadingOverlay,
  Box,
  Text,
  Transition,
  Alert,
} from '@mantine/core';
import { IconAlertCircle } from '@tabler/icons-react';
import {
  Header,
  JobForm,
  ProcessingCard,
  JobStatus,
  JobHistory,
} from '@/components';
import { useBackendHealth, useJobHistory } from '@/hooks';

export default function HomePage() {
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
    <AppShell
      header={{ height: 0 }}
      navbar={{
        width: 280,
        breakpoint: 'md',
        collapsed: { mobile: true },
      }}
      padding="md"
      style={{
        background: 'linear-gradient(135deg, #f8fafc 0%, #e6f6fd 100%)',
        minHeight: '100vh',
      }}
    >
      <AppShell.Navbar p="md" style={{ background: 'white' }}>
        <Stack gap="lg" h="100%">
          <Box>
            <Text
              size="xs"
              fw={700}
              tt="uppercase"
              c="dimmed"
              mb="xs"
              style={{ letterSpacing: '0.5px' }}
            >
              Navigation
            </Text>
            <Paper
              p="sm"
              radius="md"
              style={{
                background:
                  'linear-gradient(90deg, rgba(4, 57, 94, 0.05) 0%, rgba(0, 163, 224, 0.05) 100%)',
              }}
            >
              <Text size="sm" fw={500} c="navy">
                📊 Dashboard
              </Text>
            </Paper>
          </Box>

          <Box style={{ flex: 1 }}>
            <Text
              size="xs"
              fw={700}
              tt="uppercase"
              c="dimmed"
              mb="xs"
              style={{ letterSpacing: '0.5px' }}
            >
              Recent Jobs
            </Text>
            <JobHistory />
          </Box>

          <Box>
            <Paper
              p="md"
              radius="md"
              withBorder
              style={{ borderColor: 'rgba(0, 163, 224, 0.3)' }}
            >
              <Text size="xs" c="dimmed" ta="center">
                RFP Compliance Matrix Generator
              </Text>
              <Text size="xs" c="dimmed" ta="center" mt={4}>
                Powered by Azure OpenAI &amp; DSPy
              </Text>
            </Paper>
          </Box>
        </Stack>
      </AppShell.Navbar>

      <AppShell.Main>
        <Container size="xl" py="md">
          <LoadingOverlay
            visible={healthLoading}
            overlayProps={{ blur: 2 }}
            loaderProps={{ color: 'cyan', type: 'bars' }}
          />

          {/* Header */}
          <Header />

          {/* Backend Error Alert */}
          <Transition mounted={healthError} transition="slide-down" duration={200}>
            {(styles) => (
              <Alert
                style={{ ...styles, marginBottom: '1.5rem' }}
                icon={<IconAlertCircle size={18} />}
                title="Backend Unavailable"
                color="red"
                variant="filled"
              >
                Cannot connect to the backend API. Please ensure the backend service
                is running and try again.
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
              <Stack gap="lg">
                {!currentJobId && <ProcessingCard formData={formData} />}
                {currentJobId && <JobStatus />}
              </Stack>
            </Grid.Col>
          </Grid>
        </Container>
      </AppShell.Main>
    </AppShell>
  );
}

