SELECT id, content
FROM story_read;


SELECT DISTINCT string_split(content, ' ') AS words
FROM story_read;