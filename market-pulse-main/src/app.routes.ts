import { Routes } from '@angular/router';
import { Login } from '@/components/login/login';
import { SubAsset } from '@/components/sub-asset/sub-asset';

import { AppLayout } from '@/layout/component/app.layout';
import { Home } from '@/components/home/home';
import { ColorSelection } from '@/components/color-selection/color-selection';
import { ManualColor } from '@/components/manual-color/manual-color';
import { Settings } from '@/components/settings/settings';

export const appRoutes: Routes = [
    // Public routes (without layout)
    { path: 'login', component: Login },
    { path: 'sub-asset', component: SubAsset },

    // Protected routes with layout
    {
        path: '',
        component: AppLayout,
        children: [
            { path: 'home', component: Home },
            { path: 'color-type', component: ColorSelection },
            { path: 'manual-color', component: ManualColor },
            { path: 'settings', component: Settings },
            { path: '', redirectTo: 'home', pathMatch: 'full' }
        ]
    },

    // Redirect any unknown routes to home
    { path: '**', redirectTo: 'home' }
];