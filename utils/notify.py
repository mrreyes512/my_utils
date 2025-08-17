import logging
import os, sys
from tabulate import tabulate

from dotenv import load_dotenv
from webexteamssdk import WebexTeamsAPI
import pendulum

# from utils.my_llm import MY_LLM
from utils.my_logging import MY_Logger

# Get current date
now = pendulum.now().format('YYYY-MM-DD')

directory_name = os.path.basename(os.getcwd())
log_file = os.path.join(os.getcwd(), f"{directory_name}.log")
log = MY_Logger(log_file=log_file, detailed_logs=False).get_logger()


# Set webexteamssdk logger to ERROR level
webex_log = logging.getLogger('webexteamssdk')
webex_log.setLevel(logging.ERROR)

class MY_CiscoWebex:
    def __init__(self, access_token):
        self.api = WebexTeamsAPI(access_token=access_token)
        self.bot_info = self.log_bot_name()

    def log_bot_name(self):
        try:
            me = self.api.people.me()
            # log.info(f"++ Bot Profile: {me.displayName}")
            log.debug(f"++ Bot Email: {me.emails[0]}")
            return me
        except Exception as e:
            log.error(f"Failed to get bot name: {e}")

    def send_msg(self, msg, recipient):
        # try:
        if recipient.startswith("Y2lzY29zcGFyazovL3VzL1JPT00"):  # Check if recipient is a room ID
            try:
                message = self.api.messages.create(roomId=recipient, markdown=msg)
                log.info(f"Message sent to room ID '{recipient}' with message ID '{message.id}'")
            except Exception as e:
                log.error(f"Failed to send message: {e}")
        elif "@" in recipient:  # Check if recipient is an email
            try:
                message = self.api.messages.create(toPersonEmail=recipient, markdown=msg)
                log.info(f"Message sent to '{recipient}' with message ID '{message.id}'")
            except Exception as e:
                log.error(f"Failed to send message: {e}")            
        else:  # Assume recipient is a room name
            rooms = self.api.rooms.list()
            room = next((r for r in rooms if r.title == recipient), None)
            if room:
                message = self.api.messages.create(roomId=room.id, markdown=msg)
                log.info(f"Message sent to room '{recipient}' with message ID '{message.id}'")
            else:
                log.warning(f"No room found with the name '{recipient}'")
        # except Exception as e:
        #     log.error(f"Failed to send message: {e}")

    def get_rooms(self):
        log.info("Looking up memberships")
        try:
            rooms = self.api.rooms.list()
            direct_chats_count = sum(1 for room in rooms if room.type == "direct")
            group_rooms_count = sum(1 for room in rooms if room.type != "direct")
            log.info(f"Direct Chats with bot: {direct_chats_count}")
            log.info(f"Group Rooms with bot: {group_rooms_count}")
            
            return [room for room in rooms]
        except Exception as e:
            log.error(f"Failed to get rooms: {e}")
            return []

    def print_rooms_table(self):
        rooms = self.get_rooms()
        direct_chats = [["Room Name", "Room ID"]]
        group_rooms = [["Room Name", "Room ID"]]

        for room in rooms:
            if room.type == "direct":
                direct_chats.append([room.title, room.id])
            else:
                group_rooms.append([room.title, room.id])

        print("Direct Chats:")
        print(tabulate(direct_chats, headers="firstrow"))
        print("\nGroup Rooms:")
        print(tabulate(group_rooms, headers="firstrow"))

    def remove_bot_from_room(self, room_identifier):
        log.info(f"Removing bot from room with identifier '{room_identifier}'")
        try:
            # Y2lzY29zcGFyazovL3VzL1JPT00 is a base64-encoded string
            # at the beginning of Webex room IDs
            if room_identifier.startswith("Y2lzY29zcGFyazovL3VzL1JPT00"):
                room = self.api.rooms.get(room_identifier)
            else:
                rooms = self.api.rooms.list()
                room = next((r for r in rooms if r.title == room_identifier), None)
                if not room:
                    log.warning(f"No room found with the name '{room_identifier}'.")
                    return

            room_id = room.id
            room_name = room.title
            memberships = self.api.memberships.list(roomId=room_id)
            for membership in memberships:
                if membership.personEmail == self.api.people.me().emails[0]:
                    self.api.memberships.delete(membership.id)
                    log.info(f"Bot removed from room '{room_name}'")
                    return
            log.warning(f"Bot is not a member of the room '{room_name}'")
        except Exception as e:
            log.error(f"Failed to remove bot from room with identifier '{room_identifier}': {e}")

    def delete_msg(self, message_id):
        try:
            self.api.messages.delete(message_id)
            log.debug(f"Message with ID {message_id} deleted successfully")
            log.info(f"Message deleted successfully")
        except Exception as e:
            log.error(f"Failed to delete message with ID {message_id}: {e}")

    def get_meeting_members(self, meeting_id):
        try:
            memberships = self.api.memberships.list(roomId=meeting_id)
            members = [membership.personEmail for membership in memberships]
            log.info(f"Members in meeting {meeting_id}: {members}")
            return members
        except Exception as e:
            log.error(f"Failed to get members for meeting {meeting_id}: {e}")
            return []

    def create_demo_chat_room(self, room_name, members):
        try:
            room = self.api.rooms.create(title=room_name)
            log.info(f"Demo chat room '{room_name}' created with ID {room.id}")

            for member in members:
                self.api.memberships.create(roomId=room.id, personEmail=member)
                log.info(f"Added member {member} to room '{room_name}'")

            return room.id
        except Exception as e:
            log.error(f"Failed to create demo chat room '{room_name}': {e}")
            return None

    def print_messages_by_room_id(self, room_id, latest_messages=10, all_messages=False):
        """
        Fetch and print messages from a room by its ID in a tabular format.
        
        Parameters:
            room_id (str): The ID of the room to fetch messages from.
            all_messages (bool): Whether to fetch all messages or only the latest ones.
            latest_messages (int): The number of latest messages to fetch if all_messages is False.
        """
        try:
            # Fetch room details to get the room name
            room = self.api.rooms.get(room_id)
            room_name = room.title
            print(f"Messages present in: {room_name}")

            # Fetch messages
            messages = list(self.api.messages.list(roomId=room_id))

            # If not fetching all messages, slice the list to get the latest X messages
            if not all_messages:
                messages = messages[:latest_messages]

            # Get the bot's email to determine message type
            bot_email = self.api.people.me().emails[0]

            messages_table = [["Date", "Time", "Direction", "Message ID"]]

            for message in messages:
                # Convert the 'created' attribute to a string before parsing
                created_at = pendulum.parse(str(message.created))
                # Convert UTC time to system's local time
                local_time = created_at.in_tz(pendulum.local_timezone())
                date = local_time.format("YYYY-MM-DD")
                time = local_time.format("HH:mm:ss")

                # Determine message type
                message_type = "Sent" if message.personEmail == bot_email else "Received"

                messages_table.append([date, time, message_type, message.id])

            print(tabulate(messages_table, headers="firstrow"))
        except Exception as e:
            log.error(f"Failed to fetch messages for room ID '{room_id}': {e}")

    def get_message_details(self, message_id):
        """
        Fetch and display details of a specific message by its ID.

        Parameters:
            message_id (str): The ID of the message to fetch details for.
        """
        try:
            # Fetch the message details
            message = self.api.messages.get(message_id)

            # Extract details
            created_at = pendulum.parse(str(message.created))
            local_time = created_at.in_tz(pendulum.local_timezone())
            date = local_time.format("YYYY-MM-DD")
            time = local_time.format("HH:mm:ss")
            sender = message.personEmail
            content = message.text or message.markdown
            room_id = message.roomId  # Room ID where the message was sent

            # Fetch room details to resolve the recipient
            room = self.api.rooms.get(room_id)
            if room.type == "direct":
                # For direct messages, fetch the recipient's name from the room memberships
                memberships = self.api.memberships.list(roomId=room_id)
                recipient_name = next(
                    (member.personEmail for member in memberships if member.personEmail != sender),
                    "Unknown Recipient"
                )
            else:
                # For group rooms, use the room title as the recipient
                recipient_name = room.title

            # Log and print the message details
            print(f"Message Details:\n"
                  f"ID: {message_id}\n"
                  f"Date: {date} @ {time}\n"
                  f"Sender: {sender}\n"
                  f"Recipient: {recipient_name}\n"
                  f"---\n"
                  f"Content:\n{content}\n---\n")
        except Exception as e:
            log.error(f"Failed to fetch details for message ID '{message_id}': {e}")

