import { Routes } from '@angular/router';
import { Login } from '@/components/login/login';
import { SubAsset } from '@/components/sub-asset/sub-asset';
import { CLOSelectorComponent } from '@/components/clo-selector/clo-selector.component';

import { AppLayout } from '@/layout/component/app.layout';
import { Home } from '@/components/home/home';
import { ColorSelection } from '@/components/color-selection/color-selection';
import { ManualColor } from '@/components/manual-color/manual-color';
import { Settings } from '@/components/settings/settings';
import { TempComponent } from '@/components/temp/temp';
import { CloMappingComponent } from '@/components/clo-mapping/clo-mapping.component';

export const appRoutes: Routes = [
    // Public routes (without layout)
    { path: 'login', component: Login },
    { path: 'sub-asset', component: SubAsset },
    { path: 'clo-selection', component: CLOSelectorComponent },

    // Protected routes with layout
    {
        path: '',
        component: AppLayout,
        children: [
            { path: 'home', component: Home },
            { path: 'dashboard', component: Home },
            { path: 'color-type', component: ColorSelection },
            { path: 'manual-color', component: ManualColor },
            { path: 'settings', component: Settings },
            { path: 'clo-mappings', component: CloMappingComponent },
            { path: 'temp', component: TempComponent },
            { path: '', redirectTo: 'home', pathMatch: 'full' }
        ]
    },

    // Redirect any unknown routes to home
    { path: '**', redirectTo: 'home' }
];