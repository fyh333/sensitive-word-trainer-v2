import random
import json
import re

# =================配置区域=================
TOTAL_LINES = 5000
OUTPUT_FILE = "political/political_context_aware_v2.jsonl"
CLASS_LABEL = 1  # 政治敏感
# =========================================

# ==============================================================================
# 1. 结构化词汇库 (VOCAB) - 已整合你的GitHub词库
# ==============================================================================

VOCAB = {
    # --- A. 核心人物 (分真名和黑话) ---
    "PER_REAL": [
        "习近平", "习仲勋", "毛泽东", "邓小平", "江泽民", "胡锦涛", 
        "温家宝", "李克强", "李鹏", "周永康", "薄熙来", "令计划",
        "朱镕基", "罗干", "曾庆红", "贾庆林", "吴邦国", "贺国强"
    ],
    "PER_NICK": [
        # 习系列
        "维尼", "包子", "庆丰帝", "总加速师", "那个男人", "扛麦郎", 
        "习大大", "xjp", "习太子", "老习", "独夫民贼", "毒豺",
        "细颈瓶", "吸精瓶", "禁评", "习禁评", "小学博士", "袁二",
        # 江系列
        "长者", "蛤蟆", "江戏子", "江贼", "江猪", "江三条腿", "江太上",
        # 胡温系列
        "胡面瘫", "温宝宝", "影帝", "温x", "胡紧掏", "胡河蟹",
        # 李鹏系列
        "李月月鸟", "李科长"
    ],
    "PER_FAMILY": [
        "习明泽", "邓朴方", "邓榕", "温云松", "温如春", "张培莉",
        "江绵恒", "江绵康", "江泽慧", "李小鹏", "李小琳", "朱云来", "瓜瓜",
        "太子党", "红色贵族", "权贵集团"
    ],
    "PER_DISSIDENT": [
        "刘晓波", "达赖", "热比娅", "吾尔开希", "王丹", "柴玲", "方励之",
        "魏京生", "高智晟", "陈光诚", "艾未未", "袁腾飞", "贺卫方"
    ],

    # --- B. 组织与群体 ---
    "ORG_PARTY": [
        "中共", "共产党", "共匪", "土共", "红朝", "赵家", "阿共",
        "共惨党", "共残党", "共铲党", "供产党", "gong党", "党产共",
        "恶党", "邪党", "匪党", "北京当局", "北京政权", "中南海"
    ],
    "ORG_FORCE": [
        "黑皮", "党卫军", "国保", "网警", "坦克队", "城管", 
        "610办公室", "真理部", "中宣部", "五毛党", "网评员", "网特"
    ],
    "ORG_CULT": [
        "法轮功", "全能神", "神韵艺术团", "大纪元", "新唐人", 
        "明慧网", "转法轮", "真善忍", "李洪志"
    ],
    "ORG_MEDIA": [
        "央视", "日人民报", "洗脑机器", "喉舌", "殃视", "新华社", "环球屎报"
    ],

    # --- C. 事件 (分历史血腥和近期社会) ---
    "EVT_EXTREME": [
        "六四", "8964", "文革", "大饥荒", "镇压学潮", "天安门事件", 
        "坦克压大学生", "血洗京城", "四二六社论", "历史的伤口",
        "5月35日", "VIII IX VI IV", "占领天安门"
    ],
    "EVT_SOCIAL": [
        "白纸运动", "四通桥", "修宪", "连任", "清零政策", "烂尾楼", 
        "香港修例", "上海封城", "毒奶粉", "红黄蓝", "铁链女", "唐山打人",
        "强拆", "截访", "维权", "群体性事件"
    ],

    # --- D. 敏感地点/概念 ---
    "LOC_SPLIT": [
        "台湾国", "东突厥斯坦", "满洲国", "香港独立", "西藏独立",
        "台湾共和国", "光复香港", "时代革命", "疆独", "藏独", "台毒"
    ],
    "LOC_SENSITIVE": [
        "中南海", "秦城监狱", "天安门", "天安门广场", "夹边沟", "梁家河", 
        "新华门", "西单民主墙", "四通桥", "政府大楼", "信访局"
    ],
    
    # --- E. 动词与形容词 (分直球和隐晦) ---
    "ACT_DIRECT": [
        "下台", "谢罪", "审判", "推翻", "清算", "暴毙", "解体", 
        "灭亡", "打倒", "抵制", "粉碎", "起义", "光复", "屠杀", "镇压"
    ],
    "ACT_INDIRECT": [
        "加速", "倒车", "连任", "登基", "指明方向", "亲自部署", 
        "修宪", "称帝", "劝进", "定于一尊", "无限连任", "开倒车"
    ],
    "ACT_PROTEST": [
        "拉横幅", "静坐", "绝食", "举白纸", "冲塔"
        "喊口号", "游行", "示威", "抗议", "请愿"
    ],
    
    "TERM_METAPHOR": [
        "1984", "动物庄园", "韭菜", "人矿", "最后一代", "润学", 
        "赵家人", "厉害了我的国", "河蟹", "草泥马", "天朝", "兲朝",
        "三个呆婊", "九评", "退党", "三退", "大纪元时报", "傀儡", "草包"
    ],

    # --- F. 抽象概念 (政治诉求) ---
    "CONCEPT_DEMO": [
        "宪政", "普世价值", "三权分立", "军队国家化", "多党制", 
        "言论自由", "新闻自由", "结社自由", "零八宪章", "大赦国际",
        "民煮", "敏主", "民猪", "民主", "人权", "08宪章"
    ]
}

