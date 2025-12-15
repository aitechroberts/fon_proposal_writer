import { useQuery } from '@tanstack/react-query';
import { checkHealth } from '@/lib/api';

export function useBackendHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: checkHealth,
    refetchInterval: 30000, // Check health every 30 seconds
    retry: 2,
    staleTime: 10000,
  });
}

