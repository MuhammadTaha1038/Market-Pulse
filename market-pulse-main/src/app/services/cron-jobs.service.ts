import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../enviornments/environment';

/**
 * Cron Job Interface - Represents a scheduled automation job
 */
export interface CronJob {
  id?: number;
  name: string;
  description?: string;
  schedule_type: 'cron' | 'interval' | 'date';
  schedule_config: string | object;
  processing_type: 'automatic' | 'manual';
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
  last_run?: string;
  next_run?: string;
}

/**
 * Cron Job Response - API response when creating/updating jobs
 */
export interface CronJobResponse {
  message: string;
  job: CronJob;
}

/**
 * Cron Jobs List Response - API response for listing all jobs
 */
export interface CronJobsListResponse {
  jobs: CronJob[];
  count: number;
}

/**
 * Execution Log - Record of job execution
 */
export interface ExecutionLog {
  id: number;
  job_id: number;
  job_name: string;
  execution_time: string;
  status: 'success' | 'failed';
  duration: number;
  rows_fetched?: number;
  rows_filtered?: number;
  rows_processed?: number;
  error_message?: string;
}

/**
 * Execution Logs Response - List of execution logs
 */
export interface ExecutionLogsResponse {
  logs: ExecutionLog[];
  count: number;
}

/**
 * Trigger Response - Response when manually triggering a job
 */
export interface TriggerResponse {
  message: string;
  execution: ExecutionLog;
}

/**
 * Schedule Examples Response - Example schedule formats
 */
export interface ScheduleExamplesResponse {
  cron: Array<{
    expression: string;
    description: string;
  }>;
  interval: Array<{
    config: object;
    description: string;
  }>;
  date: Array<{
    format: string;
    example: string;
    description: string;
  }>;
}

/**
 * Cron Jobs Service - Manages scheduled automation jobs
 * 
 * This service provides all operations for the Cron Jobs system:
 * - Create, read, update, delete jobs
 * - Toggle jobs on/off
 * - Manually trigger jobs
 * - View execution logs
 * - Get schedule format examples
 */
@Injectable({
  providedIn: 'root'
})
export class CronJobsService {
  // Backend prefix is /api/cron, then we append /jobs for job operations
  private baseUrl = `${environment.baseURL}${environment.apiPrefix}${environment.endpoints.cronJobs}/jobs`;
  // Logs are at /api/cron/logs, not /api/cron/jobs/logs
  private logsUrl = `${environment.baseURL}${environment.apiPrefix}${environment.endpoints.cronJobs}/logs`;

  constructor(private http: HttpClient) {}

  /**
   * Get all cron jobs
   * @returns Observable of jobs list with count
   */
  getAllJobs(): Observable<CronJobsListResponse> {
    return this.http.get<CronJobsListResponse>(this.baseUrl);
  }

  /**
   * Get single job by ID
   * @param id - Job ID
   * @returns Observable of single job
   */
  getJobById(id: number): Observable<CronJob> {
    return this.http.get<CronJob>(`${this.baseUrl}/${id}`);
  }

  /**
   * Create new cron job
   * @param job - Job data (without ID)
   * @returns Observable of created job response
   */
  createJob(job: Omit<CronJob, 'id' | 'created_at' | 'updated_at'>): Observable<CronJobResponse> {
    return this.http.post<CronJobResponse>(this.baseUrl, job);
  }

  /**
   * Update existing job
   * @param id - Job ID
   * @param job - Updated job data
   * @returns Observable of updated job response
   */
  updateJob(id: number, job: Partial<CronJob>): Observable<CronJobResponse> {
    return this.http.put<CronJobResponse>(`${this.baseUrl}/${id}`, job);
  }

  /**
   * Delete job
   * @param id - Job ID
   * @returns Observable of delete confirmation
   */
  deleteJob(id: number): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.baseUrl}/${id}`);
  }

  /**
   * Toggle job active status
   * @param id - Job ID
   * @returns Observable of updated job
   */
  toggleJob(id: number): Observable<CronJobResponse> {
    return this.http.post<CronJobResponse>(`${this.baseUrl}/${id}/toggle`, {});
  }

  /**
   * Manually trigger job execution
   * @param id - Job ID
   * @param override - If true, cancels next scheduled run. If false, keeps scheduled run.
   * @returns Observable of execution result
   */
  triggerJob(id: number, override: boolean = false): Observable<TriggerResponse> {
    return this.http.post<TriggerResponse>(`${this.baseUrl}/${id}/trigger?override=${override}`, {});
  }

  /**
   * Get execution logs for all jobs
   * @param limit - Optional limit for number of logs
   * @returns Observable of execution logs
   */
  getExecutionLogs(limit?: number): Observable<ExecutionLogsResponse> {
    let params = new HttpParams();
    if (limit) {
      params = params.set('limit', limit.toString());
    }
    return this.http.get<ExecutionLogsResponse>(this.logsUrl, { params });
  }

  /**
   * Get execution logs for specific job
   * @param jobId - Job ID
   * @param limit - Optional limit for number of logs
   * @returns Observable of job-specific logs
   */
  getJobLogs(jobId: number, limit?: number): Observable<ExecutionLogsResponse> {
    let params = new HttpParams();
    if (limit) {
      params = params.set('limit', limit.toString());
    }
    return this.http.get<ExecutionLogsResponse>(`${this.logsUrl}/${jobId}`, { params });
  }

  /**
   * Get schedule format examples
   * @returns Observable of example schedules
   */
  getScheduleExamples(): Observable<ScheduleExamplesResponse> {
    return this.http.post<ScheduleExamplesResponse>(`${this.baseUrl}/schedule/examples`, {});
  }

  /**
   * Get next run time for a job
   * @param id - Job ID
   * @returns Observable of next run information
   */
  getNextRun(id: number): Observable<{ next_run: string; next_run_timestamp: string }> {
    return this.http.get<{ next_run: string; next_run_timestamp: string }>(`${this.baseUrl}/next-run/${id}`);
  }
}
