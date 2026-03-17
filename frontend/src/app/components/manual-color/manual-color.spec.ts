import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ManualColor } from './manual-color';

describe('ManualColor', () => {
  let component: ManualColor;
  let fixture: ComponentFixture<ManualColor>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ManualColor]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ManualColor);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
