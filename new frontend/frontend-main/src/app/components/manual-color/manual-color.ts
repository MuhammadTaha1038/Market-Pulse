import { Component, OnInit, ViewChild, ElementRef, ViewChildren, QueryList } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DialogModule } from 'primeng/dialog';
import { FileUploadModule } from 'primeng/fileupload';
import { InputTextModule } from 'primeng/inputtext';
import { ButtonModule } from 'primeng/button';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { FormsModule } from '@angular/forms';
import { MessageService } from 'primeng/api';
import { CustomTableComponent, TableColumn, TableRow, TableConfig } from '../custom-table/custom-table.component';
import { FilterDialogComponent, FilterCondition } from '../filter-dialog/filter-dialog.component';
import { ApiService, SearchFilter, Rule, RuleConditionBackend, Preset } from '../../services/api.service';
import { AutomationStatusService } from '../../services/automation-status.service';

@Component({
  selector: 'app-manual-color',
  standalone: true,
  imports: [
    CommonModule,
    DialogModule,
    FileUploadModule,
    InputTextModule,
    ButtonModule,
    ToastModule,
    TooltipModule,
    ProgressSpinnerModule,
    FormsModule,
    CustomTableComponent,
    FilterDialogComponent
  ],
  templateUrl: './manual-color.html',
  styleUrls: ['./manual-color.css'],
  providers: [MessageService]
})
export class ManualColor implements OnInit {
  @ViewChild('fileInputRef') fileInputRef!: ElementRef<HTMLInputElement>;
  @ViewChild('manualTable') manualTable!: any;

  searchText = '';
  showImportDialog = false;
  showFilterDialog = false;
  isUploading = false;
  isTableExpanded: boolean = false;
  selectedFile: File | null = null;
  fileSize: string = '';
  presetCount: number = 11;

  // Run Rules dialog state
  showRunRulesDialog = false;
  availableRules: Rule[] = [];
  selectedRuleIds: Set<number> = new Set();
  ruleSearchText = '';
  loadingRules = false;
  runningRules = false;

  // Run Automation state
  runningAutomation = false;

  // Presets state
  availablePresets: Preset[] = [];
  selectedPresetId: number | null = null;
  loadingPresets = false;
  presetsDialogVisible = false;

  // Session management
  currentSessionId: string | null = null;
  isLoadingQuery = false;
  dataSource: 'oracle' | 'excel' | null = null;

  // Undo history
  private undoStack: TableRow[][] = [];

  // Sorting state
  showSortDialog = false;
  sortSearchText = '';
  activeSortId: string = 'rank';  // Currently active sort
  sortOptions: { id: string; name: string; field: string; direction: 'asc' | 'desc' }[] = [
    { id: 'rank', name: 'Normal sorting rank', field: 'rank', direction: 'asc' },
    { id: 'date', name: 'Sort by date', field: 'date', direction: 'desc' },
    { id: 'price', name: 'Sort by price', field: 'px', direction: 'desc' }
  ];
  pendingSortId: string = 'rank';  // Selection in dialog before clicking Run

  // Active filters for display as chips
  activeFilters: FilterCondition[] = [];

  /** Oracle column names visible for the active CLO — fed to filter dialog */
  visibleOracleColumns: string[] = [];
  /** Oracle column name -> data type map for type-aware operator filtering */
  columnDataTypes: { [oracleName: string]: string } = {};

  // Table data
  tableData: TableRow[] = [];
  
  // Table configuration
  // Populated dynamically from CLO visible-column config after init; falls back to getDefaultColumns()
  tableColumns: TableColumn[] = [];

  tableConfig: TableConfig = {
    editable: true,
    selectable: true,
    showSelectButton: true,
    showRowNumbers: true,
    pagination: false,
    pageSize: 20,
    showExport: false,
    showAddRow: false
  };

  constructor(
    private messageService: MessageService,
    private apiService: ApiService,
    private automationStatusService: AutomationStatusService
  ) {}

  ngOnInit() {
    console.log('🚀 Manual Color component initialized');
    this.loadPresets();
    this.loadQueryData();
    this.loadCloColumns();
  }

  /** Resolve the active CLO from topbar (selectedAssetState) or CLO-selector (user_clo_selection). */
  private resolveActiveCloContext(): { cloId: string | undefined; cloName: string } {
    let cloId: string | undefined;
    let cloName = 'unknown';
    try {
      const rawAsset = localStorage.getItem('selectedAssetState');
      if (rawAsset) {
        const parsed = JSON.parse(rawAsset);
        cloId = parsed?.asset?.value;
        cloName = parsed?.asset?.name || cloName;
      }
    } catch { }
    try {
      const rawUser = localStorage.getItem('user_clo_selection');
      if (rawUser) {
        const sel = JSON.parse(rawUser);
        if (!cloId) { cloId = sel?.cloId; cloName = sel?.cloName || cloName; }
      }
    } catch { }
    return { cloId, cloName };
  }

