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
    // Bypass authentication for testing - navigate directly to home
    // TODO: Implement Microsoft SSO in production
    this.router.navigate(['/home']);
  }
}