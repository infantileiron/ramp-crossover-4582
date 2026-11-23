CREATE TABLE IF NOT EXISTS app_user (
    username text PRIMARY KEY,
    display_name text NOT NULL,
    password_hash text NOT NULL,
    role text NOT NULL CHECK (role IN ('reviewer', 'analyst', 'viewer'))
);
CREATE TABLE IF NOT EXISTS field_route (
    code text PRIMARY KEY,
    name text NOT NULL,
    start_at text NOT NULL,
    finish_at text NOT NULL,
    length_m integer NOT NULL CHECK (length_m > 0),
    description text NOT NULL,
    sign_a text NOT NULL,
    sign_b text NOT NULL
);
CREATE TABLE IF NOT EXISTS field_pair (
    route_code text NOT NULL REFERENCES field_route(code),
    code text NOT NULL,
    sequence text NOT NULL CHECK (sequence IN ('AB', 'BA')),
    period1 numeric(7,2) CHECK (period1 > 0 AND period1 <= 900),
    period2 numeric(7,2) CHECK (period2 > 0 AND period2 <= 900),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (period1 IS NOT NULL OR period2 IS NOT NULL),
    PRIMARY KEY (route_code, code)
);
CREATE TABLE IF NOT EXISTS analysis_plan (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    route_code text NOT NULL REFERENCES field_route(code),
    edition text NOT NULL,
    min_pairs integer NOT NULL CHECK (min_pairs BETWEEN 2 AND 50),
    gap_limit numeric(5,2) NOT NULL CHECK (gap_limit > 0 AND gap_limit <= 120),
    created_by text NOT NULL REFERENCES app_user(username),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (route_code, edition)
);
CREATE TABLE IF NOT EXISTS report (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    plan_id integer NOT NULL REFERENCES analysis_plan(id),
    created_by text NOT NULL REFERENCES app_user(username),
    created_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    state text NOT NULL DEFAULT 'queued' CHECK (state IN ('queued', 'ready', 'failed', 'published')),
    snapshot jsonb NOT NULL,
    fingerprint text NOT NULL,
    result jsonb,
    error text,
    decision text CHECK (decision IN ('retest', 'retain', 'pilot')),
    review_note text,
    reviewed_by text REFERENCES app_user(username),
    reviewed_at timestamptz
);
CREATE INDEX IF NOT EXISTS report_queue_idx ON report (id) WHERE state = 'queued';
CREATE TABLE IF NOT EXISTS audit_event (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    actor text NOT NULL REFERENCES app_user(username),
    event text NOT NULL,
    entity text NOT NULL,
    recorded_at timestamptz NOT NULL DEFAULT now(),
    detail jsonb NOT NULL
);