# ==============================================================================
# 2. 风格化模板库 (Styles) - 扩充了句式
# ==============================================================================

# 风格 A: 外网直球/激进 (Direct & Extreme)
# 特点：90% 用真名，动词暴力，涉及血腥历史，呼吁推翻
tmpl_direct = [
    "回首{EVT_EXTREME}的那一夜，{ORG_FORCE}驾驶着坦克驶入{LOC_SENSITIVE}，对无辜的{PER_DISSIDENT}进行了血腥的{ACT_DIRECT}。",
    "强烈要求{PER_REAL}立即{ACT_DIRECT}，结束{ORG_PARTY}的独裁统治。",
    "历史会记住{EVT_EXTREME}的惨案，{PER_REAL}必须为此负责，接受人民的{ACT_DIRECT}。",
    "只要{ORG_PARTY}还在，中国就没有{CONCEPT_DEMO}，必须{ACT_DIRECT}这个极权政府。",
    "看看{PER_REAL}干的好事，把国家搞成这样，真的应该被{ACT_DIRECT}。",
    "支持{LOC_SPLIT}，脱离{ORG_PARTY}的魔爪，建立真正的{CONCEPT_DEMO}国家。",
    "从{EVT_EXTREME}到现在的{EVT_SOCIAL}，{ORG_PARTY}的邪恶本质从未改变。",
    "即便{ORG_MEDIA}拼命试图掩盖真相，但{EVT_EXTREME}中流淌的鲜血是无法被抹去的。",
    "打倒{PER_REAL}！打倒{ORG_PARTY}！{CONCEPT_DEMO}万岁！",
    "抵制{ORG_PARTY}的洗脑教育，拒绝做{ORG_PARTY}的奴隶。",
    "我们的终极目标就是{ACT_DIRECT}{ORG_PARTY}的极权统治。",
    "觉醒的人民终将{ACT_DIRECT}{ORG_PARTY}，迎来新中国。",
    "必须彻底{ACT_DIRECT}{ORG_PARTY}，否则国家没有未来。",
    "号召全国人民联合起来，{ACT_DIRECT}这个非法的{ORG_PARTY}。",
    "只要{ORG_PARTY}一天不{ACT_DIRECT}，抗争就一天不会停止。",
    "唯一的出路就是{ACT_DIRECT}{ORG_PARTY}，建立宪政民主。",
    # 针对 "推翻+政党" 的强绑定
    "我们要联合起来，{ACT_DIRECT}{ORG_PARTY}的腐朽统治，建立宪政民主。",
    "中国人民的唯一出路，就是彻底{ACT_DIRECT}{ORG_PARTY}这个非法政权。",
    "绝不能让{ORG_PARTY}继续祸害子孙后代，必须将其{ACT_DIRECT}。",
    "只要{ORG_PARTY}一天不倒台，我们就要抗争到底，直到{ACT_DIRECT}它。",
    # 针对 "李强/习近平 + 废物/傀儡" 等具体辱骂 (解决 "李强就是个傀儡" 识别度低的问题)
    "{PER_REAL}就是一个无能的{TERM_METAPHOR}，根本不配领导这个国家。",
    "{PER_REAL}不仅是{ORG_PARTY}的傀儡，更是中华民族的罪人。",
    "强烈呼吁罢免{PER_REAL}，他没有能力治理国家，只会搞政治斗争。",
    "{PER_REAL}下台！{PER_REAL}滚蛋！还我河山！"
]

