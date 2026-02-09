import math
import sqlite3
import time
import threading

from camptrack.database.models import User
from camptrack.database.connection import get_db_cursor
from camptrack.utils.terminal import clear_screen
from camptrack.ui import center, clear_terminal_lines, show_header, Ansi

from datetime import datetime
from typing import Optional


class MessagingInterface:
    """
    Chat interface for a user.
    """

    _TERMINAL_WIDTH = 80

    def __init__(self, user: User, *, chats_per_page: int = 3):
        self.user = user

        self.is_executing = True

        # For pagination when displaying list of all chats a user has
        self.chats_per_page = chats_per_page
        self.chat_page = 0

        # State for current chat
        self.chatting = False
        self.recipient_id: Optional[int] = None
        self.recipient_username: Optional[str] = None
        self.messages_per_page = 10  # Load only 10 most recent when open chat
        self.last_msg: int = 0  # id of last message in a chat
        self.history_offset = 0

        # Database lock. Use threading for near realtime chat
        self.database_lock = threading.Lock()

    def run(self) -> None:
        """
        Main command loop for CampTrack's direct messaging.
        """
        while self.is_executing:
            try:
                chats = self.show_command_menu_view()

                command = input(f"\nEnter command: ").strip().lower()
                match command:
                    case 'p':
                        # Previous page
                        if self.chat_page > 0:
                            self.chat_page -= 1
                    case 'n':
                        # Next page (to show older chats)
                        total_chats = self.total_chats()
                        total_pages = math.ceil(
                            total_chats / self.chats_per_page
                        )
                        if self.chat_page < total_pages - 1:
                            self.chat_page += 1
                    case 'f':
                        # First page
                        self.chat_page = 0
                    case 'l':
                        total_chats = self.total_chats()
                        if total_chats > 0:
                            total_pages = math.ceil(
                                total_chats / self.chats_per_page
                            )
                            self.chat_page = total_pages - 1
                    case 'o':
                        # Open a chat with a user
                        recipient_id, recipient_username = \
                            self.prompt_for_recipient_and_initialize_chat()
                        if recipient_id and recipient_username:
                            self.chat_page = 0
                            self.goto_chat_view(
                                recipient_id, recipient_username
                            )
                    case 'u':
                        self.show_users_with_pagination()
                    case 'r':
                        # Refresh
                        continue
                    case 'b' | 'q':
                        # Quit
                        self.is_executing = False
                    case _ if command.isdigit():
                        # Convert from one-based index to zero-based
                        i = int(command) - 1
                        if i < 0 or i > len(chats):
                            continue
                        self.goto_chat_view(
                            chats[i]['chat_partner_id'],
                            chats[i]['chat_partner_username']
                        )

                    case _:
                        print(f"Unrecognized command: {command}")
                        time.sleep(1)

            except KeyboardInterrupt:
                self.is_executing = False
                break

            except Exception:
                print('Sorry, we are facing technical difficulties.')
                break

        print("Exiting chat interface...")
        time.sleep(1)

