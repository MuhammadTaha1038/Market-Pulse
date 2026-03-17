import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export interface SubAssetOption {
    id: string;
    name: string;
    display_name?: string;
    parent_clo_id?: string;
}

export interface MainAssetType {
    id: string;
    name: string;
    display_name: string;
    description?: string;
    sub_clos: SubAssetOption[];
}

export interface AssetOption {
    name: string;
    value: string;
}

@Injectable({
    providedIn: 'root'
})
export class AssetStateService {
    /** The currently selected sub-asset (shown in topbar dropdown) */
    private assetSubject: BehaviorSubject<AssetOption>;

    /** The main asset type (EURO_ABS, CLO, USABS) assigned to the user */
    private mainTypeSubject: BehaviorSubject<MainAssetType | null>;

    /** All sub-assets for the current main type (for topbar dropdown) */
    private subAssetsSubject: BehaviorSubject<AssetOption[]>;

    asset$;
    mainType$;
    subAssets$;

    constructor() {
        // Restore from localStorage if available
        const stored = localStorage.getItem('selectedAssetState');
        let initial: AssetOption = { name: 'US BSL CLO', value: 'CLO_US_BSL_CLO' };
        let initialMain: MainAssetType | null = null;
        let initialSubs: AssetOption[] = [];

        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                if (parsed.asset) initial = parsed.asset;
                if (parsed.mainType) initialMain = parsed.mainType;
                if (parsed.subAssets) initialSubs = parsed.subAssets;
            } catch { }
        }

        this.assetSubject = new BehaviorSubject<AssetOption>(initial);
        this.mainTypeSubject = new BehaviorSubject<MainAssetType | null>(initialMain);
        this.subAssetsSubject = new BehaviorSubject<AssetOption[]>(initialSubs);

        this.asset$ = this.assetSubject.asObservable();
        this.mainType$ = this.mainTypeSubject.asObservable();
        this.subAssets$ = this.subAssetsSubject.asObservable();
    }

    /** Set the main asset type and derive the sub-asset options */
    setMainType(mainType: MainAssetType): void {
        this.mainTypeSubject.next(mainType);

        const subs: AssetOption[] = mainType.sub_clos.map(sub => ({
            name: sub.display_name || sub.name,
            value: sub.id
        }));
        this.subAssetsSubject.next(subs);

        // Auto-select first sub-asset
        if (subs.length > 0) {
            this.setAsset(subs[0]);
        }

        this.persist();
    }

    setAsset(asset: AssetOption): void {
        this.assetSubject.next(asset);
        this.persist();
    }

    getCurrentAsset(): AssetOption {
        return this.assetSubject.value;
    }

    getMainType(): MainAssetType | null {
        return this.mainTypeSubject.value;
    }

    getSubAssets(): AssetOption[] {
        return this.subAssetsSubject.value;
    }

    private persist(): void {
        localStorage.setItem('selectedAssetState', JSON.stringify({
            asset: this.assetSubject.value,
            mainType: this.mainTypeSubject.value,
            subAssets: this.subAssetsSubject.value
        }));
    }
}
