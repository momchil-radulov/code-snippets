-- групиране по ДЕН, но може и "%H" ЧАС и т.н.
SELECT strftime('%d', created_at) AS bucket,
       SUM(COALESCE(coins, 0)) AS total_sum
  FROM coins
 WHERE device_num IN ('cw0082', 'cw0083', 'mp0174', 'mp0203', 'mp0342')
   AND datetime(created_at) >= datetime('2025-09-01 00:00:00') 
   AND datetime(created_at) <= datetime('2025-09-30 23:59:59')
 GROUP BY bucket
 ORDER BY bucket
