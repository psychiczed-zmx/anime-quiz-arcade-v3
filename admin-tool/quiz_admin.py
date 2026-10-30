# -*- coding: utf-8 -*-
"""Anime Arcade Quiz Admin — dynamic category edition."""
import json, os, shutil, sys, uuid, zipfile, re
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

TYPES = {'选择题':'single','判断题':'truefalse','填空题':'fill','听音频选择题':'audio-choice','看图猜番名':'image-title','看图猜角色':'image-character'}
TYPE_LABELS = {v:k for k,v in TYPES.items()}
PALETTE = {'bg':'#fbf8ff','surface':'#ffffff','ink':'#35254c','muted':'#8d819e','purple':'#8b68d8','lavender':'#f0eaff','pink':'#fceaf2','line':'#eadff4','deep':'#60449b'}

def default_root():
    here=Path(sys.executable if getattr(sys,'frozen',False) else __file__).resolve().parent
    for p in [here,*here.parents]:
        if (p/'data'/'quiz-bank.json').exists(): return p
    return Path.cwd()

def slug(text):
    stem=re.sub(r'[^a-zA-Z0-9]+','-',text.strip()).strip('-').lower() or 'category'
    return 'quiz-'+stem+'-'+uuid.uuid4().hex[:5]

class QuizAdmin(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('妄梦生 · 动漫题库工作台')
        self.geometry('1320x850'); self.minsize(1050,700); self.configure(bg=PALETTE['bg'])
        self.root_dir=default_root(); self.bank_path=self.root_dir/'data'/'quiz-bank.json'
        self.bank={'schemaVersion':2,'quizzes':[],'questions':[]}
        self.selected_question_id=None; self.selected_category_id=None
        self._style(); self._build_menu(); self._build_ui(); self.load_bank(self.bank_path)

    def _style(self):
        st=ttk.Style(self)
        try: st.theme_use('clam')
        except tk.TclError: pass
        st.configure('.',font=('Microsoft YaHei UI',10),background=PALETTE['bg'],foreground=PALETTE['ink'])
        st.configure('TFrame',background=PALETTE['bg'])
        st.configure('Card.TFrame',background=PALETTE['surface'],relief='flat')
        st.configure('TLabel',background=PALETTE['bg'],foreground=PALETTE['ink'])
        st.configure('Title.TLabel',font=('Microsoft YaHei UI',22,'bold'),foreground=PALETTE['deep'])
        st.configure('Sub.TLabel',font=('Microsoft YaHei UI',10),foreground=PALETTE['muted'])
        st.configure('TButton',padding=(12,8),font=('Microsoft YaHei UI',10,'bold'),background=PALETTE['lavender'])
        st.map('TButton',background=[('active','#e4d8fb')])
        st.configure('Accent.TButton',background=PALETTE['purple'],foreground='white')
        st.map('Accent.TButton',background=[('active','#7553c1')])
        st.configure('TNotebook',background=PALETTE['bg'],borderwidth=0)
        st.configure('TNotebook.Tab',padding=(20,11),font=('Microsoft YaHei UI',10,'bold'))
        st.configure('Treeview',rowheight=30,background='white',fieldbackground='white',font=('Microsoft YaHei UI',9))
        st.configure('Treeview.Heading',font=('Microsoft YaHei UI',9,'bold'),background=PALETTE['lavender'])
        self.option_add('*TCombobox*Listbox.font',('Microsoft YaHei UI',10))

    def _build_menu(self):
        menu=tk.Menu(self); fm=tk.Menu(menu,tearoff=0)
        fm.add_command(label='打开题库 JSON…',command=self.open_bank);fm.add_command(label='保存题库',command=self.save_bank)
        fm.add_separator();fm.add_command(label='导入朋友投稿 JSON…',command=self.import_submission)
        fm.add_command(label='导出投稿模板…',command=self.export_submission_template)
        fm.add_separator();fm.add_command(label='导出网站发布包 ZIP…',command=self.export_release);fm.add_command(label='退出',command=self.destroy)
        menu.add_cascade(label='文件',menu=fm)
        hm=tk.Menu(menu,tearoff=0);hm.add_command(label='使用说明',command=self.show_help)
        hm.add_command(label='关于',command=lambda:messagebox.showinfo('关于','动漫题库工作台\n动态分类 · 本地数据 · HTML 兼容'))
        menu.add_cascade(label='帮助',menu=hm);self.config(menu=menu)

    def _build_ui(self):
        shell=ttk.Frame(self,padding=20);shell.pack(fill='both',expand=True)
        top=ttk.Frame(shell);top.pack(fill='x')
        ttk.Label(top,text='✦  动漫题库工作台',style='Title.TLabel').pack(side='left')
        ttk.Label(top,text='ANIME ARCADE  /  CONTENT STUDIO',style='Sub.TLabel').pack(side='left',padx=18,pady=(12,0))
        self.stats=ttk.Label(shell,text='题目 0   ·   分类 0   ·   图片 0',font=('Microsoft YaHei UI',11,'bold'),foreground=PALETTE['purple'])
        self.stats.pack(anchor='w',pady=(8,12))
        self.path_label=ttk.Label(shell,text='题库文件：',style='Sub.TLabel');self.path_label.pack(anchor='w',pady=(0,10))
        nb=ttk.Notebook(shell);nb.pack(fill='both',expand=True)
        self.dashboard=ttk.Frame(nb,padding=18);self.qtab=ttk.Frame(nb,padding=16);self.ctab=ttk.Frame(nb,padding=16);self.asset_tab=ttk.Frame(nb,padding=16)
        nb.add(self.dashboard,text='  仪表盘  ');nb.add(self.qtab,text='  题库管理  ');nb.add(self.ctab,text='  分类管理  ');nb.add(self.asset_tab,text='  图片素材  ')
        self._build_dashboard();self._build_questions();self._build_categories();self._build_assets()
        self.status=ttk.Label(shell,text='准备就绪',relief='flat',anchor='w',foreground=PALETTE['muted']);self.status.pack(fill='x',pady=(10,0))

    def _build_dashboard(self):
        ttk.Label(self.dashboard,text='欢迎回来，管理员 ✧',style='Title.TLabel').pack(anchor='w')
        ttk.Label(self.dashboard,text='在这里维护题目、分类与解析素材。保存后的 JSON 同时供 HTML 网站读取。',style='Sub.TLabel').pack(anchor='w',pady=8)
        self.dash_stats=tk.Label(self.dashboard,text='',bg='white',fg=PALETTE['deep'],font=('Microsoft YaHei UI',16,'bold'),padx=24,pady=24,relief='flat')
        self.dash_stats.pack(fill='x',pady=20)
        ttk.Button(self.dashboard,text='保存题库',command=self.save_bank,style='Accent.TButton').pack(anchor='w')
        ttk.Label(self.dashboard,text='素材统一保存在项目 assets/images 与 assets/audio 目录；JSON 中记录相对路径。',style='Sub.TLabel').pack(anchor='w',pady=20)

    def _build_questions(self):
        pan=ttk.Panedwindow(self.qtab,orient='horizontal');pan.pack(fill='both',expand=True)
        left=ttk.Frame(pan,padding=(0,0,14,0));right=ttk.Frame(pan);pan.add(left,weight=1);pan.add(right,weight=3)
        ttk.Label(left,text='题目列表',style='Title.TLabel').pack(anchor='w')
        self.search_var=tk.StringVar();se=ttk.Entry(left,textvariable=self.search_var);se.pack(fill='x',pady=8);se.insert(0,'搜索题目 / ID')
        se.bind('<KeyRelease>',lambda e:self.refresh_questions())
        self.q_filter_var=tk.StringVar(value='全部分类');self.q_filter=ttk.Combobox(left,textvariable=self.q_filter_var,state='readonly',values=['全部分类']);self.q_filter.pack(fill='x',pady=(0,8));self.q_filter.bind('<<ComboboxSelected>>',lambda e:self.refresh_questions())
        self.q_tree=ttk.Treeview(left,columns=('id','category'),show='headings',selectmode='browse')
        self.q_tree.heading('id',text='题目');self.q_tree.heading('category',text='所属分类')
        self.q_tree.column('id',width=210);self.q_tree.column('category',width=100,stretch=False)
        self.q_tree.pack(fill='both',expand=True);self.q_tree.bind('<<TreeviewSelect>>',self.select_question)
        row=ttk.Frame(left);row.pack(fill='x',pady=8)
        ttk.Button(row,text='＋ 新建',command=self.new_question,style='Accent.TButton').pack(side='left')
        ttk.Button(row,text='删除',command=self.delete_question).pack(side='left',padx=6)
        right.columnconfigure(1,weight=1);right.rowconfigure(5,weight=1)
        self.q_vars={};self._entry(right,0,'题目 ID','id');self._combo(right,1,'题型','type',list(TYPES))
        self._entry(right,2,'题目内容','question')
        self._combo(right,3,'所属分类','category',[])
        ttk.Label(right,text='选项（每行一个；填空题留空）').grid(row=4,column=0,sticky='nw',pady=5)
        self.options_text=tk.Text(right,height=5,wrap='word',font=('Microsoft YaHei UI',10),relief='flat',highlightthickness=1,highlightbackground=PALETTE['line'])
        self.options_text.grid(row=4,column=1,columnspan=2,sticky='nsew',pady=5)
        self._entry(right,5,'正确答案','answer')
        ttk.Label(right,text='文字解析').grid(row=6,column=0,sticky='nw',pady=5)
        self.explanation_text=tk.Text(right,height=4,wrap='word',font=('Microsoft YaHei UI',10),relief='flat',highlightthickness=1,highlightbackground=PALETTE['line'])
        self.explanation_text.grid(row=6,column=1,columnspan=2,sticky='ew',pady=5)
        self.image_var=tk.StringVar();self.explanation_image_var=tk.StringVar();self.audio_var=tk.StringVar()
        self._asset_row(right,7,'题目图片','image',self.image_var)
        self._asset_row(right,8,'解析图片','explanationImage',self.explanation_image_var)
        self._asset_row(right,9,'音频文件','audio',self.audio_var)
        ttk.Label(right,text='多答案填空题用 | 分隔；选择题答案填写从 0 开始的选项序号。',style='Sub.TLabel').grid(row=10,column=0,columnspan=3,sticky='w',pady=6)
        ttk.Button(right,text='保存当前题目',command=self.save_question,style='Accent.TButton').grid(row=11,column=1,sticky='e',pady=8)

    def _entry(self,parent,row,label,key):
        ttk.Label(parent,text=label).grid(row=row,column=0,sticky='w',pady=5)
        v=tk.StringVar();self.q_vars[key]=v;ttk.Entry(parent,textvariable=v).grid(row=row,column=1,columnspan=2,sticky='ew',pady=5)
    def _combo(self,parent,row,label,key,values):
        ttk.Label(parent,text=label).grid(row=row,column=0,sticky='w',pady=5)
        v=tk.StringVar();self.q_vars[key]=v;w=ttk.Combobox(parent,textvariable=v,values=values,state='readonly')
        w.grid(row=row,column=1,columnspan=2,sticky='ew',pady=5)
        if key=='category':self.category_combo=w
    def _asset_row(self,parent,row,label,key,var):
        ttk.Label(parent,text=label).grid(row=row,column=0,sticky='w',pady=4)
        ttk.Entry(parent,textvariable=var).grid(row=row,column=1,sticky='ew',pady=4)
        ttk.Button(parent,text='选择并复制…',command=lambda:self.pick_asset(key)).grid(row=row,column=2,padx=5)

    def _build_categories(self):
        pan=ttk.Panedwindow(self.ctab,orient='horizontal');pan.pack(fill='both',expand=True)
        left=ttk.Frame(pan,padding=(0,0,14,0));right=ttk.Frame(pan);pan.add(left,weight=1);pan.add(right,weight=2)
        ttk.Label(left,text='动态分类',style='Title.TLabel').pack(anchor='w')
        ttk.Label(left,text='分类数量和名称完全由题库数据决定。',style='Sub.TLabel').pack(anchor='w',pady=5)
        self.c_tree=ttk.Treeview(left,columns=('count',),show='tree headings',height=16)
        self.c_tree.heading('#0',text='分类名称');self.c_tree.heading('count',text='题目数');self.c_tree.column('count',width=80,anchor='center')
        self.c_tree.pack(fill='both',expand=True,pady=8);self.c_tree.bind('<<TreeviewSelect>>',self.select_category)
        row=ttk.Frame(left);row.pack(fill='x')
        ttk.Button(row,text='＋ 新增',command=self.new_category,style='Accent.TButton').pack(side='left')
        ttk.Button(row,text='删除',command=self.delete_category).pack(side='left',padx=5)
        ttk.Button(row,text='↑',command=lambda:self.move_category(-1)).pack(side='left')
        ttk.Button(row,text='↓',command=lambda:self.move_category(1)).pack(side='left',padx=4)
        right.columnconfigure(1,weight=1)
        ttk.Label(right,text='分类信息',style='Title.TLabel').grid(row=0,column=0,columnspan=2,sticky='w',pady=(0,14))
        self.c_name=tk.StringVar();self.c_desc=tk.StringVar()
        ttk.Label(right,text='分类名称').grid(row=1,column=0,sticky='w',pady=8);ttk.Entry(right,textvariable=self.c_name).grid(row=1,column=1,sticky='ew')
        ttk.Label(right,text='分类描述').grid(row=2,column=0,sticky='w',pady=8);ttk.Entry(right,textvariable=self.c_desc).grid(row=2,column=1,sticky='ew')
        ttk.Button(right,text='保存分类信息',command=self.save_category,style='Accent.TButton').grid(row=3,column=1,sticky='e',pady=12)
        ttk.Label(right,text='分类归属由题目 categoryId 自动维护，不需要手工填写题目 ID。删除分类时，题目会保留并转入「未分类」。',wraplength=560,style='Sub.TLabel').grid(row=4,column=0,columnspan=2,sticky='w',pady=20)

    def _build_assets(self):
        ttk.Label(self.asset_tab,text='项目素材目录',style='Title.TLabel').pack(anchor='w')
        ttk.Label(self.asset_tab,text='题目图片与解析图片分开记录；文件均复制到 assets/images。音频复制到 assets/audio。',style='Sub.TLabel').pack(anchor='w',pady=8)
        self.assets_text=tk.Text(self.asset_tab,wrap='none',font=('Consolas',10),relief='flat',bg='white')
        self.assets_text.pack(fill='both',expand=True,pady=8)
        ttk.Button(self.asset_tab,text='刷新素材清单',command=self.refresh_assets).pack(anchor='e')

    def set_status(self,msg):
        self.status.config(text=msg)

    def migrate(self,data):
        data.setdefault('schemaVersion',1);data.setdefault('questions',[]);data.setdefault('quizzes',[])
        if not isinstance(data['questions'],list) or not isinstance(data['quizzes'],list):raise ValueError('JSON 必须包含 questions 和 quizzes 数组。')
        membership={}
        for c in data['quizzes']:
            for qid in c.get('questionIds',[]):membership.setdefault(qid,c.get('id'))
            c.setdefault('title',c.get('difficulty') or '未命名分类');c.setdefault('difficulty',c['title'])
            c.setdefault('description','');c.setdefault('published',True)
        for q in data['questions']:
            if not q.get('categoryId') and q.get('id') in membership:q['categoryId']=membership[q['id']]
            q.setdefault('explanation','');q.setdefault('image','');q.setdefault('audio','')
        data['schemaVersion']=2
        self.sync_membership(data)
        return data

    def sync_membership(self,data=None):
        d=data or self.bank
        valid={c['id'] for c in d['quizzes']}
        for q in d['questions']:
            if q.get('categoryId') not in valid:q['categoryId']=''
        for c in d['quizzes']:
            c['questionIds']=[q['id'] for q in d['questions'] if q.get('categoryId')==c['id']]
        d['difficulties']=[c['title'] for c in d['quizzes']]

    def load_bank(self,path):
        path=Path(path)
        try:
            if path.exists():data=json.loads(path.read_text(encoding='utf-8-sig'))
            else:data={'schemaVersion':2,'quizzes':[],'questions':[]}
            self.bank=self.migrate(data);self.bank_path=path;self.root_dir=path.parent.parent if path.parent.name=='data' else path.parent
            self.refresh_all();self.path_label.config(text='题库文件：'+str(path));self.set_status(f'已载入 {len(self.bank["questions"])} 道题、{len(self.bank["quizzes"])} 个分类')
        except Exception as e:messagebox.showerror('载入失败',str(e))

    def open_bank(self):
        p=filedialog.askopenfilename(title='选择题库 JSON',filetypes=[('JSON 文件','*.json')],initialdir=self.bank_path.parent)
        if p:self.load_bank(p)

    def save_bank(self):
        try:
            self.sync_membership();self.bank['schemaVersion']=2
            from datetime import datetime
            self.bank['updatedAt']=datetime.now().isoformat(timespec='seconds')
            self.bank_path.parent.mkdir(parents=True,exist_ok=True)
            tmp=self.bank_path.with_suffix('.json.tmp');tmp.write_text(json.dumps(self.bank,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            tmp.replace(self.bank_path);self.refresh_all();self.set_status('已保存：'+str(self.bank_path))
            messagebox.showinfo('保存成功','题库 JSON 已保存。HTML 网站会读取同一份数据。')
        except Exception as e:messagebox.showerror('保存失败',str(e))

    def refresh_all(self):
        self.refresh_questions();self.refresh_categories();self.refresh_assets()
        count=len(self.bank['questions']);cats=len(self.bank['quizzes']);imgs=sum(bool(q.get('image'))+bool(q.get('explanationImage')) for q in self.bank['questions'])
        self.stats.config(text=f'题目  {count}     ·     分类  {cats}     ·     图片引用  {imgs}')
        self.dash_stats.config(text=f'✦  {count} 道题目       ♡  {cats} 个动态分类       ✧  {imgs} 张题目 / 解析图片')

    def refresh_questions(self):
        if not hasattr(self,'q_tree'):return
        for x in self.q_tree.get_children():self.q_tree.delete(x)
        term=self.search_var.get().strip().lower();chosen=self.q_filter_var.get() if hasattr(self,'q_filter_var') else '全部分类'
        for q in self.bank['questions']:
            cat=next((c['title'] for c in self.bank['quizzes'] if c['id']==q.get('categoryId')),'未分类')
            if chosen not in ('全部分类','未分类',cat):continue
            if chosen=='未分类' and cat!='未分类':continue
            if term and term!='搜索题目 / id' and term not in (str(q.get('id',''))+' '+q.get('question','')).lower():continue
            self.q_tree.insert('','end',iid=q['id'],values=(f"{q['id']} · {q.get('question','')[:35]}",cat))
    def refresh_categories(self):
        if not hasattr(self,'c_tree'):return
        for x in self.c_tree.get_children():self.c_tree.delete(x)
        self.sync_membership()
        for c in self.bank['quizzes']:
            self.c_tree.insert('','end',iid=c['id'],text=c.get('title',''),values=(len(c['questionIds']),))
        if hasattr(self,'category_combo'):
            self.category_combo['values']=['未分类']+[c['title'] for c in self.bank['quizzes']]
        if hasattr(self,'q_filter'):
            self.q_filter['values']=['全部分类','未分类']+[c['title'] for c in self.bank['quizzes']]
            if self.q_filter_var.get() not in self.q_filter['values']:self.q_filter_var.set('全部分类')
    def refresh_assets(self):
        if not hasattr(self,'assets_text'):return
        self.assets_text.delete('1.0','end')
        for kind,label in [('image','题目图片'),('explanationImage','解析图片'),('audio','音频')]:
            self.assets_text.insert('end',f'[{label}]\n')
            for q in self.bank['questions']:
                val=q.get(kind)
                if val:self.assets_text.insert('end',f"{q['id']}  {val}  {'✓' if (self.root_dir/val).exists() else '⚠ 文件缺失'}\n")
            self.assets_text.insert('end','\n')

    def clear_question_form(self):
        self.selected_question_id=None
        for v in self.q_vars.values():v.set('')
        self.q_vars['type'].set('选择题');self.options_text.delete('1.0','end');self.explanation_text.delete('1.0','end')
        self.image_var.set('');self.explanation_image_var.set('');self.audio_var.set('')
        if self.q_tree.selection():self.q_tree.selection_remove(self.q_tree.selection())
    def new_question(self):
        self.clear_question_form();self.q_vars['id'].set('q-'+uuid.uuid4().hex[:8]);self.set_status('新建题目：填写后保存')
    def select_question(self,event=None):
        sel=self.q_tree.selection()
        if not sel:return
        q=next((x for x in self.bank['questions'] if x['id']==sel[0]),None)
        if not q:return
        self.selected_question_id=q['id']
        self.q_vars['id'].set(q.get('id',''));self.q_vars['type'].set(TYPE_LABELS.get(q.get('type','single'),'选择题'))
        self.q_vars['question'].set(q.get('question',''));self.q_vars['answer'].set('|'.join(map(str,q.get('answer',[]))) if isinstance(q.get('answer'),list) else str(q.get('answer','')))
        self.q_vars['category'].set(next((c['title'] for c in self.bank['quizzes'] if c['id']==q.get('categoryId')),'未分类'))
        self.options_text.delete('1.0','end');self.options_text.insert('1.0','\n'.join(q.get('options',[])))
        self.explanation_text.delete('1.0','end');self.explanation_text.insert('1.0',q.get('explanation',''))
        self.image_var.set(q.get('image',''));self.explanation_image_var.set(q.get('explanationImage',''));self.audio_var.set(q.get('audio',''))

    def save_question(self):
        qid=self.q_vars['id'].get().strip();question=self.q_vars['question'].get().strip();typ=TYPES.get(self.q_vars['type'].get(),'single')
        if not qid or not question:messagebox.showwarning('信息不完整','题目 ID 和题目内容不能为空。');return
        old=next((q for q in self.bank['questions'] if q['id']==self.selected_question_id or q['id']==qid),None)
        if old and old['id']!=qid and any(q['id']==qid for q in self.bank['questions']):messagebox.showwarning('ID 重复','题目 ID 已存在。');return
        options=[x.strip() for x in self.options_text.get('1.0','end').splitlines() if x.strip()]
        raw=self.q_vars['answer'].get().strip()
        if typ=='fill':answer=[x.strip() for x in raw.split('|') if x.strip()];answer=answer[0] if len(answer)==1 else answer
        else:
            try:answer=int(raw)
            except ValueError:messagebox.showwarning('答案格式错误','选择题答案填写从 0 开始的序号。');return
            if typ in ('single','audio-choice','image-title','image-character') and (len(options)<2 or answer<0 or answer>=len(options)):
                messagebox.showwarning('答案格式错误','请检查选项数量和答案序号。');return
            if typ=='truefalse':options=['正确','错误'];answer=0 if answer==0 else 1
        cat_name=self.q_vars['category'].get();cat=next((c for c in self.bank['quizzes'] if c['title']==cat_name),None)
        q=dict(old or {})
        q.update({'id':qid,'type':typ,'question':question,'options':options,'answer':answer,
                  'explanation':self.explanation_text.get('1.0','end').strip(),
                  'image':self.image_var.get().strip(),'explanationImage':self.explanation_image_var.get().strip(),
                  'audio':self.audio_var.get().strip(),'categoryId':cat['id'] if cat else ''})
        if old and old['id']!=qid:self.bank['questions'].remove(old)
        existing=next((i for i,x in enumerate(self.bank['questions']) if x['id']==qid),None)
        if existing is None:self.bank['questions'].append(q)
        else:self.bank['questions'][existing]=q
        self.selected_question_id=qid;self.refresh_all();self.set_status('题目已更新到内存；请保存题库写入 JSON。')

    def delete_question(self):
        sel=self.q_tree.selection()
        if not sel:return
        qid=sel[0]
        if messagebox.askyesno('确认删除',f'确定删除题目 {qid}？'):
            self.bank['questions']=[q for q in self.bank['questions'] if q['id']!=qid]
            self.clear_question_form();self.refresh_all();self.set_status('题目已删除；保存后写入 JSON。')

    def new_category(self):
        self.selected_category_id=None;self.c_name.set('');self.c_desc.set('');self.c_name_entry.focus_set() if hasattr(self,'c_name_entry') else None
    def select_category(self,event=None):
        sel=self.c_tree.selection()
        if not sel:return
        c=next((x for x in self.bank['quizzes'] if x['id']==sel[0]),None)
        if c:self.selected_category_id=c['id'];self.c_name.set(c.get('title',''));self.c_desc.set(c.get('description',''))
    def save_category(self):
        name=self.c_name.get().strip()
        if not name:messagebox.showwarning('分类名称为空','请输入分类名称。');return
        duplicate=next((c for c in self.bank['quizzes'] if c['title']==name and c['id']!=self.selected_category_id),None)
        if duplicate:messagebox.showwarning('分类已存在','请使用不同的分类名称。');return
        c=next((x for x in self.bank['quizzes'] if x['id']==self.selected_category_id),None)
        if c is None:
            c={'id':slug(name),'title':name,'difficulty':name,'description':self.c_desc.get().strip(),'questionIds':[],
               'published':True,'sortOrder':len(self.bank['quizzes'])}
            self.bank['quizzes'].append(c);self.selected_category_id=c['id']
        else:c.update({'title':name,'difficulty':name,'description':self.c_desc.get().strip()})
        self.refresh_all();self.set_status('分类信息已更新；题目归属通过分类 ID 自动保持。')
    def delete_category(self):
        sel=self.c_tree.selection()
        if not sel:return
        cid=sel[0];c=next(x for x in self.bank['quizzes'] if x['id']==cid)
        count=sum(q.get('categoryId')==cid for q in self.bank['questions'])
        if not messagebox.askyesno('确认删除分类',f'删除「{c["title"]}」？该分类的 {count} 道题目将保留并转入「未分类」。'):return
        self.bank['quizzes']=[x for x in self.bank['quizzes'] if x['id']!=cid]
        for q in self.bank['questions']:
            if q.get('categoryId')==cid:q['categoryId']=''
        self.selected_category_id=None;self.c_name.set('');self.c_desc.set('');self.refresh_all();self.set_status('分类已删除，题目已转入未分类。')
    def move_category(self,delta):
        sel=self.c_tree.selection()
        if not sel:return
        idx=next((i for i,c in enumerate(self.bank['quizzes']) if c['id']==sel[0]),-1);n=idx+delta
        if idx<0 or n<0 or n>=len(self.bank['quizzes']):return
        cats=self.bank['quizzes'];cats[idx],cats[n]=cats[n],cats[idx]
        for i,c in enumerate(cats):c['sortOrder']=i
        self.refresh_all();self.c_tree.selection_set(cats[n]['id'])

    def pick_asset(self,kind):
        if kind in ('image','explanationImage'):types=[('图片','*.png *.jpg *.jpeg *.webp *.gif *.bmp'),('所有文件','*.*')];folder='images'
        else:types=[('音频','*.mp3 *.wav *.ogg *.m4a *.aac'),('所有文件','*.*')];folder='audio'
        p=filedialog.askopenfilename(title='选择并复制素材',filetypes=types)
        if not p:return
        target=self.root_dir/'assets'/folder;target.mkdir(parents=True,exist_ok=True);src=Path(p);dest=target/src.name
        if src.resolve()!=dest.resolve():
            if dest.exists():dest=target/(src.stem+'-'+uuid.uuid4().hex[:6]+src.suffix)
            shutil.copy2(src,dest)
        rel=dest.relative_to(self.root_dir).as_posix()
        {'image':self.image_var,'explanationImage':self.explanation_image_var,'audio':self.audio_var}[kind].set(rel)
        self.set_status(f'素材已复制：{rel}');self.refresh_assets()

    def import_submission(self):
        p=filedialog.askopenfilename(title='导入朋友投稿 JSON',filetypes=[('JSON','*.json')])
        if not p:return
        try:
            d=json.loads(Path(p).read_text(encoding='utf-8-sig'));items=d.get('questions',[])
            if not isinstance(items,list) or not items:raise ValueError('投稿 JSON 没有 questions 数组。')
            existing={q['id'] for q in self.bank['questions']};added=0
            for item in items:
                if not isinstance(item,dict) or not item.get('question'):continue
                q=dict(item);base=str(q.get('id') or 'submission-q');qid=base
                if qid in existing:qid=base+'-'+uuid.uuid4().hex[:6]
                q['id']=qid;q.setdefault('type','single');q.setdefault('options',[]);q.setdefault('answer',0);q.setdefault('explanation','');q.setdefault('image','');q.setdefault('audio','');q.setdefault('explanationImage','');q['categoryId']=''
                self.bank['questions'].append(q);existing.add(qid);added+=1
            self.refresh_all();messagebox.showinfo('投稿已导入',f'已导入 {added} 道未分类题目，请审核。')
        except Exception as e:messagebox.showerror('投稿导入失败',str(e))
    def export_submission_template(self):
        p=filedialog.asksaveasfilename(title='保存投稿模板',defaultextension='.json',initialfile='anime-quiz-submission.json',filetypes=[('JSON','*.json')])
        if not p:return
        d={'schemaVersion':2,'submissionTitle':'我的题目投稿','questions':[{'id':'submission-q1','type':'single','question':'请填写题目','options':['选项 A','选项 B'],'answer':0,'explanation':'','image':'','explanationImage':'','audio':''}]}
        Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');messagebox.showinfo('已导出','投稿模板已保存。')
    def export_release(self):
        self.save_bank()
        p=filedialog.asksaveasfilename(title='导出网站发布包 ZIP',defaultextension='.zip',initialfile='anime-arcade-release.zip',filetypes=[('ZIP','*.zip')])
        if not p:return
        try:
            with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
                for rel in ['index.html','styles.css','app.js','README.md','.nojekyll','data/quiz-bank.json']:
                    src=self.root_dir/rel
                    if src.exists():z.write(src,rel)
                assets=self.root_dir/'assets'
                if assets.exists():
                    for f in assets.rglob('*'):
                        if f.is_file():z.write(f,f.relative_to(self.root_dir).as_posix())
            messagebox.showinfo('发布包已生成',f'网站发布包已生成：\n{p}')
        except Exception as e:messagebox.showerror('导出失败',str(e))
    def show_help(self):
        messagebox.showinfo('使用说明','题目管理：选择分类、编辑题目与选项。填空答案多个变体用 | 分隔。\n分类管理：新增、改名、描述、删除、调整顺序；删除分类会把题目转入未分类。\n解析：文字与解析图片可以同时使用，解析图片单独保存到 assets/images。\n保存题库：写入 data/quiz-bank.json。网站使用同一 JSON 数据。')
if __name__=='__main__':
    app=QuizAdmin();app.mainloop()
