#!/usr/bin/env python
# -*- coding: utf-8 -*-


import requests
from sqlalchemy import create_engine
from sqlalchemy.sql import text

from . import config

engine = create_engine(
    "mysql://{0}:{1}@{2}/{3}?charset=utf8".format(
        config.mysql_user,
        config.mysql_password,
        config.mysql_host,
        config.mysql_db_name
    ),
    pool_recycle=600
)


def save_result(status_id=0, type='normal', run_time=0, run_memory=0, compiler_output="", status="SystemError"):
    conn = engine.connect()
    table_name = 'fishteam_submit_status' if type == 'normal' else 'fishteam_contest_status'
    sql = text(
       '''
       update {} set `compilerOutput` = :compiler_output, `runtime` = :run_time, `runmemory` = :run_memory, `status` = :status where `id` = :status_id;
       '''.format(table_name)
    )

    conn.execute(sql, compiler_output=compiler_output, run_time=run_time, run_memory=run_memory, status=status, status_id=status_id)
    _update_counters(status_id, type)
    conn.close()


def _update_counters(status_id, type):
    argument = {
        'status_id': status_id,
        'type': type,
        'access_key': config.access_key,
    }
    requests.post(config.api_url+"/Api/v1/updatecounter/", argument)
