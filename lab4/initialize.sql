INSERT INTO main.roles (role_code, role_name) VALUES
    (1, 'User'),
    (2, 'Author'),
    (3, 'Moderator'),
    (4, 'Administrator');

INSERT INTO main.themes (theme_name, description) VALUES
    ('IT', 'Information technologies'),
    ('History', 'History'),
    ('Philosophy', 'Philosophy studies');

INSERT INTO main.themes (theme_name, parent_id, description) VALUES
    ('Databases', (SELECT theme_id FROM main.themes WHERE theme_name = 'IT'), 'Postgresql and others'),
    ('Ancient history', (SELECT theme_id FROM main.themes WHERE theme_name = 'History'), 'Real old history'),
    ('Python', (SELECT theme_id FROM main.themes WHERE theme_name = 'IT'), 'Python programming language');

INSERT INTO main.informers (informer_name, informer_type, additional_info) VALUES
    ('Informer 1', 'person', 'Test'),
    ('Informer 2', 'person', NULL),
    ('MEPhI', 'organization', 'Moscow engineering physics institute');
