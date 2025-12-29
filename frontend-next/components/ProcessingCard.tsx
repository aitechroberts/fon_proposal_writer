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
  
  // Can process if:
  // - Using HigherGov and has opportunity ID, OR
  // - Manual upload and has blob URLs
  const canProcess = formData.useHighergov
    ? formData.opportunityId.trim().length > 0
    : blobUrls.length > 0;

  const handleSubmit = async () => {
    // Generate opportunity ID for manual uploads
    const opportunityId = formData.opportunityId || `manual-upload-${Date.now()}`;

    try {
      const result = await submitMutation.mutateAsync({
        opportunity_id: opportunityId,
        custom_filename: formData.customFilename || undefined,
        use_highergov: formData.useHighergov,
        blob_urls: blobUrls,
        generate_proposal: formData.generateProposal,
        use_two_stage_writer: formData.useTwoStageWriter,
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
      <Card.Section withBorder inheritPadding py="sm">
        <Group gap="xs">
          <IconCpu size={18} color="var(--mantine-color-cyan-6)" />
          <Text fw={600} size="sm" c="navy.7">
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
          !formData.useHighergov && blobUrls.length === 0 ? (
            <Alert
              icon={<IconUpload size={16} />}
              color="blue"
              variant="light"
            >
              <Text size="sm">Upload files to cloud storage first</Text>
            </Alert>
          ) : (
            <Alert
              icon={<IconAlertCircle size={16} />}
              color="blue"
              variant="light"
            >
              <Text size="sm">Provide documents to process</Text>
            </Alert>
          )
        ) : (
          <Button
            leftSection={<IconRocket size={18} />}
            onClick={handleSubmit}
            loading={submitMutation.isPending}
            disabled={!canProcess || !isBackendHealthy}
            color="cyan"
            size="md"
            fullWidth
          >
            Extract Requirements
          </Button>
        )}

        {canProcess && (
          <Text size="xs" c="dimmed" ta="center">
            {formData.useHighergov
              ? `Opportunity: ${formData.opportunityId}`
              : `${blobUrls.length} file(s) ready`}
          </Text>
        )}
      </Stack>
    </Card>
  );
}
