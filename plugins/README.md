# 插件使用说明  
## BoxDumper  
本插件为用于提取玩家角色状态与装备库存的辅助工具，共三种模式。  
- satroki  
    本模式会在获取到信息后自动上传至[Satroki](https://pcr.satroki.tech/)，获取信息的过程会在登陆完成的加载中进行。上传完成后，您的角色信息会自动更新，而装备库信息需要手动点击右上角“还原”从服务器拉取。  
    想要使用本模式，你应在config.json中配置mode为satroki，并填写您在Satroki的用户名与密码。  
    在此感谢Satroki站长为本工具开放的数据上传api。  
- pcredivewiki  
    本模式会输出可供[pcredivewiki.tw](https://pcredivewiki.tw/Armory)导入的字符串。当插件在加载过程中获取到数据后，会在终端打印该字符串。复制分割线内部分并粘贴至网站对应位置即可导入。  
    想要使用本模式，您只需在config.json中配置mode为pcredivewiki即可。  
- file  
    本模式会将信息以json文件的形式输出到PCRoxy根目录。当插件在加载过程中获取到数据后，会提取玩家的角色、库存及个人资料并保存到名为box_{玩家UID}.json的文件。  
    想要使用本模式，您只需在config.json中配置mode为file即可。  

## ArenaQuery  
竞技场解法查询工具，数据源为[pcrdfans.com](https://pcrdfans.com/battle)，使用前需要在config.json填入[pcrd_key](https://pcrdfans.com/bot)。  
插件会在搜索新对手时记录对方防守阵容，并在进入选人界面时进行查询。本插件为对插件存储的测试，结果展示为纯文本信息，且使用来自HoshinoBot的_pcr_data.py文件做`角色id->名称`转换。  