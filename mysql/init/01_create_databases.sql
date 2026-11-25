-- ============================================================================
-- PT TelkoNusa Digital — MySQL 8.0 Isolated Database Initialization
-- Prinsip: Satu Data, Satu Pemilik (4 schema terpisah)
-- ============================================================================

CREATE DATABASE IF NOT EXISTS telconusa_crm     CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS telconusa_hrm     CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS telconusa_scm     CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS telconusa_finance CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

GRANT ALL PRIVILEGES ON telconusa_crm.*     TO 'telconusa'@'%';
GRANT ALL PRIVILEGES ON telconusa_hrm.*     TO 'telconusa'@'%';
GRANT ALL PRIVILEGES ON telconusa_scm.*     TO 'telconusa'@'%';
GRANT ALL PRIVILEGES ON telconusa_finance.* TO 'telconusa'@'%';
FLUSH PRIVILEGES;
