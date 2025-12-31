import axios, { AxiosInstance } from 'axios';
import {
  HealthResponse,
  JobSubmission,
  JobSubmitResponse,
  JobStatusResponse,
  JobResultsResponse,
  FileUploadResponse,
} from './types';

// API base URL from environment or default to localhost
const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Health check
export async function checkHealth(): Promise<HealthResponse> {
  const response = await apiClient.get<HealthResponse>('/health', {
    timeout: 35000,
  });
  return response.data;
}

// File upload
export async function uploadFiles(files: File[]): Promise<FileUploadResponse> {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });

  const response = await apiClient.post<FileUploadResponse>('/files/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 120000, // 2 minute timeout for large files
  });

  return response.data;
}

// Submit job
export async function submitJob(job: JobSubmission): Promise<JobSubmitResponse> {
  const response = await apiClient.post<JobSubmitResponse>('/jobs/submit', job);
  return response.data;
}

// Get job status
export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  const response = await apiClient.get<JobStatusResponse>(`/jobs/${jobId}/status`, {
    timeout: 10000,
  });
  return response.data;
}

// Get job results
export async function getJobResults(jobId: string): Promise<JobResultsResponse> {
  const response = await apiClient.get<JobResultsResponse>(`/jobs/${jobId}/results`, {
    timeout: 10000,
  });
  return response.data;
}

// Export the API client for custom requests if needed
export { apiClient };

// Alias for convenience (used by useJobs hook)
export const api = apiClient;

