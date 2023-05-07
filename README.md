# Diffuser Discord Bot

Run [deep-floyd/IF](https://github.com/deep-floyd/IF) as a basic discord bot.

<img width="344" alt="Discord_GZ6AmvvC6C" src="https://user-images.githubusercontent.com/6625384/236647785-fd66ba83-856f-4c18-8313-f4a214f7ade0.png">

> **/imagine** prompt:"an oil painting of a spiral galaxy" count:3

## Usage

> These instructions are fairly minimal and likely require some additional debugging to get it to work, if you run into problems feel free to create an issue. If you run into problems specifically on step #1, its best to get help on the official https://github.com/deep-floyd/IF/issues page.

1. Setup DeepFloyd IF at https://github.com/deep-floyd/IF to the point you are able to run the `Diffusers` example completely. This is the hardest part.
2. `git clone https://github.com/sshh12/diffuser-discord-bot`
3. Install requirements

- `pip install -r requirements-bot.txt` (discord bot dependencies)
- `pip install -r requirements-worker.txt` (model dependencies)

4. Set up a Discord Bot ([create bot](https://discord.com/developers/applications/))
5. Set up an Imgur API key ([create app](https://api.imgur.com/oauth2/addclient), anonymous usage)
6. Set environment variables

```
DISCORD_TOKEN= (bot secret token)
SYNC_GUILD= (optional guild id of server)
IMGUR_CLIENT_ID= (imgur client id)
```

7. `python scripts/run_bot.py`

8. Create a bot invite link and invite it to your server
