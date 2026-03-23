# bulletin-xdu

XDU 校园通知聚合平台后端。基于 GitHub Actions 定时爬取学校各学院/部门通知网站，归档为 JSON 并通过 GitHub Pages 提供静态 API 访问。

## 特性

- **Adapter 模式**: 可扩展的适配器架构，针对不同网站格式编写 adapter
- **配置驱动**: 通过 YAML 文件配置数据源，无需修改代码即可添加新站点
- **增量爬取**: 仅抓取新通知，避免重复
- **零成本部署**: GitHub Actions + GitHub Pages，无需服务器

## 支持的数据源

### 学院

| ID | 名称 | URL |
|----|------|-----|
| cs | 计算机科学与技术学院 | https://cs.xidian.edu.cn/tzgg.htm |
| ce | 网络与信息安全学院 | https://ce.xidian.edu.cn/sy/tzgg.htm |
| ste | 通信工程学院 | https://ste.xidian.edu.cn/tzgg.htm |
| math | 数学与统计学院 | https://math.xidian.edu.cn/xwgg/tzgg.htm |
| see | 电子工程学院 | https://see.xidian.edu.cn/tzgg.htm |
| phy | 物理与光电工程学院 | https://phy.xidian.edu.cn/tzgg.htm |
| soe | 光电工程学院 | https://soe.xidian.edu.cn/xwtz/tzgg.htm |
| eme | 机电工程学院 | https://eme.xidian.edu.cn/tz.htm |
| sem | 经济与管理学院 | https://sem.xidian.edu.cn/tzgg.htm |
| sfl | 语言智能学部 | https://sfl.xidian.edu.cn/tzgg.htm |
| rwxy | 人文学院 | https://rwxy.xidian.edu.cn/index/tzgg.htm |
| life | 生命科学技术学院 | https://life.xidian.edu.cn/tzgg.htm |
| amn | 先进材料与纳米科技学院 | https://amn.xidian.edu.cn/tzgg.htm |
| sai | 人工智能学院 | https://sai.xidian.edu.cn/tzgg.htm |
| sast | 空间科学与技术学院 | https://sast.xidian.edu.cn/index/tzgg.htm |
| sme | 集成电路学部 | https://sme.xidian.edu.cn/plus/list.php?tid=6 |
| jcdlyjy | 集成电路研究院 | https://jcdlyjy.xidian.edu.cn/tzgg1/tzgg.htm |
| imse | 信息力学与感知工程学院 | https://imse.xidian.edu.cn/tzgg.htm |
| xdwy | 网络与继续教育学院 | https://xdwy.xidian.edu.cn/tzgg.htm |
| sie | 国际教育学院 | https://sie.xidian.edu.cn/sy/tzgg.htm |

### 部门

| ID | 名称 | URL |
|----|------|-----|
| jwc | 教务处 | https://jwc.xidian.edu.cn/tzgg.htm |
| xgc | 学生工作处 | https://xgc.xidian.edu.cn/tzgg1.htm |
| bksy | 本科生院 | https://bksy.xidian.edu.cn/tzgg.htm |
| gr | 研究生院 | https://gr.xidian.edu.cn/tzgg1.htm |
| ygb | 党委研究生工作部 | https://ygb.xidian.edu.cn/tzgg.htm |
| jgrsrc | 人才招聘 | https://jgrsrc.xidian.edu.cn/index/tzgg.htm |
| dzb | 党政办公室 | https://dzb.xidian.edu.cn/gzdt/tzgg.htm |
| jsfz | 教师发展中心 | https://jsfz.xidian.edu.cn/tzgg.htm |
| hqbzb | 后勤保障部 | https://hqbzb.xidian.edu.cn/tzgg.htm |
| sys | 实验室与设备处 | https://sys.xidian.edu.cn/tzgg.htm |

## 快速开始

```bash
# 安装依赖
uv sync

# 运行爬取
uv run bulletin -v

# 查看输出
ls output/
```

## API 端点

部署到 GitHub Pages 后：

- `feed.json` — 全部通知（按发布时间倒序，受 `content_limit` 限制）
- `sources/{source_id}.json` — 单个数据源全部通知
- `index.md` — API 目录与使用指引

## 添加新数据源

1. 编辑 `config/sources.yaml`，添加新的 source 配置
2. 如果新站点使用相同 CMS，只需配置 `base_url` 和 `list_path`
3. 如果站点格式不同，在 `src/bulletin/adapters/` 下新建 adapter 并注册

## 项目结构

```
src/bulletin/
├── main.py          # CLI 入口
├── config.py        # 配置加载
├── models.py        # 数据模型
├── store.py         # JSON 存储
├── adapters/
│   ├── base.py      # 适配器基类
│   └── xidian_cms.py # 博达 CMS 适配器
└── utils/
    └── http.py      # HTTP 客户端
```
