import json

from sqlalchemy import MetaData, Column, types, Index, Table, select
import datetime
from sqlalchemy.sql import functions, Select

from ..core.task import Task
from ..connection.rdb import RDBConnection


class ParadeRecorder(object):
    _metadata = MetaData()
    _task_table = Table('parade_exec_tasks', _metadata,
                        Column('id', types.BigInteger, autoincrement=True, primary_key=True),
                        Column('project', types.String(128), nullable=False),
                        Column('flow', types.String(128), nullable=False),
                        Column('task', types.String(128), nullable=False),
                        Column('flow_id', types.BigInteger, nullable=False),
                        Column('attributes', types.Text, default="{}"),
                        Column('start_time', types.DateTime, default=datetime.datetime.now),
                        Column('create_time', types.DateTime, default=datetime.datetime.now),
                        Column('commit_time', types.DateTime, default=datetime.datetime.now),
                        Column('update_time', types.DateTime, default=datetime.datetime.now,
                               onupdate=datetime.datetime.now),
                        Column('status', types.Integer, default=Task.STATE_PENDING),
                        Column('message', types.Text, default='OK'),

                        Index('idx_task_create', 'task', 'create_time'),
                        )

    _flow_table = Table('parade_exec_flows', _metadata,
                        Column('id', types.BigInteger, autoincrement=True, primary_key=True),
                        Column('project', types.String(128), nullable=False),
                        Column('flow', types.String(128), nullable=False),
                        Column('tasks', types.Text, nullable=False),
                        Column('create_time', types.DateTime, default=datetime.datetime.now),
                        Column('commit_time', types.DateTime, default=datetime.datetime.now),
                        Column('update_time', types.DateTime, default=datetime.datetime.now,
                               onupdate=datetime.datetime.now),
                        Column('status', types.Integer, default=Task.STATE_EXECUTING),

                        Index('idx_flow_create', 'flow', 'create_time'),
                        )

    def __init__(self, project, conn):
        assert isinstance(conn, RDBConnection)
        self.conn = conn
        self.project = project

    def init_record_tables(self):
        _conn = self.conn.open()
        if not self._task_table.exists(_conn):
            try:
                self._task_table.create(_conn)
            except:
                pass
        if not self._flow_table.exists(_conn):
            try:
                self._flow_table.create(_conn)
            except:
                pass

    def last_success_record(self, task_name):
        _conn = self.conn.open()
        _query = self._task_table.select(). \
            where(self._task_table.c.task == task_name). \
            where(self._task_table.c.status == Task.STATE_SUCCESS). \
            order_by(self._task_table.c.create_time.desc()).limit(1)
        _last_record = _conn.execute(_query).fetchone()

        if _last_record is not None:
            return dict(_last_record)
        return None

    def create_task_record(self, task_name, attributes, flow_id, flow):
        _conn = self.conn.open()

        # 创建待提交checkpoint
        ins = self._task_table.insert().values(project=self.project,
                                               flow_id=flow_id, flow=flow,
                                               task=task_name,
                                               attributes=json.dumps(attributes))
        return _conn.execute(ins).inserted_primary_key[0]

    def create_flow_record(self, flow_name, tasks):
        _conn = self.conn.open()

        # 创建待提交checkpoint
        ins = self._flow_table.insert().values(project=self.project, flow=flow_name, tasks=','.join(tasks))
        return _conn.execute(ins).inserted_primary_key[0]

    def mark_task_start(self, exec_id):
        _conn = self.conn.open()
        sql = self._task_table.update(). \
            where(self._task_table.c.id == exec_id). \
            values(status=Task.STATE_EXECUTING, start_time=functions.now(), update_time=functions.now())
        _conn.execute(sql)

    def mark_task_success(self, exec_id, msg='OK'):
        _conn = self.conn.open()
        sql = self._task_table.update(). \
            where(self._task_table.c.id == exec_id). \
            values(status=Task.STATE_SUCCESS, message=str(msg), commit_time=functions.now(), update_time=functions.now())
        _conn.execute(sql)

    def mark_task_failed(self, exec_id, err):
        _conn = self.conn.open()
        sql = self._task_table.update(). \
            where(self._task_table.c.id == exec_id). \
            values(status=Task.STATE_FAILED, message=str(err), update_time=functions.now())
        _conn.execute(sql)

    def mark_task_cancelled(self, exec_id, failed_deps):
        _conn = self.conn.open()
        sql = self._task_table.update(). \
            where(self._task_table.c.id == exec_id). \
            values(status=Task.STATE_CANCELLED, message='canceled for failed dependencies [{}]'.format(failed_deps), update_time=functions.now())
        _conn.execute(sql)

    def mark_flow_success(self, flow_id):
        _conn = self.conn.open()
        sql = self._flow_table.update(). \
            where(self._flow_table.c.id == flow_id). \
            values(status=Task.STATE_SUCCESS, commit_time=functions.now(), update_time=functions.now())
        _conn.execute(sql)

    def mark_flow_failed(self, flow_id):
        _conn = self.conn.open()
        sql = self._flow_table.update(). \
            where(self._flow_table.c.id == flow_id). \
            values(status=Task.STATE_FAILED, update_time=functions.now())
        _conn.execute(sql)

    def load_flow_by_id(self, exec_id):
        _conn = self.conn.open()
        _query = self._flow_table.select(). \
            where(self._flow_table.c.id == exec_id)
        exec_flow = _conn.execute(_query).fetchone()

        if exec_flow is not None:
            raw = dict(exec_flow)
            raw['create_time'] = str(raw['create_time'])
            raw['update_time'] = str(raw['update_time'])
            raw['commit_time'] = str(raw['commit_time'])
            return raw
        return None

    def load_flows(self, flow=None, executing=None, page_size=0, page_no=1):
        from sqlalchemy import func
        query = self._flow_table.select()
        if flow is not None:
            query = query.where(self._flow_table.c.flow == flow)
        if executing is not None:
            query = query.where(
                self._flow_table.c.status == 0) if executing else query.where(
                self._flow_table.c.status > 0)

        total = None
        if page_size > 0:
            count_query = query.with_only_columns([func.count(self._flow_table.c.id)])
            query = query.limit(page_size).offset((page_no - 1) * page_size)
            total = self.conn.open().execute(count_query).scalar()

        query = query.order_by(self._flow_table.c.create_time.desc())
        df = self.conn.load_query(str(query.compile(compile_kwargs={"literal_binds": True})))

        df['create_time'] = df['create_time'].apply(lambda ts: str(ts))
        df['commit_time'] = df['commit_time'].apply(lambda ts: str(ts))
        df['update_time'] = df['update_time'].apply(lambda ts: str(ts))

        if not total:
            total = len(df)
        return {'data': json.loads(df.to_json(orient='records')), 'total': total}

    def load_flow_tasks(self, flow_id, page_size=0, page_no=1):
        query = self._task_table.select().where(self._task_table.c.flow_id == flow_id)
        if page_size > 0:
            query = query.limit(page_size).offset((page_no - 1) * page_size)
        df = self.conn.load_query(str(query.compile(compile_kwargs={"literal_binds": True})))

        df['start_time'] = df['start_time'].apply(lambda ts: str(ts))
        df['create_time'] = df['create_time'].apply(lambda ts: str(ts))
        df['commit_time'] = df['commit_time'].apply(lambda ts: str(ts))
        df['update_time'] = df['update_time'].apply(lambda ts: str(ts))

        tasks = json.loads(df.to_json(orient='records'))
        return tasks
