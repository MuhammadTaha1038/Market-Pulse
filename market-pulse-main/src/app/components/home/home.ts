import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CardModule } from 'primeng/card';
import { ChartModule } from 'primeng/chart';
import { TableModule } from 'primeng/table';
import { ChipModule } from 'primeng/chip';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { BadgeModule } from 'primeng/badge';
import { DialogModule } from 'primeng/dialog';
import { AutoCompleteModule } from 'primeng/autocomplete';
import { ToastModule } from 'primeng/toast';
import { FormsModule } from '@angular/forms';
import { TooltipModule } from 'primeng/tooltip';
import { Router } from '@angular/router';
import { TableStateService } from '../home/table-state.service';
import { ApiService } from '../../services/api.service';
import { PresetsService, Preset } from '../../services/presets.service';
import { CLOSelectionService, UserCLOSelection } from '../../services/clo-selection.service';
import { AutomationService } from '../../services/automation.service';
import { ColumnDefinition, getVisibleColumnDefinitions } from '../../utils/column-definitions';
import { MessageService } from 'primeng/api'; 

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [
    CommonModule, 
    CardModule, 
    ChartModule, 
    TableModule,
    ChipModule, 
    ButtonModule, 
    InputTextModule, 
    BadgeModule,
    DialogModule,
    AutoCompleteModule,
    ToastModule,
    FormsModule,
    TooltipModule
  ],
  providers: [MessageService],
  templateUrl: './home.html',
  styleUrls: ['./home.css']
})
export class Home implements OnInit {
  
  nextRunTimer = '7H:52M:25S';
  filterVisible: boolean = false;
  isTableExpanded: boolean = false;
  presets: Preset[] = [];
  selectedPreset: Preset | null = null;
  filteredPresets: Preset[] = [];
  userCLOSelection: UserCLOSelection | null = null;
  visibleColumns: string[] = [];
  displayColumns: ColumnDefinition[] = [];

  // Filter data
  filterConditions: any[] = [
    { column: 'Bwic Cover', operator: 'is equal to', values: 'JPMO' }
  ];

  columnOptions: string[] = []; // Will be populated from CLO visible columns
  filteredColumnOptions: string[] = [];
  
