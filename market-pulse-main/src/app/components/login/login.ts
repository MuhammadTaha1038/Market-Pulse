import { Component } from '@angular/core';
import { InputTextModule } from 'primeng/inputtext';
import { ButtonModule } from 'primeng/button';
import { Router } from '@angular/router';

@Component({
  selector: 'app-login',
  imports: [InputTextModule, ButtonModule],
  templateUrl: './login.html'
})
export class Login {

  constructor(private router: Router) {}

  onLogin() {
    // Navigate to CLO selection page after login
    // TODO: Implement Microsoft SSO in production
    // After SSO integration, check if CLO type is provided in claims
    // If CLO type exists in SSO claims, auto-select and go to /home
    // Otherwise, go to /clo-selection
    this.router.navigate(['/clo-selection']);
  }
}