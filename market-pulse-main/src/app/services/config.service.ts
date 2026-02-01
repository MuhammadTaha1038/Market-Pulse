import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../enviornments/environment';

/**
 * Column Configuration Service
 * Fetches dynamic column configuration from the backend API
 */
@Injectable({
  providedIn: 'root'
})
export class ConfigService {
  private baseUrl = environment.baseURL + environment.apiPrefix;

  constructor(private http: HttpClient) {}

  /**
   * Get all available columns
   */
  getAllColumns(): Observable<string[]> {
    return this.http.get<any>(`${this.baseUrl}/config/columns`).pipe(
      map(response => {
        if (response.columns && Array.isArray(response.columns)) {
          // Extract display_name from each column object
          return response.columns.map((col: any) => col.display_name || col.oracle_name || '');
        }
        return [];
      })
    );
  }

  /**
   * Get required columns for validation
   */
  getRequiredColumns(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/config/columns/required`);
  }

  /**
   * Update column configuration
   */
  updateColumns(columns: { required: string[], optional: string[] }): Observable<any> {
    return this.http.put(`${this.baseUrl}/config/columns`, columns);
  }
}
