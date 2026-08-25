"""AirKorea(에어코리아) 대기오염 정보 어댑터."""

from kpubdata.providers.airkorea.adapter import AirKoreaAdapter

__all__ = ["AirKoreaAdapter"]

AIRKOREA_CATALOGUE = [
    {
        "id": "realtime_air_quality",
        "name": "실시간 측정소별 대기질 정보",
        "description": "전국 측정소의 실시간 대기질 정보(PM10, PM2.5, O3, NO2, CO, SO2)",
        "metadata": {
            "base_url": "http://openapi.airkorea.or.kr/openapi/services/rest/ArpltnInforInqireSvc",
            "service_name": "CtprvnRltmMesureDnsty",
        },
    },
    {
        "id": "air_quality_forecast",
        "name": "대기질 예보 정보",
        "description": "전국 지역별 대기질 예보 정보",
        "metadata": {
            "base_url": "http://openapi.airkorea.or.kr/openapi/services/rest/MsrstnAlertInqireSvc",
            "service_name": "getMsrstnAcctoRltmMesureDnsty",
        },
    },
    {
        "id": "cai_index",
        "name": "통합대기환경지수(CAI)",
        "description": "전국 지역별 통합대기환경지수 정보",
        "metadata": {
            "base_url": "http://openapi.airkorea.or.kr/openapi/services/rest/ArpltnInforInqireSvc",
            "service_name": "MinCngriMiddleAirKoreaFrcstDnsty",
        },
    },
]