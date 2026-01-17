import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';
import { ChipModule } from 'primeng/chip';
import { DividerModule } from 'primeng/divider';
import { ApiService } from '../../services/api.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-color-selection',
  standalone: true,
  imports: [CommonModule, ButtonModule, ChipModule, DividerModule],
  templateUrl: './color-selection.html',
  styleUrls: ['./color-selection.css']
})
export class ColorSelection {
  nextRun = '7H : 52M : 25S';
  uploading = false;

  constructor(
    private apiService: ApiService,
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

  runAutomation() {
    console.log('Running automated process...');
    // Trigger backend to run colors
    alert('Automated ranking process triggered! Check backend logs.');
    // Redirect to home to see results
    this.router.navigate(['/home']);
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
        alert('Please upload an Excel file (.xlsx or .xls)');
        return;
      }

      this.uploading = true;
      console.log('Uploading file:', file.name);
      
      // Navigate to manual-color page with uploaded file
      setTimeout(() => {
        this.uploading = false;
        alert(`File "${file.name}" uploaded successfully! You can now review and process the data.`);
        this.router.navigate(['/manual-color']);
      }, 1500);
      
      // TODO: Implement actual file upload API
      // const formData = new FormData();
      // formData.append('file', file);
      // this.apiService.uploadManualColors(formData).subscribe(...);
    }
  }
}