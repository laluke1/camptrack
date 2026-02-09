![Tests](https://github.com/OTheDev/camptrack/actions/workflows/test.yml/badge.svg)

## Contributors
This project was developed as part of a group assignment (6 members) at UCL. The other authors wish to remain anonymous. 

laluke1:
**CLI Architecture & Design:** Designed the command-line interface structure and user interaction flow.
**Camp Management Workflows:** Implemented the core logic for creating new camps, managing sessions, and handling coordinator inputs.
**Backend Logic:** Built the SQL persistence layer for the camp creation process, ensuring data integrity when initializing new camp records.

# CampTrack

## Contents
1. [Run](#run)
2. [Conda](#conda-setup)
3. [SQLite](#sqlite)
4. [Contributing Guide](#contributing-guide)

## Run

> [!TIP]
> It's recommended to run all `python`/`pip` related commands below within an
> *activated* virtual environment. [`conda`](https://docs.conda.io/projects/conda/en/stable/user-guide/getting-started.html)
> is brilliant (see below), but the standard library
> [`venv`](https://docs.python.org/3/library/venv.html) module also usually
> suffices.

### Option 1: Install/Uninstall (recommended)

In the project root, install the package in editable mode (`-e`):

```bash
python -m pip install -e .
```

Due to the `-e` option, any changes you make to the code immediately affect the
installed package. This is useful for development. An actual user would run
the above command without the `-e` option.

Then run

```bash
camptrack
```

To uninstall:
```bash
python -m pip uninstall camptrack
```

### Option 2: No installation

If you prefer, you can avoid installation.

In the `src` directory, run:

```bash
python -m camptrack
```

However, you will need to have run `pip install` on any dependencies listed in
`pyproject.toml` to ensure the application has everything it needs to run.

## Conda Setup

If you are interested, this is the [conda](https://docs.conda.io/projects/conda/en/stable/user-guide/getting-started.html) setup I am using. You will need conda
installed.

```bash
# Create a new virtual environment called `camptrack` with python 3.12.
conda create -n camptrack python=3.12
```

Before working on `camptrack` for a session:
```bash
# Activate the virtual environment
conda activate camptrack
```

Any `python` or `pip` related commands will use the self-contained python
within the activated virtual environment. This also means that when I install
`camptrack` while in the virtual environment, the `camptrack` command only
works within it.

When done working on `camptrack` for the session:
```bash
# Deactivate the virtual environment
conda deactivate
```

Once I am done working on `camptrack` forever, or I just want to start from
a fresh virtual environment:
```bash
# Delete the virtual environment (including any installed packages within)
conda remove -n camptrack --all
```

## SQLite

`sqlite3` also has an interactive mode which allows you to read in the
database file used for an application and run SQL queries on it. Here is an
example for `camptrack`. It assumes `camptrack` has already been installed in
a virtual environment.

```bash
# Activate camptrack virtual environment
conda activate camptrack

# Find the path to the camptrack database file
# If `camptrack-dev` is not found, run:
# python -m pip install -e . in the activated virtual environment
$ camptrack-dev path
SQLite database path: /Users/od/.camptrack/camptrack.db

# Run sqlite3 in interactive mode
$ sqlite3
SQLite version 3.43.2 2023-10-10 13:08:14
Enter ".help" for usage hints.
Connected to a transient in-memory database.
Use ".open FILENAME" to reopen on a persistent database.
sqlite> .open /Users/od/.camptrack/camptrack.db
sqlite> .tables
users
sqlite> .schema users
CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT CHECK(role IN ('admin', 'coordinator', 'leader')) NOT NULL,
        is_disabled INTEGER DEFAULT 0 CHECK(is_disabled IN (0, 1))
    );
sqlite> .mode box
sqlite> .headers on
sqlite> SELECT * FROM users;
<output omitted>
sqlite> .quit
```

## Contributing Guide
> [!TIP]
> Issues can be used for fixing bugs or any other features. They do not need to be from the list of user stories. This is a generic guide.
> Feel free to ping anyone for any clarification 😊
1. [Optional] Claim user stories from [full list here](https://docs.google.com/document/d/1lshWyTaLj-9hJZG9D9B2X4BVCFqIixigIqNucdpIuy8/edit?usp=sharing).
    * You can claim one or more related user stories
    * Indicate stories that are claimed on the document (example below)
    ![Example for claiming user stories](/assets/readme_screenshots/claiming-user-stories.png)

2. Create issue on [repo's Issues page](https://github.com/OTheDev/camptrack/issues).
    * Give the issue a decent name (i.e. short, description of scope)
    * Copy and paste relevant user stories into description
    * The user stories are non-exhaustive; add more details where needed!
    * Create Issue
    ![Create issue](/assets/readme_screenshots/creating-issue.png)
3. Create branch from issue
    * On the right panel, under `Development`, click **Create branch**. Ensure the upstream is from `main`.
    * You can now run the commands on your local IDE's terminal
        ```
        git pull camptrack
        git checkout <branch-name>
        ```
4. Make your changes on the feature branch. **Commit small and frequently!**
    ```
    git add
    git commit -m "<commit-message>"
    ```
    ```
    # EXAMPLE (. for all changes in current and child directories)
    git add .
    git commit -m "add login command"
    ```
5. When you want to share your changes / ready for a review, push your branch.
    ```
    git push origin <branch-name>
    ```

6. On the github repo's [Pull Request page](https://github.com/OTheDev/camptrack/pulls), create **New pull request** on the top right hand corner.
    * Choose your branch: `base: main` ← `compare: <your-branch>`
    * Create!

7. After your work has been reviewed and approved, you may opt to merge your branch into `main` via **Squash and Merge** option.
    ![Squash and Merge](/assets/readme_screenshots/squash-and-merge.png)

8. Great work camptracking! 😃
