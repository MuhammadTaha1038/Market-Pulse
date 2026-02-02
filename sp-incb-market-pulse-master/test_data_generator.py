#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate test data for output file
"""
import pandas as pd
from datetime import datetime, timedelta
import random

# Generate 50,000+ test records
records = []
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'JPM', 'BAC', 'WFC']
sectors = ['Technology', 'Finance', 'Healthcare', 'Energy', 'Consumer']
sources = ['Bloomberg', 'Reuters', 'Internal']
biases = ['BULLISH', 'BEARISH', 'NEUTRAL']

print("Generating 50,000 test records...")

base_date = datetime.now() - timedelta(days=365)

for i in range(50000):
    date_offset = timedelta(days=random.randint(0, 365))
    records.append({
        'MESSAGE_ID': i + 1,
        'TICKER': random.choice(tickers),
        'SECTOR': random.choice(sectors),
        'CUSIP': f'CUSIP{i:06d}',
        'DATE': (base_date + date_offset).strftime('%Y-%m-%d'),
        'PRICE_LEVEL': round(random.uniform(50, 500), 2),
        'BID': round(random.uniform(50, 500), 2),
        'ASK': round(random.uniform(50, 500), 2),
        'PX': round(random.uniform(50, 500), 2),
        'SOURCE': random.choice(sources),
        'BIAS': random.choice(biases),
        'RANK': random.randint(1, 5),
        'COV_PRICE': round(random.uniform(50, 500), 2),
        'PERCENT_DIFF': round(random.uniform(-10, 10), 2),
        'PRICE_DIFF': round(random.uniform(-50, 50), 2),
        'CONFIDENCE': random.randint(1, 5),
        'DATE_1': (base_date + date_offset).strftime('%Y-%m-%d'),
        'DIFF_STATUS': random.choice(['OK', 'WARNING', 'ERROR']),
        'IS_PARENT': random.choice([True, False]),
        'PARENT_MESSAGE_ID': None if random.random() > 0.3 else random.randint(1, i) if i > 0 else None,
        'CHILDREN_COUNT': random.randint(0, 5),
        'PROCESSING_TYPE': random.choice(['AUTOMATED', 'MANUAL']),
        'PROCESSED_AT': (base_date + date_offset).strftime('%Y-%m-%d %H:%M:%S')
    })
    
    if (i + 1) % 10000 == 0:
        print(f"Generated {i + 1} records...")

# Create DataFrame
df = pd.DataFrame(records)

# Save to output file
output_path = r'd:\SKILL\watsapp project\fast api project\Data-main\Processed_Colors_Output.xlsx'
print(f"\nSaving to {output_path}...")
df.to_excel(output_path, index=False)

print(f"✅ Successfully created {len(df)} records in output file")
print(f"File size: {pd.read_excel(output_path).shape}")
print("\nSample data:")
print(df.head(3))
