import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MenuItem } from 'primeng/api';
import { AppMenuitem } from './app.menuitem';
import { TableStateService } from '../../components/home/table-state.service';
import '../custom.css'

// Extend MenuItem to support SVG icons
interface MenuItemWithSvg extends MenuItem {
    svgIcon?: string; // Path to SVG file or inline SVG
}
@Component({
    selector: 'app-menu',
    standalone: true,
    imports: [CommonModule, AppMenuitem, RouterModule],
    template: `<ul class="layout-menu">
        <ng-container *ngFor="let item of model; let i = index">
            <li class="small-title" app-menuitem *ngIf="!item.separator" [item]="item" [index]="i" [root]="true"></li>
            <li *ngIf="item.separator" class="menu-separator"></li>
        </ng-container>
    </ul> `
})
export class AppMenu {
    model: MenuItemWithSvg[] = [];

    constructor(private tableStateService: TableStateService) {}

    ngOnInit() {
        this.model = [
            {
                label: 'Main',
                items: [
                    {
                        label: 'Dashboard',
                        svgIcon: 'assets/icon/dashboard.svg',
                        routerLink: ['/home'],
                        command: () => this.collapseTable()
                    },
                    {
                        label: 'Security Search',
                        svgIcon: 'assets/icon/security.svg',
                        command: () => this.tableStateService.toggleTableExpanded()
                    },
                    {
                        label: 'Color Process',
                        svgIcon: 'assets/icon/colorprocess.svg',
                        routerLink: ['/color-type'],
                        command: () => this.collapseTable()
                    },
                    {
                        label: 'Data Statistics',
                        svgIcon: 'assets/icon/data.svg',
                        routerLink: ['/home'],
                        disabled: true,
                        title: 'Coming Soon'
                    }
                ]
            },

            {
                label: 'Settings',
                items: [
                    {
                        label: 'Rules',
                        svgIcon: 'assets/icon/rules.svg',
                        routerLink: ['/settings'],
                        queryParams: { section: 'rules' },
                        command: () => this.collapseTable()
                    },
                    {
                        label: 'Preset',
                        svgIcon: 'assets/icon/presets.svg',
                        routerLink: ['/settings'],
                        queryParams: { section: 'preset' },
                        command: () => this.collapseTable()
                    },
                    {
                        label: 'Cron Jobs',
                        svgIcon: 'assets/icon/cronjob.svg',
                        routerLink: ['/settings'],
                        queryParams: { section: 'cron-jobs' },
                        command: () => this.collapseTable()
                    },
                    {
                        label: 'Email & Restore',
                        svgIcon: 'assets/icon/info.svg',
                        routerLink: ['/settings'],
                        queryParams: { section: 'restore-email' },
                        command: () => this.collapseTable()
                    },
                    {
                        label: 'Sorting',
                        svgIcon: 'assets/icon/sorting.svg',
                        routerLink: ['/settings'],
                        queryParams: { section: 'sorting' },
                        command: () => this.collapseTable()
                    }
                ]
            },

            {
                label: 'Super Admin',
                items: [
                    {
                        label: 'CLO Mappings',
                        icon: 'pi pi-fw pi-shield',
                        routerLink: ['/clo-mappings'],
                        command: () => this.collapseTable(),
                        title: 'Configure column visibility and Oracle queries for each CLO type'
                    }
                ]
            }
        ];
    }

    toggleTableExpansion() {
        this.tableStateService.toggleTableExpanded();
    }

    collapseTable() {
        this.tableStateService.setTableExpanded(false);
    }
}
