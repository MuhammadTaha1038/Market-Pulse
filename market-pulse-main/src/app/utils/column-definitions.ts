export interface ColumnDefinition {
  oracleName: string;
  displayName: string;
  dataType: string;
  required: boolean;
  field: string;
  cssClass?: string;
  formatter?: (value: any) => string;
}

/**
 * All available column definitions matching column_config.json
 */
export const ALL_COLUMNS: ColumnDefinition[] = [
  {
    oracleName: 'MESSAGE_ID',
    displayName: 'Message ID',
    dataType: 'INTEGER',
    required: true,
    field: 'messageId',
    cssClass: 'font-mono'
  },
  {
    oracleName: 'TICKER',
    displayName: 'Ticker',
    dataType: 'VARCHAR',
    required: true,
    field: 'ticker'
  },
  {
    oracleName: 'SECTOR',
    displayName: 'Sector',
    dataType: 'VARCHAR',
    required: true,
    field: 'sector'
  },
  {
    oracleName: 'CUSIP',
    displayName: 'CUSIP',
    dataType: 'VARCHAR',
    required: true,
    field: 'cusip',
    cssClass: 'font-mono'
  },
  {
    oracleName: 'DATE',
    displayName: 'Date',
    dataType: 'DATE',
    required: true,
    field: 'date'
  },
  {
    oracleName: 'PRICE_LEVEL',
    displayName: 'Price Level',
    dataType: 'FLOAT',
    required: true,
    field: 'priceLevel',
    formatter: (value) => value?.toFixed(2) || 'N/A'
  },
  {
    oracleName: 'BID',
    displayName: 'BID',
    dataType: 'FLOAT',
    required: false,
    field: 'bid',
    cssClass: 'text-green-600 font-medium',
    formatter: (value) => value?.toFixed(1) || 'N/A'
  },
  {
    oracleName: 'ASK',
    displayName: 'ASK',
    dataType: 'FLOAT',
    required: false,
    field: 'ask',
    cssClass: 'text-red-600 font-medium',
    formatter: (value) => value?.toFixed(1) || 'N/A'
  },
  {
    oracleName: 'PX',
    displayName: 'PX',
    dataType: 'FLOAT',
    required: true,
    field: 'px',
    formatter: (value) => value?.toFixed(2) || 'N/A'
  },
  {
    oracleName: 'SOURCE',
    displayName: 'Source',
    dataType: 'VARCHAR',
    required: true,
    field: 'source'
  },
  {
    oracleName: 'BIAS',
    displayName: 'Bias',
    dataType: 'VARCHAR',
    required: true,
    field: 'bias'
  },
  {
    oracleName: 'RANK',
    displayName: 'Rank',
    dataType: 'INTEGER',
    required: true,
    field: 'rank'
  },
  {
    oracleName: 'COV_PRICE',
    displayName: 'Coverage Price',
    dataType: 'FLOAT',
    required: false,
    field: 'covPrice',
    formatter: (value) => value?.toFixed(2) || 'N/A'
  },
  {
    oracleName: 'PERCENT_DIFF',
    displayName: 'Percent Diff',
    dataType: 'FLOAT',
    required: false,
    field: 'percentDiff',
    formatter: (value) => value ? `${value.toFixed(2)}%` : 'N/A'
  },
  {
    oracleName: 'PRICE_DIFF',
    displayName: 'Price Diff',
    dataType: 'FLOAT',
    required: false,
    field: 'priceDiff',
    formatter: (value) => value?.toFixed(2) || 'N/A'
  },
  {
    oracleName: 'CONFIDENCE',
    displayName: 'Confidence',
    dataType: 'INTEGER',
    required: false,
    field: 'confidence',
    formatter: (value) => value !== null && value !== undefined ? `${value}/10` : 'N/A'
  },
  {
    oracleName: 'DATE_1',
    displayName: 'Date 1',
    dataType: 'DATE',
    required: false,
    field: 'date1'
  },
  {
    oracleName: 'DIFF_STATUS',
    displayName: 'Diff Status',
    dataType: 'VARCHAR',
    required: false,
    field: 'diffStatus'
  }
];

/**
 * Get column definitions filtered by visible column names
 * @param visibleColumnNames Array of oracle column names (e.g., ['MESSAGE_ID', 'TICKER'])
 * @returns Filtered array of ColumnDefinition
 */
export function getVisibleColumnDefinitions(visibleColumnNames: string[]): ColumnDefinition[] {
  if (!visibleColumnNames || visibleColumnNames.length === 0) {
    return ALL_COLUMNS;
  }
  
  return ALL_COLUMNS.filter(col => visibleColumnNames.includes(col.oracleName));
}
