CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,

    customer_name TEXT,

    customer_segment TEXT,

    customer_value TEXT,

    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS calls (
    call_id TEXT PRIMARY KEY,

    customer_id TEXT,

    file_name TEXT NOT NULL,

    file_path TEXT NOT NULL,

    file_size INTEGER,

    source TEXT,

    status TEXT,

    created_at TEXT,

    FOREIGN KEY(customer_id)
        REFERENCES customers(customer_id)
);


CREATE TABLE IF NOT EXISTS transcripts (
    transcript_id TEXT PRIMARY KEY,

    call_id TEXT NOT NULL,

    language TEXT,

    duration REAL,

    full_text TEXT,

    created_at TEXT,

    FOREIGN KEY(call_id)
        REFERENCES calls(call_id)
);


CREATE TABLE IF NOT EXISTS transcript_segments (
    segment_id INTEGER PRIMARY KEY AUTOINCREMENT,

    call_id TEXT NOT NULL,

    start_time REAL,

    end_time REAL,

    speaker TEXT,

    text TEXT,

    FOREIGN KEY(call_id)
        REFERENCES calls(call_id)
);


CREATE TABLE IF NOT EXISTS customer_analysis (
    analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,

    call_id TEXT NOT NULL UNIQUE,

    sentiment TEXT,

    sentiment_score REAL,

    created_at TEXT,

    FOREIGN KEY(call_id)
        REFERENCES calls(call_id)
);

CREATE TABLE IF NOT EXISTS dissatisfaction_root_causes (
    root_cause_id TEXT PRIMARY KEY,
    call_id TEXT NOT NULL UNIQUE,
    dissatisfaction TEXT NOT NULL,
    root_cause_category TEXT,
    root_cause TEXT,
    severity TEXT,
    confidence REAL,
    evidence TEXT,
    created_at TEXT NOT NULL,

    FOREIGN KEY(call_id)
        REFERENCES calls(call_id)        
);

CREATE TABLE IF NOT EXISTS customer_emotions (
    emotion_id TEXT PRIMARY KEY,
    call_id TEXT NOT NULL UNIQUE,
    primary_emotion TEXT NOT NULL,
    emotion_score REAL,
    anger_score REAL,
    frustration_score REAL,
    disappointment_score REAL,
    confusion_score REAL,
    fear_score REAL,
    sadness_score REAL,
    neutral_score REAL,
    joy_score REAL,
    surprise_score REAL,
    emotion_intensity REAL,
    confidence REAL,
    evidence TEXT,
    created_at TEXT NOT NULL,

    FOREIGN KEY(call_id)
        REFERENCES calls(call_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS agent_tool_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    reason TEXT,
    input_data TEXT,
    output_data TEXT,
    execution_status TEXT,
    execution_time REAL,
    created_at TEXT NOT NULL,

    FOREIGN KEY(call_id)
        REFERENCES calls(call_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS diarization_segments (

    diarization_segment_id
        INTEGER PRIMARY KEY AUTOINCREMENT,

    call_id TEXT NOT NULL,

    start_time REAL,

    end_time REAL,

    speaker TEXT,

    FOREIGN KEY(call_id)
        REFERENCES calls(call_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS transcript_raw_segments (

    segment_id INTEGER PRIMARY KEY AUTOINCREMENT,

    call_id TEXT NOT NULL,

    start_time REAL,

    end_time REAL,

    text TEXT,

    FOREIGN KEY(call_id)
        REFERENCES calls(call_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS churn_risk_analysis (

    churn_analysis_id TEXT PRIMARY KEY,

    call_id TEXT NOT NULL UNIQUE,

    churn_risk_score REAL NOT NULL,

    churn_risk_level TEXT NOT NULL,

    recovery_priority TEXT NOT NULL,

    customer_intent TEXT,

    closure_intent INTEGER DEFAULT 0,

    fraud_intent INTEGER DEFAULT 0,

    risk_factors TEXT,

    triggered_rules TEXT,

    recommendations TEXT,

    created_at TEXT NOT NULL,

    FOREIGN KEY(call_id)
        REFERENCES calls(call_id)
        ON DELETE CASCADE
);