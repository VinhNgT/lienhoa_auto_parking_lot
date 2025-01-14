import uuid
from typing import Callable

from uvicorn.main import Server


class RunOnShutdown:
    _jobs: dict[int, Callable[[None], None]] = dict()

    @classmethod
    def add(cls, new_job: Callable[[None], None]) -> str:
        new_uuid = uuid.uuid4()
        cls._jobs[new_uuid] = new_job
        return new_uuid

    @classmethod
    def remove(cls, job_id: uuid.UUID):
        cls._jobs.pop(job_id, None)

    @classmethod
    def get_jobs(cls) -> dict[int, Callable]:
        return cls._jobs.values()


original_handler = Server.handle_exit


class AppStatus:
    @staticmethod
    def handle_exit(*args, **kwargs):
        for job in RunOnShutdown.get_jobs():
            job()

        original_handler(*args, **kwargs)


Server.handle_exit = AppStatus.handle_exit
