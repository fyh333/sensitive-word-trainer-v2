import random
import json
import re

# =================配置区域=================
# 生成样本数量
TOTAL_LINES = 3000
# 输出文件路径
OUTPUT_FILE = "porn/porn_novel_sentence.jsonl"
# 类别标签 (2 代表色情)
CLASS_LABEL = 2
# =========================================

# ==============================================================================
# 1. 核心词汇库 (VOCAB)
# 【重要说明】：
# 下面的列表内容目前是“安全占位符”。
# 请你在本地编辑此脚本，将 "占位_xxx" 替换为你收集到的真实、露骨的词汇。
# 填入的词越丰富、越真实，生成的模型效果越好。
# ==============================================================================

VOCAB = {
    # --- 【人体部位类】 ---
    "NOUN_M": [
        "鸡巴", "阴茎", "肉棒", "几把", "龟头", "睾丸", "蛋蛋",
        "屌", "大屌", "粗屌", "大粗屌", "大黑屌", "大鸟"
    ],
    "NOUN_F": [
        "阴道", "嫩逼", "嫩屄", "骚逼", "骚屄", "逼", "屄",
        "蝴蝶逼", "蝴蝶屄", "白虎逼", "白虎屄", "臭逼", "臭屄"
        "蜜穴", "花心", "小穴", "淫穴", "小逼"
    ],
    "NOUN_BREAST": [
        "胸", "奶子", "乳房", "乳头", "双峰", "雪乳"
    ],
    "NOUN_REAR": [
        "菊花", "肛门", "屁股", "菊穴", "屁眼"
    ],
    "NOUN_BODY": [
        "玉足", "大腿根", "腰肢", "颈窝", "敏感点"
    ],

    # --- 【液体/分泌物类】 ---
    "NOUN_FLUID": [
        "爱液", "精液", "白浆", "淫水", "喷出的水"
    ],

    # --- 【道具/环境类】 ---
    "NOUN_TOY": [
        "跳蛋", "按摩棒", "假阳具", "振动棒"
    ],
    "NOUN_CLOTH": [
        "蕾丝内裤", "黑丝", "吊带袜", "情趣内衣"
    ],
    "NOUN_PLACE": [
        "办公桌", "酒店大床", "沙发", "试衣间", "野外"
    ],

    # --- 【动词类 - 按强度区分】 ---
    "VERB_HARD": [
        "猛插", "狂操", "抽送", "干死", "贯穿",
        "性虐", "凌辱", "轮奸", "轮操", "轮暴",
    ],
    "VERB_SOFT": [
        "抚摸", "揉捏", "玩弄", "挑逗", "吸吮",
        "开苞", "插阴", "作爱", "抓胸"
    ],
    "VERB_ORAL": [
        "吞吐", "深喉", "舔舐", "含住", "口交",
        "口射", "舔阴", "口爆",
    ],
    "VERB_CUM": [
        "内射", "喷射", "高潮", "射满", "灌满"
    ],

    # --- 【修饰词类】 ---
    "ADJ_STATE": [
        "湿漉漉", "硬邦邦", "粉嫩", "充血", "泥泞"
    ],
    "ADJ_FEEL": [
        "酥麻", "滚烫", "难以忍受", "销魂", "撕裂般"
    ],
    "ADV_ACT": [
        "狠狠地", "疯狂地", "不知廉耻地", "粗暴地", "贪婪地"
    ],

    # --- 【拟声/角色类】 ---
    "SOUND": [
        "呻吟", "浪叫", "喘息", "尖叫", "叫床"
    ],
    "ROLE": [
        "小骚货", "母狗", "主人", "哥哥", "荡妇",
        "性奴", "熟女", "淫女", "反差婊", "反差狗",
        "幼女", "骚货", "浪女"
    ]
}

# ==============================================================================
# 2. 句法模板库 (Templates)
# 涵盖：主动、被动、复句、侧面描写、心理描写、特殊场景
# ==============================================================================

# A. 主动-高强度动作 (SVO结构)
templates_active = [
    "他没有任何前戏，直接扶着{NOUN_M}{VERB_HARD}进了她{ADJ_STATE}的{NOUN_F}。",
    "腰部猛地发力，巨大的{NOUN_M}瞬间贯穿了那层{ADJ_STATE}的阻碍，直抵花心。",
    "他像不知疲倦的野兽，按着她的{NOUN_BODY}疯狂{VERB_HARD}，每一下都伴随着啪啪的撞击声。",
    "为了让更深处的软肉被{VERB_HARD}到，他抬高了她的{NOUN_BODY}，让{NOUN_M}进得更深。",
    "他抽出{NOUN_M}，对着那张{ADJ_STATE}的小嘴，将浓稠的{NOUN_FLUID}{VERB_CUM}了进去。",
    "手指在{NOUN_F}口打转，接着三根手指并拢，直接{VERB_HARD}了进去，撑开了紧致的肉壁。"
]

