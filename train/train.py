# main.py
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from transformers import BertModel, BertTokenizerFast 
from torch.optim import AdamW
from sklearn.model_selection import train_test_split
import json
import numpy as np
from tqdm import tqdm

from config import Config
from utils import load_data, sliding_window_split, SensitiveDataset

# ================== 模型定义 ==================
class MultiTaskBert(nn.Module):
    def __init__(self, model_name, num_cls_labels, num_ner_labels):
        super().__init__()
        self.bert = BertModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(0.3)
        # 任务1：整句分类
        self.cls_head = nn.Linear(768, num_cls_labels)
        # 任务2：NER
        self.ner_head = nn.Linear(768, num_ner_labels)

    def forward(self, input_ids, mask):
        out = self.bert(input_ids=input_ids, attention_mask=mask)
        # Pooler Output 用于分类
        cls_out = self.cls_head(self.dropout(out.pooler_output))
        # Sequence Output 用于 NER
        ner_out = self.ner_head(self.dropout(out.last_hidden_state))
        return cls_out, ner_out

# ================== 训练流程 ==================
def train_model():
    cfg = Config()
    print(f"Loading data from {cfg.train_files}...")
    
    # 1. 加载并切分数据
    raw_data, ner_to_id, id_to_ner = load_data(cfg.train_files)
    print(f"Original samples: {len(raw_data)}")
    
    # *** 关键步骤：滑动窗口扩充数据 ***
    train_stride = cfg.max_len
    train_data = sliding_window_split(raw_data, max_len=cfg.max_len, stride=train_stride)
    print(f"Augmented samples (after sliding window): {len(train_data)}")
    
    # 保存映射表供推理使用
    with open(cfg.save_map_path, 'w') as f:
        json.dump(ner_to_id, f)

    tokenizer = BertTokenizerFast.from_pretrained(cfg.model_name)
    dataset = SensitiveDataset(train_data, tokenizer, ner_to_id, cfg.max_len)
    dataloader = DataLoader(dataset, batch_size=cfg.batch_size, shuffle=True)
    
    model = MultiTaskBert(cfg.model_name, 4, len(ner_to_id)).to(cfg.device)
    if torch.cuda.device_count() > 1:
        print(f"Let's use {torch.cuda.device_count()} GPUs!")
        model = nn.DataParallel(model)

    optimizer = AdamW(model.parameters(), lr=cfg.lr)
    
    crit_cls = nn.CrossEntropyLoss()
    crit_ner = nn.CrossEntropyLoss(ignore_index=-100) # 忽略 padding
    
    print("Start Training...")
    model.train()

    for epoch in range(cfg.epochs):
        # --- 修改开始 ---
        # 使用 tqdm 创建进度条
        progress_bar = tqdm(dataloader, desc=f"Epoch {epoch+1}/{cfg.epochs}")
        total_loss = 0
        
        for i, batch in enumerate(progress_bar):
            b_ids = batch['input_ids'].to(cfg.device)
            b_mask = batch['mask'].to(cfg.device)
            b_cls = batch['label_cls'].to(cfg.device)
            b_ner = batch['label_ner'].to(cfg.device)
            
            optimizer.zero_grad()
            logits_cls, logits_ner = model(b_ids, b_mask)

            if i % 100 == 0:
                #以此判断模型是否在“瞎猜”
                pred_cls = torch.argmax(logits_cls, dim=1)[0]
                true_cls = b_cls[0]
                print(f"\n[Debug] Step {i}: True={true_cls.item()}, Pred={pred_cls.item()}")
            
            loss_cls = crit_cls(logits_cls, b_cls)
            loss_ner = crit_ner(logits_ner.view(-1, len(ner_to_id)), b_ner.view(-1))
            
            loss = loss_cls + loss_ner
            loss.backward()
            optimizer.step()
            
            current_loss = loss.item()
            total_loss += current_loss
            
            # 实时更新进度条上的 Loss 显示
            progress_bar.set_postfix({'loss': f"{current_loss:.4f}"})
        # --- 修改结束 ---
            
        avg_loss = total_loss / len(dataloader)
        print(f"Epoch {epoch+1} Finished. Average Loss: {avg_loss:.4f}")
        
    # 判断是否使用了 DataParallel
    if isinstance(model, nn.DataParallel):
        # 如果是多GPU，需要取 .module 才能拿到原始模型的参数
        torch.save(model.module.state_dict(), cfg.save_model_path)
    else:
        # 单GPU正常保存
        torch.save(model.state_dict(), cfg.save_model_path)
    
    print(f"Model saved to {cfg.save_model_path}")

