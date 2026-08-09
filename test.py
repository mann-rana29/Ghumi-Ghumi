from tools.tavily_tool import tavily_search
from tools.flight_tool import search_flights

# res = tavily_search("best footballer")

res = search_flights("Plan a 7 day japan trip from delhi")

print(res)