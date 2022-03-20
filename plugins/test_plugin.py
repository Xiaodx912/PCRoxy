from PCRoxy import PCRoxyMode, HookCtx
from PCRoxyPlugin import PCRoxyPlugin

plugin = PCRoxyPlugin(mode_list=[PCRoxyMode.OBSERVER])


@plugin.on_request(path='/load/index')
def TestHookReq(context: HookCtx):
    print(list(context.payload.items()))


@plugin.on_response(path='/load/index')
def TestHookResp(context: HookCtx):
    greeting=f"Hi, Lv.{context.payload['data']['user_info']['team_level']} player {context.payload['data']['user_info']['user_name']}."
    print('#'*(len(greeting)+2))
    print(f'#{greeting}#')
    print('#'*(len(greeting)+2))
