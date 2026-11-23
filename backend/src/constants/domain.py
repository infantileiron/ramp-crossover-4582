from enum import StrEnum


class Role(StrEnum):
    REVIEWER = 'reviewer'
    ANALYST = 'analyst'
    VIEWER = 'viewer'


class Sequence(StrEnum):
    AB = 'AB'
    BA = 'BA'


class RunState(StrEnum):
    QUEUED = 'queued'
    READY = 'ready'
    FAILED = 'failed'
    PUBLISHED = 'published'


class Decision(StrEnum):
    RETEST = 'retest'
    RETAIN = 'retain'
    PILOT = 'pilot'
