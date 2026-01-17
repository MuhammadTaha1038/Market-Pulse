import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AutoCompleteModule } from 'primeng/autocomplete';
import { ActivatedRoute, Router } from '@angular/router';

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
    AutoCompleteModule
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

  // Column options for the rule builder
  columnOptions: any[] = [
    { label: 'Bwic Cover', value: 'Bwic Cover' },
    { label: 'Security Name', value: 'Security Name' },
    { label: 'Issuer', value: 'Issuer' },
    { label: 'Cusip', value: 'Cusip' },
    { label: 'Price', value: 'Price' },
    { label: 'Yield', value: 'Yield' }
  ];
  
  filteredColumnOptions: any[] = [];

  // Operator options
  operatorOptions: any[] = [
    { label: 'is equal to', value: 'is equal to' },
    { label: 'is not equal to', value: 'is not equal to' },
    { label: 'contains', value: 'contains' },
    { label: 'does not contain', value: 'does not contain' },
    { label: 'starts with', value: 'starts with' },
    { label: 'ends with', value: 'ends with' },
    { label: 'is greater than', value: 'is greater than' },
    { label: 'is less than', value: 'is less than' }
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

  restoreEmailLogs: RestoreEmailLog[] = [
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
    private router: Router
  ) {
    this.generateCalendar();
  }

  ngOnInit() {
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
  }

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
      option.label.toLowerCase().includes(query)
    );
  }

  filterOperator(event: any): void {
    const query = event.query.toLowerCase();
    this.filteredOperatorOptions = this.operatorOptions.filter(option =>
      option.label.toLowerCase().includes(query)
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
    if (this.newJobName && this.newJobTime) {
      const selectedDays = this.daysOfWeek.filter(d => d.selected).map(d => d.label);
      this.cornJobs.push({
        name: this.newJobName,
        time: this.newJobTime,
        frequency: selectedDays,
        repeat: this.newJobRepeat
      });
      
      // Reset form
      this.newJobName = '';
      this.newJobTime = '11:40';
      this.newJobRepeat = 'Yes';
      this.showToast('Job added successfully!');
    }
  }

  editJob(job: CornJob): void {
    // Enable editing mode
    job.isEditing = true;
    job.originalData = { ...job };
  }

  saveJob(job: CornJob): void {
    job.isEditing = false;
    job.originalData = undefined;
    this.showToast('Job updated successfully!');
  }

  cancelEdit(job: CornJob): void {
    if (job.originalData) {
      Object.assign(job, job.originalData);
    }
    job.isEditing = false;
    job.originalData = undefined;
  }

  deleteJob(job: CornJob): void {
    const index = this.cornJobs.indexOf(job);
    if (index > -1) {
      this.cornJobs.splice(index, 1);
      this.showToast('Job deleted successfully!');
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
    // Add your email sending logic here
  }

  removeData(batchName: string): void {
    this.showToast(`Data removed for ${batchName}`);
    // Add your data removal logic here
  }

  revertLog(log: RestoreEmailLog): void {
    this.showToast(`Reverted: ${log.description}`);
    // Add your revert logic here
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

  savePreset(): void {
    if (this.newPresetName) {
      // Convert conditions to preset format
      const conditions = this.presetConditions.map(c => ({
        owner: c.column,
        operator: c.operator,
        value: c.value
      }));
      
      this.presets.push({
        name: this.newPresetName,
        conditions: conditions
      });
      
      this.showToast('Preset saved successfully!');
      this.togglePresetForm();
    }
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
    const index = this.presets.indexOf(preset);
    if (index > -1) {
      this.presets.splice(index, 1);
      this.showToast('Preset deleted successfully!');
    }
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