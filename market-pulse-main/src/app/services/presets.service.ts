import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../enviornments/environment';

export interface PresetCondition {
  column: string;
  operator: string;
  value: string;
  value2?: string;
}

export interface Preset {
  id?: number;
  name: string;
  description?: string;
  conditions: PresetCondition[];
  created_at?: string;
  created_by?: string;
  updated_at?: string;
}

@Injectable({
  providedIn: 'root'
})
export class PresetsService {
  private baseUrl = environment.baseURL + environment.apiPrefix + '/presets';

  constructor(private http: HttpClient) {}

  /**
   * Get all presets
   */
  getAllPresets(): Observable<{ presets: Preset[]; count: number }> {
    return this.http.get<{ presets: Preset[]; count: number }>(this.baseUrl);
  }

  /**
   * Get single preset by ID
   */
  getPreset(id: number): Observable<{ preset: Preset }> {
    return this.http.get<{ preset: Preset }>(`${this.baseUrl}/${id}`);
  }

  /**
   * Create new preset
   */
  createPreset(preset: Preset): Observable<{ message: string; preset: Preset }> {
    return this.http.post<{ message: string; preset: Preset }>(this.baseUrl, preset);
  }

  /**
   * Update existing preset
   */
  updatePreset(id: number, preset: Partial<Preset>): Observable<{ message: string; preset: Preset }> {
    return this.http.put<{ message: string; preset: Preset }>(`${this.baseUrl}/${id}`, preset);
  }

  /**
   * Delete preset
   */
  deletePreset(id: number): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.baseUrl}/${id}`);
  }

  /**
   * Apply preset filters to data
   */
  applyPreset(id: number, data: any[]): Observable<{ total_rows: number; filtered_rows: number; data: any[] }> {
    return this.http.post<{ total_rows: number; filtered_rows: number; data: any[] }>(
      `${this.baseUrl}/${id}/apply`,
      { data }
    );
  }

  /**
   * Get preset statistics
   */
  getStats(): Observable<{ total_presets: number; most_recent: Preset }> {
    return this.http.get<{ total_presets: number; most_recent: Preset }>(`${this.baseUrl}/stats`);
  }
}
