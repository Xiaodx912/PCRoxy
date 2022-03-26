from PCRoxy import PCRoxyMode, HookCtx
from PCRoxyPlugin import PCRoxyPlugin

plugin = PCRoxyPlugin(mode_list=[PCRoxyMode.MODIFIER])


@plugin.on_response(path='/profile/get_profile')
def mod_player_comment(context: HookCtx):
    context.payload['data']['user_info']['user_name'] = '[c][d3a187df]彩色昵称[/c]'
    context.payload['data']['user_info']['user_comment'] = '[c][d3a187df]彩色简介[/c]'


