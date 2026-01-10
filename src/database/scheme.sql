BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS "general" (
    "user_id" INTEGER PRIMARY KEY,
    "city" TEXT,
    "timezone_str" TEXT,
    "lng" REAL,
    "lat" REAL,
    "registration_date" INTEGER,
    "completed" INTEGER DEFAULT 0,
    "completed_ishraq" INTEGER DEFAULT 0,
    "completed_jumuah" INTEGER DEFAULT 0,
    "missed" INTEGER DEFAULT 0,
    "missed_jumuah" INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS "salah" (
    "user_id" INTEGER PRIMARY KEY,
    "fajr" INTEGER DEFAULT 0,
    "shuruq" INTEGER DEFAULT 0,
    "ishraq" INTEGER DEFAULT 0,
    "zuhr" INTEGER DEFAULT 0,
    "asr" INTEGER DEFAULT 0,
    "maghrib" INTEGER DEFAULT 0,
    "isha" INTEGER DEFAULT 0,
    "jumuah" INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS "settings" (
    "user_id" INTEGER PRIMARY KEY,
    "madhab" INTEGER DEFAULT 0,
    "ishraq" INTEGER DEFAULT 0,
    "shuruq" INTEGER DEFAULT 0,
    "statistics" INTEGER DEFAULT 0,
    "salah" INTEGER DEFAULT 0,
    "language" TEXT
);

CREATE TABLE IF NOT EXISTS "stage" (
    "user_id" INTEGER PRIMARY KEY,
    "stage" INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS "timings" (
    "user_id" INTEGER PRIMARY KEY,
    "fajr" TEXT,
    "shuruq" TEXT,
    "ishraq" TEXT, 
    "zuhr" TEXT,
    "asr" TEXT,
    "maghrib" TEXT,
    "isha" TEXT
);

COMMIT;