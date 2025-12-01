import uuid

import structlog

run_code = str(uuid.uuid4())


def add_run_code(logger, method_name, event_dict) -> dict:
    event_dict["run_code"] = run_code
    return event_dict


structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        add_run_code,
        structlog.dev.ConsoleRenderer(),
    ]
)
log = structlog.get_logger()