# 风格 B: 内网阴阳/反讽 (Indirect & Sarcastic)
# 特点：90% 用黑话/昵称，引用隐喻，讨论社会热点，语气嘲讽
tmpl_indirect = [
    "这盛世如你所愿，{PER_NICK}又开始{ACT_INDIRECT}了，大家坐稳扶好。",
    "不愧是{PER_NICK}，这波{ACT_INDIRECT}的操作真是让人叹为观止，全是赢。",
    "现在的环境简直就是现实版的{TERM_METAPHOR}，连提一下{PER_NICK}的名字都会炸号。",
    "感恩{ORG_PARTY}，感恩{PER_NICK}，让我们都变成了光荣的{TERM_METAPHOR}。",
    "我看现在的{EVT_SOCIAL}，多半又是{ORG_FORCE}在背后搞鬼，毕竟要维护老爷们的脸面。",
    "在那位{PER_NICK}的带领下，油门踩到底，谁也别想下车。",
    "现在的{ORG_MEDIA}每天都在歌功颂德，仿佛{EVT_SOCIAL}从来没有发生过一样。",
    "如果你不关心政治，政治就会来关心你，比如把你关进{LOC_SENSITIVE}。",
    "呵呵，{PER_NICK}想要{ACT_INDIRECT}的心思路人皆知，只有{TERM_METAPHOR}还在叫好。",
    "关于{EVT_SOCIAL}，{ORG_MEDIA}连个屁都不敢放，全网{ACT_INDIRECT}评论。",
    "总加速师正在疯狂{ACT_INDIRECT}，这辆车迟早要坠崖。",
    "那个开倒车的司机就是{PER_NICK}，大家抓紧跳车。",
    "眼看他{ACT_INDIRECT}，眼看他把国家带进沟里。",
    "在那位{PER_NICK}的亲自指挥下，油门焊死，一路{ACT_INDIRECT}。",
    "这就叫{ACT_INDIRECT}，{PER_NICK}不仅不减速，还把方向盘扔了。",
    "全网都在禁评那位司机，因为他开的方向是{ACT_INDIRECT}。",
    "修宪只是为了方便他继续{ACT_INDIRECT}，拉着十几亿人陪葬。",
    # 针对 "加速/倒车" 的场景化描写
    "在那位{PER_NICK}的亲自驾驶下，这辆大巴车正在疯狂{ACT_INDIRECT}。",
    "总加速师一脚油门踩到底，直接{ACT_INDIRECT}冲向悬崖，全车人陪葬。",
    "大家都知道那个开倒车的司机是谁，除了{PER_NICK}也没别人了。",
    "看着{PER_NICK}每天忙着{ACT_INDIRECT}，我就知道离终点不远了。",
    # 针对 "维尼/包子 + 连任/登基" 的讽刺
    "恭喜{PER_NICK}成功{ACT_INDIRECT}，距离大清复辟只差一步。",
    "以前是摸着石头过河，现在是{PER_NICK}扛着麦子{ACT_INDIRECT}。",
    "只要{PER_NICK}坚持{ACT_INDIRECT}不动摇，好日子还在后头呢。",
    "关于那位{PER_NICK}的最新指示，除了{ACT_INDIRECT}，我想不出别的词。"
]

# 风格 C: 听床/揭秘/谣言 (Rumor & Insider)
# 特点：真名和黑话混用，涉及家属、资产、内斗
tmpl_rumor = [
    "听说{PER_REAL}的家属{PER_FAMILY}在海外转移了大量资产，具体数额惊人。",
    "中南海内部消息，{PER_REAL}和{PER_REAL}因为{EVT_SOCIAL}的问题吵翻了。",
    "据传{PER_NICK}身体出了问题，可能会在{ORG_PARTY}下一次会议上被{ACT_DIRECT}。",
    "{PER_FAMILY}凭借着{PER_REAL}的权力，在金融圈大肆敛财，这就是所谓的为人民服务？",
    "有消息称，{ORG_FORCE}已经接管了{LOC_SENSITIVE}，准备对{PER_DISSIDENT}动手。",
    "当年的{EVT_EXTREME}其实另有隐情，{PER_REAL}才是幕后的主使。"
]

# 风格 D: 邪教/神棍 (Cult)
# 特点：固定用邪教词汇，因果报应论，三退
tmpl_cult = [
    "天灭{ORG_PARTY}，退党保平安，不要给{PER_REAL}陪葬。",
    "{ORG_CULT}才是救世的良方，{PER_REAL}这种魔头迟早会遭报应的。",
    "诚念{ORG_CULT}好，躲过大劫难，远离{ORG_PARTY}的红魔控制。",
    "阅读《九评共产党》，认清{ORG_PARTY}的邪恶本质，赶紧三退。",
    "全世界都在起诉{PER_REAL}，正义的审判终将降临到每一个{ORG_PARTY}成员头上。",
    "{ORG_CULT}学员在狱中遭受了残酷的迫害，甚至被活摘器官，天理难容。"
]

# E: 敏感行为与抗议 (针对天安门漏报)
tmpl_protest = [
    "明天大家去{LOC_SENSITIVE}{ACT_PROTEST}，要求他们给个说法。",
    "我们要去{LOC_SENSITIVE}{ACT_PROTEST}，表达我们的诉求！",
    "有人组织去{LOC_SENSITIVE}{ACT_PROTEST}吗？为了我们的未来。",
    "看见一群人在{LOC_SENSITIVE}{ACT_PROTEST}，警察都来了，场面很混乱。",
    "只有通过{ACT_PROTEST}，才能让{ORG_PARTY}听到我们的声音。",
    "为了纪念{EVT_EXTREME}，我们决定去{LOC_SENSITIVE}进行{ACT_PROTEST}。"
]

# ==============================================================================
# 针对性特训模板 (Targeted Hard Cases)
# 目的：强制修复 Stress Test 中发现的漏判 (False Negatives)
# ==============================================================================

# 1. 颠覆政权特训 (Subversion)
# 解决痛点：模型认为“推翻+统治”是中性历史描述。
# 策略：强制绑定 "推翻/结束/毁灭" + "中共/党/政权"，并强化当前时态。
tmpl_subversion = [
    "我们的终极目标就是{ACT_DIRECT}{ORG_PARTY}的极权统治。",
    "觉醒的人民终将{ACT_DIRECT}{ORG_PARTY}，迎来新中国。",
    "必须彻底{ACT_DIRECT}{ORG_PARTY}，否则国家没有未来。",
    "号召全国人民联合起来，{ACT_DIRECT}这个非法的{ORG_PARTY}。",
    "只要{ORG_PARTY}一天不{ACT_DIRECT}，抗争就一天不会停止。",
    "唯一的出路就是{ACT_DIRECT}{ORG_PARTY}，建立宪政民主。",
    # 针对 "推翻+政党" 的强绑定
    "我们要联合起来，{ACT_DIRECT}{ORG_PARTY}的腐朽统治，建立宪政民主。",
    "中国人民的唯一出路，就是彻底{ACT_DIRECT}{ORG_PARTY}这个非法政权。",
    "绝不能让{ORG_PARTY}继续祸害子孙后代，必须将其{ACT_DIRECT}。",
    "只要{ORG_PARTY}一天不倒台，我们就要抗争到底，直到{ACT_DIRECT}它。",
    # 针对 "李强/习近平 + 废物/傀儡" 等具体辱骂 (解决 "李强就是个傀儡" 识别度低的问题)
    "{PER_REAL}就是一个无能的{TERM_METAPHOR}，根本不配领导这个国家。",
    "{PER_REAL}不仅是{ORG_PARTY}的傀儡，更是中华民族的罪人。",
    "强烈呼吁罢免{PER_REAL}，他没有能力治理国家，只会搞政治斗争。",
    "{PER_REAL}下台！{PER_REAL}滚蛋！还我河山！"
]

