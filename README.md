# CA Render Engine

> 连续细胞自动机（Continuous Cellular Automata）可视化引擎  
> ECS 架构 · 数学公式驱动 · 192 配方 · 后处理特效

---

## 快速开始

```bash
pip install numpy scipy pygame asteval
python main.pyw
```

启动后通过**侧边栏**浏览和切换配方：分类下拉 → 搜索过滤 → 点击配方 → 「▶ 渲染」按钮。

---

## 架构

```
main.pyw → CAWorld (core/world.py)
            ├── systems/        EvolutionSystem / ColorSystem / RenderSystem / UISystem
            ├── components/     Grid / Formula / Config / PostProcess
            ├── entities/       RecipeEntity / TemplateRegistry
            ├── templates/      公式模板（init / evolution / color / boundary / neighborhood / postprocess / topology）
            ├── ui/             UI 组件（widgets.py）
            └── resources/     字体等资源文件
```

---

## 功能概览

| 功能 | 说明 |
|------|------|
| **192 配方** | effects/ 目录下的 JSON 配方文件 |
| **153 公式模板** | 初始化(77) + 演化规则(42) + 颜色映射(34) |
| **分类下拉** | 按类别筛选配方，显示各分类数量 |
| **搜索过滤** | 实时搜索 + 匹配高亮 |
| **选择确认** | 点击配方预览，确认后渲染（避免误触） |
| **键盘导航** | ↑↓ 导航列表 / Enter 选中 / Esc 清空搜索 |
| **后处理特效** | 辉光、边缘检测、运动轨迹、反色、暗角 |
| **颜色预设** | 9 种运行时颜色方案，一键切换 |
| **自动播放** | 定时循环切换配方 |
| **缩放** | 自适应窗口，支持全屏 |
| **过渡动画** | 配方切换时交叉淡入淡出 |
| **HUD 信息** | FPS、步数、统计、特效/状态指示 |
| **截图** | 一键保存 PNG 到 screenshots/ |
| **循环重置** | 配方内配置 cycle 自动周期性重置 |

---

## 使用方式

```bash
# 启动主程序（ECS 模式）
python main.pyw

# 打印模板详情
python main.pyw --template init       # 初始化公式 (77 个)
python main.pyw --template evolution  # 演化规则 (42 个)
python main.pyw --template color      # 颜色映射 (34 个)
python main.pyw --template all        # 全部

# 列出所有模板名称
python main.pyw --template-list

# 命令行生成配方
python main.pyw --generate "中心脉冲" "BZ反应模拟" "极光" "我的配方"
```

---

## 模板系统

### 初始化公式（77 个）

定义网格初始状态，变量：`x`, `y`, `random`

| 模板 | 效果 |
|------|------|
| 纯随机、白噪声、粉红噪声 | 随机/噪声 |
| 中心脉冲、多重斑点、高斯环 | 高斯分布 |
| 条纹、棋盘、六角网格、蜂窝 | 几何图案 |
| 螺旋波、漩涡场、Lissajous | 复杂波形 |
| Mandelbrot、Cantor、Sierpinski | 分形 |
| 双缝干涉、驻波、平面波 | 波动/物理 |
| 梯度、径向渐变 | 渐变 |

### 演化规则（42 个）

定义每步状态更新，变量：`c`, `sum_n`, `avg_n`, `x`, `y`, `t`

| 类别 | 模板 | 特点 |
|------|------|------|
| 经典 CA | Game of Life、Smooth Life | 生命游戏 |
| 反应扩散 | Gray-Scott、斑点、条纹、迷宫 | 图灵图案 |
| 激发介质 | 激发介质、BZ反应、FitzHugh–Nagumo | 螺旋波 |
| 混沌 | 逻辑斯蒂耦合、混沌耦合映射 | 分形 |
| 扩散 | 纯扩散、各向异性扩散、对流湍流 | 物理模拟 |
| 超级公式 | 反应扩散/耦合映射/振荡超级公式 | 参数调节 |

### 颜色映射（34 个）

RGB 三通道映射，变量：`v`, `x`, `y`

| 模板 | 风格 |
|------|------|
| 灰阶、反色、二值化 | 黑白 |
| 热力图、彩虹、冷暖渐变 | 渐变 |
| 春/夏/秋/冬 | 季节色 |
| 极光、霓虹、赛博朋克 | 特殊风格 |
| 相位色、方向色 | 相位映射 |

---

## JSON 配方格式

