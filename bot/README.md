# Configurations
## Environment variables
- `DATABASE_URL`: Heroku provides this when enabling the Postgres add-on, the URL starts with `postgres://`

- `HOST`: The URL of this web application Heroku is running on, like https://my-bot-app.herokuapp.com

- `TOKEN`: The Discord bot's token

- `TOPGG_TOKEN`: Top.gg token to upload the server count, this is optional.
## Buildpacks
- heroku/python
- https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest
