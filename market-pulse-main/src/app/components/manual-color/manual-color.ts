import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { FileUploadModule } from 'primeng/fileupload';
import { InputTextModule } from 'primeng/inputtext';
import { TagModule } from 'primeng/tag';
import { FormsModule } from '@angular/forms';
import { AutoCompleteModule } from 'primeng/autocomplete';
import { MultiSelectModule } from 'primeng/multiselect';
import { ToastModule } from 'primeng/toast';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { DividerModule } from 'primeng/divider';
import { CheckboxModule } from 'primeng/checkbox';
import { TooltipModule } from 'primeng/tooltip';
import { MessageService } from 'primeng/api';

import { PresetsService, Preset } from '../../services/presets.service';
import { ManualColorService, ImportResponse } from '../../services/manual-color.service';
import { RulesService } from '../../services/rules.service';

interface ColorData {
  messageId: string;
  ticketId: string;
  cusip: string;
  bias: string;
  date: string;
  bid: number;
  mid: number;
  ask: number;
  source: string;
}

@Component({
  selector: 'app-manual-color',
  standalone: true,
  imports: [
    CommonModule,
    TableModule,
    ButtonModule,
    DialogModule,
    FileUploadModule,
    InputTextModule,
    TagModule,
    FormsModule,
    AutoCompleteModule,
    MultiSelectModule,
    ToastModule,
    ProgressSpinnerModule,
    DividerModule,
    CheckboxModule,
    TooltipModule
  ],
  providers: [MessageService],
  templateUrl: './manual-color.html',
  styleUrls: ['./manual-color.css']
})
export class ManualColor implements OnInit {
  searchText = '';
  showImportDialog = false;
  showFilterDialog = false;
  presets: Preset[] = [];
  selectedPreset: Preset | null = null;
  filteredPresets: Preset[] = [];
  
  // Manual Color Processing Session
  sessionId: string | null = null;
  filename: string | null = null;
  previewData: any[] = [];
  selectedRows: any[] = [];
  
  // Statistics
  statistics: any = {
    total_rows: 0,
    valid_rows: 0,
    invalid_rows: 0,
    deleted_rows: 0,
    rules_applied_count: 0
  };
  
  // Loading states
  isUploading: boolean = false;
  isProcessing: boolean = false;
  isSaving: boolean = false;
  
  // Rules
  availableRules: any[] = [];
  selectedRules: any[] = [];
  
  // Display columns
  columns: any[] = [];

  colors: ColorData[] = [];

  constructor(
    private presetsService: PresetsService,
    private manualColorService: ManualColorService,
    private rulesService: RulesService,
    private messageService: MessageService
  ) {}
  
  ngOnInit(): void {
    console.log('🔵 ngOnInit - START');
    console.log('  Current colors:', this.colors.length);
    console.log('  Current sessionId:', this.sessionId);
    
    // Clear any previous data
    this.colors = [];
    this.previewData = [];
    this.sessionId = null;
    this.selectedRows = [];
    this.columns = [];
    
    // Reset statistics
    this.statistics = {
      total_rows: 0,
      valid_rows: 0,
      deleted_rows: 0,
      rules_applied_count: 0
    };
    
    this.loadPresets();
    this.loadRules();
    
    console.log('📋 Manual Color page initialized - ready for import');
    console.log('  Colors after clear:', this.colors.length);
    console.log('🔵 ngOnInit - END');
  }
  
  /**
   * Load available rules
   */
  loadRules(): void {
    this.rulesService.getAllRules().subscribe({
      next: (response: any) => {
        this.availableRules = response.rules || [];
        console.log('✅ Loaded rules:', this.availableRules.length);
      },
      error: (error: any) => {
        console.error('❌ Failed to load rules:', error);
      }
    });
  }

  loadPresets() {
    this.presetsService.getAllPresets().subscribe({
      next: (response) => {
        this.presets = response.presets;
        this.filteredPresets = response.presets;
      },
      error: (error) => console.error('Error loading presets:', error)
    });
  }

  searchPreset(event: any) {
    const query = event.query.toLowerCase();
    this.filteredPresets = this.presets.filter(preset =>
      preset.name.toLowerCase().includes(query)
    );
  }

  openFilterDialog() {
    this.showFilterDialog = true;
  }

