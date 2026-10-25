-- Proposed protected GET-only bridge. Review before running in WKSP_MAHAMALI.
-- Never run Pulse.sql to connect the website. This script does not change its tables.
-- Stop if any proposed object already exists; do not replace teammates' APIs.
DECLARE
  n NUMBER;
  roles OWA.VC_ARR := OWA.VC_ARR('pulse.website.reader');
  patterns OWA.VC_ARR := OWA.VC_ARR('/pulse/v1/*');
  modules OWA.VC_ARR := OWA.VC_ARR('pulse.website.read');
BEGIN
  IF SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA') <> 'WKSP_MAHAMALI' THEN
    RAISE_APPLICATION_ERROR(-20001, 'Wrong schema: stop.');
  END IF;
  SELECT COUNT(*) INTO n FROM (
    SELECT name FROM user_ords_modules WHERE name = 'pulse.website.read'
    UNION ALL SELECT name FROM user_ords_roles WHERE name = 'pulse.website.reader'
    UNION ALL SELECT name FROM user_ords_privileges WHERE name = 'pulse.website.read.access'
    UNION ALL SELECT name FROM user_ords_clients WHERE name = 'pulse.website.backend'
  );
  IF n > 0 THEN
    RAISE_APPLICATION_ERROR(-20002, 'Existing Pulse API access found: inspect, do not replace.');
  END IF;
  ORDS.CREATE_ROLE(p_role_name => 'pulse.website.reader');
  ORDS.DEFINE_MODULE(p_module_name => 'pulse.website.read',
    p_base_path => '/pulse/v1/', p_items_per_page => 100, p_status => 'NOT_PUBLISHED');
  ORDS.DEFINE_PRIVILEGE(p_privilege_name => 'pulse.website.read.access',
    p_roles => roles, p_patterns => patterns, p_modules => modules,
    p_label => 'Pulse website read-only access',
    p_description => 'Read existing current-patient, latest-vital and open-alert views only.');

  ORDS.DEFINE_TEMPLATE(p_module_name => 'pulse.website.read', p_pattern => 'patients/');
  ORDS.DEFINE_HANDLER(p_module_name => 'pulse.website.read', p_pattern => 'patients/',
    p_method => 'GET', p_source_type => ORDS.source_type_collection_feed,
    p_source => q'[SELECT patient_id, forename, surname, age, presenting_complaint,
      status, TO_CHAR(arrival_time, 'YYYY-MM-DD"T"HH24:MI:SS') arrival_time,
      triage, zone_name, assignment_id, device_id
      FROM WKSP_MAHAMALI.v_current_patients ORDER BY patient_id]', p_items_per_page => 100);

  ORDS.DEFINE_TEMPLATE(p_module_name => 'pulse.website.read', p_pattern => 'readings/latest/');
  ORDS.DEFINE_HANDLER(p_module_name => 'pulse.website.read', p_pattern => 'readings/latest/',
    p_method => 'GET', p_source_type => ORDS.source_type_collection_feed,
    p_source => q'[SELECT patient_id, assignment_id,
      TO_CHAR(recorded_at, 'YYYY-MM-DD"T"HH24:MI:SS') recorded_at,
      heart_rate, skin_temp
      FROM (
        SELECT da.patient_id, vr.assignment_id, vr.recorded_at, vr.heart_rate, vr.skin_temp,
          ROW_NUMBER() OVER (PARTITION BY vr.assignment_id
            ORDER BY vr.recorded_at DESC, vr.reading_id DESC) latest_row
        FROM WKSP_MAHAMALI.vital_reading vr
        JOIN WKSP_MAHAMALI.device_assignment da ON da.assignment_id = vr.assignment_id
        WHERE da.removed_at IS NULL
      ) WHERE latest_row = 1 ORDER BY patient_id, assignment_id]',
    p_items_per_page => 100);

  ORDS.DEFINE_TEMPLATE(p_module_name => 'pulse.website.read', p_pattern => 'alerts/');
  ORDS.DEFINE_HANDLER(p_module_name => 'pulse.website.read', p_pattern => 'alerts/',
    p_method => 'GET', p_source_type => ORDS.source_type_collection_feed,
    p_source => q'[SELECT alert_id, patient_id, patient_name, zone_name, alert_type,
      severity, message, TO_CHAR(triggered_at, 'YYYY-MM-DD"T"HH24:MI:SS') triggered_at,
      status, acknowledged_by FROM WKSP_MAHAMALI.v_open_alerts ORDER BY alert_id]', p_items_per_page => 100);

  -- Publish only after the privilege protects the module and path.
  ORDS.PUBLISH_MODULE(p_module_name => 'pulse.website.read', p_status => 'PUBLISHED');
  COMMIT;
END;
/

-- A separately registered client_credentials client must receive ONLY the above role.
-- Use ORDS_SECURITY.REGISTER_CLIENT / ROTATE_CLIENT_SECRET / GRANT_CLIENT_ROLE
-- supported by the installed ORDS version. Never put generated secrets in this file.
-- Verify anonymous GETs are rejected before using the backend client.
-- The updated VITAL_READING table has no SPO2 column. SQL NULL explicitly means
-- unavailable; it is not a reading. V_LATEST_VITALS is invalid and remains Maham-owned.
-- Read only through an explicit active assignment; do not guess patient/device joins.
