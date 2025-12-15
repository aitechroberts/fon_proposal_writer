import { useMutation } from '@tanstack/react-query';
import { submitJob } from '@/lib/api';
import { JobSubmission, JobSubmitResponse } from '@/lib/types';

export function useJobSubmit() {
  return useMutation<JobSubmitResponse, Error, JobSubmission>({
    mutationFn: submitJob,
  });
}

