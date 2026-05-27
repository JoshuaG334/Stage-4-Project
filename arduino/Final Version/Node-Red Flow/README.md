Smart Hurl Node-RED Flow
This flow provides the HTTP API backend for the Smart Hurl system. It receives data from the Android app and logs session and event data to a PostgreSQL database.
Endpoints

POST /session/start — starts a new session and returns a session_id
POST /event — logs a single classification event (swing or impact) with peak G and lambda values
POST /session/end — closes the session by stamping the ended_at timestamp

Setup

Install Node-RED on your server
Install the PostgreSQL node: npm install node-red-contrib-postgresql
Import smart_hurl_flow.json via the Node-RED editor (hamburger menu → Import)
Open the pg_config node and enter your PostgreSQL credentials
Deploy the flow

Database
The flow expects a PostgreSQL database with the following tables:


CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    player_name TEXT,
    notes TEXT,
    started_at TIMESTAMP DEFAULT now(),
    ended_at TIMESTAMP
);

CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id),
    classification TEXT,
    confidence INTEGER,
    peak_g REAL,
    decay_lambda REAL,
    recorded_at TIMESTAMP DEFAULT now()
);