import random
import json

# 配置
TOTAL_LINES = 18000 # 稍微增加数量，因为现在的样本多样性很高
OUTPUT_FILE = "normal/normal_sentence_enhanced.jsonl"

# ==========================================
# 1. 基础素材库 (扩充版)
# ==========================================

people = [
    # 原有
    "我们班的同学", "隔壁的邻居", "我的老师", "那个程序员", "快递小哥", 
    "张大爷", "李阿姨", "王叔叔", "小学生", "考研党", 
    "公司的员工", "客服人员", "社区志愿者", "我的老板", "那个陌生人",
    "外卖骑手", "网约车司机", "产品经理", "带货主播", "二次元宅男",
    "广场舞大妈", "我的前女友", "相亲对象", "房东", "健身教练",
    "李克强", "王毅", "习近平", "胡锦涛", "温家宝",
    "体育生", "那个体育生", "爱喝茶的老人", "妹妹",
    "酒店大堂经理", "前台小妹", "推销员", 
    "00后", "90后", "05后", "职场白领", "白领",
    "做兼职的学生", "英语老师", "体育老师",
    "空姐", "护士", "同城的朋友", "同城交易卖家",
    # === 新增 (丰富身份) ===
    "保洁阿姨", "保安大叔", "或者是医生", "律师", "公务员", 
    "那个网红", "up主", "博主", "大V", "小编", "楼主", "层主",
    "键盘侠", "吃瓜群众"
]

things = [
    # 原有
    "根据相关规定", "这篇文章", "这段代码", "这台机器", "根据统计数据", 
    "今天的作业", "公司的项目", "我的电脑", "这个包裹", "那份文件",
    "新的数据库", "这次会议记录", "用户的反馈", "这袋大米",
    "智能手机", "蓝牙耳机", "空气炸锅", "扫地机器人", "显卡",
    "菊花茶", "这朵菊花", "鲍鱼", "新鲜鲍鱼", "海鲜市场的鲍鱼", "馒头",
    "大鸟(动物)", "一只大鸟", "皮炎平软膏", "粉嫩的桃子",
    "红烧肉馒头", "旺仔小馒头", "盛开的菊花", "一杯菊花茶",
    "黑木耳沙拉", "森林里的大鸟", "啄木鸟", "香蕉牛奶", "水蜜桃",
    "广播体操", "家务活", "作业",
    "家里的宠物狗", "那头猪", "一群鸭子", "一只老母鸡",
    "垃圾桶里的垃圾", "不可回收垃圾", "智商测试题", "智力测验",
    "墙上的挂历", "电话听筒", "升降机", "无人机",
    "神舟飞船", "航天飞机", "风筝", "卫星", "空间站",
    # === 新增 (易误判的生活/电商物品) ===
    "充电宝", "数据线", "机械键盘", "鼠标垫", "硬盘",
    "润肤乳", "沐浴露", "香蕉", "黄瓜", "茄子", "火腿肠", "牛奶", "奶油",
    "卫生纸", "湿巾", "床单", "被罩", "枕头", "丝袜", "高跟鞋",
    "口红", "指甲油", "瑜伽裤", "垃圾袋", "快递盒"
]

places = [
    "北京", "上海", "广州", "深圳", "成都", "重庆", "杭州", "武汉", "西安", "郑州",
    "南京", "天津", "苏州", "长沙", "沈阳", "青岛", "合肥", "东莞", "澳门", "云南",
    "同城", "附近", "公寓", "图书馆", "教室", "家里", "自习室", "公司", "地铁上", 
    "网吧", "菜市场", "健身房", "火锅店", "电影院", "公园", "梦里",
    "酒店", "宾馆", "快捷酒店", "五星级酒店",
    # === 新增 ===
    "派出所", "居委会", "医院大厅", "洗手间", "阳台", "卧室"
]

subjects = [
    "高等数学", "线性代数", "英语", "物理", "化学", "Python", 
    "Java", "烹饪", "挖掘机技术", "钢琴", "马克思主义哲学"
]

global_adverbs = [
    "非常", "大概", "一直", "从来不", "经常", "偶尔", 
    "必须", "正在", "已经", "刚开始", "总共", "一共",
    "显然", "据说是", "不得不", "甚至", "竟然"
]

