# Configurations
## Environment variables
- `DATABASE_URL` the Postgres URL, starting with `postgres://`

- `HOST` The URL of this web application Heroku is running on, like https://my-bot-app.herokuapp.com

- `TOKEN` The Discord bot's token

- `TOPGG_TOKEN` Top.gg token to upload the server count, this is optional.
## Buildpacks
- heroku/python
- https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest
# Key features
- Stream and download music from [YouTube](http://youtube.com) without having to install opus library or host a Lavalink server
- Load images from [waifu.pics](https://waifu.pics), [waifu.im](https://waifu.im), [nekos.life](https://nekos.life), and [asuna.ga](https://asuna.ga)
- Fetch image source with [saucenao.com](https://saucenao.com)
- Provide search for [Urban Dictionary](https://urbandictionary.com), [MyAnimeList](https://myanimelist.net), [Pixiv](https://www.pixiv.net), [Tenor](https://tenor.com) and [nHentai](https://nhentai.net)
# Contributions
- Please don't suggest any discord.py forks here. Slash commands handling should be implemented using the built-in [slash module](https://github.com/Saratoga-CV6/haruka-rewrite/tree/main/bot/slash)
