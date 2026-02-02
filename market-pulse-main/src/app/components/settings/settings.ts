import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AutoCompleteModule } from 'primeng/autocomplete';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpClientModule } from '@angular/common/http';

// Import API Services
import { RulesService } from '../../services/rules.service';
import { CronJobsService } from '../../services/cron-jobs.service';
import { ManualUploadService } from '../../services/manual-upload.service';
import { BackupService } from '../../services/backup.service';
import { LogsService, UnifiedLogEntry } from '../../services/logs.service';
import { ConfigService } from '../../services/config.service';
import { PresetsService, Preset as PresetModel } from '../../services/presets.service';
import { CLOSelectionService, UserCLOSelection } from '../../services/clo-selection.service';
import { getVisibleColumnDefinitions } from '../../utils/column-definitions';

interface CornJob {
  name: string;
  time: string;
  frequency: string[];
  repeat: string;
  isEditing?: boolean;
  originalData?: any;
}

interface CalendarDate {
  day: number;
  isCurrentMonth: boolean;
  events: CalendarEvent[];
  isSelected?: boolean;
}

interface CalendarEvent {
  label: string;
  type: 'success' | 'error' | 'skipped' | 'override' | 'notStarted';
}

interface RestoreEmailLog {
  description: string;
  date: string;
  canRevert?: boolean;
}

interface RuleCondition {
  type: 'where' | 'and' | 'or' | 'subgroup';
  column: string;
  operator: string;
  value: string;
  conditions?: RuleCondition[];
  isSubgroup?: boolean;
}

interface Preset {
  id?: number;
  name: string;
  conditions: PresetCondition[];
}

interface PresetCondition {
  owner: string;
  operator: string;
  value: string;
}

interface RestoreData {
  details: string;
  date: string;
  time: string;
  process: string;
}

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    AutoCompleteModule,
    HttpClientModule
  ],
  templateUrl: './settings.html'
})
export class Settings implements OnInit {
  // Active dropdown options
  activeOptions: any[] = [
    { label: 'Yes', value: 'Yes' },
    { label: 'No', value: 'No' }
  ];
  
  selectedActive1: string = 'Yes';
  selectedActive2: string = 'No';
  
  filteredActiveOptions: any[] = [];

  // Column options for the rule builder (loaded dynamically from API)
  columnOptions: any[] = [];
  
  filteredColumnOptions: any[] = [];

  // Operator options (Client-Specified)
  // Numeric operators: Equal to, Not equal to, Less than, Greater than, Less than equal to, Greater than equal to, Between
  // Text operators: Equal to (Exact words), Not equal to, Contains, Starts with, Ends with
  operatorOptions: string[] = [
    'equal to',
    'not equal to',
    'less than',
    'greater than',
    'less than equal to',
    'greater than equal to',
    'between',
    'contains',
    'starts with',
    'ends with'
  ];
  
  filteredOperatorOptions: any[] = [];

  // Rule conditions - start with only WHERE condition
  ruleConditions: RuleCondition[] = [
    {
      type: 'where',
      column: 'Bwic Cover',
      operator: 'is equal to',
      value: 'JPMC'
    }
  ];

  showAdditionalConditions: boolean = false;
  newRuleName: string = '';

  // Rules from backend API
  displayedRules: any[] = [];

  // Corn Jobs data
  daysOfWeek: any[] = [
    { id: 'S', label: 'S', selected: true },
    { id: 'M', label: 'M', selected: true },
    { id: 'T', label: 'T', selected: true },
    { id: 'W', label: 'W', selected: true },
    { id: 'T2', label: 'T', selected: true },
    { id: 'F', label: 'F', selected: true },
    { id: 'S2', label: 'S', selected: true }
  ];

  newJobName: string = '';
  newJobTime: string = '11:40';
  newJobRepeat: string = 'Yes';

  repeatOptions: any[] = [
    { label: 'Yes', value: 'Yes' },
    { label: 'No', value: 'No' }
  ];
  
  filteredRepeatOptions: any[] = [];

  cornJobs: CornJob[] = [
    {
      name: 'US CLO N1800 Batch',
      time: '6:30 PM',
      frequency: ['S', 'M', 'T', 'W', 'T', 'F', 'S'],
      repeat: 'Yes'
    },
    {
      name: 'US CLO N1800 Batch',
      time: '6:30 PM',
      frequency: ['S', 'M', 'T', 'W', 'T', 'F', 'S'],
      repeat: 'No'
    }
  ];

