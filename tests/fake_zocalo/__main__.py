import json
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import ispyb.sqlalchemy
import pika
import yaml
from ispyb.sqlalchemy import DataCollection
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import AMQPConnectionError
from pika.spec import BasicProperties
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

RABBITMQ_START_TIMEOUT_S = 20

TEST_RESULT_LARGE = [
    {
        "centre_of_mass": [1, 2, 3],
        "max_voxel": [1, 2, 3],
        "max_count": 105062,
        "n_voxels": 35,
        "total_count": 2387574,
        "bounding_box": [[2, 2, 2], [8, 8, 7]],
    }
]
TEST_RESULT_MEDIUM = [
    {
        "centre_of_mass": [1, 2, 3],
        "max_voxel": [2, 4, 5],
        "max_count": 105062,
        "n_voxels": 35,
        "total_count": 2387574,
        "bounding_box": [[1, 2, 3], [3, 4, 4]],
    }
]
TEST_RESULT_SMALL = [
    {
        "centre_of_mass": [1, 2, 3],
        "max_voxel": [1, 2, 3],
        "max_count": 105062,
        "n_voxels": 35,
        "total_count": 1387574,
        "bounding_box": [[2, 2, 2], [3, 3, 3]],
    }
]
NO_DIFFRACTION_PREFIX = "NO_DIFF"

MULTIPLE_CRYSTAL_PREFIX = "MULTI_X"

DEV_ISPYB_CONFIG = "/dls_sw/dasc/mariadb/credentials/ispyb-dev.cfg"


def load_configuration_file(filename):
    conf = yaml.safe_load(Path(filename).read_text())
    return conf


def get_dcgid_and_prefix(dcid: int, session_maker: sessionmaker) -> tuple[int, str]:
    try:
        with session_maker() as session:
            assert isinstance(session, Session)
            query = (
                session.query(
                    DataCollection.dataCollectionId, DataCollection.imagePrefix
                )
                .filter(DataCollection.dataCollectionId == dcid)
                .first()
            )
            assert query is not None, (
                f"Failed to find dcid {dcid} which matches any in dev ispyb"
            )
            dcgid, prefix = query

    except Exception as e:
        print("Exception occured when reading from ISPyB database:\n")
        print(e)
        print("This is probably because you are using mock dcid/dcgid values...")
        dcgid = 1000
        prefix = ""
        print(f"Using dcgid = {dcgid} and leaving the prefix empty as defaults")
    return dcgid, prefix


def make_result(payload):
    res = {
        "environment": {"ID": "6261b482-bef2-49f5-8699-eb274cd3b92e"},
        "payload": {"results": payload},
        "recipe": {
            "start": [[1, payload]],
            "1": {
                "service": "Send XRC results to GDA",
                "queue": "xrc.i03",
                "exchange": "results",
                "parameters": {"dcid": "2", "dcgid": "4"},
            },
        },
        "recipe-path": [],
        "recipe-pointer": 1,
    }
    return res


def main() -> None:
    url = ispyb.sqlalchemy.url(DEV_ISPYB_CONFIG)
    engine = create_engine(url, connect_args={"use_pure": True})
    session_maker = sessionmaker(engine)

    config = load_configuration_file(
        os.path.expanduser("~/.zocalo/rabbitmq-credentials.yml")
    )
    creds = pika.PlainCredentials(config["username"], config["password"])
    params = pika.ConnectionParameters(
        config["host"], config["port"], config["vhost"], creds
    )

    results: dict[str, Any] = defaultdict(lambda: make_result(TEST_RESULT_LARGE))
    results[NO_DIFFRACTION_PREFIX] = make_result([])
    results[MULTIPLE_CRYSTAL_PREFIX] = make_result(
        [*TEST_RESULT_LARGE, *TEST_RESULT_SMALL]
    )

    start = time.time()
    while True:
        try:
            conn = pika.BlockingConnection(params)
        except AMQPConnectionError:
            print("Unable to connect, retrying...")
            if time.time() - start > RABBITMQ_START_TIMEOUT_S:
                print(f"RabbitMQ did not start after {RABBITMQ_START_TIMEOUT_S}s")
                exit(1)
            time.sleep(1)
        else:
            break

    channel = conn.channel()

    # Create the results exchange if it doesn't already exist
    channel.exchange_declare(exchange="results", exchange_type="topic")

    # Create the xrc.i03 queue if it doesn't already exist
    # Arguments match queue created by 'module load rabbitmq/dev'
    channel.queue_declare(
        queue="xrc.i03",
        durable=True,
        arguments={"x-single-active-consumer": False, "x-queue-type": "quorum"},
    )
    # Also create the processing_recipe queue
    channel.queue_declare(
        queue="processing_recipe",
        durable=True,
        arguments={
            "x-single-active-consumer": False,
            "x-queue-type": "quorum",
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": "dlq.processing_recipe",
        },
    )

    # Route messages from the 'results' exchange to the 'xrc.i03' channel
    channel.queue_bind(exchange="results", queue="xrc.i03", routing_key="xrc.i03")

    def on_request(ch: BlockingChannel, method, props, body):
        print(
            f"Received message: \n properties: \n\n {method} \n\n {props} \n\n{body}\n"
        )
        try:
            message = json.loads(body)
        except Exception:
            print("Malformed message body.")
            return
        if message.get("parameters").get("event") == "end":
            print('Doing "processing"...')

            dcid = message.get("parameters").get("ispyb_dcid")
            print(f"Getting info for dcid {dcid} from ispyb:")
            dcgid, prefix = get_dcgid_and_prefix(dcid, session_maker)

            time.sleep(1)
            print('Sending "results"...')
            resultprops = BasicProperties(
                delivery_mode=2,
                headers={"workflows-recipe": True, "x-delivery-count": 1},
            )

            result = results[prefix]
            result["recipe"]["1"]["parameters"]["dcid"] = str(dcid)
            result["recipe"]["1"]["parameters"]["dcgid"] = str(dcgid)

            print(f"Sending results {result}")

            result_chan = conn.channel()
            result_chan.basic_publish(
                "results", "xrc.i03", json.dumps(result), resultprops
            )
            print("Finished.\n")
        ch.basic_ack(method.delivery_tag, False)

    channel.basic_consume(queue="processing_recipe", on_message_callback=on_request)
    print("Listening for zocalo requests")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Shutting down gracefully")
        channel.close()


if __name__ == "__main__":
    main()
