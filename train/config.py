# config.py
import torch

class Config:
    def __init__(self):
        self.model_name = "bert-base-chinese"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # 路径配置
        self.train_files = "/home/fyh/python/sensitive-word-trainer-v2/**/*.jsonl" # 支持通配符
        self.save_model_path = "./sensitive_bert_slidewindow_v2.pth"
        self.save_map_path = "./ner_map.json"
        
        # 训练参数
        self.batch_size = 32
        self.lr = 3e-5
        self.epochs = 3
        self.max_len = 512       # BERT 模型硬限制
        
        # 滑动窗口关键参数
        self.slide_stride = 500  # 步幅：每次移动多少字 (重叠区域 = 512 - 400 = 112)
        self.min_chunk_len = 10  # 切分后如果片段太短则丢弃
        