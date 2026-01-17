import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class TableStateService {
  private isTableExpandedSubject = new BehaviorSubject<boolean>(false);
  isTableExpanded$ = this.isTableExpandedSubject.asObservable();

  setTableExpanded(state: boolean) {
    this.isTableExpandedSubject.next(state);
  }
}