#=============================================================================
#   Print/Display
#=============================================================================

    def show_command_menu_view(self) -> list[sqlite3.Row]:
        """
        Show the chat command menu as well as a list of previously opened
        conversations (with pagination).
        """
        clear_screen()
        show_header(center=True)
        self.show_header()

        # Calculate the total number of pages and current page (one-based idx)
        total_chats = self.total_chats()
        chats = self.chats(
            limit=self.chats_per_page,
            offset=self.chat_page * self.chats_per_page
        )
        total_pages = math.ceil(total_chats / self.chats_per_page)
        current_page = self.chat_page + 1 if total_pages > 0 else 0

        if not chats:
            print('No chats to display.')
        else:
            # Print pagination info for the user
            if total_pages > 1:
                print(f"Chats (Page {current_page}/{total_pages})")
            else:
                print("Chats")

            print('-' * self._TERMINAL_WIDTH)

            # Print chats for the page
            for idx, row in enumerate(chats, 1):
                # Time of last message within chat
                formatted_time = datetime.strptime(
                    row['timestamp'], '%Y-%m-%d %H:%M:%S'
                ).strftime('%I:%M %p - %B %d, %Y')

                # Show snippet of the message, truncating if it does not fit
                message_snippet = (
                    f"{row['message'][:20]}..."
                    if len(row['message']) > 20
                    else row['message']
                )

                # Show the users role too
                role = f"[{row['role'].capitalize()}]"

                mark_unread = f" {Ansi.BLUE}■{Ansi.END}" \
                    if row['num_unread'] > 0 \
                    else ''
                total_unread = f" ({row['num_unread']} unread)" \
                    if row['num_unread'] > 1 \
                    else ''

                print(f"{idx:2}. "
                      f"{Ansi.GREEN}{row['chat_partner_username']}{Ansi.END} "
                      f"{role}{mark_unread}{total_unread}")
                print(f"    {message_snippet}")
                print(f"    {Ansi.GRAY}{formatted_time}{Ansi.END}")

            # If more than one page, show how to advance a page or go back
            if total_pages > 1:
                print()
                print('-' * self._TERMINAL_WIDTH)
                guide = []

                # There's a previous if not on first page
                # if self.chat_page > 0:
                guide.append('f - first page')
                guide.append('p - previous')

                # There's a next if not on last page
                # if self.chat_page < total_pages - 1:
                guide.append('n - next')
                guide.append('l - last page')

                if guide:
                    print('Navigate: ' + ' | '.join(guide))

            print('-' * self._TERMINAL_WIDTH)
        self.show_menu_commands(total_chats=len(chats))

        return chats

    def show_menu_commands(self, *, total_chats: int) -> None:
        print('Commands:')
        if total_chats > 0:
            print(f"    # - Open chat from above list [1-{total_chats}]")
        print('    o - Open chat with a specified user')
        print('    u - List all users you can chat with')
        print('    r - Refresh')
        print(
            f'    {Ansi.RED}b{Ansi.END} - {Ansi.RED}Exit{Ansi.END} chat '
            f'interface'
        )

    def show_header(self) -> None:
        # TODO: don't use private variable
        role = self.user._ROLE_PUBLIC[self.user.role]

        print('═' * self._TERMINAL_WIDTH)
        print(center(
                f"{Ansi.BOLD}Messages{Ansi.END} | "
                f"{Ansi.BLUE}@{Ansi.END}{self.user.username} [{role}]",
                self._TERMINAL_WIDTH
            )
        )
        print('═' * self._TERMINAL_WIDTH)

    def show_chat_header(self, other: str) -> None:
        """
        Print a header that appears above messages within a chat.
        """
        print('═' * self._TERMINAL_WIDTH)
        print(center(
            f"Chat with {Ansi.BLUE}@{Ansi.END}{other}", self._TERMINAL_WIDTH
        ))
        print('═' * self._TERMINAL_WIDTH)
        print(f"\nEnter {Ansi.RED}/help{Ansi.END} for a list of commands, "
              f"{Ansi.RED}/b{Ansi.END} to exit the chat.\n")

    def show_chat_help(self) -> None:
        """
        Output to display to user when /help is entered within a chat.
        """
        print()
        print('Commands:')
        print(f'    {Ansi.RED}/b{Ansi.END}    - Go back to the main chat menu')
        print('    /m    - Load older messages')
        print('    /c    - Clean the chat view')
        print()

    def show_message_from(
        self,
        id: int,
        username: str,
        message: str,
        timestamp: str
    ) -> None:
        formatted_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S') \
            .strftime('%I:%M %p - %B %d, %Y')
        if self.user.id == id:
            print(f"[{Ansi.GRAY}{formatted_time}{Ansi.END}] You: {message}")
        else:
            print(
                f"[{Ansi.GRAY}{formatted_time}{Ansi.END}] {username}: "
                f"{message}"
            )

