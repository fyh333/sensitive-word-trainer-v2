import random
import json

# 配置
TOTAL_LINES = 2000
OUTPUT_FILE = "porn/porn_spam_sentence.jsonl"
CLASS_LABEL = 2

# ==========================================
# 1. 扩充后的黑话词典
# ==========================================

# 【地点】
place = [
    "北京", "上海", "广州", "深圳", "成都", "重庆", "杭州", "武汉", "西安", "郑州",
    "南京", "天津", "苏州", "长沙", "沈阳", "青岛", "合肥", "东莞", "澳门", "云南"
    "同城", "附近", "酒店", "公寓"
]

# --- 身份组 ---

# 【异性身份】
straight_identities = [
    ("学生妹", "PRN"), ("00后", "PRN"), ("少妇", "PRN"), ("人妻", "PRN"), 
    ("空姐", "PRN"), ("白领", "PRN"), ("新茶", "PRN"), ("嫩妹", "PRN"), 
    ("老师", "O"), ("兼职", "O"), ("妹子", "O"), ("白虎", "O"), ("娇妻", "O"),
    ("外围", "PRN"), ("楼凤", "PRN")
]

# 【同性/特殊身份】 (新增)
gay_identities = [
    ("体育生", "O"), ("猛1", "PRN"), ("骚0", "PRN"), ("公0", "PRN"), 
    ("直男", "O"), ("大叔", "O"), ("鲜肉", "O"), ("壮熊", "PRN"), 
    ("CD", "PRN"), ("TS", "PRN"), ("伪娘", "PRN"), ("药娘", "PRN"),
    ("男S", "PRN"), ("男M", "PRN")
]

# --- 器官组 (新增) ---

# 【男性器官】 (描述尺寸、硬度)
male_organs = [
    ("大鸟", "PRN"), ("大棒", "PRN"), ("肉棒", "PRN"), ("几把", "PRN"),
    ("JJ", "PRN"), ("巨根", "PRN"), ("阳具", "PRN"), ("鸡巴", "PRN"),
    ("丁丁", "PRN"), ("炮架", "PRN"), ("子弹", "PRN")
]

# 【女性器官】 (描述私处)
female_organs = [
    ("鲍鱼", "PRN"), ("粉鲍", "PRN"), ("黑木耳", "PRN"), ("小穴", "PRN"),
    ("妹妹", "PRN"), ("馒头", "PRN"), ("逼", "PRN"), ("B", "PRN"),
    ("水帘洞", "PRN"), ("蜜桃", "O"), ("奶", "PRN"), ("咪咪", "PRN"),
    ("双峰", "PRN")
]

# 【后庭/通用】 (针对同性或特殊玩法)
rear_organs = [
    ("菊花", "PRN"), ("后庭", "PRN"), ("皮炎", "PRN"), ("屁眼", "PRN"),
    ("菊穴", "PRN"), ("前列腺", "PRN")
]

# --- 服务与动作 ---

# 【通用服务】
services = [
    ("上门", "PRN"), ("服务", "PRN"), ("全套", "PRN"), ("修车", "PRN"), 
    ("喝茶", "PRN"), ("大选", "PRN"), ("莞式", "PRN"), ("一条龙", "PRN"),
    ("同城", "O"), ("可约", "PRN"), ("陪玩", "O"), ("按摩", "O"),
    ("特殊", "PRN"), ("释放", "PRN"), ("毒龙", "PRN"), ("漫游", "PRN"),
    ("可飞全国", "PRN"), ("口爆", "PRN"), ("内射", "PRN"), ("颜射", "PRN"),
    ("69", "PRN"), ("冰火", "PRN"), ("裸聊", "PRN"), ("文爱", "PRN")
]

# 【同性特定服务】 (新增)
gay_services = [
    ("拼刺刀", "PRN"), ("击剑", "PRN"), ("走后门", "PRN"), ("深喉", "PRN"),
    ("互撸", "PRN"), ("调教", "PRN")
]

# --- 形容词 ---

# 【形容词/描述】
descriptions = [
    ("水多", "PRN"), ("活好", "PRN"), ("听话", "O"), ("粘人", "O"),
    ("母狗", "PRN"), ("火辣", "O"), ("丰满", "PRN"), ("紧致", "PRN"),
    ("喷水", "PRN"), ("无套路", "O"), ("本人", "O"), ("真实", "O"),
    ("照片", "O"), ("视频", "O"), ("验证", "O"), ("耐操", "PRN"),
    ("骚", "PRN"), ("浪", "PRN"), ("极品", "O")
]

# 【联系方式引导词】
contact_methods = [
    ("加V", "CNT"), ("V信", "CNT"), ("威信", "CNT"), ("微", "CNT"),
    ("加薇", "CNT"), ("绿泡泡", "CNT"), ("电报", "CNT"), ("小飞机", "CNT"), 
    ("+V：", "CNT"), ("企鹅", "CNT"), ("QQ", "CNT"), ("Q", "CNT"),
    ("小蓝鸟", "CNT"), ("扣扣", "CNT"), ("电话", "CNT"), ("联系", "CNT"),
    ("私聊", "CNT"), ("推特", "CNT")
]

# 【干扰字符】
noise_chars = [" ", ".", "-", "/", "aa", "b", "~", "*", "Wait"]

# ==========================================
# 2. 辅助函数
# ==========================================

def make_segment(text, tag_type):
    if not text:
        return []
    result = []
    if tag_type == "O":
        for char in text:
            result.append((char, "O"))
    else:
        result.append((text[0], f"B-{tag_type}"))
        for char in text[1:]:
            result.append((char, f"I-{tag_type}"))
    return result

