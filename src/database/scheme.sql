BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS "general" (
    "user_id" INTEGER PRIMARY KEY,
    "city" TEXT,
    "timezone_str" TEXT, -- Example: "Europe/Moscow"
    "lng" REAL, -- float
    "lat" REAL, -- float
    "registration_date" INTEGER, -- int(datetime.now().timestamp())
    "completed" INTEGER DEFAULT 0,
    "completed_ishraq" INTEGER DEFAULT 0,
    "completed_jumuah" INTEGER DEFAULT 0,
    "missed" INTEGER DEFAULT 0,
    "missed_jumuah" INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS "salah" (
    "user_id" INTEGER PRIMARY KEY,
    "fajr" INTEGER DEFAULT 0, -- boolean
    "shuruq" INTEGER DEFAULT 0, -- boolean
    "ishraq" INTEGER DEFAULT 0, -- boolean
    "zuhr" INTEGER DEFAULT 0, -- boolean
    "asr" INTEGER DEFAULT 0, -- boolean
    "maghrib" INTEGER DEFAULT 0, -- boolean
    "isha" INTEGER DEFAULT 0, -- boolean
    "jumuah" INTEGER DEFAULT 0, -- boolean
    FOREIGN KEY (user_id) REFERENCES general(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "settings" (
    "user_id" INTEGER PRIMARY KEY,
    "madhab" INTEGER DEFAULT 0,
    "ishraq" INTEGER DEFAULT 0, -- boolean
    "shuruq" INTEGER DEFAULT 0, -- boolean
    "statistics" INTEGER DEFAULT 0, -- boolean
    "salah" INTEGER DEFAULT 0, -- boolean
    "language" TEXT,
    FOREIGN KEY (user_id) REFERENCES general(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "stage" (
    "user_id" INTEGER PRIMARY KEY,
    "stage" INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES general(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "timings" (
    "user_id" INTEGER PRIMARY KEY,
    "fajr" TEXT,
    "shuruq" TEXT,
    "ishraq" TEXT, 
    "zuhr" TEXT,
    "asr" TEXT,
    "maghrib" TEXT,
    "isha" TEXT,
    FOREIGN KEY (user_id) REFERENCES general(user_id) ON DELETE CASCADE
);

COMMIT;