import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

declare var XLSX: any;

export interface TableColumn {
    title: string;
    field: string;
    width?: number;
    headerFilter?: string;
    sorter?: string;
}

export interface TableData {
    columns: TableColumn[];
    data: any[];
}

@Injectable({
    providedIn: 'root'
})
export class TabulatorService {
    constructor(private http: HttpClient) {}

    /**
     * Parse Excel file and extract data
     */
    parseExcelFile(file: File): Promise<TableData> {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (event: any) => {
                try {
                    // Using SheetJS library (XLSX)
                    const data = new Uint8Array(event.target.result);
                    const workbook = XLSX.read(data, { type: 'array' });
                    const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
                    const rows = XLSX.utils.sheet_to_json(firstSheet);

                    if (rows.length === 0) {
                        reject(new Error('No data found in Excel file'));
                        return;
                    }

                    // Generate columns from first row keys
                    const columns: TableColumn[] = Object.keys(rows[0]).map(key => ({
                        title: key,
                        field: key,
                        headerFilter: 'input',
                        sorter: 'string',
                        width: 150
                    }));

                    resolve({
                        columns,
                        data: rows
                    });
                } catch (error) {
                    reject(new Error(`Failed to parse Excel file: ${error}`));
                }
            };
            reader.onerror = () => reject(new Error('Failed to read file'));
            reader.readAsArrayBuffer(file);
        });
    }

    /**
     * Fetch data from S3 bucket
     */
    fetchFromS3(bucketName: string, fileName: string): Observable<TableData> {
        return this.http.get<TableData>(`/api/s3/fetch`, {
            params: { bucketName, fileName }
        });
    }

    /**
     * Export table data to CSV
     */
    exportToCSV(data: any[], fileName: string): void {
        if (!data || data.length === 0) return;

        const headers = Object.keys(data[0]);
        const csvRows = [];
        
        // Add header row
        csvRows.push(headers.join(','));
        
        // Add data rows
        for (const row of data) {
            const values = headers.map((header) => {
                const value = row[header];
                return typeof value === 'string' && value.includes(',') ? `"${value}"` : value;
            });
            csvRows.push(values.join(','));
        }

        const csvContent = csvRows.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${fileName}_${new Date().toISOString().split('T')[0]}.csv`;
        link.click();
        window.URL.revokeObjectURL(url);
    }

    /**
     * Export table data to Excel
     */
    exportToExcel(data: any[], fileName: string): void {
        if (!data || data.length === 0) return;

        const worksheet = XLSX.utils.json_to_sheet(data);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, 'Data');
        XLSX.writeFile(workbook, `${fileName}_${new Date().toISOString().split('T')[0]}.xlsx`);
    }
}