  // Client-Specified Operators
  operatorOptions = [
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
  filteredOperatorOptions: string[] = [];

  availableColorsChart: any;
  availableColorsOptions: any;

  // Table data - will be loaded from backend
  tableData: any[] = [];
  
  // Search functionality
  searchColumn: string = 'MESSAGE_ID';  // Default search column
  searchValue: string = '';
  searchColumnOptions: { label: string; value: string }[] = [];

  constructor(
    private tableStateService: TableStateService,
    private apiService: ApiService,
    private presetsService: PresetsService,
    private cloSelectionService: CLOSelectionService,
    private automationService: AutomationService,
    private messageService: MessageService,
    private router: Router
  ) {}

  async ngOnInit() {
    console.log('🚀 Home component initialized - loading data from backend...');
    
    // Refresh CLO columns from backend to ensure we have the latest configuration
    await this.cloSelectionService.refreshColumnsFromBackend();
    
    // Check if user has selected CLO
    this.userCLOSelection = this.cloSelectionService.getCurrentSelection();
    
    if (!this.userCLOSelection) {
      console.log('❌ No CLO selection found - redirecting to CLO selection page');
      this.router.navigate(['/clo-selection']);
      return;
    }
    
    console.log('✅ User CLO selection found:', this.userCLOSelection.cloName);
    console.log('📊 Visible columns:', this.userCLOSelection.visibleColumns);
    this.visibleColumns = this.userCLOSelection.visibleColumns;
    
    // Set display columns based on user's CLO mapping
    this.displayColumns = getVisibleColumnDefinitions(this.visibleColumns);
    console.log('🔍 Display columns:', this.displayColumns.length, 'columns');
    
    // Initialize column options from visible columns for filters/rules/presets
    this.columnOptions = this.displayColumns.map(col => col.displayName);
    console.log('📋 Available filter columns:', this.columnOptions);
    
    // Initialize search column options
    this.searchColumnOptions = this.displayColumns.map(col => ({
      label: col.displayName,
      value: col.oracleName
    }));
    
    this.loadDataFromBackend();
    this.loadPresets();
    
    // Initialize filtered options with CLO-visible columns only
    this.filteredColumnOptions = [...this.columnOptions];
    this.filteredOperatorOptions = [...this.operatorOptions];
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

  private loadDataFromBackend() {
    console.log('📡 Fetching data from backend API...');
    
    // Load monthly stats for chart
    this.apiService.getMonthlyStats().subscribe({
      next: (response) => {
        console.log('✅ Monthly stats received:', response.stats.length, 'months');
        const data = response.stats.map(stat => stat.count);
        const labels = response.stats.map(stat => {
          const date = new Date(stat.month);
          return date.toLocaleDateString('en-US', { month: 'short' });
        });
        this.initChart(data, labels);
      },
      error: (error) => {
        console.error('❌ Error loading monthly stats:', error);
        console.log('Falling back to hardcoded chart data');
        // Fallback to hardcoded data
        this.initChart();
      }
    });

    // Load colors data for table (PERFORMANCE: limit to 50 rows for better overview)
    const cloId = this.userCLOSelection?.cloId;
    this.apiService.getColors(0, 50, undefined, cloId).subscribe({
      next: (response) => {
        console.log('✅ Colors received from backend:', response.colors.length, 'total:', response.total_count);
        console.log('📊 CLO ID sent:', cloId);
        this.tableData = response.colors.map(color => {
          return {
            // All ColorProcessed fields mapped
            messageId: color.message_id,
            ticker: color.ticker || '',
            sector: color.sector || '',
            cusip: color.cusip || '',
            date: color.date ? this.formatDate(color.date) : 'N/A',
            priceLevel: color.price_level ?? null,
            bid: color.bid ?? null,
            ask: color.ask ?? null,
            px: color.px ?? null,
            source: color.source || '',
            bias: color.bias ? this.formatBias(color.bias) : '',
            rank: color.rank ?? null,
            covPrice: color.cov_price ?? null,
            percentDiff: color.percent_diff ?? null,
            priceDiff: color.price_diff ?? null,
            confidence: color.confidence ?? null,
            date1: color.date_1 ? this.formatDate(color.date_1) : 'N/A',
            diffStatus: color.diff_status || '',
            isParent: color.is_parent || false,
            childrenCount: color.children_count || 0
          };
        });
        console.log('✅ Loaded', this.tableData.length, 'colors from backend');
        console.log('Sample data:', this.tableData[0]);
      },
      error: (error) => {
        console.error('❌ Error loading colors from backend:', error);
        console.log('Error details:', error.message);
        console.log('Using fallback hardcoded data');
        // Keep hardcoded data as fallback
      }
    });

    // Load next run time
    this.apiService.getNextRunTime().subscribe({
      next: (response) => {
        console.log('✅ Next run time received:', response.next_run);
        this.nextRunTimer = response.next_run;
      },
      error: (error) => {
        console.error('❌ Error loading next run time:', error);
      }
    });
  }

  private formatBias(bias: string): string {
    return bias.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  private formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year: 'numeric' });
  }

