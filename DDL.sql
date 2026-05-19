### ALTER TABLE WITH DEFAULT ON PRODUCTION: in/out/- ###
ALTER TABLE device_logs
    ADD COLUMN IF NOT EXISTS mqtt_direction VARCHAR(3);

UPDATE device_logs
   SET mqtt_direction = '-'
 WHERE mqtt_direction IS NULL;

ALTER TABLE device_logs
    ALTER COLUMN mqtt_direction SET DEFAULT '-',
    ALTER COLUMN mqtt_direction SET NOT NULL;
