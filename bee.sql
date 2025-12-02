DROP TABLE IF EXISTS facts;
DROP TABLE IF EXISTS dict;

CREATE TABLE IF NOT EXISTS dict (
    word TEXT PRIMARY KEY;
    as_integer INT;
    parent_integer INT
    );


CREATE TABLE IF NOT EXISTS facts (

    );
