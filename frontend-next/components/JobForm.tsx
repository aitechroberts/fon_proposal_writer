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
  Badge,
} from '@mantine/core';
import {
  IconBuildingBank,
  IconFileUpload,
  IconKey,
  IconAlertCircle,
  IconPlus,
  IconFolder,
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
    <Stack gap="md">
      {/* Job Submission Card */}
      <Card padding="lg">
        <Card.Section withBorder inheritPadding py="sm">
          <Group justify="space-between">
            <Group gap="xs">
              <IconPlus size={18} color="var(--mantine-color-cyan-6)" />
              <Text fw={600} size="sm" c="navy.7">
                Submit New Job
              </Text>
            </Group>
            <Badge variant="light" color="cyan" size="sm">
              New
            </Badge>
          </Group>
        </Card.Section>

        <Stack gap="md" mt="md">
          {/* Input Method Toggle */}
          <Box>
            <Text size="sm" fw={500} mb="xs" c="dimmed">
              Input method
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
                      <span>File Upload</span>
                    </Group>
                  ),
                },
                {
                  value: 'highergov',
                  label: (
                    <Group gap="xs">
                      <IconBuildingBank size={16} />
                      <span>HigherGov ID</span>
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
              icon={<IconAlertCircle size={16} />}
              title="API Key Required"
              color="red"
              variant="light"
            >
              HigherGov API key not configured. Contact your administrator.
            </Alert>
          )}

          <Divider />

          {/* Output Settings */}
          <Box>
            <Text size="sm" fw={500} mb="xs" c="dimmed">
              Output settings
            </Text>
            <TextInput
              label="Custom filename"
              placeholder="my-proposal-compliance-matrix"
              description="Optional name for output files"
              value={customFilename}
              onChange={(e) => {
                setCustomFilename(e.target.value);
                handleChange();
              }}
            />
          </Box>

          <Divider />

          {/* Proposal Generation Options */}
          <Box>
            <Text size="sm" fw={500} mb="sm" c="dimmed">
              Proposal generation
            </Text>
            <Stack gap="sm">
              <Switch
                label="Generate proposal document"
                description="Auto-generate a Word document from extracted requirements"
                checked={generateProposal}
                onChange={(e) => {
                  setGenerateProposal(e.currentTarget.checked);
                  handleChange();
                }}
                color="cyan"
              />
              {generateProposal && (
                <Switch
                  label="Enhanced two-stage writer"
                  description="Higher quality output using theme analysis (slower)"
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
          </Box>
        </Stack>
      </Card>

      {/* Documents Card */}
      <Card padding="lg">
        <Card.Section withBorder inheritPadding py="sm">
          <Group gap="xs">
            <IconFolder size={18} color="var(--mantine-color-cyan-6)" />
            <Text fw={600} size="sm" c="navy.7">
              Documents
            </Text>
          </Group>
        </Card.Section>

        <Box mt="md">
          {useHighergov ? (
            <Stack gap="md">
              <Text size="sm" c="dimmed">
                Enter your HigherGov opportunity ID to automatically fetch documents.
              </Text>
              <TextInput
                label="Opportunity ID"
                placeholder="e.g., abc123xyz or SAM notice ID"
                description="From HigherGov or SAM.gov"
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
            <FileUpload />
          )}
        </Box>
      </Card>
    </Stack>
  );
}
