'use strict';
// mysql2/promise pool. Reads DATABASE_URL (runtime-injected, wins over .env),
// otherwise DB_* / MYSQL_* vars. No localhost or port fallback: if the
// settings are missing we fail loudly instead of silently trying localhost.
// multipleStatements is deliberately disabled.
require('dotenv').config();
const mysql = require('mysql2/promise');

function missingDbSettings() {
  if (process.env.DATABASE_URL) return [];
  const missing = [];
  if (!(process.env.DB_HOST || process.env.MYSQL_HOST)) missing.push('DB_HOST');
  if (!(process.env.DB_USER || process.env.MYSQL_USER)) missing.push('DB_USER');
  if (!(process.env.DB_NAME || process.env.DB_DATABASE || process.env.MYSQL_DATABASE)) missing.push('DB_NAME');
  return missing;
}

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
  const missing = missingDbSettings();
  if (missing.length) {
    throw new Error(
      'Database settings missing: set DATABASE_URL, or DB_HOST/DB_USER/DB_NAME '
      + `(missing: ${missing.join(', ')}). These are injected automatically only for the app service.`
    );
  }
  const config = {
    host: process.env.DB_HOST || process.env.MYSQL_HOST,
    user: process.env.DB_USER || process.env.MYSQL_USER,
    password: process.env.DB_PASSWORD || process.env.MYSQL_PASSWORD,
    database: process.env.DB_NAME || process.env.DB_DATABASE || process.env.MYSQL_DATABASE,
    ...common,
  };
  const port = process.env.DB_PORT || process.env.MYSQL_PORT;
  if (port) config.port = Number(port);
  return config;
}

const pool = mysql.createPool(buildConfig());

module.exports = pool;
module.exports.missingDbSettings = missingDbSettings;
