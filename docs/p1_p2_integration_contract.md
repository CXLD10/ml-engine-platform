# P1-P2 Integration Contract (Schema 1.1)

## Compatibility policy
- P2 accepts only `schema_version == "1.1"`.
- Exchanges are strictly `NSE`, `BSE`, `NASDAQ`.
- All timestamps are parsed and normalized to UTC.

## Endpoint usage table
| Endpoint | Purpose | Client method |
|---|---|---|
| `/quote` | last price + timestamp | `get_quote` |
| `/intraday` | near realtime candles | `get_intraday` |
| `/historical` | training/evaluation candles | `get_historical` |
| `/fundamentals` | valuation inputs | `get_fundamentals` |
| `/company` | static company metadata | `get_company` |
| `/market-status` | pre-inference market gate | `get_market_status` |

## Validation/failure matrix
| Condition | Action |
|---|---|
| schema mismatch | reject payload with `upstream_schema_mismatch` |
| invalid OHLC/volume/timestamp | reject payload |
| non-monotonic candles | reject payload |
| `EXCHANGE_UNAVAILABLE` | retry then fail 503 |
| `RATE_LIMITED` | bounded retry with backoff |
| stale quote/candle | reject inference |
| degraded source/cache | set `degraded_input=true` and lower confidence |

## Project 3-facing prediction schema
- deterministic fields only:
  - `exchange`, `symbol`, `prediction`, `confidence`, `probability_up`, `probability_down`, `risk_score`, `expected_return`, `forecast_horizon`, `model_version`, `degraded_input`, `inference_latency_ms`, `timestamp`.