def gen_contact_info():
    is_phone = random.random() < 0.3
    if is_phone:
        num = f"1{random.randint(3,9)}{random.randint(0,9)}-{random.randint(1000,9999)}"
    else:
        num = "".join(random.choices("abcdefghijklmnopqrstuvwxyz1234567890", k=random.randint(6, 12)))
    
    if random.random() < 0.5:
        noise = random.choice([".", " ", "-"])
        num = num[:3] + noise + num[3:]
    return make_segment(num, "O")

# ==========================================
# 3. 核心生成逻辑 (支持异性/同性模式)
# ==========================================

def get_organ_desc(mode):
    """根据模式生成器官描述"""
    segments = []
    
    # 30% 的概率描述器官
    if random.random() > 0.3:
        return segments

    # 随机加个形容词前缀 (e.g. 粉嫩的鲍鱼)
    if random.random() < 0.5:
        adj = random.choice(["粉嫩", "紧致", "粗大", "黑", "白", "巨", "小"])
        segments += make_segment(adj, "PRN") # 形容器官的词通常也算敏感上下文
    
    organ = None
    if mode == "straight":
        # 异性：女器官 or 男器官
        organ = random.choice(female_organs + male_organs)
    else:
        # 同性：后庭 or 男器官
        organ = random.choice(rear_organs + male_organs)
        
    text, tag = organ
    segments += make_segment(text, tag)
    
    # 随机加个后缀
    if random.random() < 0.3:
        segments += make_segment(random.choice(["看", "玩", "爽"]), "O")
        
    # 加个分隔符
    segments += make_segment(random.choice(["，", " ", ""]), "O")
    
    return segments

def gen_simple_ad():
    segments = []
    
    # 1. 决定模式：80% 异性，20% 同性
    mode = "straight" if random.random() < 0.8 else "gay"
    
    # 地点
    if random.random() < 0.5:
        segments += make_segment(random.choice(place), "O")
    
    # 身份
    if mode == "straight":
        text, tag = random.choice(straight_identities)
    else:
        text, tag = random.choice(gay_identities)
    segments += make_segment(text, tag)
    
    # 干扰符
    if random.random() < 0.3: segments += make_segment(random.choice(noise_chars), "O")
    
    # --- 插入器官描述 (新增) ---
    segments += get_organ_desc(mode)
    # -----------------------

    # 服务
    # 混合通用服务和特定服务
    pool = services
    if mode == "gay":
        pool += gay_services
        
    text, tag = random.choice(pool)
    segments += make_segment(text, tag)
    
    # 描述
    if random.random() < 0.7:
        segments += make_segment(random.choice(["，", " ", ""]), "O")
        text, tag = random.choice(descriptions)
        segments += make_segment(text, tag)
        
    # 联系方式
    sep = random.choice(["", " ", "，", "。", "！"])
    segments += make_segment(sep, "O")
    
    text, tag = random.choice(contact_methods)
    segments += make_segment(text, tag)
    segments += make_segment(":", "O")
    segments += gen_contact_info()
    
    return segments

def gen_story_ad():
    """叙述型：找人/自述"""
    segments = []
    mode = "straight" if random.random() < 0.8 else "gay"
    
    segments += make_segment(random.choice(["本人", "自己", "刚到"]), "O")
    
    # 身份
    if mode == "straight":
        text, tag = random.choice(straight_identities)
    else:
        text, tag = random.choice(gay_identities)
    segments += make_segment(text, tag)
    segments += make_segment("，", "O")
    
    # 器官描述
    segments += get_organ_desc(mode)
    
    text, tag = random.choice(descriptions)
    segments += make_segment(text, tag)
    segments += make_segment("，", "O")
    
    # 需求
    segments += make_segment("找", "O")
    if mode == "straight":
        segments += make_segment("哥哥", "O")
    else:
        segments += make_segment(random.choice(["1", "0", "基友", "同好"]), "O")
        
    text, tag = random.choice(services)
    segments += make_segment(text, tag)
    
    # 结尾
    segments += make_segment("。", "O")
    text, tag = random.choice(contact_methods)
    segments += make_segment(text, tag)
    segments += gen_contact_info()
    
    return segments

def gen_keyword_stack():
    """关键词堆砌"""
    segments = []
    mode = "straight" if random.random() < 0.8 else "gay"
    
    for _ in range(random.randint(3, 6)):
        # 混合池
        source_pool = descriptions + services
        if mode == "straight":
            source_pool += straight_identities + female_organs + male_organs
        else:
            source_pool += gay_identities + rear_organs + male_organs
            
        text, tag = random.choice(source_pool)
        segments += make_segment(text, tag)
        segments += make_segment(" ", "O") 
        
    text, tag = random.choice(contact_methods)
    segments += make_segment(text, tag)
    segments += gen_contact_info()
    
    return segments

# ==========================================
# 4. 主程序
# ==========================================

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for _ in range(TOTAL_LINES):
        dice = random.random()
        if dice < 0.5:
            segments = gen_simple_ad()
        elif dice < 0.8:
            segments = gen_story_ad()
        else:
            segments = gen_keyword_stack()
            
        full_text = ""
        ner_labels = []
        for char, label in segments:
            full_text += char
            ner_labels.append(label)
            
        data = {
            "text": full_text,
            "label_cls": CLASS_LABEL,
            "label_ner": ner_labels
        }
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

print(f"✅ 增强版招嫖样本生成完成！文件：{OUTPUT_FILE}")
print("   - 已包含同性/异性分类")
print("   - 已包含器官、后庭等露骨描述")
