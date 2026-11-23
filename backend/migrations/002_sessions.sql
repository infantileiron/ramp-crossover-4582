CREATE TABLE IF NOT EXISTS field_session (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    route_code text NOT NULL REFERENCES field_route(code),
    slot_code text NOT NULL,
    starts_at timestamptz NOT NULL,
    sealed_seat1_sequence text NOT NULL CHECK (sealed_seat1_sequence IN ('AB', 'BA')),
    started_at timestamptz,
    started_seat smallint CHECK (started_seat IN (1, 2)),
    started_code text,
    created_by text NOT NULL REFERENCES app_user(username),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (route_code, slot_code),
    CHECK ((started_at IS NULL) = (started_seat IS NULL)),
    CHECK ((started_seat IS NULL) = (started_code IS NULL))
);

CREATE TABLE IF NOT EXISTS session_member (
    session_id integer NOT NULL REFERENCES field_session(id) ON DELETE CASCADE,
    route_code text NOT NULL REFERENCES field_route(code),
    seat smallint NOT NULL CHECK (seat IN (1, 2)),
    participant_code text NOT NULL,
    period1 numeric(7,2) CHECK (period1 > 0 AND period1 <= 900),
    period2 numeric(7,2) CHECK (period2 > 0 AND period2 <= 900),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (session_id, seat)
);

CREATE UNIQUE INDEX IF NOT EXISTS session_member_participant_idx
    ON session_member (route_code, participant_code);
CREATE INDEX IF NOT EXISTS field_session_route_time_idx
    ON field_session (route_code, starts_at, id);

CREATE TABLE IF NOT EXISTS session_assignment (
    session_id integer NOT NULL REFERENCES field_session(id) ON DELETE CASCADE,
    seat smallint NOT NULL CHECK (seat IN (1, 2)),
    participant_code text NOT NULL,
    sequence text NOT NULL CHECK (sequence IN ('AB', 'BA')),
    revealed_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (session_id, seat),
    UNIQUE (session_id, participant_code)
);