# B. 被动/无力感 (强调接受者的状态)
templates_passive = [
    "她{ADJ_STATE}的{NOUN_F}被粗暴地撑开，容纳着那根并不属于她的{NOUN_M}。",
    "双手被反剪在身后，她只能被迫承受着身后男人一次次凶猛的{VERB_HARD}。",
    "整个人被钉在{NOUN_PLACE}上，{NOUN_F}里塞满了他的{NOUN_M}，连挣扎的力气都没有。",
    "脆弱的{NOUN_BODY}被他随意摆弄成各种羞耻的姿势，任由他在体内{VERB_HARD}。",
    "那一刻，她感觉自己的灵魂仿佛都被那根{NOUN_M}给{VERB_HARD}碎了。",
    "随着{NOUN_TOY}的震动档位调高，她的{NOUN_F}被迫吐出了更多的{NOUN_FLUID}。"
]

# C. 复句与逻辑结构 (增加句法复杂度)
templates_complex = [
    "他一边用言语羞辱着这只{ROLE}，一边加快了{VERB_HARD}那个{ADJ_STATE}的{NOUN_F}的速度。",
    "虽然嘴上喊着不要，但她{ADJ_STATE}的{NOUN_F}却诚实地绞紧了他的{NOUN_M}。",
    "不仅仅是{NOUN_F}被{VERB_HARD}，连{NOUN_REAR}也被塞进了{NOUN_TOY}，双重的刺激让她崩溃。",
    "直到{NOUN_FLUID}顺着大腿根流满了一地，他才终于停止了对她{NOUN_F}的{VERB_HARD}。",
    "因为{NOUN_M}实在太大，每次{VERB_HARD}到底时，她的小腹都会鼓起一个小包。",
    "既然这张嘴这么会说，那就用来含着这根{ADJ_STATE}的{NOUN_M}好好{VERB_ORAL}吧。"
]

# D. 侧面与环境描写 (视觉/听觉)
templates_descriptive = [
    "透过落地镜，她清晰地看到那根{NOUN_M}是如何一点点挤进自己{NOUN_F}的全过程。",
    "房间里只剩下肉体撞击的啪啪声和她压抑不住的{SOUND}，空气中弥漫着{NOUN_FLUID}的腥气。",
    "昏暗的灯光下，两人结合的地方泥泞不堪，{NOUN_FLUID}随着抽插被搅得泡沫飞溅。",
    "视线变得模糊，眼前只剩下那根在她{NOUN_F}里进进出出的{ADJ_STATE}的{NOUN_M}。",
    "她的{NOUN_CLOTH}并没有被完全脱下，而是挂在{NOUN_BODY}上，更增添了几分凌虐的美感。",
    "原本粉嫩的{NOUN_F}因为长时间的{VERB_HARD}，此刻已经变得{ADJ_STATE}且充血。"
]

# E. 心理与感官描写 (Sensory)
templates_sensory = [
    "那种{ADJ_FEEL}的快感沿着脊椎直冲头顶，脑子里一片空白，只知道迎合他的{VERB_HARD}。",
    "太深了...感觉连胃都要被那根{NOUN_M}给{VERB_HARD}穿了...",
    "羞耻心在这一刻荡然无存，她只想张开腿，求他用{NOUN_M}填满自己空虚的{NOUN_F}。",
    "内壁敏感的褶皱疯狂吸附着入侵的{NOUN_M}，贪婪地索取着每一滴{NOUN_FLUID}。",
    "她感觉到一股热流在体内炸开，那是他在她的{NOUN_F}深处{VERB_CUM}了。",
    "那种被填满的充实感，让她忍不住发出了放荡的{SOUND}，乞求着更多。"
]

# F. 特殊场景 (前戏/道具/口令)
templates_special = [
    "冰凉的{NOUN_TOY}贴上滚烫的{NOUN_REAR}，剧烈的温差让她尖叫出声。",
    "他把{NOUN_CLOTH}揉成一团塞进她嘴里，然后对着那{ADJ_STATE}的{NOUN_REAR}就开始{VERB_HARD}。",
    "跪在{NOUN_PLACE}上，她努力翘高屁股，展示着那还在流着{NOUN_FLUID}的{NOUN_F}。",
    "“{ROLE}，看看你的{NOUN_F}流了多少水，真是一只欠操的母狗。”",
    "他低下头，隔着{NOUN_CLOTH}一口咬住了她挺立的{NOUN_BREAST}，舌尖不停地{VERB_SOFT}。"
]

