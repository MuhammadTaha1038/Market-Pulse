import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

@Injectable({
    providedIn: 'root'
})
export class MenuActiveService {
    private activeMenuItemSubject = new BehaviorSubject<string>('Dashboard');
    activeMenuItem$ = this.activeMenuItemSubject.asObservable();

    setActiveMenuItem(label: string) {
        this.activeMenuItemSubject.next(label);
    }

    getActiveMenuItem(): string {
        return this.activeMenuItemSubject.value;
    }
}
