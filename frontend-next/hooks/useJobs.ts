'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

interface JobListItem {
  id: string;
  job_name: string;
  created_at: string;
  completed_at: string | null;
  requirements_sas_url: string | null;
  clean_proposal_sas_url: string | null;
  cited_proposal_sas_url: string | null;
  zip_sas_url: string | null;
  file_count: number;
}

interface JobListResponse {
  jobs: JobListItem[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

interface UseJobsParams {
  page?: number;
  limit?: number;
  search?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

async function fetchJobs(params: UseJobsParams): Promise<JobListResponse> {
  const queryParams = new URLSearchParams();
  
  if (params.page) queryParams.set('page', params.page.toString());
  if (params.limit) queryParams.set('limit', params.limit.toString());
  if (params.search) queryParams.set('search', params.search);
  if (params.sortBy) queryParams.set('sort_by', params.sortBy);
  if (params.sortOrder) queryParams.set('sort_order', params.sortOrder);
  
  const url = `/jobs${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  const response = await api.get<JobListResponse>(url);
  return response.data;
}

export function useJobs(params: UseJobsParams = {}) {
  return useQuery({
    queryKey: ['jobs', params],
    queryFn: () => fetchJobs(params),
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: true,
  });
}