  /** Load CLO-visible columns and their data types for the filter dialog */
  private loadCloColumns(): void {
    const { cloId } = this.resolveActiveCloContext();
    this.apiService.getSearchableFields(cloId).subscribe({
      next: (res) => {
        this.visibleOracleColumns = res.fields.map((f: any) => f.name);
        this.columnDataTypes = Object.fromEntries(res.fields.map((f: any) => [f.name, f.data_type]));
      },
      error: (err) => console.warn('Could not load CLO column types for filter dialog:', err)
    });
  }

  /**
   * Build table columns from the CLO visible-column list returned by getUserColumns().
   * Falls back to getDefaultColumns() when the list is empty.
   */
  private buildTableColumns(visibleOracleNames: string[]): void {
    const ALL_COLS: { [k: string]: TableColumn } = {
      'MESSAGE_ID':   { field: 'messageId',   header: 'Message ID',  width: '180px', editable: true },
      'TICKER':       { field: 'ticker',       header: 'Ticker',      width: '140px', editable: true },
      'SECTOR':       { field: 'sector',       header: 'Sector',      width: '140px', editable: true },
      'CUSIP':        { field: 'cusip',        header: 'CUSIP',       width: '140px', editable: true },
      'DATE':         { field: 'date',         header: 'Date',        width: '120px', editable: true },
      'PRICE_LEVEL':  { field: 'priceLevel',   header: 'Price Level', width: '120px', editable: true, type: 'number' },
      'BID':          { field: 'bid',          header: 'BID',         width: '100px', editable: true, type: 'number' },
      'ASK':          { field: 'ask',          header: 'ASK',         width: '100px', editable: true, type: 'number' },
      'PX':           { field: 'px',           header: 'PX',          width: '100px', editable: true, type: 'number' },
      'SOURCE':       { field: 'source',       header: 'Source',      width: '140px', editable: true },
      'BIAS':         { field: 'bias',         header: 'Bias',        width: '120px', editable: true },
      'RANK':         { field: 'rank',         header: 'Rank',        width: '80px',  editable: false, type: 'number' },
      'COV_PRICE':    { field: 'covPrice',     header: 'Cov Price',   width: '110px', editable: true, type: 'number' },
      'PERCENT_DIFF': { field: 'percentDiff',  header: '% Diff',      width: '100px', editable: true, type: 'number' },
      'PRICE_DIFF':   { field: 'priceDiff',    header: 'Price Diff',  width: '110px', editable: true, type: 'number' },
      'CONFIDENCE':   { field: 'confidence',   header: 'Confidence',  width: '110px', editable: true, type: 'number' },
      'DATE_1':       { field: 'date1',        header: 'Date 1',      width: '120px', editable: true },
      'DIFF_STATUS':  { field: 'diffStatus',   header: 'Diff Status', width: '120px', editable: true },
    };
    const midCol: TableColumn = { field: 'mid', header: 'MID', width: '100px', editable: true, type: 'number' };
    const cols: TableColumn[] = [];
    for (const name of visibleOracleNames) {
      const key = name.toUpperCase().replace(/ /g, '_');
      const col = ALL_COLS[key];
      if (col) {
        cols.push(col);
        // Insert MID synthetic column between ASK and the next column
        if (key === 'ASK') cols.push(midCol);
      }
    }
    this.tableColumns = cols.length > 0 ? cols : this.getDefaultColumns();
  }

  private getDefaultColumns(): TableColumn[] {
    return [
      { field: 'messageId', header: 'Message ID', width: '180px', editable: true },
      { field: 'ticker',    header: 'Ticker',      width: '140px', editable: true },
      { field: 'cusip',     header: 'CUSIP',       width: '140px', editable: true },
      { field: 'bias',      header: 'Bias',        width: '120px', editable: true },
      { field: 'date',      header: 'Date',        width: '120px', editable: true },
      { field: 'bid',       header: 'BID',         width: '100px', editable: true, type: 'number' },
      { field: 'mid',       header: 'MID',         width: '100px', editable: true, type: 'number' },
      { field: 'ask',       header: 'ASK',         width: '100px', editable: true, type: 'number' },
      { field: 'px',        header: 'PX',          width: '100px', editable: true, type: 'number' },
      { field: 'source',    header: 'Source',      width: '140px', editable: true },
    ];
  }

