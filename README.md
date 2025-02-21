# fioneer

### Install

```bash
poetry install

source .venv/bin/activate  # Mac/Linux
.venv\Scripts\activate     # Windows
```

### CLI Commands

```bash
# Run tests with detailed output
poetry run test

# Run tests with minimal output
poetry run test-quiet
```

### finnhub

API Document: https://finnhub.io/docs/api/introduction

### ninjas

API Document: https://api-ninjas.com/api/earningscalltranscript


## dataset

```json
{
  "id": 1,
  "ticker": "NVDA",
  "year": 2024,
  "quarter": 4,
  "date": "2024-11-20",
  "sector": "Technology",
  "industry": "Semiconductors",
}
```

### Ticker Sector Industry

[huggingface](https://huggingface.co/datasets/yeong-hwan/ticker_sector_industry)


### sector
- Basic Materials
- Communication Services
- Consumer Cyclical
- Consumer Defensive
- Energy
- Financial Services
- Healthcare
- Industrials
- Real Estate
- Technology
- Utilities