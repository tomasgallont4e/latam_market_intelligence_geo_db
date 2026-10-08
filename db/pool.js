'use strict';
// mysql2/promise pool. Reads DATABASE_URL (runtime-injected, wins over .env),
// falling back to DB_* vars. multipleStatements is deliberately disabled.
require('dotenv').config();
const mysql = require('mysql2/promise');

function buildConfig() {
  const common = {
    waitForConnections: true,
    connectionLimit: 10,
    multipleStatements: false,
    charset: 'utf8mb4',
    supportBigNumbers: true,
    bigNumberStrings: false,
    dateStrings: true,
  };
  if (process.env.DATABASE_URL) {
    return { uri: process.env.DATABASE_URL, ...common };
  }
  return {
    host: process.env.DB_HOST || process.env.MYSQL_HOST,
    port: Number(process.env.DB_PORT || process.env.MYSQL_PORT || 3306),
    user: process.env.DB_USER || process.env.MYSQL_USER,
    password: process.env.DB_PASSWORD || process.env.MYSQL_PASSWORD,
    database: process.env.DB_NAME || process.env.DB_DATABASE || process.env.MYSQL_DATABASE,
    ...common,
  };
}

const pool = mysql.createPool(buildConfig());

module.exports = pool;