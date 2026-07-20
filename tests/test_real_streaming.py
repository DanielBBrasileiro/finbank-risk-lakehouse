from pathlib import Path
from types import SimpleNamespace

import duckdb
import pandas as pd

from src.streaming.consumer import run_consumer
from src.streaming.producer import run_producer


def test_producer_consumer_flow_local(tmp_path: Path, monkeypatch) -> None:
    # 1. Setup mock directories
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    streaming_dir = tmp_path / "streaming"

    # 2. Write dummy transaction
    pd.DataFrame(
        [
            {
                "transaction_id": "uuid-t1",
                "customer_id": "uuid-c1",
                "account_id": "uuid-a1",
                "transaction_date": "2026-05-23",
                "channel": "PIX",
                "amount": 5000.0,
                "is_suspicious": True,
            }
        ]
    ).to_csv(raw_dir / "transactions.csv", index=False)

    # 3. Setup mock env
    fallback_file = streaming_dir / "suspicious_transactions_fallback.jsonl"
    monkeypatch.setattr("src.streaming.producer.RAW_DIR", raw_dir)
    monkeypatch.setattr("src.streaming.producer.FALLBACK_PATH", fallback_file)
    monkeypatch.setattr("src.streaming.consumer.FALLBACK_PATH", fallback_file)

    db_file = tmp_path / "warehouse.duckdb"
    monkeypatch.setenv("DB_TARGET", "duckdb")
    monkeypatch.setenv("DUCKDB_PATH", str(db_file))

    # 4. Run producer (should fallback to JSONL since Redpanda is not running)
    run_producer()
    assert fallback_file.exists()

    # 5. Run consumer (one-shot mode to read local file)
    run_consumer(one_shot=True)

    # 6. Check database results
    con = duckdb.connect(str(db_file))
    res = con.execute("SELECT * FROM raw.streaming_suspicious_summary").fetchall()
    assert len(res) == 1
    assert res[0][0] == "uuid-c1"
    assert res[0][1] == 1  # count
    assert res[0][2] == 5000.0  # amount

    # Replaying the same fallback file must not change the serving aggregate.
    con.close()
    run_consumer(one_shot=True)

    con = duckdb.connect(str(db_file))
    replayed = con.execute("SELECT * FROM raw.streaming_suspicious_summary").fetchall()
    event_count = con.execute("SELECT count(*) FROM raw.streaming_suspicious_events").fetchone()[0]
    assert replayed == res
    assert event_count == 1
    con.close()


def test_kafka_consumer_uses_group_and_commits_after_database_write(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import socket
    import sys

    from src.streaming import consumer as consumer_module

    db_file = tmp_path / "warehouse.duckdb"
    monkeypatch.setenv("DB_TARGET", "duckdb")
    monkeypatch.setenv("DUCKDB_PATH", str(db_file))
    monkeypatch.setenv("KAFKA_GROUP_ID", "portfolio-replay-test")
    monkeypatch.setenv("KAFKA_AUTO_OFFSET_RESET", "latest")

    class ReachableSocket:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def settimeout(self, _timeout):
            return None

        def connect_ex(self, _address):
            return 0

    monkeypatch.setattr(socket, "socket", lambda *_args, **_kwargs: ReachableSocket())

    event = {
        "transaction_id": "kafka-t1",
        "customer_id": "kafka-c1",
        "amount": 125.0,
        "timestamp": "2026-05-23T12:00:00Z",
    }
    created_consumers = []

    class FakeKafkaConsumer:
        def __init__(self, topic, **options):
            self.topic = topic
            self.options = options
            self.commits = 0
            self.closed = False
            created_consumers.append(self)

        def __iter__(self):
            return iter([SimpleNamespace(value=event)])

        def commit(self):
            self.commits += 1

        def close(self):
            self.closed = True

    monkeypatch.setitem(
        sys.modules,
        "kafka",
        SimpleNamespace(KafkaConsumer=FakeKafkaConsumer),
    )

    consumer_module.run_consumer(one_shot=True)

    kafka_consumer = created_consumers[0]
    assert kafka_consumer.topic == "suspicious-transactions"
    assert kafka_consumer.options["group_id"] == "portfolio-replay-test"
    assert kafka_consumer.options["auto_offset_reset"] == "latest"
    assert kafka_consumer.options["enable_auto_commit"] is False
    assert kafka_consumer.commits == 1
    assert kafka_consumer.closed is True

    with duckdb.connect(str(db_file)) as connection:
        assert connection.execute(
            "SELECT suspicious_count FROM raw.streaming_suspicious_summary"
        ).fetchone()[0] == 1
