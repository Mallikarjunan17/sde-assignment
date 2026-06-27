-- ===========================================================
-- Post Call Processing Improvements
-- ===========================================================

-- Track every background processing job

CREATE TABLE postcall_jobs (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    interaction_id UUID NOT NULL REFERENCES interactions(id),

    customer_id UUID NOT NULL,

    campaign_id UUID NOT NULL,

    priority VARCHAR(20) DEFAULT 'NORMAL',

    status VARCHAR(30) DEFAULT 'PENDING',

    estimated_tokens INTEGER,

    actual_tokens INTEGER,

    retry_count INTEGER DEFAULT 0,

    last_error TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_postcall_jobs_status
ON postcall_jobs(status);

CREATE INDEX idx_postcall_jobs_priority
ON postcall_jobs(priority);

------------------------------------------------------------

CREATE TABLE customer_token_budget (

    customer_id UUID PRIMARY KEY,

    reserved_tokens_per_minute INTEGER NOT NULL,

    borrowed_tokens INTEGER DEFAULT 0,

    available_tokens INTEGER NOT NULL,

    updated_at TIMESTAMPTZ DEFAULT NOW()
);

------------------------------------------------------------

CREATE TABLE audit_logs (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    interaction_id UUID,

    event_type VARCHAR(100),

    status VARCHAR(50),

    details JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_interaction
ON audit_logs(interaction_id);

------------------------------------------------------------

ALTER TABLE interactions

ADD COLUMN processing_priority VARCHAR(20) DEFAULT 'NORMAL',

ADD COLUMN processing_status VARCHAR(30) DEFAULT 'PENDING',

ADD COLUMN llm_tokens_used INTEGER DEFAULT 0,

ADD COLUMN correlation_id UUID DEFAULT uuid_generate_v4();