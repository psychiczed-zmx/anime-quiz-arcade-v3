import json,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'data'/'quiz-bank.json'
d=json.loads(p.read_text(encoding='utf-8'))
errors=[]
questions=d.get('questions',[]);categories=d.get('quizzes',[])
ids=[q.get('id') for q in questions]
if len(ids)!=len(set(ids)):errors.append('重复题目 ID')
cids=[c.get('id') for c in categories]
if len(cids)!=len(set(cids)):errors.append('重复分类 ID')
byid={q.get('id'):q for q in questions}
valid=set(cids)
for c in categories:
    for qid in c.get('questionIds',[]):
        if qid not in byid:errors.append(f"分类 {c.get('title')} 引用了不存在的题目 {qid}")
    expected={q.get('id') for q in questions if q.get('categoryId')==c.get('id')}
    actual=set(c.get('questionIds',[]))
    if expected!=actual:errors.append(f"分类 {c.get('title')} 的 questionIds 与题目 categoryId 不一致")
for q in questions:
    if not q.get('question'):errors.append(f"题目 {q.get('id')} 内容为空")
    if q.get('categoryId') and q['categoryId'] not in valid:errors.append(f"题目 {q.get('id')} 分类不存在")
    if q.get('type') not in ['single','truefalse','fill','audio-choice','image-title','image-character']:errors.append(f"题目 {q.get('id')} 题型无效")
    if q.get('type') in ['single','audio-choice','image-title','image-character']:
        if len(q.get('options',[]))<2:errors.append(f"题目 {q.get('id')} 选项不足")
        if not isinstance(q.get('answer'),int) or not (0<=q['answer']<len(q.get('options',[]))):errors.append(f"题目 {q.get('id')} 答案索引无效")
if errors:
    print('\n'.join('ERROR: '+e for e in errors));sys.exit(1)
print(f"OK: {len(questions)} 道题，{len(categories)} 个动态分类；分类关系、题型和答案字段有效。")
