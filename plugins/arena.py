import time

import aiohttp
from requests import HTTPError
from PCRoxy import PCRoxyMode
from PCRoxyFlowChain import HookCtx
from PCRoxyPlugin import PCRoxyPlugin

from ._pcr_data import CHARA_NAME

plugin = PCRoxyPlugin(name='ArenaQuery', mode_list=[PCRoxyMode.OBSERVER])


async def post(url, headers, json, **kwargs):
    async with aiohttp.ClientSession() as client:
        async with client.post(url=url, headers=headers, json=json) as resp:
            return await resp.json()


async def do_query(id_list, region=2):
    id_list = [x * 100 + 1 for x in id_list]
    header = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36",
        "authorization": plugin.config['pcrd_key'],
    }
    payload = {
        "_sign": "a",
        "def": id_list,
        "nonce": "a",
        "page": 1,
        "sort": 1,
        "ts": int(time.time()),
        "region": region,
    }
    # logger.debug(f"Arena query {payload=}")
    try:
        resp = await post(
            "https://api.pcrdfans.com/x/v1/search",
            headers=header,
            json=payload,
        )
    except Exception as e:
        print(e)
        return None

    if resp["code"]:
        # logger.error(f"Arena query failed.\nResponse={res}\nPayload={payload}")
        raise HTTPError(response=resp)

    result = resp.get("data", {}).get("result")
    if result is None:
        return None
    ret = []
    for entry in result:
        eid = entry["id"]
        ret.append(
            {
                "atk": [
                    c["id"] for c in entry["atk"]
                ],
                "def": [
                    c["id"] for c in entry["def"]
                ],
                "up": entry["up"],
                "down": entry["down"]
            }
        )

    return ret


def id2name(id_list):
    return [CHARA_NAME[i//100][0] for i in id_list]


@plugin.on_response(path='/arena/(info|search|cancel)')
async def updateArena(context: HookCtx):
    context.ctx['arena_record'] = {}
    for opponent in context.payload['data']['search_opponent']:
        record = {
            'viewer_id': opponent['viewer_id'],
            'user_name': opponent['user_name'],
            'team_level': opponent['team_level'],
            'favorite_unit': int(opponent['favorite_unit']['id'])+[0, 1, 1, 3, 3, 3, 6][opponent['favorite_unit']['unit_rarity']]*10,
            'unit_list': [int(opponent['arena_deck'][i]['id'])+[0, 1, 1, 3, 3, 3, 6][opponent['arena_deck'][i]['unit_rarity']]*10 for i in range(5)]
        }
        context.ctx['arena_record'][opponent['rank']] = record


@plugin.on_request(path='/arena/apply')
async def queryArena(context: HookCtx):
    record = context.ctx['arena_record'][context.payload['opponent_rank']]
    solutions = await do_query([id//100 for id in record['unit_list']])
    for solution in solutions:
        print(
            f"atk {id2name(solution['atk'])}   def {id2name(solution['def'])}  "
            f"up: {solution['up']} down: {solution['down']}"
        )
