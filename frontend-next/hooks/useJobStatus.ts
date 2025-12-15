import { useQuery } from '@tanstack/react-query';
import { getJobStatus, getJobResults } from '@/lib/api';
import { JobStatusResponse, JobResultsResponse } from '@/lib/types';

export function useJobStatus(jobId: string | null) {
  return useQuery<JobStatusResponse>({
    queryKey: ['jobStatus', jobId],
    queryFn: () => getJobStatus(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      // Stop polling when job is completed or failed
      const status = query.state.data?.status;
      if (status === 'completed' || status === 'failed') {
        return false;
      }
      return 2000; // Poll every 2 seconds
    },
  });
}

export function useJobResults(jobId: string | null, enabled: boolean = false) {
  return useQuery<JobResultsResponse>({
    queryKey: ['jobResults', jobId],
    queryFn: () => getJobResults(jobId!),
    enabled: enabled && !!jobId,
    staleTime: Infinity, // Results don't change once fetched
  });
}

