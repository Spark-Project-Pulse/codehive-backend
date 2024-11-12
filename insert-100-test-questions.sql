-- Insert 100 Test Questions into the "Questions" table
INSERT INTO "Questions" (
    question_id,
    asker_id,
    related_project_id,
    related_community_id,
    title,
    description,
    created_at,
    search_vector,
    code_context,
    code_context_full_pathname,
    code_context_line_number
  )
SELECT uuid_generate_v4() AS question_id,
  -- Select a random existing asker_id from Users
  (
    SELECT "user_id"
    FROM "Users"
    ORDER BY RANDOM()
    LIMIT 1
  ) AS asker_id,
  -- Select a random existing related_project_id from Projects
  (
    SELECT project_id
    FROM "Projects"
    ORDER BY RANDOM()
    LIMIT 1
  ) AS related_project_id,
  -- Select a random existing related_community_id from Communities or set to NULL (80% chance of assignment)
  CASE
    WHEN random() < 0.8 THEN (
      SELECT community_id
      FROM "Communities"
      ORDER BY RANDOM()
      LIMIT 1
    )
    ELSE NULL
  END AS related_community_id,
  -- Generate Title
  CONCAT('Test Question ', gs) AS title,
  -- Generate Description
  CONCAT(
    'This is the description for test question number ',
    gs,
    '.'
  ) AS description,
  -- Generate created_at timestamp, spread over the past 100 days
  NOW() - (INTERVAL '1 day' * gs) AS created_at,
  -- Generate search_vector based on title and description
  to_tsvector(
    'english',
    CONCAT(
      'This is the description for test question number ',
      gs,
      '. Test Question ',
      gs
    )
  ) AS search_vector,
  -- Set code_context and code_context_full_pathname to empty strings
  '' AS code_context,
  '' AS code_context_full_pathname,
  -- Set code_context_line_number to NULL
  NULL AS code_context_line_number
FROM generate_series(1, 100) AS gs;