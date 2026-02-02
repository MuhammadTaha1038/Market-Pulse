import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { ChipModule } from 'primeng/chip';
import { DividerModule } from 'primeng/divider';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { ApiService } from '../../services/api.service';
import { ManualUploadService } from '../../services/manual-upload.service';
import { CronJobsService } from '../../services/cron-jobs.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-color-selection',
  standalone: true,
  imports: [CommonModule, FormsModule, ButtonModule, ChipModule, DividerModule, ToastModule],
  providers: [MessageService],
  templateUrl: './color-selection.html',
  styleUrls: ['./color-selection.css']
})
export class ColorSelection {
  nextRun = '7H : 52M : 25S';
  uploading = false;
  overrideSchedule = false;

  constructor(
    private apiService: ApiService,
    private manualUploadService: ManualUploadService,
    private cronJobsService: CronJobsService,
    private messageService: MessageService,
    private router: Router
  ) {}

  ngOnInit() {
    // Load next run time from backend
    this.apiService.getNextRunTime().subscribe({
      next: (response) => {
        this.nextRun = response.next_run;
      },
      error: (error) => {
        console.error('Error loading next run time:', error);
      }
    });
  }

  runAutomation(override: boolean = false) {
    console.log('Running automated process with override:', override);
    
    const message = override 
      ? 'This will cancel the next scheduled run and execute immediately. Continue?'
      : 'This will run automation now while keeping the scheduled run. Continue?';
    
    if (!confirm(message)) {
      return;
    }
    
    this.uploading = true;
    
    // Trigger the automation cron job (job_id = 1 is typically the main automation)
    this.cronJobsService.triggerJob(1, override).subscribe({
      next: (response) => {
        this.uploading = false;
        console.log('✅ Automation triggered:', response);
        
        this.messageService.add({
          severity: 'success',
          summary: 'Automation Started',
          detail: response.message || 'Automation job triggered successfully'
        });
        
        // Navigate to home to see results after a brief delay
        setTimeout(() => {
          this.router.navigate(['/home']);
        }, 1500);
      },
      error: (error) => {
        this.uploading = false;
        console.error('❌ Failed to trigger automation:', error);
        
        this.messageService.add({
          severity: 'error',
          summary: 'Automation Failed',
          detail: error.error?.detail || 'Failed to trigger automation'
        });
      }
    });
  }

  runManual() {
    console.log('Running manual color process...');
    this.router.navigate(['/manual-color']);
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      const file = input.files[0];
      
      // Check file type
      if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
        this.messageService.add({
          severity: 'error',
          summary: 'Invalid File',
          detail: 'Please upload an Excel file (.xlsx or .xls)'
        });
        return;
      }

      this.uploading = true;
      console.log('📤 Uploading file to buffer for automated cleaning:', file.name);
      
      // Upload to buffer (for next automation run)
      this.manualUploadService.uploadFile(file, 'automatic').subscribe({
        next: (response) => {
          this.uploading = false;
          console.log('✅ File uploaded to buffer successfully:', response);
          
          const rowCount = response.rows_uploaded || response.rows_processed || response.rows_valid || 0;
          
          this.messageService.add({
            severity: 'success',
            summary: 'Upload Successful',
            detail: `File "${file.name}" uploaded to buffer. Colors will be included in next automation run. Total: ${rowCount} rows`
          });
          
          // Clear the file input
          input.value = '';
        },
        error: (error) => {
          this.uploading = false;
          console.error('❌ Upload failed:', error);
          
          this.messageService.add({
            severity: 'error',
            summary: 'Upload Failed',
            detail: error.error?.detail || 'Failed to upload file to buffer'
          });
          
          // Clear the file input
          input.value = '';
        }
      });
    }
  }
}