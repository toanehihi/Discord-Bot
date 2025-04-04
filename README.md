
# Discord Bot Project

## Introduction
This project is a Discord bot designed to provide various features, including server moderation, music playback, utility tools, and task management. Built with `discord.py` and other libraries, this bot ensures smooth and user-friendly functionality.

## Features
- **Owner Commands**: Manage bot operations like syncing, loading, or reloading commands.
- **Moderation Commands**: Keep your server in check with tools like kick, ban, and message clearing.
- **Utility Commands**: Enhance your server experience with tools like translation, weather information, and Wikipedia searches.
- **Music Commands**: Enjoy YouTube music playback with options for queue management, shuffling, and more.
- **Todo Commands**: Manage tasks with a simple and efficient task management system.

## Installation
### Requirements
- Python 3.8 or higher
- `discord.py` library ([Installation guide](https://discordpy.readthedocs.io/en/stable/))
- `ffmpeg` installed on your system ([Download ffmpeg](https://ffmpeg.org/download.html))
- Additional dependencies: `youtube-dl`, `yt-dlp`, `aiohttp`, `redis`, etc.
### Setup
1. Install `ffmpeg` on your system:
   ```bash
   sudo apt install ffmpeg
   ```
2. Clone the repository:
   ```bash
   git clone https://github.com/toanehihi/Discord-Bot.git
   cd Discord-Bot
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the root directory to store your secret token:
   ```
   TOKEN="YOUR TOKEN HERE"
   ```
5. Run the bot:
   ```bash
   python main.py
   ```

## Commands List
### Owner Commands
- `!sync <scope>`: Synchronize bot commands (scope: `guild` or `global`).
- `!unsync <scope>`: Unsynchronize bot commands (scope: `guild` or `global`).
- `!load <cog_name>`: Load a cog dynamically.
- `!reload <cog_name>`: Reload a cog dynamically.
- `!say <text>`: Make the bot send a message with the provided text.
- `!embed <text>`: Make the bot send an embedded message with the provided text.

### Moderation Commands
- `!kick <username> <reason>`: Kick a user from the server.
- `!ban <username> <reason>`: Ban a user from the server.
- `!clear <amount_message>`: Delete a specified number of messages from a channel.

### Utility Commands
- `!help`: Display the list of commands and their descriptions.
- `!translate <text>`: Translate text to the default language.
- `!weather <city_name>`: Get weather information for a specified city.
- `!wiki <something>`: Search Wikipedia for information on a topic.

### Music Commands
- `!play <song_name_or_youtube_url>`: Play a song from YouTube.
- `!skip`: Skip the current song.
- `!pause`: Pause the music.
- `!resume`: Resume the paused music.
- `!queue`: Display the current song queue.
- `!clear_queue`: Clear all songs in the queue.
- `!shuffle`: Shuffle the song queue.
- `!leave`: Disconnect the bot from the voice channel.

### Todo Commands
- `!todo`: Display your task list.
- `!list`: Display all tasks.
- `!list_w`: Display completed tasks.
- `!list_nw`: Display incomplete tasks.
- `!clear_todo`: Clear all tasks from the list.
- `!add <task_name> <exp_date>`: Add a new task with an expiration date.
- `!edit <index_of_task> <new_task_name>`: Edit the task at the specified index.
- `!delete <index_of_task>`: Delete the task at the specified index.
- `!complete <index_of_task> <status>`: Mark a task as complete (`1`) or incomplete (`0`).
- `!deadline <index_of_task> <exp_date>`: Update the deadline for a task.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.

## Support
If you encounter any issues or have questions, please open an issue on [GitHub](https://github.com/toanehihi/Discord-Bot/issues).
