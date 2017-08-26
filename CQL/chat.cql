CREATE KEYSPACE Chat WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 3 };

CREATE TABLE chat.chat_by_chat_id (
  chat_id TEXT,
  user_id TEXT,
  chat_name TEXT,
  time TIMESTAMP,

  PRIMARY KEY (chat_id, time)
) WITH CLUSTERING ORDER BY (time DESC);

CREATE TABLE chat.chat_by_user_id (
  user_id TEXT,
  chat_name TEXT,
  chat_id TEXT,
  time TIMESTAMP,

  PRIMARY KEY (user_id, time)
) WITH CLUSTERING ORDER BY (time DESC);

CREATE TABLE chat.chat_message_by_chat_id (
  chat_id TEXT,
  message_id timeuuid,
  asset_name TEXT,
  author_id TEXT,
  message TEXT,

  PRIMARY KEY (chat_id, message_id)
) WITH CLUSTERING ORDER BY (message_id DESC);