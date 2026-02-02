import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../enviornments/environment';

// Response Models
export interface TriggerAutomationResponse {
  success: boolean;
  job_id?: number;
  job_name?: string;
  execution_log_id?: number;
  message?: string;
  original_count?: number;
  excluded_count?: number;
  processed_count?: number;
  rules_applied?: number;
  output_file?: string;
  duration_seconds?: number;
  error?: string;
}

export interface OverrideRunResponse {
  success: boolean;
  message?: string;
  processed_count?: number;
  output_file?: string;
  duration_seconds?: number;
  error?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AutomationService {
  private baseURL = environment.baseURL;

  constructor(private http: HttpClient) {}

  /**
   * Trigger manual run of automation (with rules)
   * Same as cron job but triggered manually
   */
  triggerAutomation(jobId?: number): Observable<TriggerAutomationResponse> {
    console.log('🚀 Triggering automation...' + (jobId ? ` for job ${jobId}` : ''));

    const endpoint = jobId 
      ? `${this.baseURL}/api/cron/jobs/${jobId}/trigger`
      : `${this.baseURL}/api/cron/trigger-default`;

    return this.http.post<TriggerAutomationResponse>(endpoint, {});
  }

  /**
   * Override and run - process without rules
   * Use case: Emergency processing, bypass all exclusion rules
   */
  overrideAndRun(): Observable<OverrideRunResponse> {
    console.log('⚡ Override and run - bypassing rules...');

    return this.http.post<OverrideRunResponse>(
      `${this.baseURL}/api/automation/override-run`,
      {}
    );
  }

  /**
   * Refresh colors from source
   * Fetch latest data from external sources and process
   */
  refreshColors(): Observable<any> {
    console.log('🔄 Refreshing colors from source...');

    return this.http.post(
      `${this.baseURL}/api/automation/refresh`,
      {}
    );
  }

  /**
   * Get automation status
   */
  getAutomationStatus(): Observable<any> {
    return this.http.get(`${this.baseURL}/api/automation/status`);
  }

  /**
   * Stop running automation
   */
  stopAutomation(): Observable<any> {
    return this.http.post(`${this.baseURL}/api/automation/stop`, {});
  }
}
