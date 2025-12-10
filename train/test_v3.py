import torch
import numpy as np
import time
import os
import sys

# 解决路径引用问题
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from train import SensitivePredictor
except ImportError:
    from .train import SensitivePredictor

# ==========================================
# 定义高难度测试集 (每组约20条)
# Expect: 0 (Normal), 1 (Sensitive)
# ==========================================

TEST_CASES = [
    # ==============================================================================
    # 1. 正常文本 (Label 0) - 30条
    # 挑战点：包含敏感词(人名/死/杀/性/打击)，但语义必须是安全的
    # ==============================================================================
    
    # --- A. 政治脱敏 (人名/政策) ---
    {"txt": "习近平主席在新年贺词中向全国人民致以诚挚的问候。", "exp": 0, "type": "脱敏-人名"},
    {"txt": "李强总理主持召开国务院常务会议，研究经济工作。", "exp": 0, "type": "脱敏-人名"},
    {"txt": "王毅外长就国际局势发表了重要讲话。", "exp": 0, "type": "脱敏-人名"},
    {"txt": "我们要深入贯彻党的二十大精神，推动高质量发展。", "exp": 0, "type": "脱敏-党政"},
    {"txt": "坚决打击电信网络诈骗，守护人民财产安全。", "exp": 0, "type": "脱敏-口号(打击)"},
    {"txt": "扫黑除恶专项斗争取得了阶段性胜利。", "exp": 0, "type": "脱敏-口号(黑恶)"},
    {"txt": "网络不是法外之地，请广大网民遵纪守法。", "exp": 0, "type": "脱敏-口号(警告)"},
    {"txt": "不管白猫黑猫，捉住老鼠就是好猫。", "exp": 0, "type": "脱敏-名言"},
    
    # --- B. 情绪与生活 (死/杀/炸) ---
    {"txt": "笑死我了，这个段子简直神了。", "exp": 0, "type": "生活-情绪(死)"},
    {"txt": "今天忙得要死，连口水都没喝。", "exp": 0, "type": "生活-情绪(死)"},
    {"txt": "如果不吃饭，人是会饿死的，这是常识。", "exp": 0, "type": "生活-常识(死)"},
    {"txt": "医生切除了病人体内的恶性肿瘤。", "exp": 0, "type": "医疗-切除/肿瘤"},
    {"txt": "消毒液可以有效杀灭细菌和病毒。", "exp": 0, "type": "科普-杀灭"},
    {"txt": "这电脑卡死了，进程怎么都kill不掉。", "exp": 0, "type": "IT-Kill/死"},
    {"txt": "斗地主：我出炸弹，四个二带两王！", "exp": 0, "type": "游戏-炸弹"},
    {"txt": "王者荣耀：我拿了五杀，队友都在喊666。", "exp": 0, "type": "游戏-杀"},
    {"txt": "这道菜辣得变态，但是我超级爱吃。", "exp": 0, "type": "生活-变态"},
    
    # --- C. 生理与歧义 (性/身体) ---
    {"txt": "哺乳期的妈妈非常辛苦，需要补充营养。", "exp": 0, "type": "生理-哺乳"},
    {"txt": "医生检查了我的乳腺，说是小叶增生。", "exp": 0, "type": "医疗-敏感部位"},
    {"txt": "把U盘插入USB接口时要轻轻用力。", "exp": 0, "type": "动作-插入"},
    {"txt": "小猫正在舔盘子里的牛奶，好可爱。", "exp": 0, "type": "动作-舔"},
    {"txt": "天气太热了，买根冰棍含在嘴里解暑。", "exp": 0, "type": "动作-含"},
    {"txt": "轮胎与地面剧烈摩擦，发出了刺耳的声音。", "exp": 0, "type": "物理-摩擦"},
    {"txt": "这件衣服是纯棉的，吸汗透气，穿着舒服。", "exp": 0, "type": "生活-衣物"},
    
    # --- D. 其他干扰 ---
    {"txt": "那个坏蛋终于被警察抓住了。", "exp": 0, "type": "口语-坏蛋"},
    {"txt": "我是个傻瓜，竟然忘了带钥匙。", "exp": 0, "type": "自嘲-傻瓜"},
    {"txt": "这只是个由头，其中的逻辑很复杂。", "exp": 0, "type": "逻辑-其中"},
    {"txt": "我们要建立一个独立自主的工业体系。", "exp": 0, "type": "政治-独立(正向)"},
    {"txt": "大家去广场上放风筝，散步，晒太阳。", "exp": 0, "type": "生活-广场/散步"},

    # ==============================================================================
    # 2. 政治敏感 (Label 1) - 30条
    # 挑战点：隐喻、黑话、历史事件、分裂言论
    # ==============================================================================
    
    # --- A. 直球攻击 ---
    {"txt": "强烈要求习近平下台，结束独裁统治。", "exp": 1, "type": "直球-下台"},
    {"txt": "共产党不灭，灾难不止，天灭中共。", "exp": 1, "type": "直球-灭党"},
    {"txt": "打倒共匪，还我河山。", "exp": 1, "type": "直球-口号"},
    {"txt": "李强就是个傀儡，毫无实权。", "exp": 1, "type": "直球-辱骂高官"},
    {"txt": "那头猪还在上面赖着不走，真不要脸。", "exp": 1, "type": "直球-辱骂"},
    {"txt": "我们要推翻中国共产党的极权统治。", "exp": 1, "type": "直球-推翻"},
    
    # --- B. 隐喻与黑话 (加速/倒车/包子) ---
    {"txt": "总加速师一脚油门踩到底，大家准备跳车。", "exp": 1, "type": "隐喻-加速师"},
    {"txt": "倒车请注意，倒车请注意，维尼司机正在驾驶。", "exp": 1, "type": "隐喻-倒车/维尼"},
    {"txt": "庆丰帝登基了，吾皇万岁万万岁。", "exp": 1, "type": "隐喻-庆丰/登基"},
    {"txt": "包子露宪了，这下要终身制了。", "exp": 1, "type": "隐喻-包子/修宪"},
    {"txt": "那个扛麦郎，两百斤不换肩，真能吹。", "exp": 1, "type": "隐喻-扛麦郎"},
    {"txt": "细颈瓶里的水倒不出来，得打破它。", "exp": 1, "type": "谐音-细颈瓶"},
    {"txt": "通商宽衣，萨格尔王，没文化真可怕。", "exp": 1, "type": "梗-宽衣"},
    {"txt": "在那位一尊的指挥下，我们要走向深渊了。", "exp": 1, "type": "隐喻-一尊"},
    {"txt": "我那时候啊，挑两百斤麦子走十里山路不换肩的。", "exp": 1, "type": "隐喻-名言"},
    
    # --- C. 事件与分裂 ---
    {"txt": "勿忘8964，坦克压过天安门。", "exp": 1, "type": "事件-64"},
    {"txt": "支持香港独立，光复香港，时代革命。", "exp": 1, "type": "分裂-港独"},
    {"txt": "台湾是一个主权独立的国家，不是中国的一部分。", "exp": 1, "type": "分裂-台独"},
    {"txt": "东突厥斯坦万岁，我们要自由。", "exp": 1, "type": "分裂-疆独"},
    {"txt": "白纸运动，不自由毋宁死。", "exp": 1, "type": "事件-白纸"},
    {"txt": "四通桥上的勇士，我们怀念你。", "exp": 1, "type": "事件-四通桥"},
    {"txt": "大纪元时报揭露了活摘器官的真相。", "exp": 1, "type": "邪教-轮媒"},
    {"txt": "法轮大法好，真善忍。", "exp": 1, "type": "邪教-FLG"},
    
    # --- D. 阴阳怪气与干扰 ---
    {"txt": "感恩党，感恩政府，把我们变成了最后一代。", "exp": 1, "type": "阴阳-最后一代"},
    {"txt": "这就叫全过程民主，笑话一样的选举。", "exp": 1, "type": "讽刺-民主"},
    {"txt": "X.J.P 必须谢罪。", "exp": 1, "type": "干扰-符号"},
    {"txt": "习 近 平 滚 蛋。", "exp": 1, "type": "干扰-空格"},
    {"txt": "共*产*党 没一个好东西。", "exp": 1, "type": "干扰-星号"},
    {"txt": "CCP virus is spreading.", "exp": 1, "type": "外语-CCP"},

    # ==============================================================================
    # 3. 色情文本 (Label 2) - 30条
    # 挑战点：黑话、软色情、广告、器官描写
    # ==============================================================================
    
    # --- A. 招嫖与广告 ---
    {"txt": "同城上门服务，懂的加V。", "exp": 2, "type": "招嫖-通用"},
    {"txt": "新茶上市，外围模特，可空降。", "exp": 2, "type": "招嫖-黑话"},
    {"txt": "附近可约，学生妹兼职，私聊看照。", "exp": 2, "type": "招嫖-学生"},
    {"txt": "酒店按摩，特殊服务，包你满意。", "exp": 2, "type": "招嫖-特殊"},
    {"txt": "少妇重金求子，见面付定金。", "exp": 2, "type": "诈骗-色情诱导"},
    {"txt": "高端商务伴游，陪吃陪睡。", "exp": 2, "type": "招嫖-伴游"},
    {"txt": "哥哥来喝茶吗？刚到的嫩妹。", "exp": 2, "type": "招嫖-喝茶"},
    
    # --- B. 露骨描写与行为 ---
    {"txt": "她的乳房饱满坚挺，让人忍不住想摸。", "exp": 2, "type": "描写-器官"},
    {"txt": "湿了，好想要，快点插进来。", "exp": 2, "type": "描写-行为"},
    {"txt": "粉嫩的鲍鱼，水多活好。", "exp": 2, "type": "描写-黑话"},
    {"txt": "巨大的肉棒狠狠地捣进深处。", "exp": 2, "type": "描写-性交"},
    {"txt": "丝袜足交，口爆内射，全套服务。", "exp": 2, "type": "行为-列表"},
    {"txt": "两个人赤裸着身体纠缠在一起，呻吟声不断。", "exp": 2, "type": "描写-场景"},
    {"txt": "下面好痒，哥哥帮我止痒嘛。", "exp": 2, "type": "挑逗-隐喻"},
    
    # --- C. 资源与网恋 ---
    {"txt": "裸聊+Q，在线视频。", "exp": 2, "type": "网色-裸聊"},
    {"txt": "出售原味内裤，没洗过的。", "exp": 2, "type": "变态-原味"},
    {"txt": "幼女资源，萝莉小视频，未成年。", "exp": 2, "type": "炼铜"},
    {"txt": "偷拍美女洗澡，走光合集。", "exp": 2, "type": "偷拍"},
    {"txt": "AV女优合集下载，步兵无码。", "exp": 2, "type": "资源"},
    {"txt": "文爱，磕炮，连麦睡觉。", "exp": 2, "type": "网色-文爱"},
    {"txt": "S.M 调教，女王收奴。", "exp": 2, "type": "特殊-SM"},
    
    # --- D. 干扰与符号 ---
    {"txt": "约.炮 一.夜.情。", "exp": 2, "type": "干扰-符号"},
    {"txt": "看 逼 视 频 + V。", "exp": 2, "type": "干扰-空格"},
    {"txt": "sao货，欠操。", "exp": 2, "type": "拼音-辱骂色情"},
    {"txt": "3p，群交，换妻。", "exp": 2, "type": "短语"},
    {"txt": "迷奸药，听话水，出售。", "exp": 2, "type": "违禁-性药"}, # 有时也归类为违禁，这里暂归色情场景
    {"txt": "私处粉嫩，紧致包夜。", "exp": 2, "type": "描写-服务"},

    # ==============================================================================
    # 4. 辱骂/暴恐 (Label 3) - 30条
    # 挑战点：脏话、人身攻击、威胁、违禁品
    # ==============================================================================
    
    # --- A. 直接辱骂 ---
    {"txt": "你是傻逼吗？这都听不懂。", "exp": 3, "type": "辱骂-SB"},
    {"txt": "NMSL，你妈死了。", "exp": 3, "type": "辱骂-缩写"},
    {"txt": "操你妈，滚远点。", "exp": 3, "type": "辱骂-脏话"},
    {"txt": "废物东西，活着也是浪费空气。", "exp": 3, "type": "辱骂-贬低"},
    {"txt": "你全家都炸了，户口本只有一页。", "exp": 3, "type": "辱骂-诅咒"},
    {"txt": "真是个脑残，建议去医院看看脑子。", "exp": 3, "type": "辱骂-脑残"},
    {"txt": "贱人，婊子，烂货。", "exp": 3, "type": "辱骂-女性"},
    {"txt": "狗杂种，有人生没人养。", "exp": 3, "type": "辱骂-恶毒"},
    
    # --- B. 威胁与暴力 ---
    {"txt": "我要杀了你，把你碎尸万段。", "exp": 3, "type": "威胁-杀人"},
    {"txt": "信不信我弄死你全家？", "exp": 3, "type": "威胁-全家"},
    {"txt": "今晚别睡太死，小心房子着火。", "exp": 3, "type": "威胁-隐晦"},
    {"txt": "砍死你，把你手脚剁下来。", "exp": 3, "type": "暴力-描述"},
    {"txt": "去死吧，赶紧跳楼去。", "exp": 3, "type": "教唆-自杀"},
    {"txt": "我要报复社会，炸了学校。", "exp": 3, "type": "暴恐-反社会"},
    
    # --- C. 歧视与攻击 ---
    {"txt": "死同性恋，真恶心，变态。", "exp": 3, "type": "歧视-LGBT"},
    {"txt": "河南人都偷井盖，垃圾。", "exp": 3, "type": "歧视-地域"}, # 示例，无意冒犯
    {"txt": "黑鬼滚出中国。", "exp": 3, "type": "歧视-种族"},
    {"txt": "你是孤儿吗？没教养。", "exp": 3, "type": "辱骂-孤儿"},
    
    # --- D. 违禁与黑产 (通常归为Abuse或Risk) ---
    {"txt": "出售迷药，三唑仑，昏迷水。", "exp": 3, "type": "违禁-药品"},
    {"txt": "代开发票，保真，点数低。", "exp": 3, "type": "黑产-发票"},
    {"txt": "办假证，大学毕业证，英语四级。", "exp": 3, "type": "黑产-办证"},
    {"txt": "专业收债，不还钱就断手断脚。", "exp": 3, "type": "黑产-暴力催收"},
    {"txt": "出售手枪，子弹，联系飞机号。", "exp": 3, "type": "违禁-军火"},
    {"txt": "教你制作C4炸弹，教程私聊。", "exp": 3, "type": "暴恐-教学"},
    
    # --- E. 干扰与变体 ---
    {"txt": "你 妈 炸 了。", "exp": 3, "type": "干扰-空格"},
    {"txt": "萨比，脑潭，智张。", "exp": 3, "type": "谐音-辱骂"},
    {"txt": "WSND，CNM。", "exp": 3, "type": "缩写-辱骂"},
    {"txt": "Fxxk you, piece of sh*t.", "exp": 3, "type": "外语-辱骂"},
    {"txt": "阴阳人烂屁股。", "exp": 3, "type": "网络梗-辱骂"},
    {"txt": "你长得真像车祸现场。", "exp": 3, "type": "隐喻-辱骂"}
]

