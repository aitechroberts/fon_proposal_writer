'use client';

import { Card, Text, Button, Stack, Alert, Box } from '@mantine/core';
import { IconRocket, IconAlertCircle, IconUpload } from '@tabler/icons-react';
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
    <Card shadow="sm" radius="lg" withBorder>
      <Box
        style={{
          background: 'linear-gradient(90deg, #04395E 0%, #0A2E4D 55%, #00A3E0 100%)',
          margin: '-1rem -1rem 1rem -1rem',
          padding: '0.9rem 1.15rem',
          borderRadius: '12px 12px 0 0',
        }}
      >
        <Text c="white" fw={800} size="lg">
          ⚙️ Processing
        </Text>
      </Box>

      <Stack gap="md">
        {isHealthError && (
          <Alert
            icon={<IconAlertCircle size={18} />}
            title="Backend Unavailable"
            color="red"
            variant="light"
          >
            Cannot connect to the backend API. Please try again later.
          </Alert>
        )}

        {!canProcess ? (
          !formData.useHighergov && blobUrls.length === 0 ? (
            <Alert
              icon={<IconUpload size={18} />}
              title="Upload Required"
              color="blue"
              variant="light"
            >
              Click &quot;Upload to Cloud Storage&quot; first, then extract requirements
            </Alert>
          ) : (
            <Alert
              icon={<IconAlertCircle size={18} />}
              title="Documents Required"
              color="blue"
              variant="light"
            >
              Please provide documents to process
            </Alert>
          )
        ) : (
          <Button
            leftSection={<IconRocket size={18} />}
            onClick={handleSubmit}
            loading={submitMutation.isPending}
            disabled={!canProcess || !isBackendHealthy}
            variant="gradient"
            gradient={{ from: 'cyan', to: 'teal', deg: 90 }}
            size="lg"
            fullWidth
          >
            Extract Requirements
          </Button>
        )}

        {canProcess && (
          <Text size="xs" c="dimmed" ta="center">
            {formData.useHighergov
              ? `Processing opportunity: ${formData.opportunityId}`
              : `${blobUrls.length} file(s) ready for processing`}
          </Text>
        )}
      </Stack>
    </Card>
  );
}

