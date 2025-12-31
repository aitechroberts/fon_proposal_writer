// API Types matching backend models

export interface HealthResponse {
  status: string;
  version?: string;
}

export interface JobSubmission {
  opportunity_id: string;
  custom_filename?: string;
  use_highergov: boolean;
  blob_urls: string[];
  generate_proposal: boolean;
  use_two_stage_writer: boolean;
}

export interface JobSubmitResponse {
  job_id: string;
  status: string;
  message: string;
}

export type JobStatus = 'queued' | 'running' | 'completed' | 'failed';

export interface JobStatusResponse {
  job_id: string;
  status: JobStatus;
  progress: number;
  message: string;
  error_message?: string;
}

export interface JobResultsResponse {
  job_id: string;
  status: JobStatus;
  file_count: number;
  requirements_sas_url?: string;
  clean_proposal_sas_url?: string;
  cited_proposal_sas_url?: string;
  zip_sas_url?: string;
  error_message?: string;
}

export interface FileUploadResponse {
  blob_urls: string[];
  message: string;
}

// Frontend-specific types

export interface JobHistoryItem {
  job_id: string;
  status: JobStatus;
  created_at: string;
  opportunity_id?: string;
  file_count?: number;
}

export interface UploadedFile {
  name: string;
  size: number;
  file: File;
}