conjunctions = [
    "，而且", "，但是", "。另外，", "，虽然", "，导致", 
    "。结果，", "，同时", "。值得注意的是，", "，然后",
    "；然而，", "，因为", "。所以，"
]

actions_safe = [
    "正在写代码", "去吃饭了", "刚下班", "还在加班", "去取快递", 
    "在打游戏", "在刷视频", "去健身了", "在做饭", "去遛狗", 
    "在准备考试", "在修电脑", "去买菜", "在洗衣服"
]

# ==========================================
# 2. 核心工具与生成器
# ==========================================

def fill_template(templates, fillers):
    if isinstance(templates, str): templates = [templates]
    tmpl = random.choice(templates)
    for key, vals in fillers.items():
        while "{" + key + "}" in tmpl:
            tmpl = tmpl.replace("{" + key + "}", random.choice(vals), 1)
    return tmpl

# --- 1. 共字陷阱 ---
def gen_gong_trap():
    templates_contain = [
        "{subj}其中共包含了{num}个元素",
        "{subj}统共由{num}个部件组成",
        "根据计算，{subj}一共需要{num}天才能完成",
        "{subj}总共花费了{num}元预算"
    ]
    fillers_contain = {
        "subj": things + ["这个列表", "那个箱子", "这段程序", "神舟飞船", "航天飞机"],
        "num": [str(i) for i in range(5, 1000)]
    }
    templates_concept = [
        "{org}必须坚持{concept}的原则",
        "我们要建立一个{adj}的公共场所",
        "{person}和{person}拥有共同的{noun}",
        "为了方便大家，{org}设立了共享单车停放点",
        "只要大家都献出一份爱，世界将变成美好的人间，共勉",
        "这两个原子通过共价键连接",
        "磁共振检查显示他的{body}没有问题"
    ]
    fillers_concept = {
        "org": ["我们团队", "这家公司", "社区委员会", "根据会议精神", "项目组", "大家"],
        "person": people,
        "concept": ["合作共赢", "资源共享", "和平共处", "互利互惠", "信息公开"],
        "adj": ["开放", "拥挤", "免费", "吵闹", "干净"],
        "noun": ["理想", "爱好", "话题", "记忆"],
        "body": ["头部", "膝盖", "脊椎"]
    }
    if random.random() < 0.5: return fill_template(templates_contain, fillers_contain)
    else: return fill_template(templates_concept, fillers_concept)

# --- 2. 习字陷阱 ---
def gen_xi_trap():
    templates = [
        "{person}{adv}在{place}复习{subject}",
        "{person}养成了一个{adj}的习惯",
        "刚开始实习的时候，{person}感到{adv}{emotion}",
        "这次消防演习{adv}非常成功",
        "我们要努力学习，天天向上",
        "对于这种现象，我早就习以为常了",
        "预习是学习的重要环节"
    ]
    fillers = {
        "person": people,
        "place": places,
        "subject": subjects,
        "adj": ["奇怪", "良好", "有趣", "奇葩", "早睡早起"],
        "emotion": ["紧张", "兴奋", "迷茫", "累"],
        "adv": global_adverbs
    }
    return fill_template(templates, fillers)

# --- 3. 人名与歧义陷阱 ---
def gen_name_trap():
    names = ["王毅", "李强", "温家宝", "胡锦涛", "江泽民", "李克强", "习近平"] 
    contexts = [
        "{name}是我们村唯一的修车师傅",
        "{name}最近沉迷《黑神话：悟空》",
        "我的邻居{name}昨天相亲又失败了",
        "{name}在菜市场为了两毛钱跟人吵起来了",
        "客户经理{name}态度非常好",
        "我在百度搜索{name}，发现全是重名的",
        "{name}写的这段代码有一个Bug"
    ]
    name = random.choice(names)
    tmpl = random.choice(contexts)
    return tmpl.format(name=name)

def gen_ambiguity_trap():
    traps = [
        "孩子长大了，经济独立很重要",
        "庆丰包子铺的猪肉大葱包子真好吃",
        "迪士尼乐园的花车游行太精彩了",
        "我住在64号楼，89室",
        "这次考试我只考了64分",
        "警察叔叔帮小朋友找回了走丢的宠物狗",
        "我们要遵纪守法，做一个好公民"
    ]
    return random.choice(traps)

