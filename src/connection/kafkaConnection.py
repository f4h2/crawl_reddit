import os
import logging
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import json
from config import Config


from logger_config import setup_logging

setup_logging()
logger = logging.getLogger("KafkaConnection")

class KafkaConnection:
    def __init__(self):
        self.bootstrap_servers = Config.KAFKA_BOOTSTRAP_SERVERS
        self.security_protocol = Config.KAFKA_SECURITY_PROTOCOL
        self.sasl_mechanism = Config.KAFKA_SASL_MECHANISM
        self.sasl_username = Config.KAFKA_SASL_USERNAME
        self.sasl_password = Config.KAFKA_SASL_PASSWORD

        self.producer = None
        self.consumer = None

    def get_producer(self):
        """Khởi tạo Kafka Producer"""
        if not self.producer:
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    security_protocol=self.security_protocol,
                    sasl_mechanism=self.sasl_mechanism,
                    sasl_plain_username=self.sasl_username,
                    sasl_plain_password=self.sasl_password,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    key_serializer=lambda k: str(k).encode("utf-8") if k else None,
                    retries=3,
                )
                logger.info("✅ Kafka Producer connected")
            except KafkaError as e:
                logger.error(f"❌ Kafka Producer connection failed: {e}")
                raise
        return self.producer

    def get_consumer(self, topic, group_id="default-group", auto_offset_reset="earliest"):
        """Khởi tạo Kafka Consumer"""
        if not self.consumer:
            try:
                self.consumer = KafkaConsumer(
                    topic,
                    bootstrap_servers=self.bootstrap_servers,
                    security_protocol=self.security_protocol,
                    sasl_mechanism=self.sasl_mechanism,
                    sasl_plain_username=self.sasl_username,
                    sasl_plain_password=self.sasl_password,
                    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                    key_deserializer=lambda k: k.decode("utf-8") if k else None,
                    group_id=group_id,
                    auto_offset_reset=auto_offset_reset,
                    enable_auto_commit=True,
                )
                logger.info(f"✅ Kafka Consumer connected (topic={topic}, group={group_id})")
            except KafkaError as e:
                logger.error(f"❌ Kafka Consumer connection failed: {e}")
                raise
        return self.consumer

    def close(self):
        """Đóng kết nối"""
        if self.producer:
            self.producer.close()
            logger.info(" Kafka Producer closed")
            self.producer = None

        if self.consumer:
            self.consumer.close()
            logger.info(" Kafka Consumer closed")
            self.consumer = None
