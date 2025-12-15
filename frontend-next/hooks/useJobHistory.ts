import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { JobHistoryItem, JobStatus } from '@/lib/types';

interface JobHistoryState {
  jobs: JobHistoryItem[];
  currentJobId: string | null;
  blobUrls: string[];
  addJob: (job: JobHistoryItem) => void;
  updateJobStatus: (jobId: string, status: JobStatus, fileCount?: number) => void;
  setCurrentJobId: (jobId: string | null) => void;
  setBlobUrls: (urls: string[]) => void;
  clearBlobUrls: () => void;
  clearCurrentJob: () => void;
}

export const useJobHistory = create<JobHistoryState>()(
  persist(
    (set) => ({
      jobs: [],
      currentJobId: null,
      blobUrls: [],
      
      addJob: (job) =>
        set((state) => ({
          jobs: [...state.jobs.slice(-9), job], // Keep last 10 jobs
        })),
      
      updateJobStatus: (jobId, status, fileCount) =>
        set((state) => ({
          jobs: state.jobs.map((job) =>
            job.job_id === jobId
              ? { ...job, status, file_count: fileCount ?? job.file_count }
              : job
          ),
        })),
      
      setCurrentJobId: (jobId) => set({ currentJobId: jobId }),
      
      setBlobUrls: (urls) => set({ blobUrls: urls }),
      
      clearBlobUrls: () => set({ blobUrls: [] }),
      
      clearCurrentJob: () => set({ currentJobId: null, blobUrls: [] }),
    }),
    {
      name: 'job-history-storage',
      partialize: (state) => ({
        jobs: state.jobs,
      }),
    }
  )
);