# --- 4. 基础 Normal Text ---
def gen_normal_text():
    templates = [
        "今天天气真{adj}，适合去{action}",
        "我不喜欢吃{food}，因为味道太{adj}了",
        "这个{prod}的价格是{price}元，太{adj}了",
        "如果你遇到{prob}，可以尝试{solve}",
        "关于{tech}技术，目前的最新进展是{desc}",
        "服务器又崩了，{person}正在连夜修复",
        "最近新闻说{place}那边又堵车了",
        "听我说，{person}其实是个很好的人",
        "无论如何，生活还是要继续的",
        "你听过那首{adj}的歌吗？"
    ]
    fillers = {
        "person": people,
        "place": places,
        "adj": ["不错", "糟糕", "奇怪", "贵", "美味", "离谱", "感人"],
        "action": ["爬山", "逛街", "写代码", "睡觉", "钓鱼"],
        "food": ["香菜", "榴莲", "臭豆腐", "螺蛳粉", "火锅"],
        "prod": ["手机", "电脑", "显卡", "键盘"],
        "price": [str(x) for x in range(10, 10000)],
        "prob": ["蓝屏", "死机", "感冒", "断网", "失眠"],
        "solve": ["重启", "喝热水", "百度一下", "去医院"],
        "tech": ["人工智能", "5G", "量子计算", "区块链"],
        "desc": ["令人兴奋", "还在研究中", "非常成熟"]
    }
    return fill_template(templates, fillers)

# --- 5. 各种场景 Trap (医疗/农业/殡葬等) ---
def gen_medical_trap():
    templates = [
        "医生建议病人尽快进行{term}手术",
        "这就需要我们了解{body}的构造和功能",
        "护士正在清理病人的{waste}",
        "根据病理报告，患者被确诊为{disease}",
        "医学院的学生正在进行{action}",
        "这种药物对{disease}有很好的疗效",
        "为了健康，女性应定期做{check}检查"
    ]
    fillers = {
        "term": ["阑尾切除", "肿瘤切除", "心脏搭桥", "子宫肌瘤剔除"],
        "body": ["直肠", "生殖系统", "消化道", "泌尿系统"],
        "waste": ["排泄物", "呕吐物", "伤口脓液"],
        "disease": ["晚期肺癌", "梅毒", "淋病", "艾滋病", "尿毒症"],
        "action": ["尸体解剖", "器官标本制作", "临床观摩"],
        "check": ["乳腺", "宫颈", "妇科"]
    }
    return fill_template(templates, fillers)

def gen_agri_trap():
    templates = [
        "村里的兽医正在给{animal}进行{action}",
        "这种{crop}是通过{tech}培育的新品种",
        "养殖场需要定期清理{place}以防止病菌滋生",
        "这只{animal}看起来生病了，不吃饲料",
        "我们要科学地进行{action}，提高产量",
        "虽然是{animal}，但也是一条生命"
    ]
    fillers = {
        "animal": ["母猪", "公狗", "奶牛", "种猪", "老母鸡"],
        "action": ["人工授精", "配种", "检疫", "接生"],
        "crop": ["水稻", "玉米", "油菜花"],
        "tech": ["杂交", "嫁接", "转基因"],
        "place": ["猪圈", "化粪池", "鸡窝"]
    }
    return fill_template(templates, fillers)

def gen_funeral_trap():
    templates = [
        "家属怀着沉痛的心情在{place}送别了死者",
        "按照当地习俗，老人去世后要{action}",
        "工作人员小心翼翼地将{item}交给了家属",
        "每年清明节，我们都会去{place}{action}",
        "这是一辆庄严肃穆的{vehicle}，请让行",
        "爷爷临终前，全家人都守在床前给他{action}"
    ]
    fillers = {
        "place": ["殡仪馆", "火葬场", "烈士陵园", "坟头"],
        "action": ["烧纸", "祭拜", "守灵", "送终", "火化"],
        "item": ["骨灰盒", "遗物", "死亡证明"],
        "vehicle": ["灵车", "运尸车"]
    }
    return fill_template(templates, fillers)

