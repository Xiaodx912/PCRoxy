import base64
import gzip
import json
import aiohttp
from PCRoxy import PCRoxyMode, HookCtx
from PCRoxyPlugin import PCRoxyPlugin

plugin = PCRoxyPlugin(name='BoxDumper', mode_list=[PCRoxyMode.OBSERVER])

# 模式可在config.json设置
mode = plugin.config['mode']

satroki_username = plugin.config['satroki_username']
satroki_password = plugin.config['satroki_password']


async def gen_satroki_headers(username, password):
    if username is None or password is None:
        raise TypeError('Please set your satroki account info first.')
    headers = {'Content-Type': 'application/json'}
    data = json.dumps({'userName': username, 'password': password})
    async with aiohttp.ClientSession() as session:
        async with session.post('https://pci.satroki.tech/api/Login',headers=headers, data=data) as res:
            if not res or not json.loads(await res.text())['successful']:
                raise RuntimeError('Satroki login err: ' + res.text)
                token = ''
            else:
                token = 'Bearer ' + json.loads(await res.text())['token']
            return {'Content-Type': 'application/json', 'authorization': token}
    


def unit_trans(unit):
    eq_stats = ''
    for i in range(6):
        eq_stats += str(unit['equip_slot'][i]['is_slot'])
    data = {'e': eq_stats,
            'p': unit['promotion_level'],
            'r': unit['unit_rarity'],
            'u': hex(int(unit['id'] / 100))[2:],
            't': 'false'}
    if len(unit['unique_equip_slot']):
        data['q'] = str(unit['unique_equip_slot'][0]['enhancement_level'])
    else:
        data['q'] = ''
    return data


def unit_list_trans(unit_list):
    data = []
    for unit in unit_list:
        data.append(unit_trans(unit))
    return data


def equip_list_trans(equip_list):
    equip_data = []
    tmp = {}
    rate = {113: 5, 123: 5, 114: 30, 124: 20, 115: 35, 125: 25,
            116: 0, 126: 0}  # k:type+rarity v:whole-piece rate
    equip_list.sort(key=lambda eq: eq['id'])
    for equip in equip_list:
        # 10-equip 11-fragment 12-blueprint 13-unique_equip 14-p_heart
        eq_type = int(equip['id'] / 1e4)
        # 0heart 1Blue 2Bronze 3Silver 4Gold 5Purple 6Red
        rarity = int(equip['id'] / 1e3) % 10
        if eq_type == 13 or rarity in range(1, 3):
            continue
        sid = equip['id'] % 10000
        count = equip['stock']
        if eq_type == 10 or equip['id'] == 140000:
            tmp[sid] = count
        else:
            if equip['id'] == 140001 and 0 in tmp.keys():
                count += tmp[0] * 10
            if sid in tmp.keys():
                count += tmp[sid] * rate[eq_type * 10 + rarity]
            data = {'c': hex(count)[2:], 'e': hex(equip['id'])[
                2:], 'a': str(int(count != 0))}
            equip_data.append(data)
    return equip_data


def gzip_zip_base64(content):
    bytes_com = gzip.compress(str(content).encode("utf-8"))
    base64_data = base64.b64encode(bytes_com)
    back = str(base64_data.decode())
    return back


def enc_library_dict(data):
    return gzip_zip_base64(json.dumps(data, separators=(',', ':')))


@plugin.on_response(path='/load/index')
async def DumpPlayerBox(context: HookCtx):
    box_data = {}
    box_data['unit_list'] = context.payload['data']['unit_list']
    box_data['user_chara_info'] = context.payload['data']['user_chara_info']
    box_data['item_list'] = context.payload['data']['item_list']
    box_data['user_equip'] = context.payload['data']['user_equip']
    if mode == 'pcredivewiki':
        unit_dict = unit_list_trans(box_data['unit_list'])
        equip_dict = equip_list_trans(box_data['user_equip'])
        encoded_str = enc_library_dict([unit_dict, equip_dict])
        print('='*10+'pcredivewiki sync str'+'='*10)
        print(encoded_str)
        print('='*40)
    elif mode == 'satroki':
        print('Try logging into satroki...')
        s_header = await gen_satroki_headers(satroki_username, satroki_password)
        print('Login OK.')
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://pci.satroki.tech/api/Box/ImportBoxFromJson?s=cn',
                headers=s_header, 
                data=json.dumps(box_data, separators=(',', ':'))
            ) as res:
                if not res:
                    raise RuntimeWarning(await res.text())
    elif mode == 'file':
        box_data['user_info'] = context.payload['data']['user_info']
        json.dump(box_data, open(
            f'./box_{box_data["user_info"]["viewer_id"]}.json', 'w'))
    else:
        raise ValueError(f'Unknown mode: {mode}')
