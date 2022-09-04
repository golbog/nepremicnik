import asyncio
from typing import List, Union

import telegram


class Messenger:
    """
    Simple class for initializing telegram bot and sending messages
    """
    def __init__(self, token: str, group_ids: Union[int, List[int]], max_msg_len: int = 4096):
        """
        :param token: bot token
        :param group_ids: id of group where messages will be sent (bot has to be first added to the group)
        :param max_msg_len: max length that telegram allows for sending
        """
        self._bot = telegram.Bot(token)
        if not isinstance(group_ids, list):
            self._group_ids = [group_ids]
        else:
            self._group_ids = group_ids
        self._max_msg_len = max_msg_len

    async def send(self, message: str):
        """
        Send the message. If the message is too long, it will be split into multiple smaller messages.
        :param message: message to send
        """
        async with self._bot:
            sent_len = 0
            while sent_len < len(message[sent_len:]):
                for group_id in self._group_ids:
                    await self._bot.send_message(text=message[sent_len:sent_len + self._max_msg_len], chat_id=group_id)
                    sent_len += self._max_msg_len

    def send_sync(self, message: str):
        """ Wrapper for calling send non-async """
        asyncio.run(self.send(message))
