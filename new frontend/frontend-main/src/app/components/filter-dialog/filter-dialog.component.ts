import { Component, Input, Output, EventEmitter, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DialogModule } from 'primeng/dialog';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { FormsModule } from '@angular/forms';


export interface FilterCondition {
  column: string;        // Backend column name (e.g. 'CUSIP', 'TICKER')
  columnDisplay: string; // Frontend display name (e.g. 'CUSIP', 'Ticker')
  operator: string;      // Backend operator (e.g. 'equals', 'contains')
  operatorDisplay: string; // Frontend display label (e.g. 'Equal to', 'Contains')
  values: string;
  values2?: string;      // For 'between' operator
  logicalOperator: 'AND' | 'OR';
}

export interface FilterSubgroup {
  id: number;
  logicalOperator: 'AND' | 'OR';
  conditions: FilterCondition[];
}

// Column mapping: frontend display name -> backend oracle column name
const COLUMN_MAPPING: { [key: string]: string } = {
  'Message ID': 'MESSAGE_ID',
  'Ticker': 'TICKER',
  'CUSIP': 'CUSIP',
  'Bias': 'BIAS',
  'Date': 'DATE',
  'Source': 'SOURCE',
  'Sector': 'SECTOR',
  'Rank': 'RANK',
  'Price': 'PRICE_LEVEL',
  'BID': 'BID',
  'ASK': 'ASK',
  'PX': 'PX',
  'Bwic Cover': 'BWIC_COVER',
  'Confidence': 'CONFIDENCE',
  'Cov Price': 'COV_PRICE',
  'Percent Diff': 'PERCENT_DIFF',
  'Price Diff': 'PRICE_DIFF'
};

@Component({
  selector: 'app-filter-dialog',
  standalone: true,
  imports: [
    CommonModule,
    DialogModule,
    ButtonModule,
    InputTextModule,
    FormsModule
  ],
  templateUrl: './filter-dialog.component.html',
  styleUrls: ['./filter-dialog.component.css']
})
export class FilterDialogComponent implements OnInit {
  @Input() visible: boolean = false;
  @Output() visibleChange = new EventEmitter<boolean>();
  @Output() filtersApplied = new EventEmitter<{
    conditions: FilterCondition[];
    subgroups: FilterSubgroup[];
  }>();

  // Filter data
  filterConditions: FilterCondition[] = [];
  filterSubgroups: FilterSubgroup[] = [];

  // Column options (display names)
  columnOptions = [
    'Message ID',
    'Ticker',
    'CUSIP',
    'Bias',
    'Date',
    'Source',
    'Sector',
    'Rank',
    'Price',
    'BID',
    'ASK',
    'PX',
    'Bwic Cover'
  ];

  // Operators aligned with backend (search.py + rules_service.py)
  operatorOptions = [
    { label: 'Equal to', value: 'equals' },
    { label: 'Not equal to', value: 'not equal to' },
    { label: 'Contains', value: 'contains' },
    { label: 'Starts with', value: 'starts_with' },
    { label: 'Ends with', value: 'ends with' },
    { label: 'Greater than', value: 'gt' },
    { label: 'Less than', value: 'lt' },
    { label: 'Greater than or equal', value: 'gte' },
    { label: 'Less than or equal', value: 'lte' },
    { label: 'Between', value: 'between' }
  ];

  logicalOperators = [
    { label: 'AND', value: 'AND' },
    { label: 'OR', value: 'OR' }
  ];

  ngOnInit() {
    if (this.filterConditions.length === 0) {
      this.addCondition();
    }
  }

  // ==================== COLUMN MAPPING ====================

  /** Map a frontend column display name to a backend oracle column name */
  getBackendColumn(displayName: string): string {
    return COLUMN_MAPPING[displayName] || displayName.toUpperCase();
  }

  /** Get operator display label from value */
  getOperatorLabel(value: string): string {
    const operator = this.operatorOptions.find(op => op.value === value);
    return operator ? operator.label : value;
  }

  // ==================== MAIN CONDITIONS ====================

  addCondition() {
    this.filterConditions.push({
      column: '',
      columnDisplay: '',
      operator: '',
      operatorDisplay: '',
      values: '',
      logicalOperator: 'AND'
    });
  }

  removeCondition(index: number) {
    this.filterConditions.splice(index, 1);
    if (this.filterConditions.length === 0) {
      this.addCondition();
    }
  }

  // ==================== SUBGROUPS ====================

  addSubgroup() {
    this.filterSubgroups.push({
      id: Date.now(),
      logicalOperator: 'AND',
      conditions: [{
        column: '',
        columnDisplay: '',
        operator: '',
        operatorDisplay: '',
        values: '',
        logicalOperator: 'AND'
      }]
    });
  }

  removeSubgroup(subgroupId: number) {
    const index = this.filterSubgroups.findIndex(s => s.id === subgroupId);
    if (index > -1) {
      this.filterSubgroups.splice(index, 1);
    }
  }

  addSubgroupCondition(subgroupId: number) {
    const subgroup = this.filterSubgroups.find(s => s.id === subgroupId);
    if (subgroup) {
      subgroup.conditions.push({
        column: '',
        columnDisplay: '',
        operator: '',
        operatorDisplay: '',
        values: '',
        logicalOperator: 'AND'
      });
    }
  }

  removeSubgroupCondition(subgroupId: number, conditionIndex: number) {
    const subgroup = this.filterSubgroups.find(s => s.id === subgroupId);
    if (subgroup) {
      subgroup.conditions.splice(conditionIndex, 1);
      if (subgroup.conditions.length === 0) {
        this.removeSubgroup(subgroupId);
      }
    }
  }

  // ==================== ACTIONS ====================

  removeAllFilters() {
    this.filterConditions = [];
    this.filterSubgroups = [];
    this.addCondition();
  }

  applyFilters() {
    // Map conditions: set backend column names and operator display labels
    const mappedConditions = this.filterConditions
      .filter(c => c.columnDisplay && c.operator && c.values)
      .map(c => ({
        ...c,
        column: this.getBackendColumn(c.columnDisplay),
        operatorDisplay: this.getOperatorLabel(c.operator)
      }));

    const mappedSubgroups = this.filterSubgroups.map(sg => ({
      ...sg,
      conditions: sg.conditions
        .filter(c => c.columnDisplay && c.operator && c.values)
        .map(c => ({
          ...c,
          column: this.getBackendColumn(c.columnDisplay),
          operatorDisplay: this.getOperatorLabel(c.operator)
        }))
    }));

    this.filtersApplied.emit({
      conditions: mappedConditions,
      subgroups: mappedSubgroups
    });
    this.closeDialog();
  }

  closeDialog() {
    this.visible = false;
    this.visibleChange.emit(false);
  }

  /** Check if operator is 'between' (needs two value inputs) */
  isBetweenOperator(operator: string): boolean {
    return operator === 'between';
  }
}