# 2. 高级隐喻特训 (Metaphor/Accelerator)
# 解决痛点：模型认为“加速师/司机/开倒车”是交通描述。
# 策略：强制绑定 "维尼/加速师" + "开倒车/踩油门/坠崖"。
tmpl_metaphor_hard = [
    "总加速师正在疯狂{ACT_INDIRECT}，这辆车迟早要坠崖。",
    "那个开倒车的司机就是{PER_NICK}，大家抓紧跳车。",
    "眼看他{ACT_INDIRECT}，眼看他把国家带进沟里。",
    "在那位{PER_NICK}的亲自指挥下，油门焊死，一路{ACT_INDIRECT}。",
    "这就叫{ACT_INDIRECT}，{PER_NICK}不仅不减速，还把方向盘扔了。",
    "全网都在禁评那位司机，因为他开的方向是{ACT_INDIRECT}。",
    "修宪只是为了方便他继续{ACT_INDIRECT}，拉着十几亿人陪葬。"
]

# ==============================================================================
# 3. 智能词汇选择器 (核心逻辑)
# ==============================================================================

def resolve_placeholder(key, style):
    """
    根据当前风格 (style)，智能决定从哪个词表中取词，并控制真名/黑话比例。
    """
    # -------------------------------------------
    # 核心逻辑：领导人称呼的 动态比例控制
    # -------------------------------------------
    if key == "LEADER":
        if style == "direct": 
            # 直球风格：80% 概率用真名，20% 用黑话
            pool = VOCAB["PER_REAL"] if random.random() < 0.8 else VOCAB["PER_NICK"]
        elif style == "indirect":
            # 阴阳风格：10% 概率用真名，90% 用黑话
            pool = VOCAB["PER_REAL"] if random.random() < 0.1 else VOCAB["PER_NICK"]
        else:
            # 其他风格：50/50
            pool = VOCAB["PER_REAL"] + VOCAB["PER_NICK"]
        
        word = random.choice(pool)
        return word, "PER_SENS"

    # -------------------------------------------
    # 映射逻辑
    # -------------------------------------------
    mapping = {
        "FAMILY": ("PER_FAMILY", "PER_SENS"),
        "DISSIDENT": ("PER_DISSIDENT", "PER_SENS"),
        "PARTY": ("ORG_PARTY", "ORG_SENS"),
        "FORCE": ("ORG_FORCE", "ORG_SENS"),
        "MEDIA": ("ORG_MEDIA", "ORG_SENS"),
        "CULT": ("ORG_CULT", "ORG_SENS"),
        "EVT_EXTREME": ("EVT_EXTREME", "EVT_SENS"),
        "EVT_SOCIAL": ("EVT_SOCIAL", "EVT_SENS"),
        "LOC": ("LOC_SPLIT" if style == "direct" else "LOC_SENSITIVE", "LOC_SENS"),
        "LOC_SENSITIVE": ("LOC_SENSITIVE", "LOC_SENS"),
        "LOC_SPLIT": ("LOC_SPLIT", "LOC_SENS"),
        "ACTION": ("ACT_DIRECT" if style == "direct" else "ACT_INDIRECT", "ACT_SENS"),
        "ACT_PROTEST": ("ACT_PROTEST", "EVT_SENS"),
        "ACT_DIRECT": ("ACT_DIRECT", "ACT_SENS"),
        "ACT_INDIRECT": ("ACT_INDIRECT", "ACT_SENS"),
        "METAPHOR": ("TERM_METAPHOR", "METAPHOR"),
        "CONCEPT_DEMO": ("CONCEPT_DEMO", "CONCEPT_SENS")
    }
    
    if key in mapping:
        vocab_key, tag = mapping[key]
        if isinstance(vocab_key, str):
            word = random.choice(VOCAB[vocab_key])
        else:
            word = random.choice(vocab_key)
        return word, tag
        
    return "", "O"

