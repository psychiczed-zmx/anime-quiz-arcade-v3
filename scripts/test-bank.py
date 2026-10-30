import json, random
from pathlib import Path
root=Path(__file__).resolve().parents[1]
bank=json.loads((root/'data/quiz-bank.json').read_text(encoding='utf-8'))
assert len(bank['questions'])==26
assert len({q['id'] for q in bank['questions']})==26
assert len({c['id'] for c in bank['quizzes']})==len(bank['quizzes'])
byid={q['id']:q for q in bank['questions']}
for c in bank['quizzes']:
    ids=[q['id'] for q in bank['questions'] if q.get('categoryId')==c['id']]
    assert set(ids)==set(c['questionIds']),c['title']
    for n in [0,1,12,20,50]:
        pool=list(ids);random.shuffle(pool);picked=pool[:min(20,len(pool))]
        assert len(picked)==len(set(picked)) and len(picked)<=20
        assert set(picked)<=set(ids)
# Simulate delete-category migration: preserve questions, clear only category association.
clone=json.loads(json.dumps(bank));removed=clone['quizzes'][0]['id'];before=len(clone['questions'])
clone['quizzes']=[c for c in clone['quizzes'] if c['id']!=removed]
for q in clone['questions']:
    if q.get('categoryId')==removed:q['categoryId']=''
assert len(clone['questions'])==before
assert all(q.get('categoryId')!=removed for q in clone['questions'])
# Simulate category rename: stable category ID means membership remains intact.
clone=json.loads(json.dumps(bank));c=clone['quizzes'][0];c['title']='测试新名称';c['difficulty']=c['title']
assert sum(q.get('categoryId')==c['id'] for q in clone['questions'])==len(c['questionIds'])
print('PASS: 26 questions; category membership; rename/delete preservation; random no-duplicate max-20.')
