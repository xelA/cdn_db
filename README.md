# cdn_db
xelA's method of saving custom images inside a safe place, basically CDN, but with organization in mind

## API
```
POST    /<folder>                   Upload file to storage
  args
    ?overwrite=true|false             Replace image that are duplicate
  headers
    user_id                           Discord ID of the responsible author
    channel_id                        optional: Which Channel ID it went from
    guild_id                          optional: Which Guild ID it went from

DELETE  /<folder>/<filename>        Delete file from storage
GET     /<folder>/<filename>        Get file from storage
GET     /<folder>/<filename>/stats  Get file stats from storage
```

## Requirements
- Python 3.6 or above
