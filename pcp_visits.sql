WITH inpatient_discharge AS (
    SELECT 
        individual_id, 
        inpatient_discharge_dt
    FROM 
        inpatient_visits
),

pcp_visits_within_7_days AS (
    SELECT 
        b.individual_id,
        b.inpatient_discharge_dt,
        COUNT(DISTINCT p.pcr_visit_date) AS pcp_visits_count
    FROM 
        inpatient_discharge b
    LEFT JOIN 
        pcr_visits p 
    ON 
        b.individual_id = p.patient_id 
    AND 
        p.pcr_visit_date BETWEEN b.inpatient_discharge_dt AND DATEADD(day, 7, b.inpatient_discharge_dt)
    GROUP BY
        b.individual_id, b.inpatient_discharge_dt
),

visit_counts AS (
    SELECT
        bp.individual_id,
        COUNT(DISTINCT i.inpatient_discharge_dt) AS num_admissions,
        COUNT(CASE WHEN p.pcp_visits_count > 0 THEN 1 END) AS unique_inpatient_stays_with_pcp_visits
    FROM
        base_population bp
    LEFT JOIN
        inpatient_discharge i ON bp.individual_id = i.individual_id
    LEFT JOIN
        pcp_visits_within_7_days p ON bp.individual_id = p.individual_id
    GROUP BY
        bp.individual_id
)

SELECT 
    individual_id, 
    num_admissions, 
    unique_inpatient_stays_with_pcp_visits
FROM 
    visit_counts;