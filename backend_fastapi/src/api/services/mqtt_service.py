import asyncio
import json
import logging
from typing import Optional

from ..core.config import settings
from .firestore_service import upsert_telemetry
from ..utils.alerts import evaluate_thresholds_for_device

logger = logging.getLogger("mqtt")

try:
    from asyncio_mqtt import Client as AsyncMqttClient, MqttError  # type: ignore
    ASYNC_MQTT_AVAILABLE = True
except Exception:  # pragma: no cover
    ASYNC_MQTT_AVAILABLE = False
    AsyncMqttClient = None  # type: ignore
    MqttError = Exception  # type: ignore


class MQTTClient:
    """
    Simple MQTT client that subscribes to telemetry topics and ingests messages into Firestore.
    Expected payload JSON: {"device_id": "...", "ts": 1700000000, "metrics": {"temp": 1.0}}
    """
    def __init__(self):
        self._client: Optional[AsyncMqttClient] = None
        self._task: Optional[asyncio.Task] = None
        self._connected = False

    async def connect(self):
        if not settings.MQTT_ENABLED:
            logger.info("MQTT disabled via config.")
            return
        if not ASYNC_MQTT_AVAILABLE:
            logger.warning("asyncio-mqtt not available; MQTT disabled.")
            return
        self._client = AsyncMqttClient(
            hostname=settings.MQTT_BROKER_URL,
            port=settings.MQTT_BROKER_PORT,
            username=(settings.MQTT_USERNAME or None),
            password=(settings.MQTT_PASSWORD or None),
        )
        await self._client.connect()
        self._connected = True
        logger.info("Connected to MQTT broker %s:%s", settings.MQTT_BROKER_URL, settings.MQTT_BROKER_PORT)

        topic = settings.MQTT_TELEMETRY_TOPIC_TEMPLATE.replace("{device_id}", "+")
        await self._client.subscribe(topic)
        logger.info("Subscribed to topic: %s", topic)
        self._task = asyncio.create_task(self._message_loop())

    async def _message_loop(self):
        assert self._client is not None
        try:
            async with self._client.unfiltered_messages() as messages:
                async for msg in messages:
                    try:
                        payload = json.loads(msg.payload.decode("utf-8"))
                        device_id = payload.get("device_id")
                        ts = int(payload.get("ts"))
                        metrics = payload.get("metrics") or {}
                        if device_id and metrics:
                            upsert_telemetry(device_id, ts, metrics)
                            # Threshold evaluation upon ingestion
                            await evaluate_thresholds_for_device(device_id, ts, metrics)
                    except Exception as e:
                        logger.exception("Error processing MQTT message: %s", e)
        except Exception as e:  # pragma: no cover
            logger.exception("MQTT message loop error: %s", e)

    async def disconnect(self):
        if self._task:
            self._task.cancel()
            self._task = None
        if self._client and self._connected:
            await self._client.disconnect()
        self._connected = False


mqtt_client_singleton = MQTTClient()
