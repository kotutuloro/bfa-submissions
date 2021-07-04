# BFA Sumbission Bot

**Under development**

A discord bot that tracks submissions for Black Flag Academy's weekly challenges. Includes an admin interface for admin things. Makes heavy use of [discord.py](https://discordpy.readthedocs.io/en/stable/index.html) and [Django](https://www.djangoproject.com/).

### Commands

`!help` - shows available commands

`!submit <score> {attached photo}` - Submit a score **with picture** for the BFA Weekly Challenge. This command requires a photo attachment to be part of the message.

#### Faculty/Admin only

`!newweek [optional week number] <challenge name>` - Start a new weekly challenge

## Deployment

Not yet lol

## Local Development

### Setup

**Requires Python >= 3.6 and PostgreSQL**

- Clone the repo to your computer

- Create and activate your [virtual environment](https://docs.python.org/3.9/tutorial/venv.html#creating-virtual-environments)

- Install dependencies
    ```sh
    python -m pip install -r requirements.txt
    ```

- Run database migrations
    ```sh
    python manage.py migrate
    ```

- Create a local superuser (you'll use these fake creds to log in to the admin site locally)
    ```sh
    python manage.py createsuperuser
    ```

#### Setting up a testing bot

- Copy secrets.sample to secrets.sh
    ```sh
    cp secrets.sample secrets.sh
    ```

- Create and invite a bot account to your server
    - Follow these instructions: https://discordpy.readthedocs.io/en/stable/discord.html
    - Replace `faketoken` in secrets.sh with your bot's token

- Get the ID for the specific channel you want the bot to work in
    - Right-click the channel name and select "Copy ID"
    - Replace `12345` in secrets.sh with your channel id

### Running the admin interface locally

-
    ```sh
    python manage.py runserver
    ```

- Go to `localhost:8000` in your browser

### Running the discord bot locally

-
    ```sh
    source secrets.sh
    ```

-
    ```sh
    python bot.py
    ```

### Testing

-
    ```sh
    python manage.py test
    ```

## Things to do

important/bugfixes:
- [ ] fix submission upscore calculation (should only use latest week's scores)
- [ ] add level to student model
  - https://docs.djangoproject.com/en/3.2/ref/models/fields/#choices

bot stuff:
- [x] initial bot setup
- [x] add things to db on submission
- [ ] bot testing?
- [ ] bot resume/catchup after off/on
- [ ] auto determine student level (freshman, etc) by discord role

web stuff:
- [x] figure out django lol
- [ ] implement auth req'd (adding views to admin? https://docs.djangoproject.com/en/2.2/ref/contrib/admin/#adding-views-to-admin-sites)
- [ ] view all submissions
- [ ] view by week + role/level
- [ ] view by user (in week?) (auto sort by latest or highest submission)

later:
- [ ] discord commands to close/open submissions (restricted to faculty role)
- [x] discord command to change week (restricted to faculty role)
- [ ] `python manage.py check --deploy` to look for things to change before actually hosting it
- [ ] host on heroku
- [ ] discord oauth for front end login? :thinkingface:
- [x] if the bot told you what your upscore was (if you’re replacing one) like +[x] in green
- [ ] command to let students add/change their dancer name or twitter info
- [ ] add reaction & reply to messages in response

refactoring / legibility
- [ ] move helpers in models.py to helpers.py or something?
- [ ] use discord Cogs to group commands by role requirements
- [ ] better logging
  - use logging instead of print?
- [ ] log before each command: https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.Bot.before_invoke
