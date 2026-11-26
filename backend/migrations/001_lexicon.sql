CREATE TABLE IF NOT EXISTS source_rights (
    code text PRIMARY KEY,
    title text NOT NULL,
    owner text NOT NULL,
    document_ref text NOT NULL UNIQUE,
    expires_on date NOT NULL,
    allow_recording boolean NOT NULL DEFAULT false,
    revoked_at timestamptz,
    added_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS cue_terms (
    code text PRIMARY KEY,
    source_code text NOT NULL REFERENCES source_rights(code),
    language text NOT NULL CHECK (language IN ('zh','en','ja')),
    show_cue text NOT NULL,
    spoken_text text NOT NULL,
    bridge_words text NOT NULL,
    active boolean NOT NULL DEFAULT true,
    UNIQUE (source_code, language, show_cue, spoken_text)
);
CREATE TABLE IF NOT EXISTS candidate_scans (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    origin_code text NOT NULL REFERENCES cue_terms(code),
    target_language text NOT NULL CHECK (target_language IN ('zh','en','ja')),
    status text NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','ready','failed')),
    dimensions integer,
    vocabulary_size integer,
    explained_variance numeric(9,6),
    fingerprint text,
    error text,
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz
);
CREATE UNIQUE INDEX IF NOT EXISTS one_queued_scan
    ON candidate_scans(origin_code,target_language) WHERE status = 'queued';
CREATE TABLE IF NOT EXISTS proposed_pairs (
    scan_id bigint NOT NULL REFERENCES candidate_scans(id) ON DELETE CASCADE,
    target_code text NOT NULL REFERENCES cue_terms(code),
    rank smallint NOT NULL CHECK (rank BETWEEN 1 AND 5),
    similarity numeric(9,6) NOT NULL CHECK (similarity BETWEEN -1 AND 1),
    PRIMARY KEY (scan_id,target_code),
    UNIQUE (scan_id,rank)
);
CREATE TABLE IF NOT EXISTS approved_pairs (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    origin_code text NOT NULL REFERENCES cue_terms(code),
    target_code text NOT NULL REFERENCES cue_terms(code),
    target_language text NOT NULL CHECK (target_language IN ('zh','en','ja')),
    scan_id bigint REFERENCES candidate_scans(id),
    note text NOT NULL,
    approver text NOT NULL,
    status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','superseded')),
    approved_at timestamptz NOT NULL DEFAULT now(),
    CHECK (origin_code <> target_code)
);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_pair
    ON approved_pairs(origin_code,target_language) WHERE status = 'active';
CREATE TABLE IF NOT EXISTS glossary_editions (
    code text PRIMARY KEY,
    show_title text NOT NULL,
    show_date date NOT NULL,
    target_language text NOT NULL CHECK (target_language IN ('zh','en','ja')),
    channel text NOT NULL CHECK (channel IN ('headset','recording')),
    status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','published')),
    published_at timestamptz,
    published_by text
);
CREATE TABLE IF NOT EXISTS glossary_cues (
    edition_code text NOT NULL REFERENCES glossary_editions(code) ON DELETE CASCADE,
    position smallint NOT NULL CHECK (position > 0),
    origin_code text NOT NULL REFERENCES cue_terms(code),
    pair_id bigint REFERENCES approved_pairs(id),
    origin_snapshot text,
    target_snapshot text,
    license_snapshot text,
    PRIMARY KEY (edition_code,position),
    UNIQUE (edition_code,origin_code)
);
CREATE TABLE IF NOT EXISTS change_ledger (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_time timestamptz NOT NULL DEFAULT now(),
    actor text NOT NULL,
    operation text NOT NULL,
    entity_key text NOT NULL,
    detail jsonb NOT NULL DEFAULT '{}'
);
