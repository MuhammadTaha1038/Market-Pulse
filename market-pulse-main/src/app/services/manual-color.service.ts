import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../enviornments/environment';

// Request Models
export interface DeleteRowsRequest {
  session_id: string;
  row_ids: number[];
}

export interface ApplyRulesRequest {
  session_id: string;
  rule_ids: number[];
}

export interface SaveRequest {
  session_id: string;
  user_id: number;
}

// Response Models
export interface ImportResponse {
  success: boolean;
  session_id?: string;
  filename?: string;
  rows_imported?: number;
  rows_valid?: number;
  parsing_errors?: string[];
  sorted_preview?: any[];
  statistics?: {
    total_rows: number;
    valid_rows: number;
    invalid_rows: number;
    deleted_rows?: number;
    rules_applied_count?: number;
  };
  error?: string;
  duration_seconds?: number;
}

export interface PreviewResponse {
  success: boolean;
  session_id: string;
  data: any[];
  statistics?: {
    total_rows: number;
    deleted_rows?: number;
    rules_applied_count?: number;
  };
  error?: string;
}

export interface DeleteRowsResponse {
  success: boolean;
  deleted_count: number;
  remaining_count: number;
  updated_preview: any[];
  statistics?: any;
  error?: string;
}

export interface ApplyRulesResponse {
  success: boolean;
  rules_applied: number;
  excluded_count: number;
  remaining_count: number;
  updated_preview: any[];
  statistics?: any;
  error?: string;
}

export interface SaveResponse {
  success: boolean;
  rows_saved: number;
  output_file?: string;
  message?: string;
  error?: string;
  duration_seconds?: number;
}

export interface SessionSummary {
  session_id: string;
  created_at?: string;
  updated_at?: string;
  filename?: string;
  status?: string;
  rows_count: number;
}

export interface SessionsResponse {
  success: boolean;
  sessions: SessionSummary[];
  count: number;
}

@Injectable({
  providedIn: 'root'
})
export class ManualColorService {
  private baseURL = environment.baseURL;
  private apiPath = '/api/manual-color';

  constructor(private http: HttpClient) {}

  /**
   * Step 1: Import Excel file for manual color processing
   * Returns sorted preview with ranking applied
   */
  importExcel(file: File, userId: number = 1): Observable<ImportResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', userId.toString());

    console.log('📤 Uploading Excel for manual color processing:', file.name);

    return this.http.post<ImportResponse>(
      `${this.baseURL}${this.apiPath}/import`,
      formData
    );
  }

  /**
   * Get current preview data for a session
   * Shows currently filtered data after any deletions or rule applications
   */
  getPreview(sessionId: string): Observable<PreviewResponse> {
    console.log('🔍 Fetching preview for session:', sessionId);

    return this.http.get<PreviewResponse>(
      `${this.baseURL}${this.apiPath}/preview/${sessionId}`
    );
  }

  /**
   * Delete selected rows from preview
   * User can select rows in UI and delete them
   */
  deleteRows(request: DeleteRowsRequest): Observable<DeleteRowsResponse> {
    console.log('🗑️ Deleting rows:', request.row_ids.length, 'rows from session:', request.session_id);

    return this.http.post<DeleteRowsResponse>(
      `${this.baseURL}${this.apiPath}/delete-rows`,
      request
    );
  }

  /**
   * Apply selected rules to manual color data
   * Rules are fetched from Rules module (/api/rules)
   */
  applyRules(request: ApplyRulesRequest): Observable<ApplyRulesResponse> {
    console.log('⚙️ Applying rules:', request.rule_ids, 'to session:', request.session_id);

    return this.http.post<ApplyRulesResponse>(
      `${this.baseURL}${this.apiPath}/apply-rules`,
      request
    );
  }

  /**
   * Save processed manual colors to output file (S3 in future)
   * Final step after user reviews preview
   */
  saveManualColors(request: SaveRequest): Observable<SaveResponse> {
    console.log('💾 Saving manual colors for session:', request.session_id);

    return this.http.post<SaveResponse>(
      `${this.baseURL}${this.apiPath}/save`,
      request
    );
  }

  /**
   * Get list of active manual color sessions
   */
  getSessions(userId?: number): Observable<SessionsResponse> {
    let url = `${this.baseURL}${this.apiPath}/sessions`;
    
    if (userId !== undefined) {
      url += `?user_id=${userId}`;
    }

    return this.http.get<SessionsResponse>(url);
  }

  /**
   * Clean up old session files
   */
  cleanupSessions(days: number = 1): Observable<any> {
    return this.http.delete(
      `${this.baseURL}${this.apiPath}/cleanup`,
      { params: { days: days.toString() } }
    );
  }

  /**
   * Health check
   */
  healthCheck(): Observable<any> {
    return this.http.get(`${this.baseURL}${this.apiPath}/health`);
  }
}