def gen_action_trap():
    templates = [
        "全体学生正在操场上{action_cao}",
        "那个程序员正在{action_gan}，没空理你",
        "请把U盘{action_cha}电脑的USB接口",
        "今天是{date}，天气非常晴朗",
        "前锋起脚{action_she}，球进了！",
        "这个{noun_dong}太深了，里面黑漆漆的",
        "我们要学习雷锋的{noun_sao}神" 
    ]
    fillers = {
        "action_cao": ["做广播体操", "操练队列", "操办运动会"],
        "action_gan": ["干活", "苦干实干", "埋头苦干"],
        "action_cha": ["插入", "插进", "插到"],
        "date": ["10月1日", "周日", "烈日当空的日子", "抗日战争纪念日"],
        "action_she": ["射门", "射击", "发射"],
        "noun_dong": ["山洞", "桥洞", "漏洞", "脑洞"],
        "noun_sao": ["大无畏", "螺丝钉"]
    }
    return fill_template(templates, fillers)

def gen_family_love():
    templates = [
        "我最爱吃{relative}做的红烧肉了",
        "今天陪{relative}去公园散步，感觉很温馨",
        "祝{relative}生日快乐，长命百岁",
        "小时候，{relative}经常给我讲故事",
        "我们要孝敬父母，尊老爱幼",
        "这周末带{relative}去医院体检",
        "一家人开开心心吃顿团圆饭比什么都强"
    ]
    fillers = {
        "relative": ["妈妈", "爸爸", "爷爷", "奶奶", "外婆", "孙子", "全家人"]
    }
    return fill_template(templates, fillers)

def gen_tech_trap():
    templates = [
        "系统出现故障，只能强制{action_kill}了",
        "记得定期清理{bin}里的文件释放空间",
        "这段代码进入了{dead}，导致程序卡住",
        "我们需要修复这个严重的{bug}",
        "这是工业生产产生的{waste}，需要回收利用",
        "不要随意点击不明链接，防止中{virus}"
    ]
    fillers = {
        "action_kill": ["杀死进程", "Kill掉任务", "结束运行"],
        "bin": ["回收站", "垃圾桶", "缓存"],
        "dead": ["死循环", "假死状态", "Deadlock"],
        "bug": ["Bug", "漏洞", "缺陷"],
        "waste": ["工业废料", "废物", "废渣"],
        "virus": ["病毒", "木马"]
    }
    return fill_template(templates, fillers)

def gen_movement_trap():
    templates = [
        "小朋友在草地上开心地{action_gun}",
        "周末我们要去{action_pa}",
        "广场中央的{noun_pen}非常漂亮",
        "汽车轮胎压过路面，{action_gun}向前",
        "这种昆虫依靠{action_pa}行进",
        "油漆工正在往墙上{action_pen}漆"
    ]
    fillers = {
        "action_gun": ["打滚", "滚动", "滚雪球"],
        "action_pa": ["爬山", "爬楼梯", "爬树"],
        "noun_pen": ["喷泉", "喷雾", "喷灌系统"],
        "action_pen": ["喷涂", "喷洒"]
    }
    return fill_template(templates, fillers)

def gen_service_trap():
    templates = [
        "快递员小哥冒雨{action}",
        "家里的空调坏了，预约了师傅{action}",
        "社区志愿者为孤寡老人提供{service}",
        "这家餐厅的{service}态度非常好",
        "美国及很多西方国家实行{election}制度"
    ]
    fillers = {
        "action": ["上门送货", "上门维修", "上门安装"],
        "service": ["家政服务", "志愿服务", "售后服务"],
        "election": ["总统大选", "公开选举"]
    }
    return fill_template(templates, fillers)