  applyPreset() {
    if (!this.selectedPreset || !this.selectedPreset.id) return;
    
    if (this.colors.length === 0) {
      this.messageService.add({
        severity: 'warn',
        summary: 'No Data',
        detail: 'Please import data first before applying presets'
      });
      return;
    }
    
    this.isProcessing = true;
    
    this.presetsService.applyPreset(this.selectedPreset.id, this.colors).subscribe({
      next: (response) => {
        this.isProcessing = false;
        this.colors = response.data;
        this.previewData = response.data;
        
        console.log('✅ Preset applied successfully');
        console.log('  Total rows:', response.total_rows);
        console.log('  Filtered rows:', response.filtered_rows);
        console.log('  Remaining rows:', this.colors.length);
        
        if (response.filtered_rows === 0) {
          this.messageService.add({
            severity: 'warn',
            summary: 'No Matching Rows',
            detail: `Preset filtered out all ${response.total_rows} rows. No data remaining.`
          });
        } else {
          this.messageService.add({
            severity: 'success',
            summary: 'Preset Applied',
            detail: `Filtered ${response.filtered_rows} out of ${response.total_rows} rows`
          });
        }
        
        this.showFilterDialog = false;
      },
      error: (error) => {
        this.isProcessing = false;
        console.error('Error applying preset:', error);
        
        this.messageService.add({
          severity: 'error',
          summary: 'Apply Failed',
          detail: error.error?.detail || 'Failed to apply preset'
        });
      }
    });
  }

  removeAllFilters() {
    this.selectedPreset = null;
    // Reload original data or reset filters
  }

  /**
   * Handle file upload from dialog
   */
  onUpload(event: any) {
    console.log('🔔 onUpload event triggered:', event);
    
    const file = event.files[0];
    
    if (!file) {
      console.warn('⚠️ No file selected');
      return;
    }
    
    console.log('📁 File selected:', file.name, 'Size:', file.size, 'Type:', file.type);
    
    // Validate file type
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      console.error('❌ Invalid file type:', file.name);
      this.messageService.add({
        severity: 'error',
        summary: 'Invalid File',
        detail: 'Please upload an Excel file (.xlsx or .xls)'
      });
      return;
    }
    
