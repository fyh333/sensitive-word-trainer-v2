# utils.py
import json
import glob
from torch.utils.data import Dataset
import torch

def load_data(file_pattern):
    """加载原始数据并构建标签映射"""
    all_data = []
    ner_tags = set(["O"])
    
    files = glob.glob(file_pattern, recursive=True)
    for f_path in files:
        with open(f_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    # 简单校验
                    if len(data['text']) == len(data['label_ner']):
                        all_data.append(data)
                        for t in data['label_ner']:
                            ner_tags.add(t)
                except:
                    continue
    
    # 排序保证ID固定
    ner_to_id = {tag: i for i, tag in enumerate(sorted(list(ner_tags)))}
    id_to_ner = {i: tag for tag, i in ner_to_id.items()}
    return all_data, ner_to_id, id_to_ner

def sliding_window_split(data_list, max_len=512, stride=400):
    """
    [核心函数] 将长文本切分为多个带有重叠的短文本
    """
    expanded_data = []
    # BERT 预留 [CLS] 和 [SEP]
    chunk_size = max_len - 2 
    
    for item in data_list:
        text = item['text']
        label_cls = item['label_cls']
        label_ner = item['label_ner']
        
        total_len = len(text)
        
        # 如果本来就短，直接加
        if total_len <= chunk_size:
            expanded_data.append(item)
            continue
            
        # 开始切片
        for start in range(0, total_len, stride):
            end = min(start + chunk_size, total_len)
            
            sub_text = text[start:end]
            sub_ner = label_ner[start:end]
            
            # 如果是最后一段且太短，且不是唯一一段，可以丢弃
            if len(sub_text) < 10 and start > 0:
                continue
                
            new_item = {
                'text': sub_text,
                'label_cls': label_cls, # 继承整句的分类标签
                'label_ner': sub_ner
            }
            expanded_data.append(new_item)
            
            if end == total_len:
                break
                
    return expanded_data

class SensitiveDataset(Dataset):
    def __init__(self, data, tokenizer, ner_to_id, max_len):
        self.data = data
        self.tokenizer = tokenizer
        self.ner_to_id = ner_to_id
        self.max_len = max_len

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        item = self.data[index]
        text_chars = list(item['text']) # 转为字符列表
        label_cls = int(item['label_cls'])
        label_ner_strs = item['label_ner']

        # 使用 is_split_into_words=True 确保字符级对齐
        inputs = self.tokenizer(
            text_chars,
            is_split_into_words=True,
            padding='max_length',
            truncation=True,
            max_length=self.max_len,
            return_tensors="pt"
        )

        input_ids = inputs['input_ids'].squeeze()
        mask = inputs['attention_mask'].squeeze()
        
        # NER 标签对齐：[CLS] -> -100, Char -> ID, [SEP] -> -100
        labels_ner = [-100] # [CLS]
        
        # word_ids 能够处理某些字符被 tokenizer 拆分的情况(虽然中文很少见)
        word_ids = inputs.word_ids(batch_index=0)
        
        for i in range(1, len(word_ids)):
            wid = word_ids[i]
            if wid is None: # [SEP] or [PAD]
                labels_ner.append(-100)
            else:
                if wid < len(label_ner_strs):
                    labels_ner.append(self.ner_to_id.get(label_ner_strs[wid], 0))
                else:
                    labels_ner.append(-100)
        
        # 强制截断/补齐到 max_len (防止由于 tokenizer 逻辑导致的微小长度差异)
        labels_ner = labels_ner[:self.max_len]
        while len(labels_ner) < self.max_len:
            labels_ner.append(-100)

        return {
            'input_ids': input_ids,
            'mask': mask,
            'label_cls': torch.tensor(label_cls, dtype=torch.long),
            'label_ner': torch.tensor(labels_ner, dtype=torch.long)
        }
