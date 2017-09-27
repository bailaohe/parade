from sqlalchemy import MetaData, Column, types, Index, Table
import datetime
from sqlalchemy.sql import functions
from ..connection.rdb import RDBConnection


class ParadeRecorder(object):
    _metadata = MetaData()
    _task_table = Table('parade_exec_tasks', _metadata,
                        Column('id', types.BigInteger, autoincrement=True, primary_key=True),
                        Column('project', types.String(128), nullable=False),
                        Column('flow', types.String(128), nullable=False),
                        Column('task', types.String(128), nullable=False),
                        Column('flow_id', types.BigInteger, nullable=False),
                        Column('checkpoint', types.DateTime, default=datetime.datetime.now),
                        Column('create_time', types.DateTime, default=datetime.datetime.now),
                        Column('commit_time', types.DateTime, default=datetime.datetime.now),
                        Column('update_time', types.DateTime, default=datetime.datetime.now,
                               onupdate=datetime.datetime.now),
                        Column('status', types.Integer, default=0),
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
                        Column('status', types.Integer, default=0),

                        Index('idx_flow_create', 'flow', 'create_time'),
                        )

    def __init__(self, project, conn):
        assert isinstance(conn, RDBConnection)
        self.conn = conn
        self.project = project

    def init_record_if_absent(self):
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

    def last_record(self, task_name):
        _conn = self.conn.open()
        _query = self._task_table.select(). \
            where(self._task_table.c.task == task_name). \
            where(self._task_table.c.status == 1). \
            order_by(self._task_table.c.create_time.desc()).limit(1)
        _last_record = _conn.execute(_query).fetchone()

        if _last_record is not None:
            return dict(_last_record)
        return None

    def create_record(self, task_name, new_checkpoint, flow_id, flow):
        _conn = self.conn.open()

        # 创建待提交checkpoint
        ins = self._task_table.insert().values(project=self.project, flow_id=flow_id, flow=flow, task=task_name,
                                               checkpoint=new_checkpoint)
        return _conn.execute(ins).inserted_primary_key[0]

    def create_flow_record(self, flow_name, tasks):
        _conn = self.conn.open()

        # 创建待提交checkpoint
        ins = self._flow_table.insert().values(project=self.project, flow=flow_name, tasks=','.join(tasks))
        return _conn.execute(ins).inserted_primary_key[0]

    def commit_record(self, txn_id):
        _conn = self.conn.open()
        sql = self._task_table.update(). \
            where(self._task_table.c.id == txn_id). \
            values(status=1, commit_time=functions.now())
        _conn.execute(sql)

    def rollback_record(self, txn_id, err):
        _conn = self.conn.open()
        sql = self._task_table.update(). \
            where(self._task_table.c.id == txn_id). \
            values(status=2, message=str(err))
        _conn.execute(sql)
