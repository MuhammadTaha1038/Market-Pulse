import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';
import { ChipModule } from 'primeng/chip';
import { DividerModule } from 'primeng/divider';
import { DialogModule } from 'primeng/dialog';
import { ToastModule } from 'primeng/toast';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { MessageService } from 'primeng/api';
import { ApiService } from '../../services/api.service';
import { NextRunService } from '../../services/next-run.service';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';
import * as XLSX from 'xlsx';

@Component({
  selector: 'app-color-selection',
  standalone: true,
  imports: [CommonModule, ButtonModule, ChipModule, DividerModule, DialogModule, ToastModule, ProgressSpinnerModule],
  templateUrl: './color-selection.html',
  styleUrls: ['./color-selection.css'],
  providers: [MessageService]
})
export class ColorSelection implements OnInit, OnDestroy {
  nextRunTimer = '--:--:--';
  private timerSub!: Subscription;

  // ── Buffer state ─────────────────────────────────────────────────────────
  fileBuffered = false;
  bufferFileName = '';
  bufferFileSize = '';
  bufferUploading = false;
  private bufferedFile: File | null = null;

  // ── Run Automation dialog ─────────────────────────────────────────────────
  showOverwriteDialog = false;
  processingAutomation = false;

  constructor(
    private apiService: ApiService,
    private router: Router,
    private nextRunService: NextRunService,
    private messageService: MessageService
  ) {}

  ngOnInit() {
    this.nextRunService.init();
    this.timerSub = this.nextRunService.timer$.subscribe(val => {
      this.nextRunTimer = val;
    });

    // Restore buffer state persisted across navigation
    const saved = localStorage.getItem('color_buffer_file');
    if (saved) {
      const parsed = JSON.parse(saved);
      this.fileBuffered = true;
      this.bufferFileName = parsed.name;
      this.bufferFileSize = parsed.size;
    }
  }

  goToPresetSettings() {
    this.router.navigate(['/settings'], { queryParams: { section: 'preset' } });
  }

  goToRulesPage() {
    this.router.navigate(['/settings'], { queryParams: { section: 'rules' } });
  }

  // ── Run Automation ────────────────────────────────────────────────────────

  runAutomation() {
    this.showOverwriteDialog = true;
  }

  confirmRunAutomation(withOverride: boolean) {
    this.showOverwriteDialog = false;
    this.processingAutomation = true;

    // Fetch the first active cron job and trigger it
    this.apiService.getActiveCronJobs().subscribe({
      next: (res: any) => {
        const jobs = res.jobs ?? res ?? [];
        const job = jobs[0];
        if (!job) {
          this.processingAutomation = false;
          this.messageService.add({
            severity: 'warn',
            summary: 'No Active Jobs',
            detail: 'No active automation job found. Configure a cron job first.'
          });
          return;
        }

        this.apiService.triggerCronJob(job.id, withOverride).subscribe({
          next: () => {
            this.processingAutomation = false;
            this.clearBuffer();
            this.messageService.add({
              severity: 'success',
              summary: 'Automation Triggered',
              detail: withOverride
                ? `Job "${job.name}" started and existing output will be overwritten.`
                : `Job "${job.name}" started. Scheduled run is preserved.`
            });
          },
          error: (err) => {
            this.processingAutomation = false;
            this.messageService.add({
              severity: 'error',
              summary: 'Automation Failed',
              detail: err.error?.detail || 'Failed to trigger automation job.'
            });
          }
        });
      },
      error: () => {
        this.processingAutomation = false;
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Could not fetch cron jobs.'
        });
      }
    });
  }

  cancelRunAutomation() {
    this.showOverwriteDialog = false;
  }

  // ── Manual Color ──────────────────────────────────────────────────────────

  runManual() {
    this.router.navigate(['/manual-color']);
  }

  // ── File Buffer ───────────────────────────────────────────────────────────

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;

    const file = input.files[0];

    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      this.messageService.add({
        severity: 'error',
        summary: 'Invalid File',
        detail: 'Please upload an Excel file (.xlsx or .xls)'
      });
      input.value = '';
      return;
    }

    this.bufferedFile = file;
    this.bufferFileName = file.name;
    this.bufferFileSize = this.formatFileSize(file.size);
    this.fileBuffered = true;

    // Persist across navigation
    localStorage.setItem('color_buffer_file', JSON.stringify({
      name: file.name,
      size: this.bufferFileSize
    }));

    this.messageService.add({
      severity: 'success',
      summary: 'File Queued',
      detail: `"${file.name}" is saved in buffer. Click Run Automation to process it.`
    });

    // Reset input so same file can be re-selected
    input.value = '';
  }

  clearBuffer() {
    this.bufferedFile = null;
    this.fileBuffered = false;
    this.bufferFileName = '';
    this.bufferFileSize = '';
    localStorage.removeItem('color_buffer_file');
  }

  private formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return (bytes / Math.pow(k, i)).toFixed(1) + ' ' + sizes[i];
  }

  goToHelpPage(): void {
    this.router.navigate(['/temp']);
  }

  // ── Sample File Download ──────────────────────────────────────────────────

  downloadSampleFile(event: Event): void {
    event.stopPropagation();

    // Resolve active CLO — prefer selectedAssetState (topbar flow), fall back to user_clo_selection
    let cloId: string | undefined;
    let cloName = 'sample';

    try {
      const rawAsset = localStorage.getItem('selectedAssetState');
      if (rawAsset) {
        const parsed = JSON.parse(rawAsset);
        cloId   = parsed?.asset?.value;
        cloName = parsed?.asset?.name || cloName;
      }
    } catch {}

    if (!cloId) {
      try {
        const rawUser = localStorage.getItem('user_clo_selection');
        if (rawUser) {
          const selection = JSON.parse(rawUser);
          cloId   = selection?.cloId;
          cloName = selection?.cloName || cloName;
        }
      } catch {}
    }

    if (!cloId) {
      this.messageService.add({
        severity: 'warn',
        summary: 'No Sub-Asset Selected',
        detail: 'Please select a sub-asset first to download the sample file.'
      });
      return;
    }

    this.apiService.getUserColumns(cloId).subscribe({
      next: (response: any) => {
        const columns: string[] = response.visible_columns || [];
        if (!columns.length) {
          this.messageService.add({
            severity: 'warn',
            summary: 'No Columns',
            detail: 'No visible columns found for the current sub-asset.'
          });
          return;
        }
        // Build workbook: single header row with column names
        const ws = XLSX.utils.aoa_to_sheet([columns]);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, 'Data');
        const safeName = cloName.replace(/[^a-zA-Z0-9_\-]/g, '_');
        XLSX.writeFile(wb, `${safeName}_sample.xlsx`);
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Download Failed',
          detail: 'Could not fetch column configuration. Please try again.'
        });
      }
    });
  }

  ngOnDestroy() {
    this.timerSub?.unsubscribe();
  }
}
