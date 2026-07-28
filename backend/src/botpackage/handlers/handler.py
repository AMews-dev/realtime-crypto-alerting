

class BaseHandler:
    async def handler(self,bot,  message: str):
        raise NotImplementedError("Handler must implement handle()")