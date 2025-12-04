DROP TABLE IF EXISTS facts;
DROP TABLE IF EXISTS dict;

CREATE TABLE IF NOT EXISTS dict (
    word TEXT PRIMARY KEY,
    as_integer INT,
    parent_integer INT
    );


CREATE TABLE IF NOT EXISTS pangrams (
    word TEXT PRIMARY KEY,
    letter_set CHAR(7)
    );

CREATE INDEX idx_letter_set on pangrams(letter_set);

CREATE TABLE IF NOT EXISTS facts (
    word TEXT,
    pangram TEXT,
    panletter CHAR(1)
    );


