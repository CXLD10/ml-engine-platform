from app.clients.market_data import MarketDataClient
from app.core.config import Settings
from app.features.engineering import compute_features
from app.schemas.features import FeaturesResponse


class FeatureService:
    def __init__(self, market_data_client: MarketDataClient, settings: Settings) -> None:
        self._market_data_client = market_data_client
        self._settings = settings

    async def build_features(self, symbol: str, lookback: int | None) -> FeaturesResponse:
        window = lookback or self._settings.default_lookback
        if window > self._settings.max_lookback:
            window = self._settings.max_lookback

        candles_response = await self._market_data_client.get_candles(symbol=symbol, lookback=window)
        features = compute_features(
            candles=candles_response.candles,
            ma_window=self._settings.ma_window,
            vol_window=self._settings.vol_window,
        )

        return FeaturesResponse(
            symbol=candles_response.symbol,
            window_used=window,
            upstream_latest_timestamp=candles_response.candles[-1].timestamp,
            features=features,
        )
