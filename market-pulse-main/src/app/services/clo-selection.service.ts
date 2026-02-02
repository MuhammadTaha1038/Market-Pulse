import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../enviornments/environment';
export interface UserCLOSelection {
  cloId: string;
  cloName: string;
  mainCLO: string;
  visibleColumns: string[];
  selectedAt: Date;
}

@Injectable({
  providedIn: 'root'
})
export class CLOSelectionService {
  private readonly STORAGE_KEY = 'user_clo_selection';
  private selectionSubject = new BehaviorSubject<UserCLOSelection | null>(this.loadFromStorage());
  private baseURL = environment.baseURL;

  constructor(private http: HttpClient) {}

  /**
   * Get the current CLO selection as observable
   */
  getSelection(): Observable<UserCLOSelection | null> {
    return this.selectionSubject.asObservable();
  }

  /**
   * Get the current CLO selection value
   */
  getCurrentSelection(): UserCLOSelection | null {
    return this.selectionSubject.value;
  }

  /**
   * Set user's CLO selection
   */
  setSelection(selection: UserCLOSelection): void {
    this.selectionSubject.next(selection);
    this.saveToStorage(selection);
  }

  /**
   * Clear the selection (logout)
   */
  clearSelection(): void {
    this.selectionSubject.next(null);
    localStorage.removeItem(this.STORAGE_KEY);
  }

  /**
   * Check if user has made a selection
   */
  hasSelection(): boolean {
    return this.selectionSubject.value !== null;
  }

  /**
   * Get visible columns for current selection
   */
  getVisibleColumns(): string[] {
    const selection = this.selectionSubject.value;
    return selection ? selection.visibleColumns : [];
  }

  /**
   * Refresh visible columns from backend
   * Call this to get the latest column configuration after CLO mappings are updated
   */
  async refreshColumnsFromBackend(): Promise<void> {
    const currentSelection = this.getCurrentSelection();
    if (!currentSelection) {
      console.warn('⚠️ No CLO selection found to refresh');
      return;
    }

    try {
      console.log('🔄 Refreshing CLO columns from backend for:', currentSelection.cloId);
      
      const response: any = await this.http.get(
        `${this.baseURL}/api/clo-mappings/user-columns/${currentSelection.cloId}`
      ).toPromise();

      if (response && response.visible_columns) {
        // Update with fresh columns from backend
        const updatedSelection = {
          ...currentSelection,
          visibleColumns: response.visible_columns,
          selectedAt: new Date() // Update timestamp to mark as refreshed
        };
        
        this.setSelection(updatedSelection);
        console.log('✅ CLO columns refreshed successfully:', response.visible_columns);
      } else {
        console.warn('⚠️ No visible_columns returned from backend');
      }
    } catch (error) {
      console.error('❌ Failed to refresh CLO columns from backend:', error);
      // Don't throw - allow app to continue with cached data
    }
  }

  private loadFromStorage(): UserCLOSelection | null {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        // Convert date string back to Date object
        parsed.selectedAt = new Date(parsed.selectedAt);
        return parsed;
      }
    } catch (error) {
      console.error('Error loading CLO selection from storage:', error);
    }
    return null;
  }

  private saveToStorage(selection: UserCLOSelection): void {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(selection));
    } catch (error) {
      console.error('Error saving CLO selection to storage:', error);
    }
  }
}
