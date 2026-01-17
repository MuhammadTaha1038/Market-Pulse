import { Component } from '@angular/core';
import { MenuItem } from 'primeng/api';
import { RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { StyleClassModule } from 'primeng/styleclass';
import { AppConfigurator } from './app.configurator';
import { LayoutService } from '../service/layout.service';
import { SelectModule } from 'primeng/select';
import { FormsModule } from '@angular/forms';

@Component({
    selector: 'app-topbar',
    standalone: true,
    imports: [RouterModule, CommonModule, StyleClassModule, SelectModule, FormsModule],
    template: ` <div class="layout-topbar">
        <div class="layout-topbar-logo-container">
            <button class="layout-menu-button layout-topbar-action" (click)="layoutService.onMenuToggle()">
                <i class="pi pi-bars"></i>
            </button>
            <a class="layout-topbar-logo" routerLink="/">
                <img src="./assets/logo/logo2.png" alt="Logo" class="layout-topbar-logo-image">
                <div class="flex flex-col leading-tight">
                    <span class="font-bold whitespace-nowrap">Market Pulse</span>
                    <span class="text-xs text-gray-500 whitespace-nowrap">Movement Intelligence</span>
                </div>
            </a>
        </div>

        <div class="layout-topbar-actions">
            <!-- Asset Selection Dropdown -->
            <div class="asset-selection">
               
                <p-select 
                    [options]="assetOptions" 
                    [(ngModel)]="selectedAsset" 
                    optionLabel="name"
                    class="asset-selector">
                </p-select>
            </div>

            <!-- Next Run Timer -->
            <div class="next-run">
                <span class="next-run-label">Next Run in</span>
                <span class="next-run-timer">{{ nextRunTimer }}</span>
            </div>

            <!-- User Info -->
            <div class="user-info">
                <div class="user-details">
                    <div class="user-name">Shashank S.</div>
                    <div class="user-email">Shashank.Srivastava@spglobal.com</div>
                </div>
                <div class="user-avatar">
                    <i class="pi pi-user"></i>
                </div>
            </div>

            <!-- Mobile Menu Button -->
            <button class="layout-topbar-menu-button layout-topbar-action" pStyleClass="@next" enterFromClass="hidden" enterActiveClass="animate-scalein" leaveToClass="hidden" leaveActiveClass="animate-fadeout" [hideOnOutsideClick]="true">
                <i class="pi pi-ellipsis-v"></i>
            </button>
        </div>
    </div>`,
    styles: [`
        .layout-topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 1rem;
            height: 4rem;
            background-color: var(--surface-card);
            border-bottom: 1px solid var(--surface-border);
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
        }

        .layout-topbar-logo-container {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .layout-topbar-logo {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            text-decoration: none;
            color: inherit;
        }

        .layout-topbar-logo-image {
            height: 2rem;
        }

        .layout-topbar-actions {
            display: flex;
            align-items: center;
            gap: 1.5rem;
        }

        .asset-selection {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .asset-icon {
            color: var(--text-color-secondary);
            font-size: 1rem;
        }

        .asset-selector {
            min-width: 100px;
        }

        .next-run {
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .next-run-label {
            font-size: 0.75rem;
            color: var(--text-color-secondary);
            white-space: nowrap;
        }

        .next-run-timer {
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-color);
            white-space: nowrap;
        }

        .user-info {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .user-details {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
        }

        .user-name {
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-color);
        }

        .user-email {
            font-size: 0.75rem;
            color: var(--text-color-secondary);
        }

        .user-avatar {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 2rem;
            height: 2rem;
            background-color: var(--primary-color);
            color: white;
            border-radius: 50%;
        }

        .layout-topbar-action {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 2.5rem;
            height: 2.5rem;
            border-radius: 50%;
            border: none;
            background: transparent;
            color: var(--text-color);
            transition: all 0.2s;
            cursor: pointer;
        }

        .layout-topbar-action:hover {
            background-color: var(--surface-hover);
        }

        /* Remove dropdown border and make it look like text */
        :host ::ng-deep .asset-selector .p-dropdown {
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
        }

        :host ::ng-deep .asset-selector .p-dropdown .p-dropdown-label {
            padding: 0.25rem 0.5rem !important;
            font-weight: 600;
        }

        :host ::ng-deep .asset-selector .p-dropdown-trigger {
            color: var(--text-color-secondary) !important;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .asset-selection,
            .next-run,
            .user-details {
                display: none;
            }
        }
    `]
})
export class AppTopbar {
    items!: MenuItem[];
    nextRunTimer = '7H:52M:25S';
    
    assetOptions = [
        { name: 'US CLO', value: 'us_clo' },
        { name: 'European CLO', value: 'european_clo' }
    ];
    
    selectedAsset = this.assetOptions[0];

    constructor(public layoutService: LayoutService) {}
}