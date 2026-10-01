import json
import logging
import os
import queue
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import paho.mqtt.client as mqtt


LOG_ROOT = Path(os.getenv("LOG_ROOT", "/logs"))
MQTT_HOST = os.environ["MQTT_HOST"]
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "America/Sao_Paulo"))
MESSAGE_QUEUE: queue.Queue[tuple[str, mqtt.MQTTMessage]] = queue.Queue()


def devices_from_environment() -> list[dict[str, str]]:
    devices = json.loads(os.environ["MQTT_DEVICES_JSON"])
    if not isinstance(devices, list) or not devices:
        raise ValueError("MQTT_DEVICES_JSON deve ser uma lista nao vazia")
    for device in devices:
        if not all(key in device for key in ("username", "password", "topic")):
            raise ValueError("cada dispositivo precisa de username, password e topic")
    return devices


def log_path(received_at: datetime) -> Path:
    return LOG_ROOT / f"{received_at.year:04d}" / f"{received_at.month:02d}" / f"{received_at.day:02d}.json"


def load_day(path: Path, date: str) -> dict:
    if not path.exists():
        return {"date": date, "readings": []}
    try:
        with path.open("r", encoding="utf-8") as file:
            document = json.load(file)
        if not isinstance(document, dict) or not isinstance(document.get("readings"), list):
            raise ValueError("formato esperado: objeto com lista readings")
        return document
    except (OSError, json.JSONDecodeError, ValueError) as error:
        logging.error("Arquivo invalido %s: %s", path, error)
        path.replace(path.with_suffix(path.suffix + ".corrupt"))
        return {"date": date, "readings": []}


def save_day(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            json.dump(document, file, ensure_ascii=False, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def save_message(authenticated_user: str, message: mqtt.MQTTMessage) -> None:
    received_at = datetime.now(TIMEZONE)
    try:
        data = json.loads(message.payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        data = {"raw_payload": message.payload.decode("utf-8", errors="replace")}

    reading = {
        "received_at": received_at.isoformat(timespec="seconds"),
        "device_id": authenticated_user,
        "mqtt_user": authenticated_user,
        "topic": message.topic,
        "data": data,
    }
    path = log_path(received_at)
    document = load_day(path, received_at.date().isoformat())
    document["readings"].append(reading)
    save_day(path, document)
    logging.info("Mensagem de %s salva em %s", authenticated_user, path)


def writer() -> None:
    while True:
        authenticated_user, message = MESSAGE_QUEUE.get()
        try:
            save_message(authenticated_user, message)
        except Exception:
            logging.exception("Falha ao salvar mensagem de %s", authenticated_user)
        finally:
            MESSAGE_QUEUE.task_done()


def run_device(device: dict[str, str]) -> None:
    username = device["username"]
    client_id = f"iot-log-collector-{username}"
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    client.username_pw_set(username, device["password"])

    def on_connect(
        connected_client: mqtt.Client,
        userdata: object,
        flags: dict,
        reason_code: mqtt.ReasonCode,
        properties: object,
    ) -> None:
        if reason_code.is_failure:
            logging.error("Falha MQTT de %s: %s", username, reason_code)
            return
        connected_client.subscribe(device["topic"], qos=1)
        logging.info("%s conectado e inscrito em %s", username, device["topic"])

    def on_message(
        connected_client: mqtt.Client,
        userdata: object,
        message: mqtt.MQTTMessage,
    ) -> None:
        MESSAGE_QUEUE.put((username, message))

    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=60)
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_forever(retry_first_connection=True)


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(message)s",
    )
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    threading.Thread(target=writer, name="json-writer", daemon=True).start()

    for device in devices_from_environment():
        threading.Thread(target=run_device, args=(device,), name=device["username"], daemon=True).start()

    threading.Event().wait()


if __name__ == "__main__":
    main()
