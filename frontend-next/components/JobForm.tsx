'use client';

import { useState } from 'react';
import {
  Card,
  Text,
  TextInput,
  Switch,
  Stack,
  Group,
  Divider,
  Box,
  Alert,
  Badge,
} from '@mantine/core';
import {
  IconFileUpload,
  IconInfoCircle,
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
  const [opportunityId, setOpportunityId] = useState('');
  const [customFilename, setCustomFilename] = useState('');
  const [generateProposal, setGenerateProposal] = useState(true);
  
  // HigherGov integration not yet completed - always use manual upload
  const useHighergov = false;
  
  // Two-stage writer not yet implemented - always false
  const useTwoStageWriter = false;

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
              <IconPlus size={18} color="var(--mantine-color-fonBlue-5)" />
              <Text fw={600} size="sm" c="charcoal.7">
                Submit New Job
              </Text>
            </Group>
            <Badge variant="light" color="fonBlue" size="sm">
              New
            </Badge>
          </Group>
        </Card.Section>

        <Stack gap="md" mt="md">
          {/* Input Method - Manual Upload Only */}
          <Box>
            <Text size="sm" fw={500} mb="xs" c="charcoal.5">
              Input method
            </Text>
            <Alert
              icon={<IconFileUpload size={16} />}
              color="fonBlue"
              variant="light"
            >
              <Group gap="xs">
                <IconFileUpload size={16} />
                <Text size="sm" fw={500}>Manual File Upload</Text>
              </Group>
            </Alert>
            
            {/* HigherGov integration notice */}
            <Alert
              icon={<IconInfoCircle size={16} />}
              color="gray"
              variant="light"
              mt="xs"
            >
              <Text size="xs" c="charcoal.5">
                HigherGov integration not yet completed. Please use manual upload.
              </Text>
            </Alert>
          </Box>

          {/* 
            HigherGov Selection - COMMENTED OUT - Not yet implemented
            
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
              color="fonBlue"
            />
            
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
          */}

          <Divider />

          {/* Job Name */}
          <Box>
            <Text size="sm" fw={500} mb="xs" c="charcoal.5">
              Job identification
            </Text>
            <TextInput
              label="Job Name"
              placeholder="Enter a name for this job"
              description="Required - used for output files and tracking"
              value={customFilename}
              onChange={(e) => {
                setCustomFilename(e.target.value);
                handleChange();
              }}
              required
              error={customFilename.trim() === "" ? undefined : undefined}
            />
          </Box>

          <Divider />

          {/* Proposal Generation Options */}
          <Box>
            <Text size="sm" fw={500} mb="sm" c="charcoal.5">
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
                color="fonBlue"
              />
              
              {/* 
                Two-Stage Writer - COMMENTED OUT - Not yet implemented/tested
                
                {generateProposal && (
                  <Switch
                    label="Enhanced two-stage writer"
                    description="Higher quality output using theme analysis (slower)"
                    checked={useTwoStageWriter}
                    onChange={(e) => {
                      setUseTwoStageWriter(e.currentTarget.checked);
                      handleChange();
                    }}
                    color="fonBlue"
                    ml="md"
                  />
                )}
              */}
            </Stack>
          </Box>
        </Stack>
      </Card>

      {/* Documents Card */}
      <Card padding="lg">
        <Card.Section withBorder inheritPadding py="sm">
          <Group gap="xs">
            <IconFolder size={18} color="var(--mantine-color-fonBlue-5)" />
            <Text fw={600} size="sm" c="charcoal.7">
              Documents
            </Text>
          </Group>
        </Card.Section>

        <Box mt="md">
          {/* Manual upload only - HigherGov integration not yet completed */}
          <FileUpload />
          
          {/* 
            HigherGov ID Input - COMMENTED OUT - Not yet implemented
            
            {useHighergov ? (
              <Stack gap="md">
                <Text size="sm" c="charcoal.5">
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
          */}
        </Box>
      </Card>
    </Stack>
  );
}
