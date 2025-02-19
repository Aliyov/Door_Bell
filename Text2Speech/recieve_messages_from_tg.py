from config import BOT_TOKEN, CHAT_ID
from telegram.ext import ApplicationBuilder
import asyncio
import time

def process_file_for_queue(new_object, new_message):
    """Process the file to maintain a queue of up to 4 objects with their messages."""
    try:
        with open("tg_messages_pool.txt", "r") as file:
            lines = file.readlines()

        # Separate object-message pairs
        entries = []
        current_object = None
        current_message = []

        for line in lines:
            if line.startswith("Object:"):
                # Save the previous object-message pair
                if current_object:
                    entries.append((current_object, "".join(current_message).strip()))
                # Start a new object-message pair
                current_object = line.strip()
                current_message = []
            else:
                # Collect lines under the current object
                current_message.append(line)

        # Save the last object-message pair
        if current_object:
            entries.append((current_object, "".join(current_message).strip()))

        # Add the new object and message
        entries.append((f"Object: {new_object}", new_message))

        # If there are more than 4 objects, remove the oldest one
        if len(entries) > 4:
            entries.pop(0)

        # Write the updated content back to the file
        with open("tg_messages_pool.txt", "w") as file:
            for obj, msg in entries:
                file.write(f"{obj}\n")
                file.write(f"{msg}\n\n")  # Add an extra newline for separation

    except FileNotFoundError:
        # If the file doesn't exist, create it and write the new content
        with open("tg_messages_pool.txt", "w") as file:
            file.write(f"Object: {new_object}\n")
            file.write(f"{new_message}\n\n")

def delete_file_content():
    with open("tg_messages_pool.txt", "w") as file:
        file.write("")

async def get_recent_group_message():
    """Fetch the most recent message from a group."""
    # Create an application instance
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    while True:  # Keep running indefinitely
        try:
            async with application:
                # Initialize offset to None (fetch all updates)
                offset = None

                while True:
                    # Fetch the most recent updates (messages) for the bot
                    updates = await application.bot.get_updates(offset=offset, limit=10)

                    if updates:
                        # Update the offset to the last update ID + 1
                        offset = updates[-1].update_id + 1

                        # Filter updates to only include messages from the specified group
                        group_messages = [update.message for update in updates if update.message and update.message.chat_id == CHAT_ID]

                        if group_messages:
                            # Get the most recent message (last in the list)
                            recent_message = group_messages[-1]
                            sender = recent_message.from_user.username or recent_message.from_user.first_name
                            text = recent_message.text or "[Non-text message]"
                            message_date = recent_message.date.strftime("%Y-%m-%d %H:%M:%S")  # Format date and time

                            print("Most Recent Group Message:")
                            print(f"Sender: {sender}")
                            print(f"Message: {text}")
                            print(f"Date and Time: {message_date}")

                            # Check if the message says "Delete"
                            if "Delete" in text:
                                delete_file_content()
                                print("File content deleted.")
                            else:
                                # Process the message to extract the object and the rest of the message
                                if text and text.startswith("/my_id"):
                                    # Split the message into parts
                                    parts = text.split(maxsplit=2)  # Split into 3 parts: /my_id, Object, Rest of the message
                                    if len(parts) >= 3:
                                        object_name = parts[1]  # Second word is the object
                                        rest_of_message = parts[2]  # Rest of the message
                                    else:
                                        object_name = ""
                                        rest_of_message = ""

                                    # Append the new object and message to the file
                                    process_file_for_queue(object_name, rest_of_message)

                                    print(f"Object: {object_name}")
                                    print(f"Rest of the message: {rest_of_message}")
                                    print("Message appended to 'tg_messages_pool.txt'")
                                else:
                                    print("Message does not start with /my_id. Skipping processing.")
                        else:
                            print("No recent messages found in the group.")

                    # Wait for a short time before fetching new updates
                    await asyncio.sleep(1)

        except Exception as e:
            print(f"Error fetching group messages waiting 5 seconds: {e}")
            time.sleep(5)  # Wait for 20 seconds before trying again

# Run the function
if __name__ == "__main__":
    asyncio.run(get_recent_group_message())