#=============================================================================
#   Database Queries
#=============================================================================

    def nondisabled_users(self) -> list[sqlite3.Row]:
        """
        Return a list of all nondisabled users.
        """
        with get_db_cursor(check_same_thread=False, enable_wal=True) as cursor:
            cursor.execute("""
                SELECT id, username, role
                FROM users
                WHERE is_disabled = 0 AND id != ?
                ORDER BY role, username
            """, (self.user.id,))
            return cursor.fetchall()

    def total_chats(self) -> int:
        """
        Return the total number of chats this user has with nondisabled users.
        """
        with get_db_cursor(check_same_thread=False, enable_wal=True) as cursor:
            query = """
                SELECT COUNT(DISTINCT
                    CASE
                        WHEN sender_id = ?
                        THEN recipient_id
                        ELSE sender_id
                    END
                ) as total_chats
                FROM messages
                WHERE (
                    sender_id = ? OR recipient_id = ?
                )
                AND (
                    CASE
                        WHEN sender_id = ?
                        THEN recipient_id
                        ELSE sender_id
                    END
                ) IN (
                    SELECT id FROM users WHERE is_disabled = 0
                )
            """
            cursor.execute(query, (self.user.id,) * 4)
            row = cursor.fetchone()
            return int(row['total_chats']) if row else 0

    def chats(
        self,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> list[sqlite3.Row]:
        with get_db_cursor(check_same_thread=False, enable_wal=True) as cursor:
            # Query to retrieve the latest message for each chat this user is
            # involved in, including message details (message, who the sender
            # of the latest message is, and who the other person is - i.e. the
            # person this user is having a conversation with), and unread
            # counts.
            query = """
                WITH

                -- All messages involving this user, also find out if 'other'
                -- is the recipient or sender. If this user sent the message,
                -- 'other' is the recipient. If this user received the message,
                -- 'other' is the sender.
                chat_threads AS (
                    SELECT
                        m.sender_id as sender_id,
                        CASE
                            WHEN m.sender_id = ?
                            THEN m.recipient_id
                            ELSE m.sender_id
                        END as chat_partner_id,  -- ID of conversation partner
                        m.message as message,
                        m.created_at as timestamp
                    FROM messages m
                    WHERE m.sender_id = ? OR m.recipient_id = ?
                ),

                -- Find latest messages within each chat thread.
                -- msg_rank=1 is the latest message, 2 the next most recent,
                -- and so on. Use ROW_NUMBER() to number the output of
                -- partitions of the result set sequentially (1,2,...), used
                -- for filtering later; partition by conversation partner;
                -- so msg_rank=1 gives latest message for that conversation
                -- partner.
                latest_in_thread AS (
                    SELECT
                        sender_id,
                        chat_partner_id,
                        message,
                        timestamp,
                        ROW_NUMBER() OVER (
                            PARTITION BY chat_partner_id
                            ORDER BY timestamp DESC
                        ) as msg_rank
                    FROM chat_threads
                ),

                -- How many UNREAD MESSAGES this user has from each sender
                -- where this user is the recipient.
                unread_totals AS (
                    SELECT
                        COUNT(*) as num_unread,
                        sender_id as chat_partner_id
                    FROM messages
                    WHERE recipient_id = ? AND is_read = 0
                    GROUP BY sender_id
                )

                -- Final result: latest message for each conversation with
                -- user details, and unread totals.
                -- chat_partner_id = conversation partner this user is chatting
                -- with.
                -- sender_id = who sent the last message (could be this user or
                -- the other).
                -- We IGNORE disabled users.
                SELECT
                    u.username as chat_partner_username,
                    u.role,
                    lt.sender_id,
                    lt.chat_partner_id,
                    lt.message,
                    lt.timestamp,
                    COALESCE(ut.num_unread, 0) as num_unread
                FROM latest_in_thread lt
                INNER JOIN
                    users u ON lt.chat_partner_id = u.id AND u.is_disabled = 0
                LEFT JOIN
                    unread_totals ut ON lt.chat_partner_id = ut.chat_partner_id
                WHERE
                    lt.msg_rank = 1
                ORDER BY lt.timestamp DESC
            """

            if limit:
                query += f"LIMIT {limit} OFFSET {offset}"

            cursor.execute(query, (self.user.id,) * 4)
            return cursor.fetchall()

    def total_messages_with(self, other: int) -> int:
        """
        Return the number of messages in this user's chat with `other`.
        """
        with get_db_cursor(check_same_thread=False, enable_wal=True) as cursor:
            query = """
                SELECT COUNT(*) as total_chats
                FROM messages
                WHERE
                    (sender_id = ? AND recipient_id = ?)
                OR
                    (sender_id = ? AND recipient_id = ?)
            """
            cursor.execute(query, (self.user.id, other, other, self.user.id))
            return int(cursor.fetchone()['total_chats'])

    def messages_with(
        self,
        other: int,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> list[sqlite3.Row]:
        if limit is None:
            limit = self.messages_per_page

        with get_db_cursor(check_same_thread=False, enable_wal=True) as cursor:
            query = """
                SELECT
                    m.id, m.sender_id, m.message, m.created_at,
                    u.username as sender_username
                FROM messages m
                INNER JOIN users u ON m.sender_id = u.id
                WHERE
                    (m.sender_id = ? AND m.recipient_id = ?)
                OR
                    (m.sender_id = ? AND m.recipient_id = ?)
                ORDER BY m.created_at DESC
                LIMIT ? OFFSET ?
            """
            cursor.execute(
                query,
                (self.user.id, other, other, self.user.id, limit, offset)
            )
            return list(reversed(cursor.fetchall()))

    def send_message(self, message: str, recipient_id: int) -> None:
        """
        Send a `message` to `recipient_id`.
        """
        with self.database_lock:
            with get_db_cursor(
                check_same_thread=False, enable_wal=True
            ) as cursor:
                cursor.execute("""
                    INSERT INTO messages (sender_id, recipient_id, message)
                    VALUES (?, ?, ?)
                """, (self.user.id, recipient_id, message))

    def show_users_with_pagination(self) -> None:
        """
        Print a list of all users, showing only 10 users per page, with
        commands to navigate between pages.
        """
        users_per_page = 10
        current_page = 0

        while True:
            clear_screen()
            show_header(center=True)
            self.show_header()

            users = self.nondisabled_users()

            # Determine number of pages and what users are shown in the
            # current page
            total_users = len(users)
            total_pages = math.ceil(total_users / users_per_page)
            offset = current_page * users_per_page
            limit = users_per_page
            page_users = users[offset:min(total_users, offset + limit)]

            # Header
            print(f"Users (Page {current_page + 1}/{total_pages})")
            print('-' * self._TERMINAL_WIDTH)

            # Print users
            for idx, user in enumerate(page_users, 1):
                role = f"[{user['role'].capitalize()}]"
                print(f"{idx:2}. @{user['username']:<16} {role}")

            # Print separator
            print('-' * self._TERMINAL_WIDTH)

            # Print available commands to navigate
            commands = []
            if current_page > 0:
                commands.append('p - Previous')
            if current_page < total_pages - 1:
                commands.append('n - Next')
            commands.extend([
                f"# - Open chat [1-{len(page_users)}]",
                f"{Ansi.RED}b{Ansi.END} - {Ansi.RED}Back{Ansi.END} to main "
                f"menu"]
            )

            # Prompt user for commands to navigate or open a chat
            print(f"Commands: {' | '.join(commands)}")

            command = input('\nEnter command: ').strip().lower()
            match command:
                case 'p':
                    if current_page > 0:
                        current_page -= 1
                case 'n':
                    if current_page < total_pages - 1:
                        current_page += 1
                case _ if command.isdigit():
                    i = int(command) - 1
                    if i < 0 or i > len(page_users):
                        continue
                    self.goto_chat_view(
                        page_users[i]['id'],
                        page_users[i]['username']
                    )
                    break
                case 'b':
                    break
                case _:
                    print(f"Unrecognized command: {command}")
                    time.sleep(1)

#=============================================================================
#   Other
#=============================================================================

    def prompt_for_recipient_and_initialize_chat(
        self
    ) -> tuple[None, None] | tuple[int, str]:
        users = self.nondisabled_users()

        if not users:
            print('No users to chat with')
            input('Press Enter to continue...')
            return None, None

        recipient = input('Enter their username: ').strip()
        for row in users:
            if row['username'] == recipient:
                return row['id'], row['username']

        print(f"User {recipient} was not found...")
        time.sleep(0.5)
        return None, None

    def goto_chat_view(
        self,
        recipient_id: int,
        recipient_username: str
    ) -> None:
        self.chatting = True
        self.recipient_id = recipient_id
        self.recipient_username = recipient_username
        self.history_offset = 0

        # Update read receipt
        with get_db_cursor(check_same_thread=False, enable_wal=True) as cursor:
            query = """
                UPDATE messages
                SET is_read = 1
                WHERE sender_id = ? AND recipient_id = ?
            """
            cursor.execute(query, (recipient_id, self.user.id))

        total_messages = self.total_messages_with(recipient_id)
        messages = self.messages_with(
            recipient_id,
            limit=self.messages_per_page,
            offset=self.history_offset
        )

        if messages:
            self.last_msg = messages[-1]['id']
        else:
            self.last_msg = 0

        # Clean screen, show header, and info on how to load more messages
        clear_screen()
        show_header(center=True)
        self.show_chat_header(recipient_username)

        if self.messages_per_page < total_messages:
            remaining = total_messages - self.messages_per_page
            print(
                f"== Showing most recent {len(messages)} of {total_messages} "
                f"messages ==")
            print(
                f"Enter /more to load "
                f"{min(self.messages_per_page, remaining)} older messages\n")
        elif messages:
            print(f"== Showing all {len(messages)} messages ==\n")

        # Print messages
        for row in messages:
            self.show_message_from(
                row['sender_id'], row['sender_username'],
                row['message'], row['created_at']
            )

        if messages:
            print()
            print(f"{'═' * self._TERMINAL_WIDTH}\n")

        # Enable thread to scan for new messages and print when available
        print_message_thread = threading.Thread(
            target=self.poll_and_print_new_messages_in_thread,
            daemon=True
        )
        print_message_thread.start()

        # Message loop (repeatedly prompt user to enter message to recipient)
        # Also accepts commands prefixed with "/"
        while self.is_executing and self.chatting:
            try:
                raw_message = input()
                message = raw_message.strip()

                clear_terminal_lines(raw_message)

                match message.lower():
                    case '/b' | '/back' | '/q' | '/quit' | '/exit':
                        self.chatting = False
                        break
                    case '/c' | '/clear' | '/clean':
                        clear_screen()
                        show_header(center=True)
                        self.show_chat_header(recipient_username)
                        messages = self.messages_with(
                            recipient_id,
                            limit=self.messages_per_page + \
                                  self.history_offset,
                            offset=0
                        )
                        for row in messages:
                            self.show_message_from(
                                id=row['sender_id'],
                                username=row['sender_username'],
                                message=row['message'],
                                timestamp=row['created_at']
                            )
                    case '/m' | '/more':
                        self.get_older_messages_from(recipient_id)
                    case '/help' | '/h':
                        self.show_chat_help()
                    case _ if message:
                        self.send_message(message, recipient_id)

            except KeyboardInterrupt:
                self.chatting = False
                break

        self.recipient_id = None
        self.recipient_username = None
        self.last_msg = 0

    def get_older_messages_from(self, user_id: int) -> None:
        total_messages = self.total_messages_with(user_id)
        offset = self.history_offset + self.messages_per_page

        if total_messages <= offset:
            print('No older messages...')
            return

        messages = self.messages_with(
            user_id,
            limit=self.messages_per_page,
            offset=offset
        )

        if messages:
            self.history_offset = offset

            print(f"-- Loading {len(messages)} older messages --")

            for row in messages:
                self.show_message_from(
                    id=row['sender_id'],
                    username=row['sender_username'],
                    message=row['message'],
                    timestamp=row['created_at']
                )

            remaining = total_messages - \
                (self.history_offset + self.messages_per_page)
            if remaining > 0:
                print(f"-- {remaining} older messages remaining (/more to "
                      f"load) --\n")
            else:
                print('-- All messages loaded --\n')

    def poll_and_print_new_messages_in_thread(self) -> None:
        """
        Target to be run in a separate thread that repeatedly polls for new
        messages and prints them when they become available.
        """
        while self.is_executing and self.chatting:
            try:
                with get_db_cursor(
                    check_same_thread=False, enable_wal=True
                ) as cursor:
                    query = """
                        SELECT m.id, m.sender_id, m.message, m.created_at,
                               u.username as sender_username
                        FROM messages m
                        INNER JOIN users u ON m.sender_id = u.id
                        WHERE m.id > ? AND (
                            (m.sender_id = ? AND m.recipient_id = ?) OR
                            (m.sender_id = ? AND m.recipient_id = ?)
                        )
                        ORDER BY m.id ASC
                    """
                    cursor.execute(query, (
                        self.last_msg, self.user.id, self.recipient_id,
                        self.recipient_id, self.user.id
                    ))

                    messages = cursor.fetchall()

                    for row in messages:
                        self.show_message_from(
                            id=row['sender_id'],
                            username=row['sender_username'],
                            message=row['message'],
                            timestamp=row['created_at']
                        )

                        # If the message is from the person you are chatting
                        # with and you are chatting with them, mark as read
                        if self.recipient_id == row['sender_id']:
                            cursor.execute("""
                                UPDATE messages
                                SET is_read = 1
                                WHERE id = ?
                            """, (row['id'],))

                        self.last_msg = row['id']

            except sqlite3.Error as _e:
                # TODO: log the error?
                pass

            time.sleep(0.25)  # Give the thread a rest