# ================== 推理类 (支持超长文本) ==================
class SensitivePredictor:
    def __init__(self, device_id=None):
        self.cfg = Config()
        
        # 1. 决定使用哪个设备
        # 如果外部指定了 device_id (例如 0), 则使用 cuda:0
        # 否则使用 Config 里的配置，或者自动回退到 CPU
        if device_id is not None and torch.cuda.is_available():
            self.device = torch.device(f"cuda:{device_id}")
        else:
            # 自动检测：如果有卡就用卡，没卡用CPU
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            
        print(f"Loading model on: {self.device} ...")

        self.tokenizer = BertTokenizerFast.from_pretrained(self.cfg.model_name, local_files_only=True)
        
        # 加载映射
        with open(self.cfg.save_map_path, 'r') as f:
            self.ner_to_id = json.load(f)
        self.id_to_ner = {v: k for k, v in self.ner_to_id.items()}
        
        # 加载模型结构
        self.model = MultiTaskBert(self.cfg.model_name, 4, len(self.ner_to_id))
        
        # === 关键修改：map_location 解决卡顿 ===
        # 无论模型是在哪张卡上训练的，加载时都强制映射到当前指定的 self.device
        state_dict = torch.load(self.cfg.save_model_path, map_location=self.device)
        self.model.load_state_dict(state_dict)
        
        self.model.to(self.device)
        self.model.eval()
        print("Model loaded successfully!")

    def predict(self, long_text):
        # ... (predict 部分代码保持不变，注意下面的 device 也要改) ...
        # ...
        # 注意：原代码里可能有 b_ids = torch.cat(batch_ids).to(self.cfg.device)
        # 请全部改成 .to(self.device)
        # ...
        
        # 1. 切分
        chunks = []
        offsets = []
        chunk_len = self.cfg.max_len - 2
        
        if len(long_text) == 0: return {}
        
        for start in range(0, len(long_text), self.cfg.slide_stride):
            end = min(start + chunk_len, len(long_text))
            chunks.append(long_text[start:end])
            offsets.append(start)
            if end == len(long_text): break
            
        # 2. 批量推理
        batch_ids = []
        batch_masks = []
        for chunk in chunks:
            inp = self.tokenizer(list(chunk), is_split_into_words=True, 
                                 padding='max_length', truncation=True, 
                                 max_length=self.cfg.max_len, return_tensors="pt")
            batch_ids.append(inp['input_ids'])
            batch_masks.append(inp['attention_mask'])
        
        # === 修改点：使用 self.device 而不是 cfg.device ===
        b_ids = torch.cat(batch_ids).to(self.device)
        b_masks = torch.cat(batch_masks).to(self.device)
        
        with torch.no_grad():
            logits_cls, logits_ner = self.model(b_ids, b_masks)
            
        # ... (后续处理逻辑不变) ...
        # 3. 结果合并
        cls_preds = torch.argmax(logits_cls, dim=1).cpu().numpy()
        final_cls = int(np.max(cls_preds)) 
        
        full_tags = ["O"] * len(long_text)
        ner_preds = torch.argmax(logits_ner, dim=2).cpu().numpy()
        
        for i, pred_seq in enumerate(ner_preds):
            offset = offsets[i]
            valid_len = len(chunks[i])
            tags_idx = pred_seq[1 : 1 + valid_len]
            
            for j, tid in enumerate(tags_idx):
                tag = self.id_to_ner.get(tid, "O")
                if tag != "O":
                    full_tags[offset + j] = tag
                    
        return {
            "class": final_cls,
            "entities": self._extract_entities(long_text, full_tags)
        }

    def _extract_entities(self, text, tags):
        # ... (保持不变) ...
        res = []
        curr_word = ""
        curr_type = ""
        
        for char, tag in zip(text, tags):
            if tag.startswith("B-"):
                if curr_word: res.append((curr_word, curr_type))
                curr_word = char
                curr_type = tag.split("_")[1] if "_" in tag else tag
            elif tag.startswith("I-") and curr_word:
                curr_word += char
            else:
                if curr_word:
                    res.append((curr_word, curr_type))
                    curr_word = ""
                    curr_type = ""
        if curr_word: res.append((curr_word, curr_type))
        return res

if __name__ == "__main__":
    # 训练模式 (第一次运行取消注释)
    train_model()
    
    # 推理模式示例
    print("\n--- Testing Inference ---")
    predictor = SensitivePredictor()
    
    # 造一个超长文本: 前面正常，中间夹杂敏感词，后面正常
    test_text = "今天天气不错" * 50 + "必须打倒习近平和李强" + "我们去吃饭" * 100
    print(f"Test text length: {len(test_text)}")
    
    result = predictor.predict(test_text)
    print(f"Classification Result: {result['class']}")
    print(f"Detected Entities: {result['entities']}")
  