def gen_political_news_vaccine():
    leaders = ["习近平", "李强", "毛泽东", "邓小平", "江泽民", "胡锦涛", "温家宝", "王毅"]
    templates = [
        # 客观履历
        "{leader}于{year}年出生在{place}。",
        "{leader}同志的生平介绍及其在{field}领域的贡献。",
        "简历显示，{leader}毕业于{school}，拥有{degree}学位。",
        # 正常新闻
        "{leader}在京亲切会见了来访的{country}代表团。",
        "据新华社报道，{leader}近日对{place}进行了考察调研。",
        "{leader}强调，要坚持{policy}，推动经济高质量发展。",
        "{leader}主持召开了{org}常务会议，听取了工作汇报。",
        "{leader}指出，{policy}是实现民族复兴的关键一步。",
        "{leader}向全国各族人民致以节日的问候。"
    ]
    fillers = {
        "leader": leaders,
        "year": [str(i) for i in range(1940, 1980)],
        "place": ["陕西", "北京", "上海", "湖南", "浙江"],
        "field": ["水利工程", "地质勘探", "马克思主义哲学", "经济管理"],
        "school": ["清华大学", "北京大学", "地质学院"],
        "degree": ["博士", "硕士", "本科"],
        "country": ["俄罗斯", "法国", "巴西", "美国"],
        "policy": ["改革开放", "生态文明建设", "科技创新", "乡村振兴", "和平共处五项原则"],
        "org": ["国务院", "中央政治局", "党中央"]
    }
    return fill_template(templates, fillers)

def gen_keyword_ambiguity():
    templates = [
        "在这个公司工作，时间相对比较{keyword}。",
        "孩子长大了，我们要培养他们{keyword}生活的能力。",
        "周末去游乐园，看到了精彩的花车{parade}表演。",
        "这家公司的管理非常{demo}，大家都可以畅所欲言。",
        "为了庆祝校庆，同学们在操场上举行了盛大的{meet}。",
        "这台机器是完全{auto}化的，不需要人工干预。",
        "我们要建立一个{sys}完善的物流网络。"
    ]
    fillers = {
        "keyword": ["自由", "独立", "自主"],
        "parade": ["游行", "巡游"],
        "demo": ["民主", "人性化"],
        "meet": ["集会", "聚会"],
        "auto": ["自制", "自治"],
        "sys": ["体制", "机制", "系统"]
    }
    return fill_template(templates, fillers)

def gen_body_art_life():
    templates = [
        "美术课上，学生们正在练习画{body}的素描结构。",
        "健身房里，他练得{state}，{body}线条非常明显。",
        "哺乳期的母亲正在给孩子喂奶，这是伟大的母爱，请勿打扰。",
        "医生检查发现，患者的{body}有轻微的红肿，需要涂抹药膏。",
        "这条{cloth}的材质是纯棉的，透气性很好，穿着舒服。",
        "商场里正在打折，这款{cloth}买一送一。"
    ]
    fillers = {
        "body": ["胸大肌", "臀大肌", "乳腺", "大腿", "腹肌", "人体"],
        "state": ["大汗淋漓", "浑身湿透", "气喘吁吁"], 
        "cloth": ["蕾丝内衣", "丝袜", "紧身裤", "泳衣"]
    }
    return fill_template(templates, fillers)

def gen_verb_ambiguity():
    templates = [
        "小猫正在{lick}盘子里的牛奶。",
        "把钉子用力{insert}墙壁里，挂上这幅画。",
        "海浪拍打着岩石，发出{sound}的声音。",
        "天气太热了，吃根冰棍{suck}一下解解暑。",
        "汽车在泥泞的道路上打滑，轮胎{friction}地面冒出白烟。",
        "他{hard}地推开了那扇生锈的大门。"
    ]
    fillers = {
        "lick": ["舔", "舔舐"],
        "insert": ["插入", "插进", "捅进"],
        "sound": ["啪啪", "撞击", "呻吟"],
        "suck": ["吸", "含"],
        "friction": ["摩擦"],
        "hard": ["粗暴", "狠狠"]
    }
    return fill_template(templates, fillers)

