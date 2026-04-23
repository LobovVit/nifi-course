# Импорт процесса в NiFi

1. Откройте UI: `http://localhost:8080/nifi`
2. Логин: `admin`
3. Пароль: `adminadminadmin`
4. Импортируйте файл `nifi/flows/rms_data_migration-version-2.json`.
5. Создайте Parameter Context `rms_data_migration` и задайте:
   - `postgres_class = org.postgresql.Driver`
   - `postgres_driver = /opt/nifi/nifi-current/drivers/postgresql-42.7.1.jar`
   - `postgres_source_url = jdbc:postgresql://pg_src:5432/rms_demo`
   - `postgres_source_user = demo`
   - `postgres_source_password = demo`
   - `postgres_source_connections = 8`
   - `postgres_target_url = jdbc:postgresql://pg_dst:5432/rms_demo`
   - `postgres_target_user = demo`
   - `postgres_target_password = demo`
   - `postgres_target_connections = 8`
   - `data_migration_config = <содержимое файла nifi/config/data_migration_config.demo.json>`
6. Включите controller services `postgres_source` и `postgres_target`.
7. Запустите процесс.
