'use client';

import { useState } from 'react';
import {
  Card,
  Text,
  TextInput,
  Switch,
  SegmentedControl,
  Stack,
  Group,
  Divider,
  Box,
  Alert,
} from '@mantine/core';
import {
  IconBuildingBank,
  IconFileUpload,
  IconKey,
  IconAlertCircle,
} from '@tabler/icons-react';
import { FileUpload } from './FileUpload';
import { useJobHistory } from '@/hooks';

interface JobFormProps {
  onFormChange: (data: {
    opportunityId: string;
    customFilename: string;
    useHighergov: boolean;
    generateProposal: boolean;
    useTwoStageWriter: boolean;
  }) => void;
}

export function JobForm({ onFormChange }: JobFormProps) {
  const [inputMethod, setInputMethod] = useState<'manual' | 'highergov'>('manual');
  const [opportunityId, setOpportunityId] = useState('');
  const [customFilename, setCustomFilename] = useState('');
  const [generateProposal, setGenerateProposal] = useState(true);
  const [useTwoStageWriter, setUseTwoStageWriter] = useState(false);
  
  const { blobUrls } = useJobHistory();
  const useHighergov = inputMethod === 'highergov';

  // Check if HigherGov API key is available (would be set via env)
  const hasHighergovKey = typeof window !== 'undefined' 
    ? false // In production, this would check server-side
    : false;

  const handleChange = () => {
    onFormChange({
      opportunityId,
      customFilename,
      useHighergov,
      generateProposal,
      useTwoStageWriter,
    });
  };

  return (
    <Stack gap="lg">
      {/* Job Submission Card */}
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
            ➕ Submit New Job
          </Text>
        </Box>

        <Stack gap="md">
          {/* Input Method Toggle */}
          <Box>
            <Text size="sm" fw={500} mb="xs">
              Choose input method:
            </Text>
            <SegmentedControl
              value={inputMethod}
              onChange={(value) => {
                setInputMethod(value as 'manual' | 'highergov');
                handleChange();
              }}
              data={[
                {
                  value: 'manual',
                  label: (
                    <Group gap="xs">
                      <IconFileUpload size={16} />
                      <span>Manual File Upload</span>
                    </Group>
                  ),
                },
                {
                  value: 'highergov',
                  label: (
                    <Group gap="xs">
                      <IconBuildingBank size={16} />
                      <span>HigherGov Opportunity ID</span>
                    </Group>
                  ),
                },
              ]}
              fullWidth
              color="cyan"
            />
          </Box>

          {useHighergov && !hasHighergovKey && (
            <Alert
              icon={<IconAlertCircle size={18} />}
              title="API Key Required"
              color="red"
              variant="light"
            >
              HigherGov API key not configured. Please contact your administrator.
            </Alert>
          )}

          <Divider />

          {/* Output Settings */}
          <Text size="sm" fw={600}>
            Output Settings
          </Text>
          <TextInput
            label="Custom filename (optional)"
            placeholder="my-proposal-compliance-matrix"
            description="Custom name for the output files"
            value={customFilename}
            onChange={(e) => {
              setCustomFilename(e.target.value);
              handleChange();
            }}
          />

          <Divider />

          {/* Proposal Generation Options */}
          <Text size="sm" fw={600}>
            Proposal Generation
          </Text>
          <Switch
            label="Generate proposal document"
            description="Automatically generate a Word proposal document from extracted requirements"
            checked={generateProposal}
            onChange={(e) => {
              setGenerateProposal(e.currentTarget.checked);
              handleChange();
            }}
            color="cyan"
          />
          {generateProposal && (
            <Switch
              label="Use enhanced two-stage writer (higher quality, slower)"
              description="Uses a two-stage DSPy pipeline: theme analysis then drafting"
              checked={useTwoStageWriter}
              onChange={(e) => {
                setUseTwoStageWriter(e.currentTarget.checked);
                handleChange();
              }}
              color="cyan"
              ml="md"
            />
          )}
        </Stack>
      </Card>

      {/* Documents Card */}
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
            📁 Provide Documents
          </Text>
        </Box>

        {useHighergov ? (
          <Stack gap="md">
            <Text size="sm" fw={600}>
              HigherGov Integration
            </Text>
            <TextInput
              label="Opportunity ID"
              placeholder="e.g., abc123xyz or SAM notice ID"
              description="Enter the opportunity ID from HigherGov or SAM.gov"
              leftSection={<IconKey size={16} />}
              value={opportunityId}
              onChange={(e) => {
                setOpportunityId(e.target.value);
                handleChange();
              }}
              disabled={!hasHighergovKey}
            />
          </Stack>
        ) : (
          <Stack gap="md">
            <Text size="sm" fw={600}>
              Manual File Upload
            </Text>
            <FileUpload />
          </Stack>
        )}
      </Card>
    </Stack>
  );
}