  // Calendar data
  weekDays: string[] = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];
  currentMonth: string = 'September 2024';
  calendarDates: CalendarDate[] = [];
  selectedDate: CalendarDate | null = null;

  // Restore & Email data
  restoreData: RestoreData[] = [
    {
      details: 'US OLONI8000 Batch',
      date: 'Nov. 22, 2005',
      time: '08:03 AM',
      process: 'Automated'
    },
    {
      details: 'US OLONI8000 Batch',
      date: 'Nov. 22, 2005',
      time: '08:03 AM',
      process: 'Manual'
    }
  ];

  // Manual upload history - will be loaded from backend
  manualUploadHistory: any[] = [];

  // Logs for each section - loaded from backend
  ruleLogs: UnifiedLogEntry[] = [];
  cronLogs: UnifiedLogEntry[] = [];
  manualUploadLogs: UnifiedLogEntry[] = [];
  backupLogs: UnifiedLogEntry[] = [];

  restoreEmailLogs: RestoreEmailLog[] = [];

  restoreLogs: RestoreEmailLog[] = [
    {
      description: 'Email sent by Shusharak Shwazhan',
      date: 'Nov. 22, 2005',
      canRevert: false
    },
    {
      description: 'Removed data by LUIS Sharma', 
      date: 'Nov. 22, 2005',
      canRevert: true
    }
  ];

  // Presets data - exactly as in screenshot
  presets: Preset[] = [
    {
      name: 'Select 102 bank securities',
      conditions: [
        { owner: 'Owner', operator: 'is equal to', value: 'Becalato' },
        { owner: 'Pno', operator: 'is equal to', value: 'Becalato' },
        { owner: 'Pno', operator: 'is equal to', value: 'Becalato' }
      ]
    },
    {
      name: 'Select Performance Trust Offer',
      conditions: [
        { owner: 'Owner', operator: 'is equal to', value: 'Becalato' },
        { owner: 'Pno', operator: 'is equal to', value: 'Becalato' }
      ]
    }
  ];

  presetLogs: any[] = [
    { description: 'Preset added by Sharebank Sihasidara', date: 'Nov 02, 2005' },
    { description: 'Preset removed by Usti Sharma', date: 'Nov 02, 2005' }
  ];

  // Preset form data
  newPresetName: string = '';
  showPresetForm: boolean = false;

  presetConditions: RuleCondition[] = [
    {
      type: 'where',
      column: 'Bwic Cover',
      operator: 'is equal to',
      value: 'JPMC'
    }
  ];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private rulesService: RulesService,
    private cronJobsService: CronJobsService,
    private manualUploadService: ManualUploadService,
    private backupService: BackupService,
    private logsService: LogsService,
    private configService: ConfigService,
    private presetsService: PresetsService,
    private cloSelectionService: CLOSelectionService
  ) {
    this.generateCalendar();
  }

  async ngOnInit() {
    // Subscribe to query parameters to handle section navigation
    this.route.queryParams.subscribe(params => {
      const section = params['section'];
      if (section) {
        // Use setTimeout to ensure the DOM is rendered before scrolling
        setTimeout(() => {
          this.scrollToSection(section + '-section');
        }, 100);
      }
    });
  this.loadAllLogs();
  
    // Refresh CLO columns from backend to ensure we have the latest configuration
    await this.cloSelectionService.refreshColumnsFromBackend();
    
    // Load data from APIs
    this.loadColumnOptions();
    this.loadRules();
    this.loadCronJobs();
    this.loadBackupHistory();
    this.loadManualUploadHistory();
    this.loadPresets();
  }

  // ===== API INTEGRATION METHODS =====

  // Column Configuration API Methods
  loadColumnOptions(): void {
    // Get visible columns from CLO selection
    const cloSelection = this.cloSelectionService.getCurrentSelection();
    
    if (cloSelection && cloSelection.visibleColumns) {
      // Use only visible columns from CLO mapping
      const visibleColumnDefs = getVisibleColumnDefinitions(cloSelection.visibleColumns);
      this.columnOptions = visibleColumnDefs.map(col => col.displayName);
      
      console.log('✅ Loaded CLO-filtered column options:', this.columnOptions);
      console.log('📊 CLO:', cloSelection.cloName, '- Visible columns:', this.columnOptions.length);
      
      // Set default column if ruleConditions is empty or has default value
      if (this.ruleConditions.length > 0 && this.columnOptions.length > 0) {
        if (!this.ruleConditions[0].column || !this.columnOptions.includes(this.ruleConditions[0].column)) {
          this.ruleConditions[0].column = this.columnOptions[0];
        }
      }
      
      // Update preset conditions default column too
      if (this.presetConditions.length > 0 && this.columnOptions.length > 0) {
        if (!this.presetConditions[0].column || !this.columnOptions.includes(this.presetConditions[0].column)) {
          this.presetConditions[0].column = this.columnOptions[0];
        }
      }
    } else {
      // Fallback to API if no CLO selection (should not happen)
      console.warn('⚠️ No CLO selection found, loading all columns from API');
      this.configService.getAllColumns().subscribe({
        next: (columns) => {
          this.columnOptions = columns;
          console.log('Loaded column options from API:', this.columnOptions);
        },
        error: (error) => {
          console.error('Error loading column options:', error);
          this.columnOptions = ['Ticker', 'CUSIP', 'Date', 'Source'];
        }
      });
    }
  }

  // Rules API Methods
  loadRules(): void {
    console.log('Loading rules from backend...');
    this.rulesService.getAllRules().subscribe({
      next: (response) => {
        console.log('Rules response:', response);
        if (response.rules && response.rules.length > 0) {
          // Store rules for display in table
          this.displayedRules = response.rules;
          
          // Also update ruleConditions for the form (flatten first rule's conditions)
          const firstRule = response.rules[0];
          if (firstRule.conditions && firstRule.conditions.length > 0) {
            this.ruleConditions = firstRule.conditions.map((condition: any, index: number) => ({
              type: index === 0 ? 'where' : condition.type,
              column: condition.column,
              operator: condition.operator,
              value: condition.value
            }));
            
            if (this.ruleConditions.length > 1) {
              this.showAdditionalConditions = true;
            }
          }
          
          console.log('Displayed rules:', this.displayedRules);
        } else {
          console.log('No rules found');
          this.displayedRules = [];
          this.ruleConditions = [{
            type: 'where',
            column: 'Bwic Cover',
            operator: 'is equal to',
            value: ''
          }];
        }
      },
      error: (error) => {
        console.error('Error loading rules:', error);
        this.showToast('Failed to load rules from server');
        this.displayedRules = [];
      }
    });
  }

  saveRule(): void {
    if (!this.newRuleName) {
      this.showToast('Please enter a rule name');
      return;
    }

    // Convert rule conditions to backend format (conditions array)
    const ruleData: any = {
      name: this.newRuleName,
      conditions: this.ruleConditions.map(condition => ({
        type: condition.type,
        column: condition.column,
        operator: condition.operator,
        value: condition.value
      })),
      is_active: true
    };

    console.log('Creating rule:', ruleData);

    this.rulesService.createRule(ruleData as any).subscribe({
      next: (response) => {
        console.log('Rule created:', response);
        if (response.message) {
          this.showToast('Rule saved successfully!');
          this.newRuleName = '';
          // Reset to default WHERE condition
          this.ruleConditions = [{
            type: 'where',
            column: 'Bwic Cover',
            operator: 'is equal to',
            value: ''
          }];
          this.showAdditionalConditions = false;
          this.loadRules(); // Reload rules
        }
      },
      error: (error) => {
        console.error('Error saving rule:', error);
        this.showToast('Failed to save rule');
      }
    });
  }

  deleteRule(ruleId: number): void {
    if (!ruleId) {
      this.showToast('Rule ID not found');
      return;
    }

    if (confirm('Are you sure you want to delete this rule?')) {
      this.rulesService.deleteRule(ruleId).subscribe({
        next: (response) => {
          if (response.message) {
            this.showToast('Rule deleted successfully!');
            this.loadRules(); // Reload rules
          }
        },
        error: (error) => {
          console.error('Error deleting rule:', error);
          this.showToast('Failed to delete rule');
        }
      });
    }
  }

  editRule(rule: any): void {
    // Populate form with rule data for editing
    this.newRuleName = rule.name;
    if (rule.conditions && rule.conditions.length > 0) {
      this.ruleConditions = rule.conditions.map((condition: any, index: number) => ({
        type: index === 0 ? 'where' : condition.type,
        column: condition.column,
        operator: condition.operator,
        value: condition.value
      }));
      
      if (this.ruleConditions.length > 1) {
        this.showAdditionalConditions = true;
      }
    }
    
    // Scroll to form
    this.scrollToSection('rules-section');
    this.showToast('Edit the rule and click "Save Exclusions" to update');
  }

  clearRule(): void {
    // Reset form to initial state
    this.newRuleName = '';
    this.ruleConditions = [{
      type: 'where',
      column: 'Bwic Cover',
      operator: 'is equal to',
      value: ''
    }];
    this.showAdditionalConditions = false;
    this.showToast('Rule form cleared');
  }

  // Cron Jobs API Methods
  loadCronJobs(): void {
    this.cronJobsService.getAllJobs().subscribe({
      next: (response) => {
        if (response.jobs && response.jobs.length > 0) {
          // Convert API cron jobs to component format
          this.cornJobs = response.jobs.map((job: any) => ({
            name: job.name,
            time: job.next_run || '6:30 PM',
            frequency: ['S', 'M', 'T', 'W', 'T', 'F', 'S'], // Default all days
            repeat: job.is_active ? 'Yes' : 'No',
            jobId: job.id,
            active: job.is_active
          }));
        }
      },
      error: (error) => {
        console.error('Error loading cron jobs:', error);
        this.showToast('Failed to load cron jobs from server');
      }
    });
  }

  saveCronJob(): void {
    if (!this.newJobName || !this.newJobTime) {
      this.showToast('Please enter job name and time');
      return;
    }

    // Parse time (e.g., "11:40" -> hour=11, minute=40)
    const [hour, minute] = this.newJobTime.split(':');
    
    // Build cron expression: "minute hour * * *" (every day at specified time)
    // Example: "40 11 * * *" means 11:40 AM every day
    const cronExpression = `${minute} ${hour} * * *`;
    
    const jobData: any = {
      name: this.newJobName,
      schedule: cronExpression,  // Backend expects 'schedule' not 'schedule_config'
      is_active: this.newJobRepeat === 'Yes'
    };

    this.cronJobsService.createJob(jobData).subscribe({
      next: (response) => {
        if (response.message) {
          this.showToast('Cron job created successfully!');
          this.newJobName = '';
          this.newJobTime = '11:40';
          this.newJobRepeat = 'Yes';
          this.loadCronJobs(); // Reload jobs
        }
      },
      error: (error) => {
        console.error('Error creating cron job:', error);
        this.showToast('Failed to create cron job');
      }
    });
  }

  triggerCronJob(jobId: number): void {
    if (!jobId) {
      this.showToast('Job ID not found');
      return;
    }

    this.cronJobsService.triggerJob(jobId).subscribe({
      next: (response) => {
        if (response.message) {
          this.showToast('Cron job triggered successfully!');
        }
      },
      error: (error) => {
        console.error('Error triggering cron job:', error);
        this.showToast('Failed to trigger cron job');
      }
    });
  }

  deleteCronJob(jobId: number): void {
    if (!jobId) {
      this.showToast('Job ID not found');
      return;
    }

    this.cronJobsService.deleteJob(jobId).subscribe({
      next: (response) => {
        if (response.message) {
          this.showToast('Cron job deleted successfully!');
          this.loadCronJobs(); // Reload jobs
        }
      },
      error: (error) => {
        console.error('Error deleting cron job:', error);
        this.showToast('Failed to delete cron job');
      }
    });
  }

  // Backup & Restore API Methods
  loadBackupHistory(): void {
    this.backupService.getBackupHistory().subscribe({
      next: (response) => {
        if (response.backups && response.backups.length > 0) {
          // Convert API backup history to component format
          this.restoreData = response.backups.map((backup: any) => ({
            details: backup.filename || backup.description || 'Backup',
            date: new Date(backup.created_at).toLocaleDateString('en-US', { 
              year: 'numeric', 
              month: 'short', 
              day: '2-digit' 
            }),
            time: new Date(backup.created_at).toLocaleTimeString('en-US', { 
              hour: '2-digit', 
              minute: '2-digit' 
            }),
            process: 'Manual',
            backupId: backup.id
          }));
        }
      },
      error: (error) => {
        console.error('Error loading backup history:', error);
        this.showToast('Failed to load backup history from server');
      }
    });
    
    // Load activity logs from backend
    this.backupService.getActivityLogs().subscribe({
      next: (response) => {
        if (response.logs && response.logs.length > 0) {
          this.restoreEmailLogs = response.logs.map((log: any) => ({
            description: `${log.action} by ${log.user}`,  // Backend returns 'user' not 'performed_by'
            date: new Date(log.timestamp).toLocaleDateString('en-US', { 
              year: 'numeric', 
              month: 'short', 
              day: '2-digit' 
            }),
            canRevert: log.action.toLowerCase().includes('delete') || log.action.toLowerCase().includes('remove')
          }));
        }
      },
      error: (error) => {
        console.error('Error loading activity logs:', error);
      }
    });
  }

  createBackup(description: string = 'Manual Backup', createdBy: string = 'User'): void {
    this.backupService.createBackup(description, createdBy).subscribe({
      next: (response) => {
        if (response.message) {
          this.showToast('Backup created successfully!');
          this.loadBackupHistory(); // Reload backup history
        }
      },
      error: (error) => {
        console.error('Error creating backup:', error);
        this.showToast('Failed to create backup');
      }
    });
  }

  restoreFromBackup(backupId: number, restoredBy: string = 'User', reason: string = 'Restore from Settings page'): void {
    if (!backupId) {
      this.showToast('Backup ID not found');
      return;
    }

    this.backupService.restoreBackup(backupId, restoredBy, reason).subscribe({
      next: (response) => {
        if (response.message) {
          this.showToast('Backup restored successfully!');
          // Reload all data after restore
          this.loadRules();
          this.loadCronJobs();
          this.loadBackupHistory();
        }
      },
      error: (error) => {
        console.error('Error restoring backup:', error);
        this.showToast('Failed to restore backup');
      }
    });
  }

  // Manual Upload API Methods
  uploadFile(event: any): void {
    const file = event.target?.files?.[0];
    if (!file) {
      this.showToast('No file selected');
      return;
    }

    // Validate file type
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      this.showToast('Please upload an Excel file (.xlsx or .xls)');
      return;
    }

    this.showToast('Uploading file... Please wait');

    this.manualUploadService.uploadFile(file).subscribe({
      next: (response) => {
        if (response.success) {
          // File is now buffered, not processed immediately
          const rowsUploaded = response.rows_uploaded || 0;
          const message = response.message || 'File uploaded successfully';
          
          this.showToast(`✅ Success! File buffered with ${rowsUploaded} rows. ${message}`);
          
          // Reload logs to show the pending upload
          this.loadManualUploadHistory();
          this.loadAllLogs();
          
          // No redirect - file will be processed in next cron run
        } else {
          // Show detailed error
          const errorMsg = response.error || 'Upload failed';
          const validationErrors = response.validation_errors?.join(', ') || '';
          this.showToast(`❌ Upload failed: ${errorMsg}. ${validationErrors}`);
        }
      },
      error: (error) => {
        console.error('Error uploading file:', error);
        const errorDetail = error.error?.detail || error.message || 'Unknown error';
        this.showToast(`❌ Upload failed: ${errorDetail}`);
      }
    });
  }

  loadManualUploadHistory(): void {
    this.manualUploadService.getUploadHistory().subscribe({
      next: (response) => {
        if (response.uploads && response.uploads.length > 0) {
          this.manualUploadHistory = response.uploads.map((upload: any) => ({
            id: upload.id,
            filename: upload.filename,
            uploadedBy: upload.uploaded_by,
            uploadedAt: new Date(upload.uploaded_at).toLocaleString('en-US', {
              year: 'numeric',
              month: 'short',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit'
            }),
            rowsProcessed: upload.rows_processed,
            status: upload.status
          }));
        }
      },
      error: (error) => {
        console.error('Error loading manual upload history:', error);
      }
    });
  }

  clearManualUpload(): void {
    // Reset the file input
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    if (fileInput) {
      fileInput.value = '';
    }
    this.showToast('File input cleared');
  }

  deleteManualUpload(uploadId: number): void {
    if (!uploadId) {
      this.showToast('Upload ID not found');
      return;
    }

    if (confirm('Are you sure you want to delete this upload record?')) {
      this.manualUploadService.deleteUpload(uploadId).subscribe({
        next: (response) => {
          if (response.message) {
            this.showToast('Upload deleted successfully!');
            this.loadManualUploadHistory(); // Reload history
          }
        },
        error: (error) => {
          console.error('Error deleting upload:', error);
          this.showToast('Failed to delete upload');
        }
      });
    }
  }

  // ===== END API INTEGRATION METHODS =====

  // ===== LOGS LOADING METHODS =====

  loadAllLogs(): void {
    // Load recent logs from all sources (4 most recent per section)
    this.logsService.getAllRecentLogs(4).subscribe({
      next: (logs) => {
        this.ruleLogs = logs.rules;
        this.cronLogs = logs.cron;
        this.manualUploadLogs = logs.manual;
        this.backupLogs = logs.backup;
      },
      error: (error) => {
        console.error('Error loading logs:', error);
      }
    });
  }

  formatLogTimestamp(timestamp: string): string {
    return this.logsService.formatTimestamp(timestamp);
  }

  revertLog(logId: number): void {
    if (!confirm('Are you sure you want to revert this operation?')) {
      return;
    }

    this.logsService.revertLog(logId, 'admin').subscribe({
      next: (response) => {
        alert(response.message || 'Operation reverted successfully');
        // Reload logs and rules to show updated state
        this.loadAllLogs();
        this.loadRules();
      },
      error: (error) => {
        console.error('Error reverting log:', error);
        alert('Failed to revert operation: ' + (error.error?.detail || error.message));
      }
    });
  }

  // ===== END LOGS METHODS =====

  // ===== PRESETS METHODS =====

  loadPresets(): void {
    this.presetsService.getAllPresets().subscribe({
      next: (response) => {
        // Map backend presets to component format
        this.presets = response.presets.map(preset => ({
          id: preset.id,  // Map the ID from backend
          name: preset.name,
          conditions: preset.conditions.map(cond => ({
            owner: cond.column,
            operator: cond.operator,
            value: cond.value
          }))
        }));
      },
      error: (error) => {
        console.error('Error loading presets:', error);
      }
    });
  }

  savePreset(): void {
    if (!this.newPresetName || this.newPresetName.trim() === '') {
      alert('Please enter a preset name');
      return;
    }

    const preset: PresetModel = {
      name: this.newPresetName,
      description: '',
      conditions: this.presetConditions.map(cond => ({
        column: cond.column,
        operator: cond.operator,
        value: cond.value
      }))
    };

    this.presetsService.createPreset(preset).subscribe({
      next: (response) => {
        alert(response.message);
        this.loadPresets();
        this.newPresetName = '';
        // Reset preset conditions
        this.presetConditions = [{
          type: 'where',
          column: 'Bwic Cover',
          operator: 'is equal to',
          value: 'JPMC'
        }];
      },
      error: (error) => {
        console.error('Error saving preset:', error);
        alert('Failed to save preset: ' + (error.error?.detail || error.message));
      }
    });
  }

  // ===== END PRESETS METHODS =====


  // Navigation method - Updated with highlight effect
  scrollToSection(sectionId: string): void {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
      
      // Add a highlight effect
      element.classList.add('bg-blue-50', 'transition-colors', 'duration-300');
      setTimeout(() => {
        element.classList.remove('bg-blue-50');
      }, 2000);
    }
  }

  // Filter methods for autocomplete
  filterActive(event: any): void {
    const query = event.query.toLowerCase();
    this.filteredActiveOptions = this.activeOptions.filter(option =>
      option.label.toLowerCase().includes(query)
    );
  }

  filterColumn(event: any): void {
    const query = event.query.toLowerCase();
    this.filteredColumnOptions = this.columnOptions.filter(option => 
      option.toLowerCase().includes(query)
    );
  }

  filterOperator(event: any): void {
    const query = event.query.toLowerCase();
    this.filteredOperatorOptions = this.operatorOptions.filter(option =>
      option.toLowerCase().includes(query)
    );
  }

  filterRepeat(event: any): void {
    const query = event.query.toLowerCase();
    this.filteredRepeatOptions = this.repeatOptions.filter(option =>
      option.label.toLowerCase().includes(query)
    );
  }

  // Rule Conditions methods
  addCondition(): void {
    this.showAdditionalConditions = true;
    this.ruleConditions.push({
      type: 'and',
      column: 'Bwic Cover',
      operator: 'is equal to',
      value: ''
    });
  }

  addSubgroup(): void {
    this.showAdditionalConditions = true;
    this.ruleConditions.push({
      type: 'subgroup',
      column: 'Bwic Cover',
      operator: 'is equal to',
      value: '',
      conditions: [
        {
          type: 'where',
          column: 'Bwic Cover',
          operator: 'is equal to',
          value: ''
        }
      ],
      isSubgroup: true
    });
  }

  addSubgroupCondition(subgroup: RuleCondition): void {
    if (subgroup.conditions) {
      subgroup.conditions.push({
        type: 'and',
        column: 'Bwic Cover',
        operator: 'is equal to',
        value: ''
      });
    }
  }

  removeCondition(index: number): void {
    this.ruleConditions.splice(index, 1);
    // Hide additional conditions if only WHERE condition remains
    if (this.ruleConditions.length === 1 && this.ruleConditions[0].type === 'where') {
      this.showAdditionalConditions = false;
    }
  }

  removeSubgroupCondition(subgroup: RuleCondition, conditionIndex: number): void {
    if (subgroup.conditions) {
      subgroup.conditions.splice(conditionIndex, 1);
    }
  }

  getConditionLabel(condition: RuleCondition, index: number): string {
    if (index === 0 && condition.type === 'where') return 'Where';
    return condition.type === 'or' ? 'OR' : 'AND';
  }

  // Corn Jobs methods
  toggleDay(day: any): void {
    day.selected = !day.selected;
  }

  addJob(): void {
    // Call API method instead of directly manipulating array
    this.saveCronJob();
  }

  editJob(job: CornJob): void {
    // Enable editing mode
    job.isEditing = true;
    job.originalData = { ...job };
  }

  saveJob(job: CornJob): void {
    job.isEditing = false;
    job.originalData = undefined;
    
    // Update job via API if jobId exists
    const jobData: any = job;
    if (jobData.jobId) {
      // Parse time (format: HH:MM)
      const [hours, minutes] = job.time.split(':').map(t => t || '0');
      
      const updateData: any = {
        name: job.name,
        schedule: `${minutes} ${hours} * * *`,  // Backend expects: schedule field with cron expression
        is_active: true
      };
      
      this.cronJobsService.updateJob(jobData.jobId, updateData).subscribe({
        next: (response) => {
          if (response.message) {
            this.showToast('Job updated successfully!');
            this.loadCronJobs(); // Reload jobs
          }
        },
        error: (error) => {
          console.error('Error updating job:', error);
          this.showToast('Failed to update job');
        }
      });
    } else {
      this.showToast('Job updated successfully!');
    }
  }

  cancelEdit(job: CornJob): void {
    if (job.originalData) {
      Object.assign(job, job.originalData);
    }
    job.isEditing = false;
    job.originalData = undefined;
  }

  deleteJob(job: CornJob): void {
    const jobData: any = job;
    if (jobData.jobId) {
      // Delete via API
      this.deleteCronJob(jobData.jobId);
    } else {
      // Fallback to local deletion
      const index = this.cornJobs.indexOf(job);
      if (index > -1) {
        this.cornJobs.splice(index, 1);
        this.showToast('Job deleted successfully!');
      }
    }
  }

  // Calendar methods
  generateCalendar(): void {
    this.calendarDates = [];
    // Generate September 2024 calendar
    const daysInMonth = 30;
    const startDay = 6; // September 1, 2024 starts on Sunday
    
    // Add previous month days
    for (let i = startDay - 1; i >= 0; i--) {
      this.calendarDates.push({
        day: 29 + (startDay - 1 - i),
        isCurrentMonth: false,
        events: []
      });
    }
    
    // Add current month days
    for (let i = 1; i <= daysInMonth; i++) {
      const events: CalendarEvent[] = [];
      
      // Add sample events
      if (i === 9) {
        events.push({ label: '6:30 PM', type: 'override' });
      } else if (i === 12 || i === 18) {
        events.push({ label: '6:30 PM', type: 'notStarted' });
      } else if (i === 24) {
        events.push({ label: '6:30 PM', type: 'success' });
      }
      
      this.calendarDates.push({
        day: i,
        isCurrentMonth: true,
        events: events
      });
    }
    
    // Add next month days to complete the grid
    const remainingDays = 42 - this.calendarDates.length;
    for (let i = 1; i <= remainingDays; i++) {
      this.calendarDates.push({
        day: i,
        isCurrentMonth: false,
        events: []
      });
    }
  }

  selectDate(date: CalendarDate): void {
    // Deselect previously selected date
    this.calendarDates.forEach(d => d.isSelected = false);
    
    // Select new date if it's in current month
    if (date.isCurrentMonth) {
      date.isSelected = true;
      this.selectedDate = date;
      this.showToast(`Selected date: September ${date.day}, 2024`);
    }
  }

  navigateCalendar(direction: 'prev' | 'next'): void {
    // Simple navigation for demo
    const months = ['January', 'February', 'March', 'April', 'May', 'June', 
                   'July', 'August', 'September', 'October', 'November', 'December'];
    const currentIndex = months.indexOf('September');
    
    if (direction === 'prev' && currentIndex > 0) {
      this.currentMonth = `${months[currentIndex - 1]} 2024`;
    } else if (direction === 'next' && currentIndex < 11) {
      this.currentMonth = `${months[currentIndex + 1]} 2024`;
    }
    
    this.generateCalendar();
    this.showToast(`Navigated to ${this.currentMonth}`);
  }

  // Restore & Email methods
  sendEmail(batchName: string): void {
    this.showToast(`Email sent for ${batchName}`);
    // Add your email sending logic here - if API available
  }

  removeData(batchName: string): void {
    // Create a backup before removing data
    this.createBackup(`Backup before removing ${batchName}`);
    this.showToast(`Data removed for ${batchName}`);
  }

  // Presets methods
  togglePresetForm(): void {
    this.showPresetForm = !this.showPresetForm;
    if (this.showPresetForm) {
      // Reset form
      this.newPresetName = '';
      this.presetConditions = [
        {
          type: 'where',
          column: 'Bwic Cover',
          operator: 'is equal to',
          value: 'JPMC'
        }
      ];
    }
  }

  addPresetCondition(): void {
    this.presetConditions.push({
      type: 'and',
      column: 'Bwic Cover',
      operator: 'is equal to',
      value: ''
    });
  }

  addPresetSubgroup(): void {
    this.presetConditions.push({
      type: 'subgroup',
      column: 'Bwic Cover',
      operator: 'is equal to',
      value: '',
      conditions: [
        {
          type: 'where',
          column: 'Bwic Cover',
          operator: 'is equal to',
          value: ''
        }
      ],
      isSubgroup: true
    });
  }

  removePresetCondition(index: number): void {
    this.presetConditions.splice(index, 1);
  }

  clearPreset(): void {
    this.newPresetName = '';
    this.presetConditions = [
      {
        type: 'where',
        column: 'Bwic Cover',
        operator: 'is equal to',
        value: 'JPMC'
      }
    ];
  }

  editPreset(preset: Preset): void {
    this.showToast(`Editing preset: ${preset.name}`);
    // Add your edit logic here
  }

  deletePreset(preset: Preset): void {
    if (!preset.id) {
      console.error('Cannot delete preset: missing ID');
      this.showToast('Cannot delete preset: missing ID');
      return;
    }

    if (!confirm('Are you sure you want to delete this preset?')) {
      return;
    }

    // Call backend API to delete
    this.presetsService.deletePreset(preset.id).subscribe({
      next: (response) => {
        // Remove from local array after successful backend deletion
        const index = this.presets.indexOf(preset);
        if (index > -1) {
          this.presets.splice(index, 1);
        }
        
        this.showToast('Preset deleted successfully!');
        console.log('✅ Preset deleted:', preset.name);
      },
      error: (error) => {
        console.error('❌ Failed to delete preset:', error);
        this.showToast('Failed to delete preset: ' + (error.error?.detail || error.message));
      }
    });
  }

  // Utility methods
  showToast(message: string): void {
    // Simple toast notification
    console.log('Toast:', message);
    // In a real app, you would use PrimeNG ToastService here
    alert(message); // Simple alert for demo
  }

  getDayColor(day: string, index: number): string {
    const colors: {[key: string]: string} = {
      'S': 'bg-green-500',
      'M': 'bg-red-500', 
      'T': index === 2 ? 'bg-green-400' : 'bg-yellow-500',
      'W': 'bg-teal-500',
      'F': 'bg-yellow-500'
    };
    return colors[day] || 'bg-gray-200';
  }

  getEventColor(type: string): string {
    const colors: {[key: string]: string} = {
      'success': 'bg-green-500',
      'error': 'bg-red-500',
      'skipped': 'bg-blue-500',
      'override': 'bg-blue-400',
      'notStarted': 'bg-yellow-500'
    };
    return colors[type] || 'bg-gray-500';
  }
}