  /**
   * Auto-load CLO data on page init. Reads the active CLO from both localStorage
   * sources (topbar selectedAssetState OR CLO-selector user_clo_selection), then:
   * 1. Fetches visible columns to build table columns dynamically.
   * 2. Calls the backend fetch-from-query endpoint (which uses DATA_SOURCE env var).
   */
  private loadQueryData() {
    const { cloId, cloName } = this.resolveActiveCloContext();
    if (!cloId) {
      console.warn('⚠️ No CLO selected — manual color page cannot auto-load data');
      this.tableColumns = this.getDefaultColumns();
      return;
    }

    this.isLoadingQuery = true;
    console.log('🔍 Loading data for CLO:', cloId, '(', cloName, ')');

    // Fetch visible columns to populate table columns before data arrives
    this.apiService.getUserColumns(cloId).subscribe({
      next: (colRes: any) => this.buildTableColumns(colRes.visible_columns || []),
      error: () => { this.tableColumns = this.getDefaultColumns(); }
    });

    this.apiService.fetchManualColorFromQuery(cloId, 1).subscribe({
      next: (response: any) => {
        if (response.success) {
          this.applyPreviewResponse(response);
          this.dataSource = this.normalizeDataSource(response.data_source);
          this.messageService.add({
            severity: 'success',
            summary: 'Data Loaded',
            detail: `Loaded ${response.rows_imported} rows for ${cloName} from ${this.dataSource === 'oracle' ? 'Oracle query' : 'Excel data source'}`
          });
        } else {
          console.warn('⚠️ fetch-from-query returned error:', response.error);
          this.messageService.add({
            severity: 'warn',
            summary: 'Could Not Load Data',
            detail: response.error || 'Import an Excel file to work with data'
          });
        }
      },
      error: (err) => {
        console.warn('⚠️ fetch-from-query endpoint error:', err);
        this.messageService.add({
          severity: 'warn',
          summary: 'Data Source Unavailable',
          detail: 'Could not load data automatically. Import an Excel file to get started.'
        });
      },
      complete: () => { this.isLoadingQuery = false; }
    });
  }

  /**
   * Shared helper: take a /import or /fetch-from-query response and populate the table.
   */
  private applyPreviewResponse(response: any) {
    this.currentSessionId = response.session_id;
    this.tableData = (response.sorted_preview ?? []).map((row: any) => ({
      _rowId: `row_${row.row_id ?? row.message_id}`,
      _selected: false,
      rowNumber: String(row.message_id),
      messageId: row.message_id,
      ticker: row.ticker,
      sector: row.sector,
      cusip: row.cusip,
      bias: row.bias,
      date: row.date ? new Date(row.date).toLocaleDateString() : '',
      priceLevel: row.price_level,
      bid: row.bid,
      mid: ((row.bid ?? 0) + (row.ask ?? 0)) / 2,
      ask: row.ask,
      px: row.px,
      source: row.source,
      rank: row.rank,
      covPrice: row.cov_price,
      percentDiff: row.percent_diff,
      priceDiff: row.price_diff,
      confidence: row.confidence,
      date1: row.date_1 ? new Date(row.date_1).toLocaleDateString() : '',
      diffStatus: row.diff_status,
      isParent: row.is_parent,
      parentRow: row.parent_message_id,
      childrenCount: row.children_count ?? 0
    }));
  }

  private normalizeDataSource(source: any): 'oracle' | 'excel' {
    return String(source ?? 'excel').toLowerCase() === 'oracle' ? 'oracle' : 'excel';
  }

  // ==================== FILE UPLOAD ====================

  /**
   * Trigger native file input dialog
   */
  triggerFileInput() {
    if (this.fileInputRef && this.fileInputRef.nativeElement) {
      this.fileInputRef.nativeElement.click();
    }
  }

  /**
   * Handle native file selection
   */
  onNativeFileSelect(event: any) {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    const file: File = files[0];
    
    // Validate file type
    const validExtensions = ['.xlsx', '.xls'];
    const fileName = file.name.toLowerCase();
    const isValidFile = validExtensions.some(ext => fileName.endsWith(ext));

    if (!isValidFile) {
      this.messageService.add({
        severity: 'error',
        summary: 'Invalid File',
        detail: 'Only .xlsx and .xls files are supported'
      });
      return;
    }

    // Store file and display info
    this.selectedFile = file;
    this.fileSize = this.formatFileSize(file.size);

    console.log('📄 File selected:', file.name, 'Size:', this.fileSize);

    // Reset file input so same file can be selected again if needed
    event.target.value = '';
  }

  openImportDialog() {
    this.showImportDialog = true;
    this.selectedFile = null;
    this.fileSize = '';
    this.isUploading = false;
  }

