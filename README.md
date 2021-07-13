# BFA Sumbission Bot

**Under development**

A discord bot that tracks submissions for Black Flag Academy's weekly challenges. Includes an admin interface for admin things. Makes heavy use of [discord.py](https://discordpy.readthedocs.io/en/stable/index.html) and [Django](https://www.djangoproject.com/).

## Commands

`!help` - shows available commands

`!submit <score> {attached photo}` - Submit a score **with picture** for the BFA Weekly Challenge. This command requires a photo attachment to be part of the message.

### Faculty/Admin only

`!newweek [optional week number] <challenge name>` - Start a new weekly challenge and open submissions

`!close` - Prevent submissions for the current challenge

`!reopen` - Resume submissions for the current challenge

## Deployment/Management

This app is hosted on heroku at https://bfa-submissions.herokuapp.com/.
Changes merged to the main branch are automatically deployed.

### Configs

These can all be set via the Heroku settings dashboard for this app or using the `heroku config:set` cli command.

- `SECRET_KEY`: Randomly generated Django secret key
- `DISCORD_BOT_TOKEN`: Token for the Discord bot (for instructions on creating one, see the [discord.py docs](https://discordpy.readthedocs.io/en/stable/discord.html)
- `SUBMISSION_CHANNEL_ID`: Discord channel ID for the submissions channel

### Creating an admin user

From the app's heroku dashboard:
- Click "More" >> "Run console"
- Enter `python manage.py createsuperuser`
- From there you will be prompted to enter a username, email, and password.
  - (If you're creating an account for someone else, enter a temporary password that you can send to them later. They'll be able to change this password once they login.)

Alternatively, if you have the [heroku-cli](https://devcenter.heroku.com/articles/heroku-cli) installed, you can run this from your terminal instead:
```sh
heroku run -a bfa-submissions python manage.py createsuperuser
```

## Local Development

Instructions to run this from your local computer.

### Initial Setup

**Requires Python >= 3.6 and PostgreSQL**

- Clone the repo to your computer

- Create and activate your [virtual environment](https://docs.python.org/3.9/tutorial/venv.html#creating-virtual-environments)

- Install dependencies
    ```sh
    python -m pip install -r requirements.txt
    ```

- Create database
    ```sh
    createdb bfa
    ```

- Run database migrations
    ```sh
    python manage.py migrate
    ```

- Create a local superuser (you'll use these fake creds to log in to the admin site locally)
    ```sh
    python manage.py createsuperuser
    ```

- Copy secrets.sample to secrets.sh
    ```sh
    cp secrets.sample secrets.sh
    ```

#### Setting up a discord bot for testing

- Create and invite a bot account to your server
    - Follow these instructions: https://discordpy.readthedocs.io/en/stable/discord.html
    - Replace `faketoken` in secrets.sh with your bot's token

- Get the ID for the specific channel you want the bot to work in
    - Right-click the channel name and select "Copy ID"
    - Replace `12345` in secrets.sh with your channel id

### Running the admin interface locally

- (Activate your virtual environment)
-
    ```sh
    source secrets.sh && python manage.py runserver
    ```
- Go to `localhost:8000` in your browser

### Running the discord bot locally

- (Activate your virtual environment)
-
    ```sh
    source secrets.sh && python bot.py
    ```

### Running tests

-
    ```sh
    SECRET_KEY=abc pytest
    ```

## Things to do

bot stuff:
- [x] initial bot setup
- [x] add things to db on submission
- [x] bot testing
- [ ] bot resume/catchup after off/on
- [x] auto determine student level (freshman, etc) by discord role

web stuff:
- [x] figure out django lol
- [x] implement auth req'd
- [x] view all submissions
- [x] view by week + role/level
- [x] view by user (in week?) (auto sort by latest or highest submission)
- [x] leaderboard view (https://docs.djangoproject.com/en/3.2/ref/contrib/admin/#adding-views-to-admin-sites)

later:
- [x] discord commands to close/open submissions (restricted to faculty role)
- [x] discord command to change week (restricted to faculty role)
- [ ] command to let students add/change their dancer name or twitter info
- [x] `python manage.py check --deploy` to look for things to change before actually hosting it
- [x] host on heroku
- [ ] discord oauth for front end login? :thinkingface:
- [x] if the bot told you what your upscore was (if you’re replacing one) like +[x] in green
- [ ] add reaction & reply to messages in response

refactoring / legibility
- [ ] move helpers in models.py to helpers.py or something?
- [ ] use discord Cogs to group commands by role requirements
- [ ] better logging
  - use logging instead of print?
- [ ] log before each command: https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.Bot.before_invoke