# G. 招嫖/暗语小广告 (Short & Implicit)
templates_spam = [
    "同城{NOUN_PLACE}可约，{ROLE}在线，加V看照。",
    "新到{ROLE}资源，{NOUN_BREAST}大，活好不粘人。",
    "高端外围，可空降，{VERB_ORAL}{VERB_CUM}全套。",
    "寂寞少妇求安慰，想找个{NOUN_M}大的哥哥。",
    "学生兼职，懂的来，非诚勿扰，{NOUN_PLACE}交易。",
    "茶馆新茶已到，{ADJ_STATE}多汁，欢迎品尝。"
]

# 合并所有模板 (调整倍数以控制生成比例，可自由微调)
ALL_TEMPLATES = (
    templates_active * 3 +      # 核心动作 (占比最大)
    templates_passive * 2 +     # 被动描写
    templates_complex * 2 +     # 复杂句式
    templates_descriptive * 2 + # 画面感
    templates_sensory * 2 +     # 心理描写
    templates_special * 2 +     # 特殊/前戏
    templates_spam * 1          # 招嫖/暗语小广告
)

# ==============================================================================
# 3. 连接词库 (用于长句拼接)
# ==============================================================================
CONJUNCTIONS = [
    "，紧接着", "。此时，", "，然后", "，但是", "。与此同时，",
    "，伴随着这一动作，", "。结果，", "，导致", "；然而，", "，于是"
]

# ==============================================================================
# 4. 生成逻辑
# ==============================================================================

def get_single_sentence_data():
    """
    生成单个短句的 (chars, labels)
    """
    tmpl = random.choice(ALL_TEMPLATES)
    # 去掉末尾的句号，方便后面拼接
    tmpl = tmpl.rstrip("。")
    
    result_chars = []
    result_labels = []
    
    parts = re.split(r'(\{.*?\})', tmpl)
    for part in parts:
        if part.startswith("{") and part.endswith("}"):
            key = part[1:-1]
            if key in VOCAB:
                word = random.choice(VOCAB[key])
                for i, char in enumerate(word):
                    result_chars.append(char)
                    result_labels.append("B-PRN" if i == 0 else "I-PRN")
            else:
                for char in part:
                    result_chars.append(char)
                    result_labels.append("O")
        else:
            for char in part:
                result_chars.append(char)
                result_labels.append("O")
                
    return result_chars, result_labels

def gen_long_fiction():
    """
    拼接多个短句，形成长文本
    """
    # 随机决定拼接 2 到 4 个短句
    num_parts = random.randint(1, 4)
    
    full_chars = []
    full_labels = []
    
    for i in range(num_parts):
        # 1. 获取一个短句
        chars, labels = get_single_sentence_data()
        
        # 2. 加入主列表
        full_chars.extend(chars)
        full_labels.extend(labels)
        
        # 3. 如果不是最后一句，加连接词
        if i < num_parts - 1:
            conn = random.choice(CONJUNCTIONS)
            for char in conn:
                full_chars.append(char)
                full_labels.append("O") # 连接词标签为 O
                
    # 4. 句尾补全标点 (30% 概率不补，增加鲁棒性)
    if random.random() > 0.3:
        end_punc = random.choice(["。", "！", "...", "~~"])
        for char in end_punc:
            full_chars.append(char)
            full_labels.append("O")
            
    return "".join(full_chars), full_labels

# ==============================================================================
# 5. 执行程序
# ==============================================================================

if __name__ == "__main__":
    print(f"开始生成 {TOTAL_LINES} 条长文本色情小说样本...")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for i in range(TOTAL_LINES):
            text, labels = gen_long_fiction()
            
            # 长度校验
            if len(text) != len(labels):
                print(f"[Error] Length mismatch at line {i}")
                continue
                
            data = {
                "text": text,
                "label_cls": CLASS_LABEL,
                "label_ner": labels
            }
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
            
    print(f"✅ 生成完成！文件: {OUTPUT_FILE}")
    
    # 预览
    print("\n=== 预览 (占位符模式) ===")
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        for _ in range(2):
            d = json.loads(f.readline())
            print(f"TEXT: {d['text']}")
