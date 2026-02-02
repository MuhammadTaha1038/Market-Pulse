import { Routes } from '@angular/router';
import { Login } from '@/components/login/login';
import { SubAsset } from '@/components/sub-asset/sub-asset';
import { CLOSelectorComponent } from '@/components/clo-selector/clo-selector.component';

import { AppLayout } from '@/layout/component/app.layout';
import { Home } from '@/components/home/home';
import { ColorSelection } from '@/components/color-selection/color-selection';
import { ManualColor } from '@/components/manual-color/manual-color';
import { Settings } from '@/components/settings/settings';
import { CloMappingComponent } from '@/components/clo-mapping/clo-mapping.component';

export const appRoutes: Routes = [
    // Root redirects to login
    { path: '', redirectTo: 'login', pathMatch: 'full' },
    
    // Public routes (without layout)
    { path: 'login', component: Login },
    { path: 'clo-selection', component: CLOSelectorComponent },
    { path: 'sub-asset', component: SubAsset },

    // Protected routes with layout (require CLO selection)
    {
        path: '',
        component: AppLayout,
        children: [
            { path: 'home', component: Home },
            { path: 'dashboard', component: Home }, // Alias for home
            { path: 'color-type', component: ColorSelection },
            { path: 'manual-color', component: ManualColor },
            { path: 'settings', component: Settings },
            { path: 'clo-mappings', component: CloMappingComponent }
        ]
    },

    // Redirect any unknown routes to login
    { path: '**', redirectTo: 'login' }
];