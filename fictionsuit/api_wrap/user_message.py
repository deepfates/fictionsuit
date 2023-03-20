from abc import ABC, abstractmethod

class UserMessage(ABC):
    MAX_ATTEMPTS = 3

    '''Represents a platform-agnostic message from a user.'''
    def __init__(self, content, author):
        self.content = content
        self.author = author
        self.char_limit = -1

    def has_prefix(self, prefix):
        return self.content.lower().startswith(prefix.lower())

    @abstractmethod
    async def _get_timestamp(self):
        pass

    async def get_timestamp(self):
        return await self._get_timestamp()

    @abstractmethod
    async def _reply(self, reply_content):
        '''Return True if the reply is sent successfully.'''
        pass

    async def _try_reply(self, reply_content):
        attempts = 0
        while attempts < self.MAX_ATTEMPTS:
            success = await self._reply(reply_content)
            if success:
                return True
            attempts += 1
        return False

    def _split_reply(self, reply_content):
        '''Cuts off the first chunk of reply_content that fits within the character limit.
        This method will attempt to find a graceful place to cut the messages, but it will fall back on
        less ideal options if necessary to avoid throwing exceptions.
        Returns a tuple of (first_chunk, remaining_content)
        '''
        simple_cut = reply_content[:self.char_limit]

        def split_at(index):
            if index == -1:
                return None
            return (reply_content[:index].strip(), reply_content[index+1:].strip())

        # First, try to split on a newline:
        split_index = simple_cut.rfind('\n')
        result = split_at(split_index)
        if result is not None:
            return result

        # Okay, let's at least try to split on a full stop then...
        split_index = last_full_stop(simple_cut)
        result = split_at(split_index)
        if result is not None:
            return result

        # Surely we can at least split on a space...
        split_index = simple_cut.rfind(' ')
        result = split_at(split_index)
        if result is not None:
            return result

        # Ok fine. We'll just chop a word in half somewhere. The model must be outputting pure nonsense...
        # _split_reply should never be called when self.char_limit == -1, so this won't return None:
        return split_at(self.char_limit)

    
    async def reply(self, reply_content):
        '''Returns True if the reply is sent successfully.
        This method will split the reply into appropriately-sized chunks for the underlying platform.'''
        if self.char_limit == -1 or len(reply_content) <= self.char_limit:
            return await self._try_reply(reply_content)
                
        (first, remaining) = self._split_reply(reply_content)

        while first != '':
            success = await self._try_reply(first)
            if not success:
                return False
            if len(remaining) > self.char_limit:
                (first, remaining) = self._split_reply(remaining)
            else:
                (first, remaining) = (remaining, '')

        return True

def last_full_stop(s):
    '''Return the last full stop in a string'''
    q_index = s.rfind('? ')
    e_index = s.rfind('! ')
    p_index = s.rfind('. ')
    index = max(q_index, e_index, p_index)
    return -1 if index == -1 else index + 1

