---
note subject: GoRuck Calendar
creation date: 2025-08-24 13:13
type: quick_note
tags: [  ]
---

```dataview
CALENDAR file.day
WHERE file.folder = this.file.folder
WHERE file.day
```

## Workout List
```dataview
table without id
  link(file.link, sort_title) as "Workout",
  "[" + string(post_date) + "](" + post_url + ")" as "Posted"
FROM "journal/goruck_wod"
WHERE type = "goruck_wod" AND post_date
SORT post_date desc

```