# ==========================================
# 执行测试逻辑
# ==========================================
def run_stress_test():
    print("😈 Loading Model for STRESS Test V2...")
    # 使用 GPU 如果可用
    predictor = SensitivePredictor()
    
    print(f"\n🔥 Start Torture V2! Total Cases: {len(TEST_CASES)}")
    
    # 打印表头
    header = f"{'Text (Snippet)':<25} | {'Type':<12} | {'Exp':<3} | {'Pred':<4} | {'Entities':<30} | {'Res'}"
    print("-" * len(header))
    print(header)
    print("-" * len(header))
    
    passed = 0
    failed_cases = []
    category_stats = {"safe": {"total": 0, "pass": 0}, "risky": {"total": 0, "pass": 0}}
    
    start_time = time.time()
    
    for i, case in enumerate(TEST_CASES):
        text = case['txt']
        exp = case['exp']
        
        # 推理
        res = predictor.predict(text)
        pred_cls = res['class']
        entities = res['entities']
        
        # 判定逻辑
        if exp == 0:
            is_correct = (pred_cls == 0)
            cat = "safe"
        else:
            is_correct = (pred_cls == exp)
            cat = "risky"
            
        # 统计
        category_stats[cat]["total"] += 1
        if is_correct:
            passed += 1
            category_stats[cat]["pass"] += 1
            status = "✅"
        else:
            status = "❌"
            failed_cases.append({**case, "pred": pred_cls, "ents": entities})
            
        # 打印
        display_text = (text[:23] + "..") if len(text) > 25 else text
        pred_str = str(pred_cls) if pred_cls != 0 else "0"
        ent_str = str(entities)
        if len(ent_str) > 30: ent_str = ent_str + ".."
        
        print(f"{display_text:<25} | {case['type']:<12} | {exp:<3} | {pred_str:<4} | {ent_str:<30} | {status}")

    # 总结报告
    duration = time.time() - start_time
    total = len(TEST_CASES)
    acc = passed / total * 100
    
    print("-" * len(header))
    print(f"\n📊 V2 Final Report:")
    print(f"Total: {total}, Passed: {passed}, Accuracy: {acc:.2f}%")
    print(f"Time: {duration:.2f}s")
    
    print(f"\n📈 Category Breakdown:")
    safe_acc = category_stats['safe']['pass'] / category_stats['safe']['total'] * 100
    risky_acc = category_stats['risky']['pass'] / category_stats['risky']['total'] * 100
    print(f"  - Safe Samples (Normal):  {safe_acc:.2f}% ({category_stats['safe']['pass']}/{category_stats['safe']['total']})")
    print(f"  - Risky Samples (Sens):   {risky_acc:.2f}% ({category_stats['risky']['pass']}/{category_stats['risky']['total']})")
    
    if failed_cases:
        print("\n💀 Failed Cases Analysis:")
        for fc in failed_cases:
            print(f"- [{fc['type']}] Exp:{fc['exp']} | Pred:{fc['pred']}")
            print(f"  Txt: {fc['txt']}")
            print(f"  Ent: {fc['ents']}")
            print("-" * 30)

if __name__ == "__main__":
    run_stress_test()