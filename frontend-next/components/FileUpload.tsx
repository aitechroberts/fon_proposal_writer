'use client';

import { useState } from 'react';
import {
  Box,
  Text,
  Group,
  Stack,
  Button,
  Paper,
  Badge,
  ActionIcon,
  Progress,
} from '@mantine/core';
import { Dropzone, FileWithPath, MIME_TYPES } from '@mantine/dropzone';
import {
  IconUpload,
  IconFile,
  IconX,
  IconCheck,
  IconCloudUpload,
  IconFileTypePdf,
  IconFileTypeDocx,
  IconFileSpreadsheet,
} from '@tabler/icons-react';
import { useFileUpload, useJobHistory } from '@/hooks';
import { notifications } from '@mantine/notifications';

const ACCEPTED_MIME_TYPES = [
  MIME_TYPES.pdf,
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
];

function getFileIcon(filename: string) {
  const ext = filename.split('.').pop()?.toLowerCase();
  if (ext === 'pdf') return <IconFileTypePdf size={20} />;
  if (['doc', 'docx'].includes(ext || '')) return <IconFileTypeDocx size={20} />;
  if (['xls', 'xlsx'].includes(ext || '')) return <IconFileSpreadsheet size={20} />;
  return <IconFile size={20} />;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export function FileUpload() {
  const [files, setFiles] = useState<FileWithPath[]>([]);
  const { blobUrls, setBlobUrls } = useJobHistory();
  const uploadMutation = useFileUpload();

  const isUploaded = blobUrls.length > 0;

  const handleDrop = (acceptedFiles: FileWithPath[]) => {
    setFiles((prev) => [...prev, ...acceptedFiles]);
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;

    try {
      const result = await uploadMutation.mutateAsync(files);
      setBlobUrls(result.blob_urls);
      notifications.show({
        title: 'Upload Successful',
        message: `${result.blob_urls.length} file(s) uploaded to cloud storage`,
        color: 'teal',
        icon: <IconCheck size={18} />,
      });
    } catch (error) {
      notifications.show({
        title: 'Upload Failed',
        message: error instanceof Error ? error.message : 'Failed to upload files',
        color: 'red',
        icon: <IconX size={18} />,
      });
    }
  };

  return (
    <Stack gap="md">
      <Dropzone
        onDrop={handleDrop}
        accept={ACCEPTED_MIME_TYPES}
        disabled={isUploaded}
        loading={uploadMutation.isPending}
        style={{
          borderColor: isUploaded ? '#4caf50' : undefined,
          backgroundColor: isUploaded ? '#e8f5e8' : undefined,
        }}
      >
        <Group justify="center" gap="xl" mih={140} style={{ pointerEvents: 'none' }}>
          <Dropzone.Accept>
            <IconUpload size={52} stroke={1.5} color="#00A3E0" />
          </Dropzone.Accept>
          <Dropzone.Reject>
            <IconX size={52} stroke={1.5} color="red" />
          </Dropzone.Reject>
          <Dropzone.Idle>
            {isUploaded ? (
              <IconCheck size={52} stroke={1.5} color="#4caf50" />
            ) : (
              <IconCloudUpload size={52} stroke={1.5} color="#04395E" />
            )}
          </Dropzone.Idle>

          <Box>
            <Text size="lg" fw={600} inline>
              {isUploaded
                ? 'Files uploaded successfully!'
                : 'Drag documents here or click to browse'}
            </Text>
            <Text size="sm" c="dimmed" inline mt={7}>
              {isUploaded
                ? `${blobUrls.length} file(s) ready for processing`
                : 'Accepts PDF, Word (.doc, .docx), and Excel (.xls, .xlsx) files'}
            </Text>
          </Box>
        </Group>
      </Dropzone>

      {files.length > 0 && !isUploaded && (
        <>
          <Paper p="md" withBorder>
            <Text size="sm" fw={600} mb="sm">
              Selected Files ({files.length})
            </Text>
            <Stack gap="xs">
              {files.map((file, index) => (
                <Group key={`${file.name}-${index}`} justify="space-between">
                  <Group gap="sm">
                    {getFileIcon(file.name)}
                    <Text size="sm">{file.name}</Text>
                    <Badge size="sm" variant="light">
                      {formatFileSize(file.size)}
                    </Badge>
                  </Group>
                  <ActionIcon
                    variant="subtle"
                    color="red"
                    size="sm"
                    onClick={() => removeFile(index)}
                  >
                    <IconX size={16} />
                  </ActionIcon>
                </Group>
              ))}
            </Stack>
          </Paper>

          {uploadMutation.isPending && (
            <Progress value={100} animated color="cyan" />
          )}

          <Button
            leftSection={<IconCloudUpload size={18} />}
            onClick={handleUpload}
            loading={uploadMutation.isPending}
            disabled={files.length === 0}
            variant="gradient"
            gradient={{ from: 'cyan', to: 'teal', deg: 90 }}
            size="md"
          >
            Upload to Cloud Storage
          </Button>
        </>
      )}

      {isUploaded && (
        <Badge size="lg" color="teal" variant="light" leftSection={<IconCheck size={14} />}>
          {blobUrls.length} file(s) ready for processing
        </Badge>
      )}
    </Stack>
  );
}