  private initChart(data?: number[], labels?: string[]) {
    // Use provided data or fallback to hardcoded pattern
    const chartData = data || [1200, 2100, 1200, 2100, 1200, 2100, 1200, 2100, 1200, 2100, 1200, 2100];
    const chartLabels = labels || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    this.availableColorsChart = {
      labels: chartLabels,
      datasets: [{
        label: 'Colors',
        data: chartData,
        backgroundColor: () => {
          // Create single gradient array for all bars
          const gradients = [];
          for (let i = 0; i < chartData.length; i++) {
            gradients.push('#6B7280'); // Use solid gray color
          }
          return gradients;
        },
        borderRadius: 6,
        barThickness: 28,
        categoryPercentage: 0.8,
        barPercentage: 0.9,
        borderWidth: 0
      }]
    };

    this.availableColorsOptions = {
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          enabled: true,
          callbacks: {
            label: (context: any) => {
              const value = context.parsed.y;
              return value >= 1000 ? `${(value / 1000).toFixed(1)}k Colors` : `${value} Colors`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            color: '#6B7280',
            font: { size: 11 }
          },
          border: { display: false }
        },
        y: {
          grid: { color: '#E5E7EB', drawTicks: false },
          ticks: {
            color: '#6B7280',
            font: { size: 11 },
            callback: (value: any) => value >= 1000 ? `${value / 1000}k` : value,
            padding: 10
          },
          border: { display: false },
          beginAtZero: true,
          max: 2500
        }
      },
      animation: {
        duration: 800
      }
    };
  }

  // AutoComplete search methods
  filterColumns(event: any) {
    const query = event.query.toLowerCase();
    this.filteredColumnOptions = this.columnOptions.filter(option => 
      option.toLowerCase().includes(query)
    );
  }

  searchOperator(event: any) {
    const query = event.query.toLowerCase();
    this.filteredOperatorOptions = this.operatorOptions.filter(option => 
      option.toLowerCase().includes(query)
    );
  }

  // Filter methods
  showFilterDialog() {
    this.filterVisible = true;
  }

  addCondition() {
    this.filterConditions.push({ column: 'Bwic Cover', operator: 'is equal to', values: '' });
  }

  addSubgroup() {
    // Implementation for adding subgroup
    console.log('Add subgroup clicked');
  }

  addGroup() {
    // Implementation for adding group
    console.log('Add group clicked');
  }

  removeAllFilters() {
    this.filterConditions = [];
    this.selectedPreset = null;
  }

  applyPreset() {
    if (!this.selectedPreset || !this.selectedPreset.id) {
      this.messageService.add({
        severity: 'warn',
        summary: 'No Preset Selected',
        detail: 'Please select a preset to apply'
      });
      return;
    }
    
    const presetId = this.selectedPreset.id; // Store id to avoid undefined issues
    console.log('📋 Applying preset:', this.selectedPreset.name);
    
    // Fetch fresh data from backend and apply preset filter
    const cloId = this.userCLOSelection?.cloId;
    this.apiService.getColors(0, 500, undefined, cloId).subscribe({
      next: (response) => {
        console.log('✅ Fetched data for preset filtering:', response.colors.length, 'rows');
        console.log('Sample color data:', response.colors[0]);
        
        // Convert backend data to table format
        const backendData = response.colors.map(color => ({
          MESSAGE_ID: color.message_id,
          TICKER: color.ticker || '',
          SECTOR: color.sector || '',
          CUSIP: color.cusip || '',
          DATE: color.date,
          PRICE_LEVEL: color.price_level,
          BID: color.bid,
          ASK: color.ask,
          PX: color.px,
          SOURCE: color.source || '',
          BIAS: color.bias || '',
          RANK: color.rank,
          COV_PRICE: color.cov_price,
          PERCENT_DIFF: color.percent_diff,
          PRICE_DIFF: color.price_diff,
          CONFIDENCE: color.confidence,
          DATE_1: color.date_1,
          DIFF_STATUS: color.diff_status || '',
          IS_PARENT: color.is_parent,
          PARENT_MESSAGE_ID: color.parent_message_id,
          CHILDREN_COUNT: color.children_count
        }));
        
        console.log('Converted backend data sample:', backendData[0]);
        console.log('Calling applyPreset with presetId:', presetId, 'and', backendData.length, 'rows');
        
        // Apply preset via backend
        this.presetsService.applyPreset(presetId, backendData).subscribe({
          next: (presetResponse) => {
            console.log('✅ Preset applied:', presetResponse.filtered_rows, '/', presetResponse.total_rows);
            
            // Convert filtered data back to table format
            this.tableData = presetResponse.data.map(row => ({
              messageId: row.MESSAGE_ID,
              ticker: row.TICKER || '',
              sector: row.SECTOR || '',
              cusip: row.CUSIP || '',
              date: row.DATE ? this.formatDate(row.DATE) : 'N/A',
              priceLevel: row.PRICE_LEVEL ?? null,
              bid: row.BID ?? null,
              ask: row.ASK ?? null,
              px: row.PX ?? null,
              source: row.SOURCE || '',
              bias: row.BIAS ? this.formatBias(row.BIAS) : '',
              rank: row.RANK ?? null,
              covPrice: row.COV_PRICE ?? null,
              percentDiff: row.PERCENT_DIFF ?? null,
              priceDiff: row.PRICE_DIFF ?? null,
              confidence: row.CONFIDENCE ?? null,
              date1: row.DATE_1 ? this.formatDate(row.DATE_1) : 'N/A',
              diffStatus: row.DIFF_STATUS || '',
              isParent: row.IS_PARENT || false,
              childrenCount: row.CHILDREN_COUNT || 0
            }));
            
            this.messageService.add({
              severity: 'success',
              summary: 'Preset Applied',
              detail: `Showing ${presetResponse.filtered_rows} of ${presetResponse.total_rows} rows`
            });
            
            this.filterVisible = false;
          },
          error: (error) => {
            console.error('❌ Error applying preset:', error);
            this.messageService.add({
              severity: 'error',
              summary: 'Preset Failed',
              detail: error.message || 'Failed to apply preset'
            });
          }
        });
      },
      error: (error) => {
        console.error('❌ Error fetching data:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Data Fetch Failed',
          detail: 'Failed to load data for filtering'
        });
      }
    });
  }

  applyFilters() {
    if (this.filterConditions.length === 0) {
      this.messageService.add({
        severity: 'warn',
        summary: 'No Filters',
        detail: 'Please add at least one filter condition'
      });
      return;
    }
    
    console.log('📋 Applying filters:', this.filterConditions);
    
    // Fetch fresh data and apply client-side filtering
    const cloId = this.userCLOSelection?.cloId;
    this.apiService.getColors(0, 500, undefined, cloId).subscribe({
      next: (response) => {
        let filteredData = response.colors;
        
        // Apply each condition
        for (const condition of this.filterConditions) {
          if (!condition.column || !condition.operator || !condition.values) {
            continue;
          }
          
          // Map display name back to field name
          const columnDef = this.displayColumns.find(col => col.displayName === condition.column);
          if (!columnDef) continue;
          
          const fieldName = columnDef.oracleName.toLowerCase();
          const filterValue = condition.values.toString().toLowerCase();
          
          filteredData = filteredData.filter(color => {
            let cellValue = '';
            
            // Get the value based on oracle name
            switch (columnDef.oracleName) {
              case 'MESSAGE_ID': cellValue = color.message_id?.toString() || ''; break;
              case 'TICKER': cellValue = color.ticker || ''; break;
              case 'SECTOR': cellValue = color.sector || ''; break;
              case 'CUSIP': cellValue = color.cusip || ''; break;
              case 'SOURCE': cellValue = color.source || ''; break;
              case 'BIAS': cellValue = color.bias || ''; break;
              case 'RANK': cellValue = color.rank?.toString() || ''; break;
              case 'PRICE_LEVEL': cellValue = color.price_level?.toString() || ''; break;
              case 'BID': cellValue = color.bid?.toString() || ''; break;
              case 'ASK': cellValue = color.ask?.toString() || ''; break;
              default: cellValue = '';
            }
            
            cellValue = cellValue.toLowerCase();
            
            // Apply operator
            switch (condition.operator) {
              case 'equal to':
              case 'is equal to':
                return cellValue === filterValue;
              case 'not equal to':
                return cellValue !== filterValue;
              case 'contains':
                return cellValue.includes(filterValue);
              case 'starts with':
                return cellValue.startsWith(filterValue);
              case 'ends with':
                return cellValue.endsWith(filterValue);
              case 'less than':
                return parseFloat(cellValue) < parseFloat(filterValue);
              case 'greater than':
                return parseFloat(cellValue) > parseFloat(filterValue);
              case 'less than equal to':
                return parseFloat(cellValue) <= parseFloat(filterValue);
              case 'greater than equal to':
                return parseFloat(cellValue) >= parseFloat(filterValue);
              default:
                return true;
            }
          });
        }
        
        // Convert to table format
        this.tableData = filteredData.map(color => ({
          messageId: color.message_id,
          ticker: color.ticker || '',
          sector: color.sector || '',
          cusip: color.cusip || '',
          date: color.date ? this.formatDate(color.date) : 'N/A',
          priceLevel: color.price_level ?? null,
          bid: color.bid ?? null,
          ask: color.ask ?? null,
          px: color.px ?? null,
          source: color.source || '',
          bias: color.bias ? this.formatBias(color.bias) : '',
          rank: color.rank ?? null,
          covPrice: color.cov_price ?? null,
          percentDiff: color.percent_diff ?? null,
          priceDiff: color.price_diff ?? null,
          confidence: color.confidence ?? null,
          date1: color.date_1 ? this.formatDate(color.date_1) : 'N/A',
          diffStatus: color.diff_status || '',
          isParent: color.is_parent || false,
          childrenCount: color.children_count || 0
        }));
        
        this.messageService.add({
          severity: 'success',
          summary: 'Filters Applied',
          detail: `Showing ${this.tableData.length} of ${response.colors.length} rows`
        });
        
        this.filterVisible = false;
        console.log('✅ Filtered data:', this.tableData.length, 'rows');
      },
      error: (error) => {
        console.error('❌ Error applying filters:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Filter Failed',
          detail: 'Failed to apply filters'
        });
      }
    });
  }

  removeCondition(index: number) {
    this.filterConditions.splice(index, 1);
  }

  // Table expansion methods
  toggleTableExpansion() {
    this.isTableExpanded = !this.isTableExpanded;
    this.tableStateService.setTableExpanded(this.isTableExpanded);
  }

  // Button handlers
  fetchData() {
    console.log('Fetching latest data...');
    this.loadDataFromBackend();
  }
  
  searchData() {
    if (!this.searchValue.trim()) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Search Required',
        detail: 'Please enter a search value'
      });
      return;
    }
    
    console.log(`🔍 Searching ${this.searchColumn} = ${this.searchValue}`);
    const cloId = this.userCLOSelection?.cloId;
    
    // Build search params based on selected column
    let searchParams: any = {
      skip: 0,
      limit: 100,  // Get more results for search
      cloId: cloId
    };
    
    // Map search column to API parameter
    switch (this.searchColumn) {
      case 'MESSAGE_ID':
        searchParams.message_id = parseInt(this.searchValue);
        break;
      case 'CUSIP':
        searchParams.cusip = this.searchValue;
        break;
      case 'TICKER':
        searchParams.ticker = this.searchValue;
        break;
      case 'SECTOR':
        searchParams.asset_class = this.searchValue;
        break;
      case 'SOURCE':
        searchParams.source = this.searchValue;
        break;
      case 'BIAS':
        searchParams.bias = this.searchValue;
        break;
      default:
        // For other columns, we'll need to filter client-side after fetching
        console.log(`Column ${this.searchColumn} not supported for backend search, will filter client-side`);
    }
    
    this.apiService.getColors(
      searchParams.skip, 
      searchParams.limit, 
      searchParams.asset_class,
      searchParams.cloId,
      searchParams.cusip,
      searchParams.ticker,
      searchParams.message_id,
      searchParams.source,
      searchParams.bias
    ).subscribe({
      next: (response) => {
        this.tableData = response.colors.map(color => ({
          messageId: color.message_id,
          ticker: color.ticker || '',
          sector: color.sector || '',
          cusip: color.cusip || '',
          date: color.date ? this.formatDate(color.date) : 'N/A',
          priceLevel: color.price_level ?? null,
          bid: color.bid ?? null,
          ask: color.ask ?? null,
          px: color.px ?? null,
          source: color.source || '',
          bias: color.bias ? this.formatBias(color.bias) : '',
          rank: color.rank ?? null,
          covPrice: color.cov_price ?? null,
          percentDiff: color.percent_diff ?? null,
          priceDiff: color.price_diff ?? null,
          confidence: color.confidence ?? null,
          date1: color.date_1 ? this.formatDate(color.date_1) : 'N/A',
          diffStatus: color.diff_status || '',
          isParent: color.is_parent || false,
          childrenCount: color.children_count || 0
        }));
        
        this.messageService.add({
          severity: 'success',
          summary: 'Search Complete',
          detail: `Found ${this.tableData.length} results`
        });
        
        console.log('✅ Search results:', this.tableData.length);
      },
      error: (error) => {
        console.error('❌ Search error:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Search Failed',
          detail: error.message || 'Failed to search data'
        });
      }
    });
  }

  exportAll() {
    console.log('Exporting all visible data...');
    // Export all current table data with all columns
    const exportData = this.tableData.map(row => {
      const exportRow: any = {};
      this.displayColumns.forEach(col => {
        exportRow[col.displayName] = this.getCellValue(row, col);
      });
      return exportRow;
    });
    
    const csvContent = this.convertToCSV(exportData);
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    link.download = `security_search_export_${timestamp}.csv`;
    link.click();
    window.URL.revokeObjectURL(url);
    
    this.messageService.add({
      severity: 'success',
      summary: 'Export Complete',
      detail: `Exported ${this.tableData.length} rows`
    });
  }

  private convertToCSV(data: any[]): string {
    if (!data || data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const csvRows = [];
    
    // Add header row
    csvRows.push(headers.join(','));
    
    // Add data rows
    for (const row of data) {
      const values = headers.map(header => {
        const value = row[header];
        return typeof value === 'string' && value.includes(',') ? `"${value}"` : value;
      });
      csvRows.push(values.join(','));
    }
    
    return csvRows.join('\n');
  }

  importViaExcel() {
    console.log('Import ID via Excel clicked');
    alert('Excel import feature - Upload file with Message IDs to filter');
  }

  refreshColors() {
    console.log('🔄 Refreshing colors - triggering automation...');
    
    this.messageService.add({
      severity: 'info',
      summary: 'Automation Started',
      detail: 'Running color automation with rules...'
    });
    
    this.automationService.triggerAutomation().subscribe({
      next: (response) => {
        if (response.success) {
          this.messageService.add({
            severity: 'success',
            summary: 'Automation Complete',
            detail: `Processed ${response.processed_count} colors. Applied ${response.rules_applied} rules.`
          });
          
          // Reload table data
          this.loadDataFromBackend();
          
          console.log('✅ Automation completed:', response);
        } else {
          this.messageService.add({
            severity: 'error',
            summary: 'Automation Failed',
            detail: response.error || 'Failed to run automation'
          });
        }
      },
      error: (error) => {
        console.error('❌ Automation failed:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Automation Error',
          detail: error.error?.detail || 'Failed to trigger automation'
        });
      }
    });
  }

  overrideAndRun() {
    console.log('⚡ Override & Run - bypassing all rules...');
    
    this.messageService.add({
      severity: 'warn',
      summary: 'Override Mode',
      detail: 'Running without rules exclusion...'
    });
    
    this.automationService.overrideAndRun().subscribe({
      next: (response) => {
        if (response.success) {
          this.messageService.add({
            severity: 'success',
            summary: 'Override Complete',
            detail: `Processed ${response.processed_count} colors without rules.`
          });
          
          // Reload table data
          this.loadDataFromBackend();
          
          console.log('✅ Override run completed:', response);
        } else {
          this.messageService.add({
            severity: 'error',
            summary: 'Override Failed',
            detail: response.error || 'Failed to run override'
          });
        }
      },
      error: (error) => {
        console.error('❌ Override failed:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Override Error',
          detail: error.error?.detail || 'Failed to run override'
        });
      }
    });
  }

  importSample() {
    console.log('Import Sample clicked');
    // Navigate to color process page
    window.location.href = '/color-type';
  }

  rulesAndPresets() {
    console.log('Rules & Presets clicked');
    window.location.href = '/settings?section=rules';
  }

  restoreLastRun() {
    console.log('Restore last run clicked');
    alert('Restore last run: This will reload the previous ranking results.');
  }

  cronJobsAndTime() {
    console.log('Cron Jobs & Time clicked');
    window.location.href = '/settings?section=corn-jobs';
  }

  /**
   * Navigate to CLO selector to change asset class
   */
  changeCLOSelection() {
    this.router.navigate(['/clo-selection']);
  }

  /**
   * Get formatted CLO selection display
   */
  getCLOSelectionDisplay(): string {
    if (this.userCLOSelection) {
      return `${this.userCLOSelection.cloName} (${this.userCLOSelection.mainCLO})`;
    }
    return 'No selection';
  }

  /**
   * Get formatted cell value based on column definition
   */
  getCellValue(row: any, column: ColumnDefinition): string {
    const value = row[column.field];
    
    if (value === null || value === undefined) {
      return '-';
    }
    
    // Apply formatter if defined
    if (column.formatter) {
      return column.formatter(value);
    }
    
    return value.toString();
  }

  /**
   * Get CSS classes for a table cell
   */
  getCellClass(row: any, column: ColumnDefinition): string {
    let classes = column.cssClass || '';
    
    // Special handling for BIAS column
    if (column.oracleName === 'BIAS') {
      if (row.bias === 'BWIC_COVER') {
        classes += ' bg-purple-100 text-purple-700 px-3 py-1 rounded-full text-xs font-medium';
      } else {
        classes += ' bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-xs font-medium';
      }
    }
    
    // Special handling for SOURCE column
    if (column.oracleName === 'SOURCE') {
      classes += ' text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded';
    }
    
    return classes;
  }

  /**
   * Check if column should be displayed (for special rendering)
   */
  shouldRenderAsChip(column: ColumnDefinition): boolean {
    return column.oracleName === 'BIAS' || column.oracleName === 'SOURCE';
  }
}

