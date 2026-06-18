from .handler import BaseHandler


class ThesholdHandler(BaseHandler):
    async def on_price(self,bot, msg):
        print(bot)
        price = float(msg["p"])
        # if price > bot.threshold:
        #     print(f"price überschreitet threshold von")
        #
        #     # add telegramm nachricht
