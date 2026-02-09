/******************************************************************************
 *  Tables
 ******************************************************************************/

CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,

    username        TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL CHECK(
                        role IN ('admin', 'coordinator', 'leader')
                    ),
    is_disabled     INTEGER DEFAULT 0 CHECK(is_disabled IN (0, 1)) NOT NULL
);

-- Assumes a direct chat messaging system is desired, not broadcast messaging.
CREATE TABLE IF NOT EXISTS messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id       INTEGER NOT NULL REFERENCES users(id),
    recipient_id    INTEGER NOT NULL REFERENCES users(id),

    message         TEXT NOT NULL,
    is_read         INTEGER NOT NULL DEFAULT 0 CHECK(is_read IN (0, 1)),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS camps (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,                      -- One-to-many: coordinator -> camps
    name            TEXT NOT NULL,
    coordinator_id  INTEGER NOT NULL REFERENCES users(id),                  -- One-to-many: leader -> camps. NULL until a leader selects the camp.
    leader_id       INTEGER REFERENCES users(id),
    location        TEXT NOT NULL,                                          -- TODO: how should we encode location information? Should there be a table
                                                                            -- of available locations this organization has?
    latitude        REAL,
    longitude       REAL,
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    type            TEXT NOT NULL CHECK(                                    -- Represents the initial food stock per day on camp creation, but may
                        type IN ('day_camp', 'overnight', 'expedition')     -- change if the coordinator manually sets a new level.
                    ),
    approved_daily_food_stock
                    INTEGER NOT NULL DEFAULT 0,
    leader_daily_payment_rate
                    DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    capacity        INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    daily_food_per_camper INTEGER DEFAULT 0,
    CHECK (end_date >= start_date)
);

-- For bulk CSV import.
CREATE TABLE IF NOT EXISTS campers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    camp_id         INTEGER NOT NULL REFERENCES camps(id) ON DELETE CASCADE,

    name            TEXT NOT NULL CHECK(name != ''),
                    -- 'yyyy-mm-dd'
    date_of_birth   TEXT NOT NULL CHECK(
        LENGTH(date_of_birth) = 10 AND date_of_birth LIKE '____-__-__'
    ),
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- If multiple imports, helps ensure the same camper is not imported twice
    -- to the same camp. Assume only one person with a given name and date of
    -- birth in a given camp.
    -- e.g. INSERT OR IGNORE INTO campers (camp_id, name, date_of_birth)
    --      VALUES (?, ? , ?) ...
    UNIQUE(camp_id, name, date_of_birth)
);

-- This table will be necessary if we want users to be able to register for
-- specific days or weeks of a camp. Initial implementation will assume that
-- each camper will be there for each day of the camp for simplicity
CREATE TABLE IF NOT EXISTS camper_registration (
    registration_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    camper_id           INTEGER REFERENCES campers(id),
    camp_id             INTEGER REFERENCES camps(id),
    start_date          TEXT NOT NULL CHECK(
                        LENGTH(start_date) = 10 AND start_date LIKE '____-__-__'
                        ),
    end_date        TEXT NOT NULL CHECK(
                        LENGTH(end_date) = 10 AND end_date LIKE '____-__-__'
                    ),

    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    camp_id         INTEGER NOT NULL REFERENCES camps(id) ON DELETE CASCADE,
    coordinator_id  INTEGER NOT NULL REFERENCES users(id),

    -- TODO(ed): maybe use the old version of type
    type            TEXT DEFAULT NULL 
                         CHECK(type IS NULL OR TYPE IN ('not_enough_food', 'low_daily_payment_rate')),
    message         TEXT NOT NULL,
    is_read         INTEGER DEFAULT 0 CHECK(is_read IN (0, 1)),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activities (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    camp_id         INTEGER NOT NULL REFERENCES camps(id) ON DELETE CASCADE,

    -- TODO: probably not necessary, but could add optional start/end time
    activity_date   DATE NOT NULL,
    activity_name   TEXT NOT NULL,

    incident_count  INTEGER DEFAULT 0, -- Used to derive incident count in stats report
    notes           TEXT, -- Daily activity outcomes and special achievements here
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- To model the case where a Scout might not participate in all camp
-- activities)
CREATE TABLE IF NOT EXISTS activity_campers (
    activity_id     INTEGER NOT NULL REFERENCES activities(id)
                        ON DELETE CASCADE,
    camper_id       INTEGER NOT NULL REFERENCES campers(id)
                        ON DELETE CASCADE,
    PRIMARY KEY (activity_id, camper_id)
);


-- Stores per-camper, per-day attendance for camps, including flagged absences 
-- for coordinator notifications
CREATE TABLE IF NOT EXISTS attendance_records (
    record_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    camp_id         INTEGER NOT NULL REFERENCES camps(id),
    camper_id       INTEGER NOT NULL REFERENCES campers(id),
    date            TEXT NOT NULL CHECK(
                        LENGTH(date) = 10 AND date LIKE '____-__-__'
                    ),
    status          TEXT NOT NULL CHECK( 
                        status IN ('absent', 'present', 'pending')
                    ),
    -- Whether the coordinator has been notified of an absence
    -- flagged         INTEGER DEFAULT 0 CHECK(flagged IN (0, 1)) NOT NULL,
    -- notes           TEXT,
    -- leader_id       INTEGER NOT NULL REFERENCES users(id),
    timestamp       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS food_stock_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camp_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    stock_available INTEGER NOT NULL,
    -- optional metadata if you want to track source of change
    change_reason TEXT,        -- e.g., "daily usage", "top-up", "manual adjust"
    change_amount INTEGER,     -- positive or negative
    FOREIGN KEY (camp_id) REFERENCES camps(id)
);


/******************************************************************************
 *  Indexes
 ******************************************************************************/

CREATE INDEX IF NOT EXISTS
    idx_users_username              ON users(username, is_disabled);

CREATE INDEX IF NOT EXISTS
    idx_messages_recipient          ON messages(recipient_id, is_read);

CREATE INDEX IF NOT EXISTS
    idx_camps_leader                ON camps(leader_id);

CREATE INDEX IF NOT EXISTS
    idx_camps_start_end             ON camps(start_date, end_date);

CREATE INDEX IF NOT EXISTS
    idx_notifications_coordinator   ON notifications(coordinator_id, is_read);

CREATE INDEX IF NOT EXISTS
    idx_activity_campers_camper_id  ON activity_campers(camper_id);

CREATE INDEX IF NOT EXISTS
    idx_activities_camp_date        ON activities(camp_id, activity_date);
