'use client';

import { useState } from 'react';
import {
  AppShell,
  Container,
  Grid,
  Stack,
  LoadingOverlay,
  Box,
  Text,
  Transition,
  Alert,
  NavLink,
  Divider,
} from '@mantine/core';
import {
  IconAlertCircle,
  IconLayoutDashboard,
  IconHistory,
  IconBolt,
} from '@tabler/icons-react';
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
        width: 260,
        breakpoint: 'md',
        collapsed: { mobile: true },
      }}
      padding="md"
    >
      <AppShell.Navbar
        p="md"
        style={{
          background: 'white',
          borderRight: '1px solid var(--mantine-color-gray-2)',
        }}
      >
        <Stack gap="xs" h="100%">
          {/* Logo / Brand */}
          <Box pb="sm">
            <Text size="xs" fw={700} tt="uppercase" c="dimmed" style={{ letterSpacing: '0.5px' }}>
              Menu
            </Text>
          </Box>

          {/* Navigation */}
          <NavLink
            label="Dashboard"
            leftSection={<IconLayoutDashboard size={18} />}
            active
            variant="light"
            color="cyan"
          />

          <Divider my="sm" />

          {/* Job History Section */}
          <Box style={{ flex: 1, overflow: 'auto' }}>
            <Text
              size="xs"
              fw={700}
              tt="uppercase"
              c="dimmed"
              mb="sm"
              style={{ letterSpacing: '0.5px' }}
            >
              Recent Jobs
            </Text>
            <JobHistory />
          </Box>

          <Divider my="sm" />

          {/* Footer */}
          <Box pt="xs">
            <Stack gap={4} align="center">
              <IconBolt size={16} color="var(--mantine-color-cyan-5)" />
              <Text size="xs" c="dimmed" ta="center">
                Powered by Azure OpenAI
              </Text>
              <Text size="xs" c="dimmed" ta="center" opacity={0.7}>
                &amp; DSPy
              </Text>
            </Stack>
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
      </AppShell.Main>
    </AppShell>
  );
}
