from functools import lru_cache

from app.clients.market_data import MarketDataClient
from app.core.config import Settings, get_settings
from app.services.feature_service import FeatureService


@lru_cache
def _get_market_data_client() -> MarketDataClient:
    settings: Settings = get_settings()
    return MarketDataClient(settings=settings)


@lru_cache
def get_feature_service() -> FeatureService:
    settings: Settings = get_settings()
    return FeatureService(
        market_data_client=_get_market_data_client(),
        settings=settings,
    )
