import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { FileUploadModule } from 'primeng/fileupload';
import { InputTextModule } from 'primeng/inputtext';
import { TagModule } from 'primeng/tag';
import { FormsModule } from '@angular/forms';

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
    FormsModule
  ],
  templateUrl: './manual-color.html',
  styleUrls: ['./manual-color.css']
})
export class ManualColor {
  searchText = '';
  showImportDialog = false;

  colors: ColorData[] = [
    { messageId: 'TRB5829340A63B91', ticketId: 'BESXP15 12X A1', cusip: '961644AC4', bias: 'BWC_COVER', date: '07/19/2025', bid: 100.2, mid: 101.3, ask: 102.2, source: 'Bwc Cover' },
    { messageId: 'TRB5829340A63B92', ticketId: 'BESXP15 12X A1', cusip: '961644AC4', bias: 'BID', date: '07/19/2025', bid: 100.3, mid: 101.2, ask: 102.2, source: 'Bid' },
    { messageId: 'TRB5829340A63B93', ticketId: 'BESXP15 12X A1', cusip: '961644AC4', bias: 'MARKET', date: '07/19/2025', bid: 100.3, mid: 101.3, ask: 102.2, source: 'Market' },
    { messageId: 'TRB5829340A63B94', ticketId: 'BESXP15 12X A1', cusip: '961644AC4', bias: 'OFFER', date: '07/19/2025', bid: 100.3, mid: 101.3, ask: 102.2, source: 'Offer' },
  ];

  runAutomation() {
    console.log('Running automation...');
  }

  openImportDialog() {
    this.showImportDialog = true;
  }

  onUpload(event: any) {
    console.log('File uploaded:', event);
    this.showImportDialog = false;
  }

  onCancelUpload() {
    this.showImportDialog = false;
  }
}
