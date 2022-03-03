[![Discord Bots](https://top.gg/api/widget/status/848178172536946708.svg)](https://top.gg/bot/848178172536946708)
[![Discord Bots](https://top.gg/api/widget/servers/848178172536946708.svg)](https://top.gg/bot/848178172536946708)
[![Discord Bots](https://top.gg/api/widget/owner/848178172536946708.svg)](https://top.gg/bot/848178172536946708)
# Developer notes
### Key features
- Stream and download music from [YouTube](https://youtube.com) without having to install an opus library or host a Lavalink server
- Load images from [waifu.pics](https://waifu.pics), [waifu.im](https://waifu.im), [nekos.life](https://nekos.life), and [asuna.ga](https://asuna.ga)
- Fetch image source with [saucenao.com](https://saucenao.com)
- Provide search for [Urban Dictionary](https://urbandictionary.com), [MyAnimeList](https://myanimelist.net), [Pixiv](https://www.pixiv.net), [Tenor](https://tenor.com), [Zerochan](https://zerochan.net) and [nHentai](https://nhentai.net)
- Automatically leave the guild if no text command or slash command has been used within the last 30 days
### Configurations
#### Environment variables
- `DATABASE_URL` The Postgres URL, starting with `postgres://`

- `HOST` The URL of this web application Heroku is running on, like https://my-bot-app.herokuapp.com

- `TOKEN` The Discord bot's token

- `TOPGG_TOKEN` Top.gg token to upload the server count, this is optional.
#### Buildpacks
- heroku/python
- https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest
#### Running
- Python 3.9 is required. Install the dependencies with
```bash
pip install -r requirements.txt
```
- Note that since [uvloop](https://github.com/MagicStack/uvloop) does not support Windows, you will have to delete or comment out the line `uvloop==0.16.0` in the `requirements.txt` before running the above command on this platform.
- Navigate to the git directory and run
```bash
python ./bot/main.py
```
### Contributions
- Please don't suggest any discord.py forks here. Slash commands handling should be implemented using the built-in [slash module](https://github.com/Serious-senpai/haruka-rewrite/tree/main/bot/slash)
# Report errors
If you find an error, or want to request a feature, [open a GitHub issue](https://github.com/Serious-senpai/haruka-rewrite/issues/new) or send me via DM: `Serious-senpai#6929`
