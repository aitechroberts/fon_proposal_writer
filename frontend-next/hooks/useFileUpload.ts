import { useMutation } from '@tanstack/react-query';
import { uploadFiles } from '@/lib/api';
import { FileUploadResponse } from '@/lib/types';

export function useFileUpload() {
  return useMutation<FileUploadResponse, Error, File[]>({
    mutationFn: uploadFiles,
  });
}

