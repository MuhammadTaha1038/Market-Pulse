import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ColorSelection } from './color-selection';

describe('ColorSelection', () => {
  let component: ColorSelection;
  let fixture: ComponentFixture<ColorSelection>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ColorSelection]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ColorSelection);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