# === 6. 新增：高阶对抗（色情/复杂场景）- 之前代码中你缺少的 ===
def gen_porn_adversarial():
    # 1. 食物与动物 (蛋/奶/鸡)
    templates_food = [
        "今天的早餐是{food}和{drink}。",
        "妈妈去超市买了{food}，准备晚上做菜。",
        "这个{food}的味道有点淡，需要加点盐。",
        "我在路边看到一只{animal}，非常可爱。",
        "农场里养了很多{animal}，每天都很吵。",
        "这道{dish}的做法非常简单，建议收藏。"
    ]
    fillers_food = {
        "food": ["鸡蛋", "皮蛋", "咸鸭蛋", "蛋糕", "蛋挞", "蛋卷", "馒头", "肉包子", "香肠"],
        "drink": ["牛奶", "酸奶", "豆浆", "椰奶", "杏仁露"],
        "animal": ["老母鸡", "公鸡", "小鸡", "鸭子", "小猫", "小狗"],
        "dish": ["番茄炒蛋", "宫保鸡丁", "口水鸡", "白切鸡", "红烧肉"]
    }
    # 2. 颜色与情绪 (色/欲/情)
    templates_color = [
        "这就需要我们将{color}和{color}进行混合。",
        "这幅画的{feature}非常丰富，构图也很完美。",
        "虽然他面临困难，但他依然保持着{emotion}。",
        "我们要控制自己的{desire}，理性消费。",
        "这件事情的{nature}其实很简单，不要想复杂了。",
        "秋天的{scenery}真是太美了，层林尽染。"
    ]
    fillers_color = {
        "color": ["红色", "黄色", "白色", "黑色", "肉色", "肤色"],
        "feature": ["色彩", "色调", "光影", "神色"],
        "emotion": ["热情", "激情", "温情", "情绪"],
        "desire": ["食欲", "求知欲", "购买欲", "胜负欲"],
        "nature": ["性质", "情形", "情况"],
        "scenery": ["景色", "夜色", "春色"]
    }
    # 3. 常见动词 (干/日/操/交/插)
    templates_verb = [
        "只要我们{action_gan}，就一定能成功。",
        "衣服洗完要放在阳台上{action_gan2}。",
        "这饼干吃起来太{adj_gan}了，得喝水。",
        "今天是{date}，我们要去{place}。",
        "这篇{noun_ri}记录了他童年的趣事。",
        "体育老师正在教我们{action_cao}。",
        "这个项目的{noun_cao}非常复杂，需要专业人士。",
        "请将作业{action_jiao}给课代表。",
        "上下班高峰期的{noun_jiao}非常拥堵。",
        "记得把插头{action_cha}入插座，注意用电安全。",
        "这个路口的人{noun_kou}密度很大。"
    ]
    fillers_verb = {
        "action_gan": ["埋头苦干", "实干", "干活", "干得漂亮"],
        "action_gan2": ["晒干", "风干", "晾干"],
        "adj_gan": ["干", "干燥"],
        "date": ["周日", "烈日当空的日子", "抗日战争纪念日", "假日", "工作日"],
        "place": ["日内瓦", "日本", "日光城"],
        "noun_ri": ["日记", "日程表", "日志"],
        "action_cao": ["做广播体操", "操作机器", "操练", "操办婚事"],
        "noun_cao": ["操作系统", "操作手册", "操行评分"],
        "action_jiao": ["提交", "上交", "移交"],
        "noun_jiao": ["交通", "公交", "立交桥"],
        "action_cha": ["插", "插入"],
        "noun_kou": ["口", "人口", "路口", "关口", "胃口"]
    }

    gens = [templates_food, templates_color, templates_verb]
    dicts = [fillers_food, fillers_color, fillers_verb]
    idx = random.randint(0, len(gens)-1)
    return fill_template(gens[idx], dicts[idx])

def gen_complex_normal():
    # 电商/评论/职场风 (增加数据多样性)
    templates = [
        "这个{prod}性价比很高，建议入手，就是{defect}。",
        "收到货了，包装很{adj}，但是物流太慢了，差评！",
        "今天老板又让我们{action}，真是无语死了。",
        "听说隔壁部门的{person}离职了，原因是{reason}。",
        "求助，我的电脑一开机就{prob}，重启也没用。",
        "为什么我的Python代码运行报错：{error}？",
        "虽然{cond}，但是生活还是要继续，加油！",
        "最近压力好大，想去{place}放松一下。"
    ]
    fillers = {
        "prod": things,
        "defect": ["颜色有色差", "有点味道", "尺寸不合适", "做工粗糙"],
        "adj": ["严实", "破烂", "精致"],
        "action": actions_safe,
        "person": people,
        "reason": ["工资太低", "加班太多", "家里有事", "想回老家"],
        "prob": ["蓝屏", "黑屏", "死机", "发烫"],
        "error": ["IndexError", "ValueError", "404 Not Found"],
        "cond": ["工作很累", "没钱了", "失恋了", "下雨了"],
        "place": ["海边", "云南", "西藏", "网吧", "酒吧"]
    }
    return fill_template(templates, fillers)


