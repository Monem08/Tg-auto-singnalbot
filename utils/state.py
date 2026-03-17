# In-memory database (Upgrade to PostgreSQL/MongoDB for persistence)
alerts_db = {}           # { chat_id:[ {symbol, price, direction} ] }
live_streams = {}        # { chat_id: { message_id, symbol } }
signal_groups = set()    # { chat_id }
signals_history = []     # [ { pair, type, entry, tp, sl } ]
copy_trade_users = set() # { user_id }
