import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SubAsset } from './sub-asset';

describe('SubAsset', () => {
  let component: SubAsset;
  let fixture: ComponentFixture<SubAsset>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SubAsset]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SubAsset);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