  onUpload() {
    if (!this.selectedFile) {
      this.messageService.add({
        severity: 'warn',
        summary: 'No File Selected',
        detail: 'Please select a file to import'
      });
      return;
    }

    console.log('📥 Uploading file to backend:', this.selectedFile.name);
    this.isUploading = true;

    this.apiService.importManualColorFile(this.selectedFile, 1).subscribe({
      next: (response: any) => {
        console.log('✅ File imported successfully:', response);

        if (response.success) {
          this.applyPreviewResponse(response);
          this.dataSource = 'excel';
          this.showImportDialog = false;

          this.messageService.add({
            severity: 'success',
            summary: 'Import Successful',
            detail: `Imported ${response.rows_imported} rows from Excel. ${response.statistics?.parent_rows ?? 0} parents, ${response.statistics?.child_rows ?? 0} children.`
          });

          if (response.parsing_errors?.length > 0) {
            this.messageService.add({
              severity: 'warn',
              summary: 'Parsing Warnings',
              detail: `${response.parsing_errors.length} errors found. Check console for details.`
            });
            console.warn('Parsing errors:', response.parsing_errors);
          }
        } else {
          throw new Error(response.error || 'Import failed');
        }
      },
      error: (error) => {
        console.error('❌ Error uploading file:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Upload Failed',
          detail: error.error?.detail || 'Failed to upload file to backend'
        });
      },
      complete: () => {
        this.isUploading = false;
      }
    });
  }

  onCancelUpload() {
    this.showImportDialog = false;
    this.selectedFile = null;
    this.fileSize = '';
    this.isUploading = false;
  }

  /**
   * Format file size to human readable format
   */
  private formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }

  /**
   * Get file extension icon
   */
  getFileIcon(): string {
    if (!this.selectedFile) return 'pi-file';
    
    const name = this.selectedFile.name.toLowerCase();
    if (name.endsWith('.xlsx') || name.endsWith('.xls')) {
      return 'pi-file-excel';
    }
    return 'pi-file';
  }

  // ==================== TABLE EXPANSION ====================

  toggleTableExpansion() {
    console.log('📄 Toggling table expansion - Current state:', this.isTableExpanded);
    this.isTableExpanded = !this.isTableExpanded;
    
    // Notify sidebar to collapse/expand
    if (this.isTableExpanded) {
      // Collapse sidebar
      document.body.style.overflow = 'hidden';
      const sidebar = document.querySelector('.layout-sidebar');
      if (sidebar) {
        (sidebar as HTMLElement).style.display = 'none';
      }
    } else {
      // Restore sidebar
      document.body.style.overflow = 'auto';
      const sidebar = document.querySelector('.layout-sidebar');
      if (sidebar) {
        (sidebar as HTMLElement).style.display = 'block';
      }
    }
    
    console.log('📄 New expanded state:', this.isTableExpanded);
  }

  // ==================== TABLE EVENTS ====================

  onTableDataChanged(data: TableRow[]) {
    console.log('📊 Table data changed:', data.length, 'rows');
    this.tableData = data;
  }

  onTableRowsSelected(selectedRows: TableRow[]) {
    console.log('✅ Rows selected:', selectedRows.length);
  }

  onCellEdited(event: any) {
    console.log('📝 Cell edited:', event);
  }

  // ==================== ACTIONS ====================

  addNewRow() {
    this.saveUndoState();
    const newRow: TableRow = {
      _rowId: `row_new_${Date.now()}`,
      _selected: false,
      rowNumber: String(this.tableData.length + 1),
      messageId: '',
      ticker: '',
      cusip: '',
      bias: '',
      date: new Date().toLocaleDateString(),
      bid: 0,
      mid: 0,
      ask: 0,
      px: 0,
      source: 'MANUAL',
      rank: 5,
      isParent: true,
      childrenCount: 0
    };
    
    this.tableData = [newRow, ...this.tableData];
    
    this.messageService.add({
      severity: 'success',
      summary: 'Row Added',
      detail: 'New row added to table'
    });
  }

  // ==================== RUN RULES ====================

  openRunRulesDialog() {
    this.showRunRulesDialog = true;
    this.ruleSearchText = '';
    this.selectedRuleIds.clear();
    this.selectedPresetId = null;
    this.loadRules();
  }

  loadRules() {
    this.loadingRules = true;
    this.apiService.getRules().subscribe({
      next: (response) => {
        this.availableRules = response.rules;
        // Pre-select active rules
        this.availableRules.forEach(rule => {
          if (rule.is_active) {
            this.selectedRuleIds.add(rule.id);
          }
        });
        this.loadingRules = false;
      },
      error: (error) => {
        console.error('Error loading rules:', error);
        this.loadingRules = false;
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load rules'
        });
      }
    });
  }

  toggleRuleSelection(ruleId: number) {
    if (this.selectedRuleIds.has(ruleId)) {
      this.selectedRuleIds.delete(ruleId);
    } else {
      this.selectedRuleIds.add(ruleId);
    }
  }

  isRuleSelected(ruleId: number): boolean {
    return this.selectedRuleIds.has(ruleId);
  }

  /**
   * Get filtered table data based on search query
   * Searches by messageId or cusip fields
   */
  get filteredTableData(): TableRow[] {
    if (!this.searchText.trim()) {
      return this.tableData;
    }

    const searchLower = this.searchText.toLowerCase().trim();
    return this.tableData.filter(row => {
      const messageId = String(row['messageId'] || '').toLowerCase();
      const cusip = String(row['cusip'] || '').toLowerCase();
      return messageId.includes(searchLower) || cusip.includes(searchLower);
    });
  }

  get filteredRules(): Rule[] {
    if (!this.ruleSearchText.trim()) return this.availableRules;
    const search = this.ruleSearchText.toLowerCase();
    return this.availableRules.filter(r => r.name.toLowerCase().includes(search));
  }

  get allFilteredRulesSelected(): boolean {
    return this.filteredRules.length > 0 && this.filteredRules.every(r => this.selectedRuleIds.has(r.id));
  }

  toggleSelectAll() {
    if (this.allFilteredRulesSelected) {
      this.filteredRules.forEach(r => this.selectedRuleIds.delete(r.id));
    } else {
      this.filteredRules.forEach(r => this.selectedRuleIds.add(r.id));
    }
  }

  cancelRunRules() {
    this.showRunRulesDialog = false;
  }

  runSelectedRules() {
    if (this.selectedRuleIds.size === 0) {
      this.messageService.add({
        severity: 'warn',
        summary: 'No Rules Selected',
        detail: 'Please select at least one rule to run'
      });
      return;
    }

    if (this.tableData.length === 0) {
      this.messageService.add({
        severity: 'warn',
        summary: 'No Data',
        detail: 'No data in the table to filter'
      });
      return;
    }

    this.saveUndoState();
    this.runningRules = true;

    const selectedRules = this.availableRules.filter(r => this.selectedRuleIds.has(r.id));
    const originalCount = this.tableData.length;

    // Apply rules - remove rows that match any selected rule (exclusion rules)
    const filteredData = this.tableData.filter(row => {
      for (const rule of selectedRules) {
        if (this.evaluateRule(row, rule)) {
          return false; // Exclude this row
        }
      }
      return true; // Keep this row
    });

    const excludedCount = originalCount - filteredData.length;
    this.tableData = filteredData;
    this.runningRules = false;
    this.showRunRulesDialog = false;

    // Save snapshot after rules applied
    this.apiService.createBackup('Rules run - ' + new Date().toISOString()).subscribe();

    this.messageService.add({
      severity: 'success',
      summary: 'Rules Applied',
      detail: `${selectedRules.length} rule(s) applied. ${excludedCount} row(s) excluded, ${filteredData.length} remaining. Data saved.`
    });
  }

  /**
   * Run automation with two modes:
   * - override=false: Apply all active rules client-side + save
   * - override=true: Override cron schedule and trigger server-side automation
   */
  runAutomation(override: boolean = false) {
    if (override) {
      this.runningAutomation = true;
      this.automationStatusService.beginRun();
      this.messageService.add({
        severity: 'info',
        summary: 'Override & Run',
        detail: 'Overriding cron schedule and running automation...'
      });

      this.apiService.getActiveCronJobs().subscribe({
        next: (response) => {
          if (response.jobs.length === 0) {
            this.messageService.add({
              severity: 'warn',
              summary: 'No Active Jobs',
              detail: 'No active cron jobs found to override'
            });
            this.runningAutomation = false;
            this.automationStatusService.endRun();
            return;
          }

          const job = response.jobs[0];
          this.apiService.triggerCronJob(job.id, true).subscribe({
            next: (res) => {
              this.messageService.add({
                severity: 'success',
                summary: 'Automation Complete',
                detail: res.message || 'Cron job overridden and executed'
              });
              this.runningAutomation = false;
              this.automationStatusService.endRun();
            },
            error: (err) => {
              this.messageService.add({
                severity: 'error',
                summary: 'Error',
                detail: err.error?.detail || 'Failed to trigger automation'
              });
              this.runningAutomation = false;
              this.automationStatusService.endRun();
            }
          });
        },
        error: () => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to fetch active cron jobs'
          });
          this.runningAutomation = false;
          this.automationStatusService.endRun();
        }
      });
    } else {
      if (this.tableData.length === 0) {
        this.messageService.add({
          severity: 'warn',
          summary: 'No Data',
          detail: 'Please import data first'
        });
        return;
      }

      this.runningAutomation = true;
      this.automationStatusService.beginRun();
      this.messageService.add({
        severity: 'info',
        summary: 'Processing',
        detail: 'Running all active rules...'
      });

      this.apiService.getActiveRules().subscribe({
        next: (response) => {
          const activeRules = response.rules;
          if (activeRules.length === 0) {
            this.messageService.add({
              severity: 'warn',
              summary: 'No Active Rules',
              detail: 'No active rules found. Go to Settings to configure rules.'
            });
            this.runningAutomation = false;
            this.automationStatusService.endRun();
            return;
          }

          this.saveUndoState();
          const originalCount = this.tableData.length;

          const filteredData = this.tableData.filter(row => {
            for (const rule of activeRules) {
              if (this.evaluateRule(row, rule)) {
                return false;
              }
            }
            return true;
          });

          const excludedCount = originalCount - filteredData.length;
          this.tableData = filteredData;

          // Save snapshot after automation
          this.apiService.createBackup('Automation run - ' + new Date().toISOString()).subscribe({
            next: () => {
              this.messageService.add({
                severity: 'success',
                summary: 'Automation Complete',
                detail: `${activeRules.length} rule(s) applied. ${excludedCount} row(s) excluded, ${filteredData.length} remaining. Data saved.`
              });
            },
            error: () => {
              this.messageService.add({
                severity: 'success',
                summary: 'Automation Complete',
                detail: `${activeRules.length} rule(s) applied. ${excludedCount} row(s) excluded, ${filteredData.length} remaining.`
              });
            }
          });

          this.runningAutomation = false;
          this.automationStatusService.endRun();
        },
        error: () => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to fetch active rules'
          });
          this.runningAutomation = false;
          this.automationStatusService.endRun();
        }
      });
    }
  }

  // ==================== PRESETS ====================

  loadPresets() {
    this.loadingPresets = true;
    this.apiService.getPresets().subscribe({
      next: (response) => {
        this.availablePresets = response.presets;
        this.presetCount = response.presets.length;
        this.loadingPresets = false;
      },
      error: () => {
        this.loadingPresets = false;
      }
    });
  }

  applyPreset(presetId: number) {
    const preset = this.availablePresets.find(p => p.id === presetId);
    if (!preset) return;

    this.selectedPresetId = presetId;

    const filters: FilterCondition[] = preset.conditions.map(c => ({
      column: c.column,
      operator: c.operator,
      values: c.value,
      values2: c.value2 || '',
      columnDisplay: c.column,
      operatorDisplay: c.operator,
      logicalOperator: 'AND' as const
    }));

    this.activeFilters = filters;
    this.onFiltersApplied({ conditions: filters, subgroups: [] });

    this.messageService.add({
      severity: 'success',
      summary: 'Preset Loaded',
      detail: `Loaded preset "${preset.name}" with ${preset.conditions.length} filter(s)`
    });
  }

  // ==================== RULE EVALUATION ENGINE ====================
  // Mirrors backend rules_service.py logic

  private evaluateRule(row: any, rule: Rule): boolean {
    const conditions = rule.conditions || [];
    if (conditions.length === 0) return false;

    let result: boolean | null = null;

    for (const condition of conditions) {
      const conditionType = condition.type || 'where';
      const conditionMatch = this.evaluateCondition(row, condition);

      if (result === null) {
        result = conditionMatch;
      } else if (conditionType === 'and') {
        result = result && conditionMatch;
      } else if (conditionType === 'or') {
        result = result || conditionMatch;
      } else if (conditionType === 'where') {
        result = conditionMatch;
      }
    }

    return result ?? false;
  }

  private evaluateCondition(row: any, condition: RuleConditionBackend): boolean {
    const column = condition.column || '';
    let operator = (condition.operator || '').toLowerCase();
    const value = condition.value || '';
    const value2 = condition.value2 || '';

    // Normalize operators (matching backend operator_map)
    const operatorMap: { [key: string]: string } = {
      'equal to': 'equal_to',
      'not equal to': 'not_equal_to',
      'less than': 'less_than',
      'greater than': 'greater_than',
      'less than equal to': 'less_than_equal_to',
      'greater than equal to': 'greater_than_equal_to',
      'between': 'between',
      'contains': 'contains',
      'starts with': 'starts_with',
      'ends with': 'ends_with',
      'is equal to': 'equal_to',
      'is not equal to': 'not_equal_to',
      'equals': 'equal_to',
      'not_equals': 'not_equal_to',
      'not_contains': 'not_contains',
      'does not contain': 'not_contains',
      'greater_than': 'greater_than',
      'less_than': 'less_than',
      'greater_or_equal': 'greater_than_equal_to',
      'less_or_equal': 'less_than_equal_to'
    };

    operator = operatorMap[operator] || operator;

    const rowValue = this.getRowValue(row, column);
    const compareValue = String(value);

    switch (operator) {
      case 'equal_to': {
        const numRow = parseFloat(rowValue);
        const numCmp = parseFloat(compareValue);
        if (!isNaN(numRow) && !isNaN(numCmp)) return numRow === numCmp;
        return rowValue.toLowerCase() === compareValue.toLowerCase();
      }
      case 'not_equal_to': {
        const numRow = parseFloat(rowValue);
        const numCmp = parseFloat(compareValue);
        if (!isNaN(numRow) && !isNaN(numCmp)) return numRow !== numCmp;
        return rowValue.toLowerCase() !== compareValue.toLowerCase();
      }
      case 'contains':
        return rowValue.toLowerCase().includes(compareValue.toLowerCase());
      case 'not_contains':
        return !rowValue.toLowerCase().includes(compareValue.toLowerCase());
      case 'starts_with':
        return rowValue.toLowerCase().startsWith(compareValue.toLowerCase());
      case 'ends_with':
        return rowValue.toLowerCase().endsWith(compareValue.toLowerCase());
      case 'less_than': {
        const a = parseFloat(rowValue), b = parseFloat(compareValue);
        return !isNaN(a) && !isNaN(b) && a < b;
      }
      case 'greater_than': {
        const a = parseFloat(rowValue), b = parseFloat(compareValue);
        return !isNaN(a) && !isNaN(b) && a > b;
      }
      case 'less_than_equal_to': {
        const a = parseFloat(rowValue), b = parseFloat(compareValue);
        return !isNaN(a) && !isNaN(b) && a <= b;
      }
      case 'greater_than_equal_to': {
        const a = parseFloat(rowValue), b = parseFloat(compareValue);
        return !isNaN(a) && !isNaN(b) && a >= b;
      }
      case 'between': {
        const rowNum = parseFloat(rowValue);
        const minVal = parseFloat(compareValue);
        const maxVal = parseFloat(value2);
        return !isNaN(rowNum) && !isNaN(minVal) && !isNaN(maxVal) && minVal <= rowNum && rowNum <= maxVal;
      }
      default:
        return false;
    }
  }

  /**
   * Get row value by column name with case-insensitive + snake_case→camelCase lookup
   * Handles backend Oracle column names (MESSAGE_ID) matching frontend keys (messageId)
   */
  private getRowValue(row: any, column: string): string {
    const lowerCol = column.toLowerCase();

    // Direct case-insensitive match
    for (const key of Object.keys(row)) {
      if (key.toLowerCase() === lowerCol) return String(row[key] ?? '');
    }

    // Snake_case to camelCase conversion (e.g., MESSAGE_ID → messageId)
    const camelCase = lowerCol.replace(/_([a-z])/g, (_, c: string) => c.toUpperCase());
    for (const key of Object.keys(row)) {
      if (key.toLowerCase() === camelCase.toLowerCase()) return String(row[key] ?? '');
    }

    return '';
  }

  saveData() {
    if (!this.currentSessionId) {
      this.messageService.add({
        severity: 'warn',
        summary: 'No Session',
        detail: 'Please import data first'
      });
      return;
    }

    console.log('💾 Saving data...');
    
    this.apiService.saveManualColors(this.currentSessionId, 1).subscribe({
      next: (response: any) => {
        console.log('✅ Data saved:', response);
        
        if (response.success) {
          this.messageService.add({
            severity: 'success',
            summary: 'Saved',
            detail: `Saved ${response.rows_saved} rows successfully`
          });
        }
      },
      error: (error) => {
        console.error('❌ Error saving data:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Save Failed',
          detail: error.error?.detail || 'Failed to save data'
        });
      }
    });
  }

  // ==================== FILTERS ====================

  showFilters() {
    this.showFilterDialog = true;
  }

  onFiltersApplied(filters: { conditions: FilterCondition[]; subgroups: any[] }) {
    console.log('✅ Filters applied:', filters);

    // Collect all valid conditions
    const allConditions: FilterCondition[] = [...filters.conditions];
    if (filters.subgroups) {
      for (const sg of filters.subgroups) {
        allConditions.push(...sg.conditions);
      }
    }

    this.activeFilters = allConditions;

    if (allConditions.length === 0) {
      return;
    }

    // Build SearchFilter array for the backend
    const searchFilters: SearchFilter[] = allConditions.map(c => ({
      field: c.column,
      operator: c.operator,
      value: c.values,
      value2: c.values2 || undefined
    }));

    console.log('📡 Calling backend search with filters:', searchFilters);

    this.apiService.searchColors(searchFilters, 0, 500).subscribe({
      next: (response) => {
        console.log('✅ Search results:', response.total_count, 'records');

        this.tableData = response.results.map((record: any, index: number) => ({
          _rowId: `row_${record.MESSAGE_ID || index}`,
          _selected: false,
          rowNumber: String(index + 1),
          messageId: String(record.MESSAGE_ID || ''),
          ticker: record.TICKER || '',
          cusip: record.CUSIP || '',
          bias: record.BIAS || '',
          date: record.DATE ? new Date(record.DATE).toLocaleDateString() : '',
          bid: record.BID || 0,
          mid: ((record.BID || 0) + (record.ASK || 0)) / 2,
          ask: record.ASK || 0,
          px: record.PX || 0,
          source: record.SOURCE || '',
          rank: record.RANK || 5,
          isParent: record.IS_PARENT ?? true,
          parentRow: record.PARENT_MESSAGE_ID || undefined,
          childrenCount: record.CHILDREN_COUNT || 0
        }));

        this.messageService.add({
          severity: 'success',
          summary: 'Filters Applied',
          detail: `Found ${response.total_count} matching record(s)`
        });
      },
      error: (error) => {
        console.error('❌ Search error:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Filter Error',
          detail: 'Failed to apply filters'
        });
      }
    });
  }

  removeFilter(index: number) {
    this.activeFilters.splice(index, 1);
    if (this.activeFilters.length > 0) {
      this.onFiltersApplied({ conditions: this.activeFilters, subgroups: [] });
    }
  }

  removeAllActiveFilters() {
    this.activeFilters = [];
    this.messageService.add({
      severity: 'info',
      summary: 'Filters Cleared',
      detail: 'All filters removed'
    });
  }

  // ==================== SORTING ====================

  showSortingDialog() {
    this.sortSearchText = '';
    this.pendingSortId = this.activeSortId;
    this.showSortDialog = true;
  }

  get filteredSortOptions() {
    if (!this.sortSearchText.trim()) return this.sortOptions;
    const q = this.sortSearchText.toLowerCase();
    return this.sortOptions.filter(s => s.name.toLowerCase().includes(q));
  }

  cancelSort() {
    this.showSortDialog = false;
  }

  runSort() {
    this.activeSortId = this.pendingSortId;
    this.showSortDialog = false;
    this.applySorting();
  }

  private applySorting() {
    const opt = this.sortOptions.find(s => s.id === this.activeSortId);
    if (!opt || this.tableData.length === 0) return;

    this.saveUndoState();

    // Separate parents and children
    const parents = this.tableData.filter(r => r['isParent'] === true);
    const children = this.tableData.filter(r => r['isParent'] !== true);

    // Sort parents
    parents.sort((a, b) => {
      const valA = this.getSortValue(a, opt.field);
      const valB = this.getSortValue(b, opt.field);
      const cmp = valA < valB ? -1 : valA > valB ? 1 : 0;
      return opt.direction === 'asc' ? cmp : -cmp;
    });

    // Rebuild: parents in sorted order, each followed by their children
    const sorted: TableRow[] = [];
    for (const parent of parents) {
      sorted.push(parent);
      const parentChildren = children.filter(c => {
        const ref = String(c['parentRow'] || '');
        const pid = parent['_rowId'] || '';
        const mid = String(parent['messageId'] || '');
        return ref === pid || ref === mid || `row_${ref}` === pid;
      });
      // Sort children by the same field
      parentChildren.sort((a, b) => {
        const valA = this.getSortValue(a, opt.field);
        const valB = this.getSortValue(b, opt.field);
        const cmp = valA < valB ? -1 : valA > valB ? 1 : 0;
        return opt.direction === 'asc' ? cmp : -cmp;
      });
      sorted.push(...parentChildren);
    }

    this.tableData = sorted;

    this.messageService.add({
      severity: 'success',
      summary: 'Sorted',
      detail: `Data sorted by ${opt.name}`
    });
  }

  private getSortValue(row: any, field: string): number | string {
    const val = row[field];
    if (field === 'date') {
      if (!val) return 0;
      const parsed = new Date(val).getTime();
      return isNaN(parsed) ? 0 : parsed;
    }
    if (field === 'rank' || field === 'px' || field === 'bid' || field === 'ask' || field === 'mid') {
      const num = parseFloat(val);
      return isNaN(num) ? 0 : num;
    }
    return String(val || '').toLowerCase();
  }

  // ==================== UNDO ====================

  undoLastAction() {
    if (this.undoStack.length === 0) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Nothing to Undo',
        detail: 'No previous actions to undo'
      });
      return;
    }

    this.tableData = this.undoStack.pop()!;
    this.messageService.add({
      severity: 'success',
      summary: 'Undo',
      detail: 'Last action undone'
    });
  }

  saveUndoState() {
    this.undoStack.push([...this.tableData.map(row => ({ ...row }))]);
  }

  // ==================== PRESETS ====================

  showPresetsDialog() {
    this.loadPresets();
    this.presetsDialogVisible = true;
  }
}