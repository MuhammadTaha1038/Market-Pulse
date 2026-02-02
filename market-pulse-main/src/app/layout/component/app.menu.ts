import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MenuItem } from 'primeng/api';
import { AppMenuitem } from './app.menuitem';

@Component({
  selector: 'app-menu',
  standalone: true,
  imports: [CommonModule, AppMenuitem, RouterModule],
  template: `<ul class="layout-menu">
        <ng-container *ngFor="let item of model; let i = index">
            <li app-menuitem *ngIf="!item.separator" [item]="item" [index]="i" [root]="true"></li>
            <li *ngIf="item.separator" class="menu-separator"></li>
        </ng-container>
    </ul> `
})
export class AppMenu {
  model: MenuItem[] = [];

  ngOnInit() {
    this.model = [
      {
        label: 'Main',
        items: [
          { label: 'Dashboard', icon: 'pi pi-fw pi-home', routerLink: ['/home'] },
          { label: 'Security Search', icon: 'pi pi-fw pi-search', routerLink: ['/home'], disabled: true, title: 'Coming Soon' },
          {
            label: 'Color Process',
            icon: 'pi pi-fw pi-palette',
            routerLink: ['/color-type']
          },
          {
            label: 'Data Statistics',
            icon: 'pi pi-fw pi-chart-bar',
            routerLink: ['/home'],
            disabled: true,
            title: 'Coming Soon'
          },
        ]
      },

      {
        label: 'Settings',
      items: [
          { 
            label: 'Rules', 
            icon: 'pi pi-fw pi-cog', 
            routerLink: ['/settings'], 
            queryParams: { section: 'rules' }
          },
          { 
            label: 'Preset', 
            icon: 'pi pi-fw pi-sliders-h', 
            routerLink: ['/settings'], 
            queryParams: { section: 'preset' }
          },
          { 
            label: 'Cron Jobs', 
            icon: 'pi pi-fw pi-clock', 
            routerLink: ['/settings'], 
            queryParams: { section: 'corn-jobs' }
          },
          { 
            label: 'Email & Restore', 
            icon: 'pi pi-fw pi-envelope', 
            routerLink: ['/settings'], 
            queryParams: { section: 'restore-email' }
          },
        ]
      },

      {
        label: 'Super Admin',
        items: [
          { 
            label: 'CLO Mappings', 
            icon: 'pi pi-fw pi-shield', 
            routerLink: ['/clo-mappings'],
            title: 'Configure column visibility for each CLO type'
          },
        ]
      }
    ];
  }
}