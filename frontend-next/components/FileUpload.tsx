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
  Skeleton,
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
  if (ext === 'pdf') return <IconFileTypePdf size={18} color="var(--mantine-color-red-5)" />;
  if (['doc', 'docx'].includes(ext || '')) return <IconFileTypeDocx size={18} color="var(--mantine-color-blue-5)" />;
  if (['xls', 'xlsx'].includes(ext || '')) return <IconFileSpreadsheet size={18} color="var(--mantine-color-green-5)" />;
  return <IconFile size={18} />;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function UploadingSkeleton() {
  return (
    <Stack gap="sm">
      <Skeleton height={120} radius="md" />
      <Group justify="space-between">
        <Skeleton height={14} width={120} />
        <Skeleton height={20} width={80} radius="sm" />
      </Group>
      <Skeleton height={36} radius="md" />
    </Stack>
  );
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
        message: `${result.blob_urls.length} file(s) uploaded`,
        color: 'teal',
        icon: <IconCheck size={16} />,
      });
    } catch (error) {
      notifications.show({
        title: 'Upload Failed',
        message: error instanceof Error ? error.message : 'Failed to upload files',
        color: 'red',
        icon: <IconX size={16} />,
      });
    }
  };

  // Show skeleton during upload
  if (uploadMutation.isPending) {
    return <UploadingSkeleton />;
  }

  return (
    <Stack gap="sm">
      <Dropzone
        onDrop={handleDrop}
        accept={ACCEPTED_MIME_TYPES}
        disabled={isUploaded}
        radius="md"
        style={{
          borderColor: isUploaded ? 'var(--mantine-color-teal-5)' : undefined,
          backgroundColor: isUploaded ? 'var(--mantine-color-teal-0)' : undefined,
        }}
      >
        <Group justify="center" gap="lg" mih={100} style={{ pointerEvents: 'none' }}>
          <Dropzone.Accept>
            <IconUpload size={40} stroke={1.5} color="var(--mantine-color-cyan-5)" />
          </Dropzone.Accept>
          <Dropzone.Reject>
            <IconX size={40} stroke={1.5} color="var(--mantine-color-red-5)" />
          </Dropzone.Reject>
          <Dropzone.Idle>
            {isUploaded ? (
              <IconCheck size={40} stroke={1.5} color="var(--mantine-color-teal-5)" />
            ) : (
              <IconCloudUpload size={40} stroke={1.5} color="var(--mantine-color-dimmed)" />
            )}
          </Dropzone.Idle>

          <Box>
            <Text size="sm" fw={500}>
              {isUploaded
                ? 'Files uploaded successfully'
                : 'Drag documents here or click to browse'}
            </Text>
            <Text size="xs" c="dimmed" mt={4}>
              {isUploaded
                ? `${blobUrls.length} file(s) ready`
                : 'PDF, Word, Excel supported'}
            </Text>
          </Box>
        </Group>
      </Dropzone>

      {files.length > 0 && !isUploaded && (
        <>
          <Paper p="sm" withBorder radius="md">
            <Text size="xs" fw={500} c="dimmed" mb="xs">
              Selected ({files.length})
            </Text>
            <Stack gap="xs">
              {files.map((file, index) => (
                <Group key={`${file.name}-${index}`} justify="space-between" wrap="nowrap">
                  <Group gap="xs" style={{ overflow: 'hidden', flex: 1 }}>
                    {getFileIcon(file.name)}
                    <Text size="xs" truncate style={{ flex: 1 }}>
                      {file.name}
                    </Text>
                  </Group>
                  <Group gap="xs" wrap="nowrap">
                    <Text size="xs" c="dimmed" className="font-mono">
                      {formatFileSize(file.size)}
                    </Text>
                    <ActionIcon
                      variant="subtle"
                      color="gray"
                      size="xs"
                      onClick={() => removeFile(index)}
                    >
                      <IconX size={14} />
                    </ActionIcon>
                  </Group>
                </Group>
              ))}
            </Stack>
          </Paper>

          <Button
            leftSection={<IconCloudUpload size={16} />}
            onClick={handleUpload}
            loading={uploadMutation.isPending}
            disabled={files.length === 0}
            color="cyan"
            size="sm"
            fullWidth
          >
            Upload to Cloud
          </Button>
        </>
      )}

      {isUploaded && (
        <Group justify="center">
          <Badge
            size="md"
            color="teal"
            variant="light"
            leftSection={<IconCheck size={12} />}
          >
            {blobUrls.length} file(s) ready
          </Badge>
        </Group>
      )}
    </Stack>
  );
}