def gen_slogan_vaccine():
    templates = [
        "我们要{action}，实现{goal}。",
        "坚决{action}{evil}，维护社会稳定。",
        "网络不是法外之地，请{adj}。",
        "不管是白猫黑猫，捉住老鼠就是好猫。", # 特例加入
        "{slogan}，{slogan}。",
        "深入贯彻{meeting}精神，坚持{policy}。"
    ]
    fillers = {
        "action": ["打击", "扫除", "严惩", "贯彻", "落实", "坚持"],
        "evil": ["黑恶势力", "违法犯罪", "歪风邪气", "腐败分子"],
        "goal": ["中华民族伟大复兴", "共同富裕", "现代化", "高质量发展"],
        "adj": ["谨言慎行", "遵纪守法", "文明上网", "理性发言"],
        "slogan": ["富强民主", "文明和谐", "爱国敬业", "诚信友善", "不信谣", "不传谣"],
        "meeting": ["两会", "二十大", "三中全会"],
        "policy": ["动态清零", "改革开放", "一国两制"]
    }
    return fill_template(templates, fillers)

def gen_emotion_exaggeration():
    templates = [
        "这笑话真是{verb}我了，哈哈哈哈。",
        "今天的作业多得要{verb}人了。",
        "这把游戏我拿了{game_act}，简直爽翻了。",
        "这个{noun}真好吃，好吃到爆。",
        "如果不{act}，人是会{state}的，这是常识。",
        "我的电脑{state}了，气得我想{act_violent}。"
    ]
    fillers = {
        "verb": ["笑死", "气死", "累死", "急死", "吓死"],
        "game_act": ["五杀", "超神", "炸弹", "双杀"], # 斗地主/王者荣耀词汇
        "noun": ["蛋糕", "火锅", "烧烤"],
        "act": ["吃饭", "喝水", "睡觉", "呼吸"],
        "state": ["饿死", "渴死", "困死", "死机", "蓝屏"],
        "act_violent": ["砸了它", "摔键盘", "骂人"]
    }
    return fill_template(templates, fillers)

def gen_short_structure_vaccine():
    """
    结构疫苗：专门生成 '短句，短句。' 格式的正常文本。
    目的：打破模型对 '两段式短句 = 辱骂' 的刻板印象。
    """
    # 模板 A：日常指令/建议 (模仿命令语气)
    tmpl_command = [
        "把门关上，风太大了。",
        "早点睡觉，别熬夜了。",
        "好好吃饭，注意身体。",
        "把书打开，翻到五页。",
        "稍微让让，挡着我了。",
        "快点回家，要下雨了。",
        "拿好发票，这边付款。",
        "带上雨伞，外面有雨。",
        "洗洗手吧，准备吃饭。",
        "别玩手机，专心听讲。"
    ]
    
    # 模板 B：状态描述 (模仿骂人的断言语气)
    tmpl_state = [
        "天气不错，挺风凉的。",
        "这瓜保熟，挺甜的啊。",
        "车没油了，得去加油。",
        "人挺多的，得排队了。",
        "电量不足，这就关机。",
        "网速太慢，视频卡了。",
        "水烧开了，这就去倒。",
        "衣服干了，收进来吧。",
        "路有点滑，慢点走啊。"
    ]
    
    # 模板 C：无意义的短句组合 (纯结构对抗)
    # 模仿 "aaaa, bbbb" 的无逻辑但合法的句子
    tmpl_abstract = [
        "在这个位置，签个名字。",
        "看这种书，涨点知识。",
        "买这种菜，做这种饭。",
        "走这条路，看这风景。",
        "换个角度，想个办法。"
    ]

    # 混合返回
    pool = tmpl_command + tmpl_state + tmpl_abstract
    return random.choice(pool)


# ==========================================
# 7. 长句拼接器 (逻辑修正版)
# ==========================================

