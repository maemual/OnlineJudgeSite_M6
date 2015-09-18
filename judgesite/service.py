#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import pika

from . import config
from task import JudgeTask


class JudgeSite(object):

    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=config.rmq_host, port=config.rmq_port))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=config.rmq_queue, durable=True)

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(self._consume, queue=config.rmq_queue)

    def _consume(self, ch, method, properties, body):
        logging.info("GOT A TASK!")
        task = JudgeTask(body)
        task.go()
        self.channel.basic_ack(delivery_tag=method.delivery_tag)
        logging.info("TASK IS DONE!")

    def run(self):
        self.channel.start_consuming()

