CREATE TABLE IF NOT EXISTS history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ingredients TEXT,
  markdown TEXT,
  nutrition TEXT,
  date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
