import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../enviornments/environment';

/**
 * Upload History Interface - Record of manual file upload
 */
export interface UploadHistory {
  id: number;
  filename: string;
  upload_date: string;
  uploaded_by: string;
  rows_processed: number;
  status: 'success' | 'failed';
  processing_type: 'manual' | 'automatic';
  file_path: string;
  error_message?: string;
}

/**
 * Upload Response - API response when uploading file
 */
export interface UploadResponse {
  success: boolean;
  upload_id: number;
  filename?: string;
  rows_uploaded?: number;
  rows_valid?: number;
  rows_processed?: number;
  parsing_errors?: string[];
  validation_errors?: string[];
  error?: string;
  duration_seconds?: number;
  message?: string;  // Keep for backward compatibility
  upload?: UploadHistory;  // Keep for backward compatibility
}

/**
 * Upload History List Response - List of all uploads
 */
export interface UploadHistoryListResponse {
  uploads: UploadHistory[];
  count: number;
}

/**
 * Upload Statistics Response - Statistics about uploads
 */
export interface UploadStatsResponse {
  total_uploads: number;
  successful_uploads: number;
  failed_uploads: number;
  total_rows_processed: number;
  last_upload_date?: string;
  average_rows_per_upload: number;
}

/**
 * Template Info Response - Information about Excel template
 */
export interface TemplateInfoResponse {
  required_columns: string[];
  file_format: string;
  instructions: string;
  example_data: any[];
}

/**
 * Manual Upload Service - Manages manual data file uploads
 * 
 * This service provides all operations for manual data uploads:
 * - Upload Excel files
 * - View upload history
 * - Get upload statistics
 * - Get template information
 * - Delete upload records
 */
@Injectable({
  providedIn: 'root'
})
export class ManualUploadService {
  private baseUrl = `${environment.baseURL}${environment.apiPrefix}${environment.endpoints.manualUpload}`;

  constructor(private http: HttpClient) {}

  /**
   * Upload Excel file
   * @param file - Excel file to upload
   * @param processingType - Type of processing ('manual' or 'automatic')
   * @returns Observable of upload response
   */
  uploadFile(file: File, processingType: 'manual' | 'automatic' = 'manual'): Observable<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('processing_type', processingType);

    return this.http.post<UploadResponse>(`${this.baseUrl}/upload`, formData);
  }

  /**
   * Get upload history
   * @param limit - Optional limit for number of records
   * @returns Observable of upload history list
   */
  getUploadHistory(limit?: number): Observable<UploadHistoryListResponse> {
    let params = new HttpParams();
    if (limit) {
      params = params.set('limit', limit.toString());
    }
    return this.http.get<UploadHistoryListResponse>(`${this.baseUrl}/history`, { params });
  }

  /**
   * Get single upload record by ID
   * @param id - Upload ID
   * @returns Observable of single upload record
   */
  getUploadById(id: number): Observable<UploadHistory> {
    return this.http.get<UploadHistory>(`${this.baseUrl}/history/${id}`);
  }

  /**
   * Delete upload record
   * @param id - Upload ID
   * @returns Observable of delete confirmation
   */
  deleteUpload(id: number): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.baseUrl}/history/${id}`);
  }

  /**
   * Get upload statistics
   * @returns Observable of statistics
   */
  getUploadStats(): Observable<UploadStatsResponse> {
    return this.http.get<UploadStatsResponse>(`${this.baseUrl}/stats`);
  }

  /**
   * Get Excel template information
   * @returns Observable of template info
   */
  getTemplateInfo(): Observable<TemplateInfoResponse> {
    return this.http.get<TemplateInfoResponse>(`${this.baseUrl}/template-info`);
  }
}
