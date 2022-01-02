# Configurations
## Environment variables
- `DATABASE_URL`: the Postgres URL, starting with `postgres://`

- `HOST`: The URL of this web application Heroku is running on, like https://my-bot-app.herokuapp.com

- `TOKEN`: The Discord bot's token

- `TOPGG_TOKEN`: Top.gg token to upload the server count, this is optional.
## Buildpacks
- heroku/python
- https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest
# Contributions
- Please don't suggest any discord.py forks here. Slash commands handling should be implemented using the built-in [slash module](https://github.com/Saratoga-CV6/haruka-rewrite/tree/main/bot/slash)
