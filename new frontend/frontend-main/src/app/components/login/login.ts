import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api.service';

@Component({
    selector: 'app-login',
    standalone: true,
    imports: [CommonModule, FormsModule],
    templateUrl: './login.html',
    styleUrls: ['./login.css']
})
export class Login implements OnInit {
    isDarkMode = false;
    email = '';
    password = '';
    loggingIn = false;

    constructor(
        private router: Router,
        private apiService: ApiService
    ) {}

    ngOnInit(): void {
        const savedTheme = localStorage.getItem('theme');

        if (savedTheme === 'dark') {
            this.isDarkMode = true;
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    }

    toggleTheme(): void {
        this.isDarkMode = !this.isDarkMode;

        if (this.isDarkMode) {
            document.documentElement.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.classList.remove('dark');
            localStorage.setItem('theme', 'light');
        }
    }

    onLogin(): void {
        if (!this.email || !this.password) return;
        this.loggingIn = true;

        // Fetch hierarchy and assign the main asset type based on auth
        // In production, the backend would return the user's assigned main type
        this.apiService.getCloHierarchy().subscribe({
            next: (res) => {
                const mainTypes = res.main_clos || [];
                if (mainTypes.length > 0) {
                    // Auto-assign the first main type (in production, this comes from user role)
                    localStorage.setItem('userMainAssetType', mainTypes[0].id);
                }
                this.loggingIn = false;
                this.router.navigate(['/sub-asset']);
            },
            error: () => {
                this.loggingIn = false;
                // Navigate anyway — sub-asset page will handle the error
                this.router.navigate(['/sub-asset']);
            }
        });
    }
}