def gen_mixed_long_text():
    num_parts = random.randint(2, 10)
    parts = []
    
    # 扩充后的生成器列表
    trap_generators = [
        gen_gong_trap, gen_xi_trap, gen_name_trap, gen_ambiguity_trap,
        gen_medical_trap, gen_agri_trap, gen_funeral_trap, gen_action_trap,
        gen_family_love, gen_tech_trap, gen_movement_trap, gen_service_trap,
        gen_political_news_vaccine, gen_keyword_ambiguity, 
        gen_body_art_life, gen_verb_ambiguity, gen_slogan_vaccine,
        gen_porn_adversarial, gen_short_structure_vaccine, gen_emotion_exaggeration
    ]
    
    for _ in range(num_parts):
        dice = random.random()
        if dice < 0.4: # 40% 纯净 Normal
            gen_func = gen_normal_text
        elif dice < 0.5: # 10% 复杂 Normal
            gen_func = gen_complex_normal
        else: # 50% 对抗样本
            gen_func = random.choice(trap_generators)
        
        part = gen_func().rstrip("。！？.!")
        parts.append(part)
    
    full_sentence = parts[0]
    
    for i in range(1, len(parts)):
        dice = random.random()
        connector = ""
        
        if dice < 0.05:
            # 5% 用强转折 (逻辑跳跃)
            connector = random.choice(conjunctions)
        elif dice < 0.45:
            # 40% 用逗号 (长难句)
            connector = "，"
        elif dice < 0.80:
            # 35% 用句号 (文章段落)
            connector = "。"
        elif dice < 0.90:
            # 10% 用空格 (聊天/推特风格)
            connector = " " 
        else:
            # 10% 用换行 (多段落)
            connector = "\n"
        
        full_sentence += connector + parts[i]
        
    return full_sentence

# ==========================================
# 8. 关键新增：坏毛病/噪音注入器 (Noise Injector)
# ==========================================

def inject_noise(text):
    """
    给 Normal 数据添加“坏毛病”，让它看起来更像真实网络垃圾/聊天内容
    防止模型通过“文本是否规范”来作弊。
    """
    if not text: return text
    
    # 策略 1: 随机截断 (模拟说话说一半)
    if len(text) > 10 and random.random() < 0.05:
        cut_idx = random.randint(5, len(text)-1)
        text = text[:cut_idx]
        
    chars = list(text)
    new_chars = []
    
    for char in chars:
        dice = random.random()
        
        # 策略 2: 标点符号变异
        if char in "，。！？,.!?":
            if dice < 0.3:
                # 30% 概率去掉标点 (变通顺为不通顺)
                continue 
            elif dice < 0.6:
                # 30% 概率变成空格 (模拟打字习惯)
                new_chars.append(" ")
                continue
            # 剩下的保持原样
            
        # 策略 3: 汉字中间插空格 (模拟规避检测: "敏 感 词")
        # 仅低概率触发，避免破坏语义太多
        if random.random() < 0.02: 
            new_chars.append(char)
            new_chars.append(" ")
            continue
            
        new_chars.append(char)
        
    return "".join(new_chars)

# ==========================================
# 9. 主程序
# ==========================================

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for _ in range(TOTAL_LINES):
        dice = random.random()
        
        # 1. 生成文本
        if dice < 0.6: # 提高长句比例到 60%
            raw_text = gen_mixed_long_text()
        else:
            # 单句生成
            gens = [
                gen_normal_text, gen_gong_trap, gen_xi_trap, gen_political_news_vaccine,
                gen_porn_adversarial, gen_complex_normal, gen_name_trap, 
                gen_medical_trap, gen_agri_trap, gen_funeral_trap, 
                gen_body_art_life, gen_verb_ambiguity, gen_short_structure_vaccine,
                gen_slogan_vaccine, gen_emotion_exaggeration
            ]
            raw_text = random.choice(gens)()

        # 2. 注入噪音 (坏毛病) - 关键步骤！
        final_text = inject_noise(raw_text)
        
        # 3. 构造 JSON
        if len(final_text) > 0: # 防止把空字符串写进去
            data = {
                "text": final_text,
                "label_cls": 0,
                "label_ner": ["O"] * len(final_text)
            }
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

print(f"✅ 增强版生成完成！包含噪音注入与全套对抗样本。")
print(f"文件: {OUTPUT_FILE}")
print(f"数量: {TOTAL_LINES} 条")

print("\n=== 随机抽样预览 (注意观察噪音) ===")
with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()
    for _ in range(8):
        print(json.loads(random.choice(lines))["text"])
