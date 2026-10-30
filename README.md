# 妄梦生 · 动漫游戏厅 v3（本地题库管理 + GitHub Pages）

本项目采用完全静态的网站和本地管理工具，不依赖 Firebase、云端数据库、付费云函数或付费文件存储。

## 项目结构

```text
anime-quiz-arcade-v3/
├── index.html                  # 在线答题网站
├── styles.css                  # 响应式游戏厅样式
├── app.js                      # 答题、正确率积分、错题本、个人资料
├── data/quiz-bank.json         # 正式题库（管理员维护）
├── data/submission-template.json # 投稿格式示例
├── assets/images/              # 题目图片
├── assets/audio/               # 题目音频
├── admin-tool/quiz_admin.py    # 本地题库管理工具源码
└── admin-tool/build_windows.bat # Windows EXE 打包脚本
```

## 本地预览网站

需要 Python 3，在项目根目录运行：

```bat
py -m http.server 8000
```

然后浏览器打开 `http://localhost:8000`。请不要直接双击 `index.html`，浏览器可能会阻止读取 JSON 题库。

## 运行本地题库管理工具（Windows）

安装 Python 3.10+ 后，在项目根目录执行：

```bat
py admin-tool\quiz_admin.py
```

工具包含仪表盘、题目管理、动态分类管理（新增、改名、描述、删除、排序）、题目图片/解析图片/音频复制、投稿 JSON 导入、投稿模板导出和网站发布包导出。

### 打包 EXE

在 Windows 电脑上双击 `admin-tool\build_windows.bat`。脚本会安装 PyInstaller 并生成：

`admin-tool\dist\AnimeQuizAdmin.exe`

推荐把 EXE 保留在项目文件夹的 `admin-tool\dist\` 里运行，这样工具能找到项目根目录的 `data/quiz-bank.json` 和 `assets/`。当前环境不能直接运行 Windows EXE，因此请在 Windows 上完成最后的启动验证。

## 题库与动态分类规则

分类保存在 `data/quiz-bank.json` 的 `quizzes` 数组中，分类 ID 稳定；题目通过 `categoryId` 关联分类。为兼容旧版，分类仍同步维护 `questionIds`，旧版仅有 `questionIds` 的题库会在管理工具和网站加载时迁移。分类名称、数量和顺序均由 JSON 动态决定，不再固定为四档。

- 新增、改名、描述编辑、删除和排序均在 EXE 的「分类管理」页完成。
- 删除分类不会删除题目；题目会保留并转入「未分类」。
- 题目编辑页通过分类下拉框设置归属；分类 ID 不因改名而变化。
- 每次挑战从该分类中无放回随机抽取最多 20 道；少于 20 道则全部使用，重新挑战会重新抽取。
- 解析支持文字、图片或文字与图片同时使用；解析图片字段为 `explanationImage`，与题目图片字段 `image` 分开保存。
- 题型兼容 `single`、`truefalse`、`fill`、`audio-choice`、`image-title`、`image-character`。

题目素材路径使用相对项目根目录的路径，例如 `assets/images/example.webp`、`assets/audio/example.mp3`。管理工具选择素材时会复制到对应目录并写入相对路径。

## 积分规则

每次挑战满分 100 XP，按正确率结算：

`本次积分 = round(100 × 答对题数 ÷ 总题数)`

因此 10 题答对 8 题获得 80 XP，答错不可能仍然获得满分。由于这是公开静态网页，题库答案能被访问者通过网页资源查看；本方案适合朋友间娱乐，不提供服务器级防作弊。

## 个人数据与投稿

- 昵称、头像、积分、错题和成就保存在当前浏览器 IndexedDB 中，不会上传云端。
- 个人记录可导出 JSON 备份；换设备或清理浏览器数据前请先备份。
- 朋友可以在网站投稿界面填写一道题，选择本地图片或小于 1 MB 的音频；图片会压缩后嵌入投稿 JSON，音频也会以 Data URL 嵌入。管理员在本地工具导入后，工具会把内嵌素材提取到 `assets/`，再审核并把通过的题目 ID 加入合适的正式题库。
- 由于没有服务器，朋友不能通过网页直接把投稿传到管理员电脑；需要通过你们已有的文件传递方式发送投稿文件。
- 头像上传会在浏览器本地压缩并保存，不会上传到网站服务器。

## 发布到 GitHub Pages

1. 在 GitHub 创建一个你自己的仓库。
2. 上传项目根目录中的网站文件，至少包括 `index.html`、`styles.css`、`app.js`、`data/`、`assets/`、`.nojekyll`。
3. 进入仓库 **Settings → Pages**。
4. 在 Build and deployment 选择 **Deploy from a branch**，分支选 `main`，目录选 `/(root)`，保存。
5. 等待 GitHub Pages 显示网站地址。项目使用相对路径，适用于 `https://用户名.github.io/仓库名/` 这种项目站点路径。

### 每次更新题库

1. 打开 `admin-tool/quiz_admin.py` 或打包后的 EXE。
2. 编辑题目、图片/音频素材和正式题库；点击“保存题库”。
3. 使用“导出 GitHub 发布包 ZIP”，或者手动提交 `data/quiz-bank.json` 和新增素材。
4. 在 GitHub 仓库上传并覆盖对应文件，提交更改。
5. 等 GitHub Pages 部署完成，朋友刷新页面即可使用新题库。若看到旧题库，尝试强制刷新。

## 安全边界（请务必阅读）

- 只有你拥有 GitHub 仓库写入权限时，才能把正式题库更新发布给所有人。不要给朋友仓库写入权限。
- 静态网页无法阻止访问者修改自己的浏览器副本，也无法隐藏公开题库的答案；但修改本地副本不会修改 GitHub 仓库。
- 本方案不包含云端账号、跨设备同步、全球排行榜或服务器级防作弊。
- EXE 的打包需要在 Windows 上执行；本项目提供源码与脚本，不声称已经在当前环境完成 Windows EXE 实测。

## 本次数据与素材说明

本次交付使用随本次上传一并提供的完整 `quiz-bank.json` 恢复并保留 26 道题；题目原有字段、答案变体、解析和图片路径均保留，另增加 `categoryId` 与空的 `explanationImage` 字段。原始项目 ZIP 内部的题库实际只有 8 道题，故以单独上传的 26 题 JSON 作为完整题库数据来源。

原始 ZIP 未包含 `assets/images/` 中的图片文件。题目图片路径已原样保留，管理工具与网站均按相对路径读取；对应图片文件需要由管理员按原路径放入素材目录，不能从缺失的 ZIP 内容中恢复或替换。
