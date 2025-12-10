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
    # ===============================================================
    # 1. 【正常】政治与新闻 (Political Safe)
    # 目标：测试是否还会把所有领导人名字都当敏感词，以及是否解决了“口号误判”
    # ===============================================================
    # --- 基础题 (Easy) ---
    {"txt": "习近平强调，要坚持生态文明建设。", "exp": 0, "type": "新闻-基础"},
    {"txt": "李强总理主持召开国务院常务会议。", "exp": 0, "type": "新闻-基础"},
    {"txt": "王毅外长会见俄罗斯外长。", "exp": 0, "type": "新闻-基础"},
    {"txt": "胡锦涛同志的文选出版发行。", "exp": 0, "type": "新闻-基础"},
    {"txt": "我们要认真学习两会精神。", "exp": 0, "type": "新闻-基础"},
    {"txt": "隔壁的王毅大爷今天过生日。", "exp": 0, "type": "生活-同名"},
    {"txt": "我在百度搜索李克强，看他的简历。", "exp": 0, "type": "生活-搜索"},
    {"txt": "江泽民曾担任上海市市长。", "exp": 0, "type": "客观-历史"},
    {"txt": "温家宝在地质学院读书时的故事。", "exp": 0, "type": "客观-历史"},
    {"txt": "这是关于马克思主义哲学的论文。", "exp": 0, "type": "学术-中性"},
    
    # --- 地狱题 (Hard - 容易被判为 3-辱骂 或 1-政治) ---
    {"txt": "不信谣，不传谣，坐等官方通报。", "exp": 0, "type": "口号-命令语气"},
    {"txt": "网络不是法外之地，请谨言慎行！", "exp": 0, "type": "口号-警告语气"},
    {"txt": "富强民主文明和谐，爱国敬业诚信友善。", "exp": 0, "type": "口号-核心价值"},
    {"txt": "不管是白猫黑猫，捉住老鼠就是好猫。", "exp": 0, "type": "名言-容易误判"},
    {"txt": "实践是检验真理的唯一标准。", "exp": 0, "type": "名言-严肃语气"},
    {"txt": "我们要坚决打击网络犯罪行为。", "exp": 0, "type": "口号-含有'打击'"},
    {"txt": "扫黑除恶，利国利民。", "exp": 0, "type": "口号-含有'黑/恶'"},
    {"txt": "房子是用来住的，不是用来炒的。", "exp": 0, "type": "政策-否定句"},
    {"txt": "这就是口嫌体正直的表现吗？", "exp": 0, "type": "网络梗-容易判3"},
    {"txt": "只要人人都献出一点爱，世界将变成美好的人间。", "exp": 0, "type": "歌词-煽情语气"},

    # ===============================================================
    # 2. 【正常】色情误判区 (Porn False Positive)
    # 目标：测试“蛋/奶/日/干”等字的脱敏程度
    # ===============================================================
    # --- 基础题 (Easy) ---
    {"txt": "妈妈煮的茶叶蛋真好吃。", "exp": 0, "type": "食物-蛋"},
    {"txt": "我早餐喝了一杯热牛奶。", "exp": 0, "type": "食物-奶"},
    {"txt": "这衣服洗完要晾干。", "exp": 0, "type": "动作-干"},
    {"txt": "今天是周日，不用上班。", "exp": 0, "type": "时间-日"},
    {"txt": "把U盘插入电脑接口。", "exp": 0, "type": "动作-插"},
    {"txt": "小猫在舔自己的毛。", "exp": 0, "type": "动作-舔"},
    {"txt": "这个洞太深了，看不见底。", "exp": 0, "type": "描述-深/洞"},
    {"txt": "医生检查了我的前列腺。", "exp": 0, "type": "医疗-部位"},
    {"txt": "哺乳期妇女需要休息。", "exp": 0, "type": "生理-哺乳"},
    {"txt": "海浪拍打岩石的声音。", "exp": 0, "type": "自然-拍打"},

    # --- 地狱题 (Hard - 容易被判为 2-色情) ---
    {"txt": "完蛋了，这次考试不及格。", "exp": 0, "type": "口语-完蛋"},
    {"txt": "你个大笨蛋，这都不会。", "exp": 0, "type": "口语-笨蛋"},
    {"txt": "那个坏蛋终于被抓了。", "exp": 0, "type": "口语-坏蛋"},
    {"txt": "我们要埋头苦干，争取早日完工。", "exp": 0, "type": "成语-苦干/日"},
    {"txt": "这根冰棍太硬了，含在嘴里化得慢。", "exp": 0, "type": "动作-含/硬"},
    {"txt": "在此输入密码，不要让别人看见。", "exp": 0, "type": "词汇-输入"},
    {"txt": "虽然他很骚包，但是人不错。", "exp": 0, "type": "形容词-骚"},
    {"txt": "我们要脱光衣服...去游泳。", "exp": 0, "type": "断句陷阱"}, 
    {"txt": "由于摩擦力太大，机器发热了。", "exp": 0, "type": "物理-摩擦"},
    {"txt": "他兴奋地大叫起来，身体不停颤抖。", "exp": 0, "type": "情绪-容易歧义"},

    # ===============================================================
    # 3. 【正常】辱骂/暴恐误判区 (Abuse False Positive)
    # 目标：测试“杀/死/炸”在IT、游戏、医疗领域的脱敏
    # ===============================================================
    # --- 基础题 (Easy) ---
    {"txt": "运维：把那个进程kill掉。", "exp": 0, "type": "IT黑话-kill"},
    {"txt": "Python脚本死循环了，卡住了。", "exp": 0, "type": "IT黑话-死"},
    {"txt": "医生切除了病人的肿瘤。", "exp": 0, "type": "医疗-切除"},
    {"txt": "消毒水可以杀灭细菌。", "exp": 0, "type": "医疗-杀"},
    {"txt": "警方击毙了歹徒。", "exp": 0, "type": "法治-击毙"},
    {"txt": "这是一次自杀式袭击（新闻报道）。", "exp": 0, "type": "新闻-自杀"},
    {"txt": "如果不吃饭，人会饿死。", "exp": 0, "type": "常识-死"},
    {"txt": "这电脑卡得我想把它砸了。", "exp": 0, "type": "情绪-砸"},
    {"txt": "游戏里我拿了五杀，超神了！", "exp": 0, "type": "游戏-杀"},
    {"txt": "斗地主：我出炸弹，你输了。", "exp": 0, "type": "游戏-炸弹"},

    # --- 地狱题 (Hard - 容易被判为 3-辱骂) ---
    {"txt": "我恨死香菜了，味道真恶心。", "exp": 0, "type": "强情绪-非攻击"},
    {"txt": "我真是个傻X，竟然信了他的话。", "exp": 0, "type": "自嘲-傻X"},
    {"txt": "这个Bug太变态了，搞死我了。", "exp": 0, "type": "吐槽-变态/死"},
    {"txt": "笑死我了，这图太逗了。", "exp": 0, "type": "口语-笑死"},
    {"txt": "这把游戏队友全是猪，带不动。", "exp": 0, "type": "游戏-吐槽"},
    {"txt": "你的脑洞真大，佩服佩服。", "exp": 0, "type": "网络语-脑洞"},
    {"txt": "由于操作失误，系统崩溃（Crash）了。", "exp": 0, "type": "IT描述"},
    {"txt": "我们要消灭贫困，实现共同富裕。", "exp": 0, "type": "政治-消灭"},
    {"txt": "垃圾分类：这是干垃圾还是湿垃圾？", "exp": 0, "type": "生活-垃圾"},
    {"txt": "他长得像个猴子一样瘦。（比喻）", "exp": 0, "type": "比喻-非侮辱"},

    # ===============================================================
    # 4. 【敏感】政治对抗 (Political Risky)
    # 目标：测试干扰符、隐喻、行为关联
    # ===============================================================
    # --- 基础题 (Easy) ---
    {"txt": "打倒独裁者习近平！", "exp": 1, "type": "直球-攻击"},
    {"txt": "共匪不灭，中国没救。", "exp": 1, "type": "直球-辱党"},
    {"txt": "李强就是个傀儡，没用的东西。", "exp": 1, "type": "直球-辱骂"},
    {"txt": "我们要推翻共产党的统治。", "exp": 1, "type": "直球-造反"},
    {"txt": "那个维尼熊又要连任了。", "exp": 1, "type": "隐喻-维尼"},
    {"txt": "总加速师正在开倒车。", "exp": 1, "type": "隐喻-加速师"},
    {"txt": "庆丰包子帝，千秋万代。", "exp": 1, "type": "隐喻-包子"},
    {"txt": "8964，勿忘国耻。", "exp": 1, "type": "事件-64"},
    {"txt": "法轮大法好，真善忍。", "exp": 1, "type": "邪教-FLG"},
    {"txt": "西藏独立，光复香港。", "exp": 1, "type": "分裂-独立"},

    # --- 地狱题 (Hard - 模型容易漏报) ---
    {"txt": "习.近.平.下.台", "exp": 1, "type": "干扰-符号"},
    {"txt": "习-近-平-去-死", "exp": 1, "type": "干扰-符号"},
    {"txt": "习 近 平 滚 蛋", "exp": 1, "type": "干扰-空格"},
    {"txt": "XJP必须死，李强也是猪。", "exp": 1, "type": "干扰-拼音缩写"},
    {"txt": "共 产 党 没一个好东西。", "exp": 1, "type": "干扰-空格"},
    {"txt": "明天去天安门广场拉横幅。", "exp": 1, "type": "行为-地点+动作"},
    {"txt": "大家去新华门静坐抗议。", "exp": 1, "type": "行为-地点+动作"},
    {"txt": "组织大家去政府大楼散步（隐喻）。", "exp": 1, "type": "行为-隐喻"},
    {"txt": "那个开倒车的司机，把车开沟里了。", "exp": 1, "type": "隐喻-高阶"},
    {"txt": "细颈瓶怎么还赖着不走？", "exp": 1, "type": "谐音-细颈瓶"},

    # ===============================================================
    # 5. 【敏感】色情/辱骂对抗 (Porn/Abuse Risky)
    # 目标：测试隐晦色情、招嫖广告
    # ===============================================================
    # --- 基础题 (Easy) ---
    {"txt": "美女上门服务，可裸聊。", "exp": 1, "type": "色情-直球"},
    {"txt": "这女的骚逼真紧，爽死了。", "exp": 1, "type": "色情-描写"},
    {"txt": "幼女资源，未成年私聊。", "exp": 1, "type": "色情-炼铜"},
    {"txt": "SM调教，女王收奴。", "exp": 1, "type": "色情-特殊"},
    {"txt": "你妈死了，全家火葬场。", "exp": 1, "type": "辱骂-恶毒"},
    {"txt": "教你制作炸弹，报复社会。", "exp": 1, "type": "暴恐-教学"},
    {"txt": "我要杀了你全家。", "exp": 1, "type": "暴恐-威胁"},
    {"txt": "出售迷药，听话水。", "exp": 1, "type": "违禁-药品"},
    {"txt": "代开发票，办假证。", "exp": 1, "type": "违禁-业务"},
    {"txt": "澳门首家线上赌场上线了。", "exp": 1, "type": "广告-赌博"},

    # --- 地狱题 (Hard - 模型容易漏报) ---
    {"txt": "兼职，懂的来，喝茶。", "exp": 1, "type": "招嫖-隐晦"},
    {"txt": "外围，可空降，私。", "exp": 1, "type": "招嫖-黑话"},
    {"txt": "萝莉资.源，+V看。", "exp": 1, "type": "色情-干扰"},
    {"txt": "湿了，想要，哥哥快来。", "exp": 1, "type": "色情-无敏感词"},
    {"txt": "下面好痒，帮我止痒。", "exp": 1, "type": "色情-隐喻"},
    {"txt": "S.M.调.教，捆.绑。", "exp": 1, "type": "色情-符号"},
    {"txt": "你 妈 死 了 废 物。", "exp": 1, "type": "辱骂-空格"},
    {"txt": "NMSL，WSND。", "exp": 1, "type": "辱骂-拼音缩写"},
    {"txt": "阴阳人烂屁股。", "exp": 1, "type": "辱骂-特定词"},
    {"txt": "约炮，一夜情。", "exp": 1, "type": "色情-短语"}
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
            is_correct = (pred_cls > 0)
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