# ==============================================================================
# 4. 生成引擎
# ==============================================================================

def get_sentence_by_style(style_name, template_list):
    tmpl = random.choice(template_list).rstrip("。！？")
    
    # 映射模板中的Key到逻辑Key
    key_map = {
        "PER_REAL": "LEADER", "PER_NICK": "LEADER", 
        "ACT_DIRECT": "ACT_DIRECT", "ACT_INDIRECT": "ACT_INDIRECT",
        "EVT_EXTREME": "EVT_EXTREME", "EVT_SOCIAL": "EVT_SOCIAL",
        "LOC_SPLIT": "LOC_SPLIT", "LOC_SENSITIVE": "LOC_SENSITIVE",
        "ORG_PARTY": "PARTY", "ORG_FORCE": "FORCE", "ORG_CULT": "CULT", "ORG_MEDIA": "MEDIA",
        "PER_FAMILY": "FAMILY", "PER_DISSIDENT": "DISSIDENT",
        "TERM_METAPHOR": "METAPHOR", "CONCEPT_DEMO": "CONCEPT_DEMO"
    }

    result_chars = []
    result_labels = []

    parts = re.split(r'(\{.*?\})', tmpl)
    for part in parts:
        if part.startswith("{") and part.endswith("}"):
            raw_key = part[1:-1]
            logic_key = key_map.get(raw_key, raw_key)
            
            word, tag_type = resolve_placeholder(logic_key, style_name)
            
            if word:
                for i, char in enumerate(word):
                    result_chars.append(char)
                    if tag_type == "O":
                        result_labels.append("O")
                    else:
                        result_labels.append(f"B-{tag_type}" if i == 0 else f"I-{tag_type}")
            else:
                for char in part: result_chars.append(char), result_labels.append("O")
        else:
            for char in part:
                result_chars.append(char)
                result_labels.append("O")
                
    return result_chars, result_labels

def gen_mixed_text():
    # 调整比例：直球(30%)，阴阳(40%)，谣言(20%)，邪教(10%)
    dice = random.random()
    if dice < 0.25: return get_sentence_by_style("direct", tmpl_direct)
    elif dice < 0.50: return get_sentence_by_style("indirect", tmpl_indirect)
    elif dice < 0.70: return get_sentence_by_style("protest", tmpl_protest) # 20% 抗议类
    elif dice < 0.90: return get_sentence_by_style("rumor", tmpl_rumor)
    else: return get_sentence_by_style("cult", tmpl_cult)

# ==============================================================================
# 5. 长文本拼接与执行
# ==============================================================================

CONJUNCTIONS = ["，而且", "。结果", "；甚至", "，可见", "。所以说", "。更重要的是", "，毕竟"]

if __name__ == "__main__":
    print(f"开始生成 {TOTAL_LINES} 条 V2版 政治样本...")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for _ in range(TOTAL_LINES):
            num_parts = random.randint(2, 4) # 增加长度，2-4句
            full_chars = []
            full_labels = []
            
            for i in range(num_parts):
                sub_chars, sub_labels = gen_mixed_text()
                if sub_chars and sub_chars[-1] in ["。", "！", "？", "!", "?"]:
                    sub_chars.pop()
                    sub_labels.pop()

                full_chars.extend(sub_chars)
                full_labels.extend(sub_labels)
                if i < num_parts - 1:
                    conn = random.choice(CONJUNCTIONS)
                    for char in conn:
                        full_chars.append(char)
                        full_labels.append("O")
            
            # 随机标点结尾
            if random.random() > 0.3:
                for char in random.choice(["。", "！", "...", "！！！"]):
                    full_chars.append(char)
                    full_labels.append("O")

            data = {
                "text": "".join(full_chars),
                "label_cls": CLASS_LABEL,
                "label_ner": full_labels
            }
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

    print(f"✅ 完成！文件：{OUTPUT_FILE}")
    print("此版本已包含：")
    print("1. 大量 GitHub 来源的真实敏感词（谐音/黑话/邪教/民运）")
    print("2. 细分的语体风格：直球冲塔 vs 阴阳怪气")
    print("3. 丰富的句式模板：涵盖历史、现实、谣言、口号")
