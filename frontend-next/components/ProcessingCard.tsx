'use client';

import { Card, Text, Button, Stack, Alert, Box, Group } from '@mantine/core';
import { IconRocket, IconAlertCircle, IconUpload, IconCpu } from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import { useJobSubmit, useJobHistory, useBackendHealth } from '@/hooks';

interface ProcessingCardProps {
  formData: {
    opportunityId: string;
    customFilename: string;
    useHighergov: boolean;
    generateProposal: boolean;
    useTwoStageWriter: boolean;
  };
}

export function ProcessingCard({ formData }: ProcessingCardProps) {
  const { blobUrls, addJob, setCurrentJobId } = useJobHistory();
  const submitMutation = useJobSubmit();
  const { data: health, isError: isHealthError } = useBackendHealth();

  const isBackendHealthy = health?.status === 'healthy';
  
  // Job name is required
  const hasJobName = formData.customFilename.trim().length > 0;
  
  // Manual upload only - HigherGov not yet implemented
  const hasDocuments = blobUrls.length > 0;
  
  const canProcess = hasJobName && hasDocuments;

  const handleSubmit = async () => {
    // Generate opportunity ID for manual uploads
    const opportunityId = `manual-upload-${Date.now()}`;

    try {
      const result = await submitMutation.mutateAsync({
        opportunity_id: opportunityId,
        custom_filename: formData.customFilename || undefined,
        use_highergov: false, // HigherGov not yet implemented
        blob_urls: blobUrls,
        generate_proposal: formData.generateProposal,
        use_two_stage_writer: false, // Two-stage writer not yet implemented
      });

      // Add to history
      addJob({
        job_id: result.job_id,
        status: 'queued',
        created_at: new Date().toLocaleString(),
        opportunity_id: opportunityId,
      });

      // Set as current job
      setCurrentJobId(result.job_id);

      notifications.show({
        title: 'Job Submitted',
        message: `Job ${result.job_id.slice(0, 8)}... submitted successfully`,
        color: 'teal',
      });
    } catch (error) {
      notifications.show({
        title: 'Submission Failed',
        message: error instanceof Error ? error.message : 'Failed to submit job',
        color: 'red',
      });
    }
  };

  return (
    <Card padding="lg">
      <Card.Section withBorder inheritPadding py="sm" bg="charcoal.6">
        <Group gap="xs">
          <IconCpu size={18} color="white" />
          <Text fw={600} size="sm" c="white">
            Processing
          </Text>
        </Group>
      </Card.Section>

      <Stack gap="md" mt="md">
        {isHealthError && (
          <Alert
            icon={<IconAlertCircle size={16} />}
            title="Backend Unavailable"
            color="red"
            variant="light"
          >
            Cannot connect to the backend API.
          </Alert>
        )}

        {!canProcess ? (
          !hasJobName ? (
            <Alert
              icon={<IconAlertCircle size={16} />}
              color="orange"
              variant="light"
            >
              <Text size="sm">Enter a job name to continue</Text>
            </Alert>
          ) : (
            <Alert
              icon={<IconUpload size={16} />}
              color="fonBlue"
              variant="light"
            >
              <Text size="sm">Upload files to cloud storage first</Text>
            </Alert>
          )
        ) : (
          <Button
            leftSection={<IconRocket size={18} />}
            onClick={handleSubmit}
            loading={submitMutation.isPending}
            disabled={!canProcess || !isBackendHealthy}
            color="fonBlue"
            size="md"
            fullWidth
          >
            Extract Requirements
          </Button>
        )}

        {canProcess && (
          <Text size="xs" c="charcoal.5" ta="center">
            {blobUrls.length} file(s) ready
          </Text>
        )}
      </Stack>
    </Card>
  );
}
