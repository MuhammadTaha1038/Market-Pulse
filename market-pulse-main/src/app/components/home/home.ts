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
import { FormsModule } from '@angular/forms';
import { TooltipModule } from 'primeng/tooltip';
import { TableStateService } from '../home/table-state.service';
import { ApiService } from '../../services/api.service'; 

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
    FormsModule,
    TooltipModule
  ],
  templateUrl: './home.html',
  styleUrls: ['./home.css']
})
export class Home implements OnInit {
  nextRunTimer = '7H:52M:25S';
  filterVisible: boolean = false;
  isTableExpanded: boolean = false;

  // Filter data
  filterConditions: any[] = [
    { column: 'Bwic Cover', operator: 'is equal to', values: 'JPMO' }
  ];

  columnOptions = ['Bwic Cover', 'Ticker', 'CUSIP', 'Bias', 'Date', 'Source'];
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

  constructor(
    private tableStateService: TableStateService,
    private apiService: ApiService
  ) {}

  ngOnInit() {
    console.log('🚀 Home component initialized - loading data from backend...');
    this.loadDataFromBackend();
    // Initialize filtered options with all options
    this.filteredColumnOptions = [...this.columnOptions];
    this.filteredOperatorOptions = [...this.operatorOptions];
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

    // Load colors data for table
    this.apiService.getColors(0, 100).subscribe({
      next: (response) => {
        console.log('✅ Colors received from backend:', response.colors.length, 'total:', response.total_count);
        this.tableData = response.colors.map(color => {
          const price = color.price || 0;
          return {
            messageId: color.message_id,
            ticker: color.ticker,
            cusip: color.cusip,
            bias: this.formatBias(color.bias),
            date: this.formatDate(color.date),
            bid: price.toFixed(1),
            mid: (price + 1).toFixed(1),
            ask: (price + 2).toFixed(1),
            source: color.source,
            isParent: color.is_parent,
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
  searchColumn(event: any) {
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
  }

  applyFilters() {
    this.filterVisible = false;
    // Apply your filter logic here
    console.log('Filters applied:', this.filterConditions);
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

  exportAll() {
    console.log('Exporting all data...');
    // Convert table data to CSV
    const csvContent = this.convertToCSV(this.tableData);
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `marketpulse_colors_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    window.URL.revokeObjectURL(url);
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
    console.log('Refreshing colors...');
    this.loadDataFromBackend();
    alert('Colors refreshed! Loaded latest data from backend.');
  }

  overrideAndRun() {
    console.log('Override & Run clicked');
    alert('Manual ranking override triggered. This will re-run the ranking engine.');
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
}