    this.uploadFile(file);
  }
  
  /**
   * Upload file to backend for processing
   */
  uploadFile(file: File): void {
    console.log('🟢 uploadFile - START');
    console.log('  File:', file.name, file.size, 'bytes');
    
    this.isUploading = true;
    this.filename = file.name;
    
    console.log('📤 Calling manualColorService.importExcel...');
    console.log('  API will call: POST /api/manual-color/import');
    
    this.manualColorService.importExcel(file, 1).subscribe({
      next: (response: ImportResponse) => {
        this.isUploading = false;
        
        if (response.success && response.session_id) {
          this.sessionId = response.session_id;
          this.previewData = response.sorted_preview || [];
          this.statistics = response.statistics || this.statistics;
          this.statistics.total_rows = response.rows_imported || 0;
          this.statistics.valid_rows = response.rows_valid || 0;
          
          // Extract columns from first data row
          if (this.previewData.length > 0) {
            this.columns = Object.keys(this.previewData[0]).map(key => ({
              field: key,
              header: key.replace(/_/g, ' ').toUpperCase()
            }));
            
            // Update the colors array for display
            this.colors = this.previewData;
          }
          
          this.showImportDialog = false;
          
          this.messageService.add({
            severity: 'success',
            summary: 'Upload Successful',
            detail: `Imported ${response.rows_imported} rows. Sorted preview ready.`
          });
          
          console.log('✅ Import successful. Session:', this.sessionId);
          console.log('📊 Preview data:', this.colors.length, 'rows');
        } else {
          this.messageService.add({
            severity: 'error',
            summary: 'Upload Failed',
            detail: response.error || 'Unknown error occurred'
          });
        }
      },
      error: (error) => {
        this.isUploading = false;
        console.error('❌ Upload failed:', error);
        console.error('  Error status:', error.status);
        console.error('  Error message:', error.message);
        console.error('  Error detail:', error.error?.detail);
        console.error('  Full error object:', JSON.stringify(error, null, 2));
        
        this.messageService.add({
          severity: 'error',
          summary: 'Upload Failed',
          detail: error.error?.detail || error.message || 'Failed to upload file'
        });
      }
    });
  }
  
  /**
   * Delete selected rows from preview
   */
  deleteSelectedRows(): void {
    if (this.selectedRows.length === 0) {
      this.messageService.add({
        severity: 'warn',
        summary: 'No Selection',
        detail: 'Please select rows to delete'
      });
      return;
    }
    
    if (!this.sessionId) {
      this.messageService.add({
        severity: 'error',
        summary: 'Error',
        detail: 'No active session. Please import a file first.'
      });
      return;
    }
    
    this.isProcessing = true;
    
    // Extract row IDs (assuming each row has an 'id' or use index)
    const rowIds = this.selectedRows.map((row, index) => row.id || index);
    
    this.manualColorService.deleteRows({
      session_id: this.sessionId,
      row_ids: rowIds
    }).subscribe({
      next: (response) => {
        this.isProcessing = false;
        
        if (response.success) {
          this.previewData = response.updated_preview || [];
          this.colors = this.previewData;
          this.selectedRows = [];
          this.statistics = response.statistics || this.statistics;
          
          this.messageService.add({
            severity: 'success',
            summary: 'Rows Deleted',
            detail: `Deleted ${response.deleted_count} rows. ${response.remaining_count} remaining.`
          });
          
          console.log('✅ Deleted rows successfully');
        } else {
          this.messageService.add({
            severity: 'error',
            summary: 'Delete Failed',
            detail: response.error || 'Failed to delete rows'
          });
        }
      },
      error: (error) => {
        this.isProcessing = false;
        console.error('❌ Delete failed:', error);
        
        this.messageService.add({
          severity: 'error',
          summary: 'Delete Failed',
          detail: error.error?.detail || 'Failed to delete rows'
        });
      }
    });
  }
  
  /**
   * Apply selected rules to current preview data
   */
  applySelectedRules(): void {
    if (!this.sessionId || this.colors.length === 0) {
      this.messageService.add({
        severity: 'warn',
        summary: 'No Data',
        detail: 'Please import data first before applying rules'
      });
      return;
    }
    
    if (this.selectedRules.length === 0) {
      this.messageService.add({
        severity: 'warn',
        summary: 'No Rules Selected',
        detail: 'Please select at least one rule to apply'
      });
      return;
    }
    
    this.isProcessing = true;
    
    const ruleIds = this.selectedRules.map(rule => rule.id);
    
    this.manualColorService.applyRules({
      session_id: this.sessionId,
      rule_ids: ruleIds
    }).subscribe({
      next: (response) => {
        this.isProcessing = false;
        
        if (response.success) {
          this.previewData = response.updated_preview || [];
          this.colors = this.previewData;
          this.statistics = response.statistics || this.statistics;
          
          this.messageService.add({
            severity: 'success',
            summary: 'Rules Applied',
            detail: `Applied ${response.rules_applied} rules. Excluded ${response.excluded_count} rows.`
          });
          
          console.log('✅ Applied rules successfully');
        } else {
          this.messageService.add({
            severity: 'error',
            summary: 'Apply Failed',
            detail: response.error || 'Failed to apply rules'
          });
        }
      },
      error: (error) => {
        this.isProcessing = false;
        console.error('❌ Apply rules failed:', error);
        
        this.messageService.add({
          severity: 'error',
          summary: 'Apply Failed',
          detail: error.error?.detail || 'Failed to apply rules'
        });
      }
    });
  }

  runAutomation() {
    if (!this.sessionId || this.colors.length === 0) {
      this.messageService.add({
        severity: 'warn',
        summary: 'No Data',
        detail: 'Please import data first before running automation'
      });
      return;
    }
    
    this.isSaving = true;
    
    console.log('💾 Saving processed colors to output...');
    console.log('📊 Data to save:', this.colors.length, 'rows');
    
    this.manualColorService.saveManualColors({
      session_id: this.sessionId,
      user_id: 1
    }).subscribe({
      next: (response) => {
        this.isSaving = false;
        
        if (response.success) {
          this.messageService.add({
            severity: 'success',
            summary: 'Save Successful',
            detail: `Saved ${response.rows_saved} rows to output. ${response.message || ''}`
          });
          
          console.log('✅ Saved successfully:', response.output_file);
          
          // Reset session after save
          setTimeout(() => {
            this.resetSession();
          }, 2000);
        } else {
          this.messageService.add({
            severity: 'error',
            summary: 'Save Failed',
            detail: response.error || 'Failed to save colors'
          });
        }
      },
      error: (error) => {
        this.isSaving = false;
        console.error('❌ Save failed:', error);
        
        this.messageService.add({
          severity: 'error',
          summary: 'Save Failed',
          detail: error.error?.detail || 'Failed to save colors'
        });
      }
    });
  }
  
  /**
   * Reset session data
   */
  resetSession(): void {
    console.log('🔄 Resetting session...');
    
    this.sessionId = null;
    this.filename = null;
    this.previewData = [];
    this.colors = [];
    this.selectedRows = [];
    this.selectedRules = [];
    this.statistics = {
      total_rows: 0,
      valid_rows: 0,
      invalid_rows: 0,
      deleted_rows: 0,
      rules_applied_count: 0
    };
    
    this.messageService.add({
      severity: 'info',
      summary: 'Session Reset',
      detail: 'All data cleared. Ready for new import.'
    });
    
    console.log('✅ Session reset complete');
  }

  openImportDialog() {
    this.showImportDialog = true;
  }

  onCancelUpload() {
    this.showImportDialog = false;
  }
  
  /**
   * Get severity for statistics display
   */
  getSeverity(key: string): string {
    const severityMap: any = {
      total_rows: 'info',
      valid_rows: 'success',
      invalid_rows: 'warning',
      deleted_rows: 'danger',
      rules_applied_count: 'info'
    };
    return severityMap[key] || 'info';
  }
  
  /**
   * Format key for display
   */
  formatKey(key: string): string {
    return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }
}