```json
{
  "name": "配方名称",
  "version": "1.0",
  "description": "描述",
  "grid": {
    "width": 256,
    "height": 192,
    "wrap": true,
    "initial": {
      "type": "formula",
      "expression": "exp(-((x-0.5)**2 + (y-0.5)**2) / 0.02)"
    }
  },
  "neighborhood": {
    "type": "moore",
    "radius": 1
  },
  "evolution": {
    "rule": "c + 0.16*(avg_n - c) + 0.045*c*(1-c) - 0.02*c",
    "variables": ["c", "avg_n"]
  },
  "color": {
    "mode": "per_channel",
    "red": "v",
    "green": "v",
    "blue": "v"
  },
  "tick": {
    "fps": 30,
    "steps_per_frame": 1
  },
  "cycle": {
    "steps": 300
  }
}
```

| 字段 | 说明 |
|------|------|
| `grid.initial.expression` | 初始化公式 (变量: x, y, random) |
| `evolution.rule` | 演化公式 (变量: c, sum_n, avg_n, x, y, t) |
| `color.red/green/blue` | RGB 颜色映射 (变量: v, x, y) |
| `cycle.steps` | 循环步数 (0=不循环) |
| `tick.fps` / `tick.steps_per_frame` | 帧率 / 每帧步数 |

---

## 后处理特效

| 特效 | 效果 |
|------|------|
| none | 无特效 |
| bloom | 辉光（高斯模糊叠加） |
| edge | 边缘检测（Sobel 算子） |
| motion_trail | 运动轨迹（历史帧叠加） |
| invert | 反色 |
| vignette | 暗角 |

## 颜色预设

| 预设 | 风格 |
|------|------|
| default | 原始颜色 |
| fire | 火焰红 |
| ocean | 海洋蓝 |
| sunset | 日落橙 |
| rainbow | 彩虹 |
| neon | 霓虹 |
| ice | 冰霜 |
| invert | 反色 |
| thermal | 热力图 |

---

## 项目结构

```
draw/
├── main.pyw             # 程序入口
├── requirements.txt     # Python 依赖
├── run.bat              # Windows 快速启动
├── .gitignore           # Git 忽略规则
├── README.md            # 本文件
├── components/          # ECS 组件层（纯数据）
│   ├── __init__.py
│   ├── config.py        #   配方配置
│   ├── formula.py       #   编译后的公式函数
│   ├── grid.py          #   网格状态
│   └── postprocess.py   #   后处理特效状态
├── core/                # 核心模块
│   ├── __init__.py
│   └── world.py         #   CAWorld 主循环调度器
├── entities/            # ECS 实体层
│   ├── __init__.py
│   ├── recipe.py        #   RecipeEntity 配方实体
│   └── registry.py      #   TemplateRegistry 模板注册表
├── systems/             # ECS 系统层
│   ├── __init__.py
│   ├── evolution.py     #   网格演化系统
│   ├── colormap.py      #   颜色映射系统
│   ├── render.py        #   Pygame 渲染系统
│   └── ui.py            #   UI 事件系统
├── templates/           # 公式模板库（153 个数学公式）
│   ├── __init__.py
│   ├── init.py          #   初始化公式模板
│   ├── evolution.py     #   演化规则模板
│   ├── color.py         #   颜色映射模板
│   ├── boundary.py      #   边界处理模板
│   ├── neighborhood.py  #   邻域模板
│   ├── postprocess.py   #   后处理模板
│   ├── recipes.py       #   配方模板
│   ├── super_params.py  #   超级参数模板
│   └── topology.py      #   拓扑模板
├── ui/                  # UI 组件
│   ├── __init__.py
│   └── widgets.py       #   HUD / 下拉菜单 / 搜索框 / 确认面板 / 特效
├── tools/               # 开发工具脚本
│   ├── split_templates.py    # 拆分模板文件
│   ├── split_v2.py           # 拆分工具 v2
│   ├── update_categories.py  # 更新配方分类
│   ├── verify_all.py         # 验证所有配方
│   └── verify_super.py       # 验证超级公式
├── resources/           # 资源文件
│   └── NotoSansSC-VF.ttf  # 中文字体（Noto Sans SC）
├── docs/                # 文档
│   └── render_optimization.md  # 渲染优化笔记
├── effects/             # 192 个 JSON 配方文件
└── screenshots/         # 截图输出目录
```

---

## 依赖

- **numpy** — 网格数组运算
- **scipy** — 卷积、高斯滤波、边缘检测
- **pygame** — 窗口、渲染、事件处理
- **asteval** — 安全表达式求值

## License

MIT
