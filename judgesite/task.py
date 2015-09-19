#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import io
import json
import subprocess
import tempfile
import os

from . import config
from models import save_result


class NoTestDataException(Exception):
    pass


class JudgeTask(object):

    def __init__(self, message):
        task = json.loads(message)
        self.submit_type = task["submit_type"]
        self.status_id = str(task["status_id"])
        self.code = task["code"]
        self.language = task["language"]
        self.testdata_id = str(task["testdata_id"])
        self.time_limit = str(task["time_limit"])
        self.memory_limit = str(task["memory_limit"])

        self.result = ""
        self.run_time = 0
        self.run_memory = 0
        self.others = ""

    def go(self):
        self._dump_code_to_file()
        try:
            self._prepare_testdata_file()
        except NoTestDataException, e:
            self.result = 'NoTestDataError'
            self._save_result()
            return
        logging.info(1)
        try:
            self._run()
        except Exception as e:
            logging.error(e)
            logging.info(2)
            self.result = "System Error"
            self._save_result()
            return
        logging.info(3)

        self._read_result()

        self._save_result()

    def _dump_code_to_file(self):
        logging.info("Dump code to file")
        filename = "Main." + self.language
        self.code_file = os.path.join(tempfile.mkdtemp(), filename)
        code_file = io.open(self.code_file, 'w', encoding='utf8')
        code_file.write(self.code)
        code_file.close()

    def _prepare_testdata_file(self):
        logging.info("Prepare testdata")
        self.input_file = os.path.join(
            config.testdata_path, self.testdata_id, "in.in")
        self.output_file = os.path.join(
            config.testdata_path, self.testdata_id, "out.out")
        if not os.path.exists(self.input_file) or\
                not os.path.exists(self.output_file):
            raise NoTestDataException

    def _run(self):
        logging.info("GO!GO!GO!")
        commands = ["ljudge", "--max-cpu-time", str(float(self.time_limit) / 1000),
                    "--max-memory", str(int(self.memory_limit) * 1024),
                    "--user-code", self.code_file,
                    "--testcase",
                    "--input", self.input_file,
                    "--output", self.output_file]
        self.output_result = subprocess.check_output(commands)

    def _read_result(self):
        logging.info("Read result")
        result = json.loads(self.output_result)
        if not result['compilation']['success']:
            self.result = "Compile Error"
            self.others = result['compilation']['log']
            return
        if result['testcases'][0]['result'] == "ACCEPTED":
            self.result = "Accepted"
            self.run_time = result['testcases'][0]['time'] * 1000
            self.run_memory = result['testcases'][0]['memory'] / 1024.0
            return
        if result['testcases'][0]['result'] == "WRONG_ANSWER":
            self.result = "Wrong Answer"
            return
        if result['testcases'][0]['result'] == "TIME_LIMIT_EXCEEDED":
            self.result = "Time Limit Exceeded"
            return
        if result['testcases'][0]['result'] == "MEMORY_LIMIT_EXCEEDED":
            self.result = "Memory Limit Exceeded"
            return
        if result['testcases'][0]['result'] == "PRESENTATION_ERROR":
            self.result = "Presentation Error"
            return
        self.result = "Runtime Error"

    def _save_result(self):
        logging.info("Save result")
        save_result(status_id=self.status_id,
                    type=self.submit_type,
                    run_time=self.run_time,
                    run_memory=self.run_memory,
                    compiler_output=self.others,
                    status=self.result)
