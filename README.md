# Diffuser Discord Bot

This repository allows you to run [deep-floyd/IF](https://github.com/deep-floyd/IF) as a basic Discord bot.

![Discord Bot Image](https://user-images.githubusercontent.com/6625384/236647785-fd66ba83-856f-4c18-8313-f4a214f7ade0.png)

Use the **/imagine** command with a prompt like `"an oil painting of a spiral galaxy"` to interact with the bot.

## Commands

The following commands are supported:

- `/imagine prompt: <your_prompt_here>`
- `/enhance prompt: <your_prompt_here> image_url: <image_url_here>`

Both prompts support {template} syntax, e.g., `a {photo, painting} of a {dog, cat}` generates 4 different prompts.

## Setup

The setup instructions are provided below. If you encounter any issues, feel free to create an issue in this repository. For problems specifically related to step 1, it is recommended to seek help on the official [DeepFloyd IF issues page](https://github.com/deep-floyd/IF/issues).

1. Set up DeepFloyd IF at https://github.com/deep-floyd/IF until you can run the `Diffusers` example. This is the most challenging part.
2. Clone this repository using `git clone https://github.com/sshh12/diffuser-discord-bot`.
3. Install the required dependencies:

    - Run `pip install -r requirements-bot.txt` to install Discord bot dependencies.
    - Run `pip install -r requirements-worker.txt` to install model dependencies.

4. Set up a Discord Bot. You can create one [here](https://discord.com/developers/applications/).
5. Obtain an Imgur API key by creating an app [here](https://api.imgur.com/oauth2/addclient). You can use it anonymously.
6. Set up the following environment variables:

    ```
    DISCORD_TOKEN= (your bot's secret token)
    SYNC_GUILD= (optional guild id of your server)
    IMGUR_CLIENT_ID= (your Imgur client id)
    ```

7. Run the bot using `python scripts/run_bot.py`.
8. Create a bot invite link and invite the bot to your server.
