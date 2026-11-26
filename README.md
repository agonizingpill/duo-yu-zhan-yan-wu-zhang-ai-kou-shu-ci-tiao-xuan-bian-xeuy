# 浮桥口述词页

为浮桥无障碍演出协作组维护多语舞台口述。从剧本原句检索可读的译词，经人工核验语义和许可后，按走台顺序发布可离线使用的口述词单。

## 工作场景

浮桥小组由 6 名词库编辑、2 名来源审核员和约 12 名轮班口述员组成，配合剧场为复排与巡演提供中文、英语和日文口述。过去使用舞台监督发出的 PDF 批注和两份分开的译词表。词汇随场次滚动时，相似旧译难找，同一词会出现多个生效版本，巡演许可也容易混进回放录制词单。

上游提供剧本批注、原讲稿、翻译稿、许可编号及用途。工作席接管原译词对照、许可复核、译词调整和版本归档。现场口述员下载定稿 CSV，按舞台提示开读。

| 账号 | 角色 | 工作席与操作 |
|---|---|---|
| editor | 词库编辑 | 登记许可和词条、生成相似候选、建词单、调整走台顺序 |
| reviewer | 许可审核 | 生成候选、签审替换目标语种映射、撤销许可、发布词单 |
| reader | 现场口述 | 查看词单和资料、下载已发布词单 |

本地演示账号使用密码 `StageDesk2026!`。对外部署时更换环境中的 JWT 密钥及密码。

## 演示剧本

1. 09:00 黄曼对照 `FB-STAGE-R4`，在「来源与词库」核对 `ZH-WATER`、`ZH-LANTERN` 和 `ZH-FOG` 的舞台提示。
2. 09:20 检查 `FO-TOUR-025`。旧英语稿 `EN-WATER-OLD` 只允许现场使用，授权截止 2026-12-01。
3. 09:35 在「相似候选」对 `ZH-WATER` 查英语候选，查看字符词表维度、语料指纹和相似度，再对照 `EN-WATER` 与 `EN-WATER-DIM`。
4. 10:10 童雨在「演出词单」尝试发布 2026-12-18 的 `FB-WINTER`。系统显示旧许可未覆盖演出日，并从已算候选提示可用的录制新版。
5. 10:20 从替代候选跳到「映射批注」。核对 `FO-WINTER-R2` 和口述长度后，用 `EN-WATER` 替换旧映射。
6. 10:40 黄曼在「演出词单」检查 A01 水幕起和 A02 灯笼入的走台顺序。若增加 A03 雾升须先补审其语种映射。
7. 11:00 童雨发布，固定两条译词、各自的许可引用和审签人。陈嘉以现场口述身份下载 `FB-WINTER.csv`，以后再签审的译词不改写已发布内容。

## 算法

输入由原句和启用的目标语词条构成，加入舞台提示与由编辑填写的桥接关键词。NFKC 规范化与大小写折叠后，用 2–4 字符 n-gram 和对数词频建立稀疏 TF-IDF 矩阵，以随机种子 1078 的 TruncatedSVD 投影到最多 8 维。投影向量经 L2 归一化后与原词做余弦内积，按相似度与词条编号排序取前五。扫描展示输入 SHA-256、权重维数、词表大小和解释方差。少于两个目标语词条时保留失败记录。相似度供审核参考，既不自动翻译，也不会自动签审。回放词单另以演出日、当前日和授权用途过滤替代候选。

待运算扫描先写 PostgreSQL，Redis 唤醒 worker 并维护健康心跳。worker 获取行锁后在同一事务写入所有结果与扫描状态。Redis 通知中断时，worker 仍定期查询待计算扫描。

## 使用

```sh
cp .env.example .env
docker compose config --quiet
docker compose up -d --wait --build
docker compose exec -T backend python -m scripts.seed_demo
```

浏览器访问 `http://127.0.0.1:18302`，后端访问 `http://127.0.0.1:19302/docs`，本地数据库端口为 `17802`。退出后如需删除此项目的演示数据，执行 `docker compose down -v --remove-orphans`。

| 层 | 技术 | 职责 |
|---|---|---|
| 前端 | Nginx、HTML、CSS、ES modules | 剧本批注席、编辑操作、播放版本和下载 |
| Web 后端 | Python 3.12、FastAPI、JWT、psycopg | 权限、审签、词单与 CSV |
| 算法 | scikit-learn、NumPy | 稀疏 TF-IDF、SVD 和归一化相似度 |
| 后台 | Redis、Python worker | 扫描唤醒和后台健康检查 |
| 数据库 | PostgreSQL 16 | 许可、映射、扫描、词单快照与审签账 |

`backend/src/services` 是编目、候选、映射、授权检查、发布、导出逻辑，`backend/src/routes` 是各模块接口。SQL 表结构在 `backend/migrations`，seed 在 `backend/scripts`。前端 `frontend/src/pages` 含四个业务页面，`components` 含共用的状态标记、台词行及反馈。Redis、PostgreSQL 和后端共享产物使用三个独立卷。

本地前端开发直接改 `frontend/src` 后重建 frontend。单独运行后端时，可先启动 Compose 的 db 与 redis。Redis 默认仅在内部网络，建议直接 `docker compose up -d backend worker`。要在宿主运行所有 Python 进程需提供可达的 `REDIS_URL`，进入 `backend` 后安装 `requirements.txt`，用 `uvicorn src.app:app --reload` 和 `python -m src.worker` 启动。

`.env.example` 指定项目短名、前后端与数据库端口、数据库密码、签名密钥、演示密码和自动 seed 开关。数据库的密码若含 URL 保留字符，连接字符串中需作百分号转义。演示 seed 下以自然键插入，已有映射修订、许可撤销和已发布词单都保留。

共享枚举定义于 `backend/src/enums.py` 与 `frontend/src/labels.js`。角色用于 `auth.py`、三个路由模块及页面按钮开关。语种用于 `schemas.py`、`read_models.py`、SQL 约束及词库、候选、映射和词单页面。渠道用于 SQL 约束、`schemas.py`、`read_models.py`、`services/rights.py` 和词单页面。

许可证见 `LICENSE`。
