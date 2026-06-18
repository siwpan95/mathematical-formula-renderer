# 超级公式模板 — 局限性与未实现部分

## 概述

本文档记录超级公式模板的实现情况，以及哪些数学公式/系统**无法**被统一到单个超级公式中。

---

## ✅ 已实现（可参数化）

### Init 超级公式（6个）
- `Super_SineField` — 正弦场（含棋盘、条纹、波包）
- `Super_Gaussian` — 高斯（可调位置、宽度）
- `Super_PerlinLike` — Perlin类噪声（多频叠加）
- `Super_Checker` — 棋盘（连续）
- `Super_Spiral` — 螺旋（可调臂数、密度）
- `Super_WavePacket` — 波包（高斯×振荡）

### Evolution 超级公式（5个）
- `Super_EvolutionFourier` — Fourier反应扩散（f1=扩散，f2=反应，w1=非线性）
- `Super_CoupledMap` — 耦合映射（f1=耦合，f2=混沌）
- `Super_Threshold` — 阈值扩散（f1=扩散，f2=阈值偏好）
- `Super_Oscillation` — 时间振荡（f1=扩散，f2=振荡振幅）
- `Super_ReactionDiffusion` — 广义反应扩散（f1=扩散，f2=反应速率，w1=偏好值）

### Color 超级公式（7个）
- `Super_IQPalette` — IQ色板（p1-p3频率，d1-d3相位）
- `Super_WarmCool` — 冷暖（f1,f2频率，d1,d2相位）
- `Super_Phase` — 相位（f1-f3频率，p1-p3相位）
- `Super_Contrast` — 对比度（c1-c3各通道对比度）
- `Super_Gradient` — 渐变（a1-a3偏移，b1-b3斜率）
- `Super_SinePalette` — 正弦调色板（f1-f3频率，g1-g3增益）
- `Super_Thermal` — 热力图（f1红，f2绿，f3蓝标度）

---

## ❌ 无法实现（或极难实现）

### 1. 统一 Init + Evolution + Color 为单个公式

**原因：** 这三类公式在数学本质上是不同的：
- Init: 空间函数 `f(x, y)` — 定义初始状态
- Evolution: 迭代函数 `g(c, neighbors, t)` — 定义状态更新
- Color: 映射函数 `h(v)` — 定义可视化

它们操作在不同的变量上，无法用单个表达式统一。

**替代方案：** 每个类别单独做超级公式（已实现）。

---

### 2. 将 Game of Life 与 ODE（如 Lorenz）统一到同一个 Evolution 超级公式

**原因：** 
- Game of Life 是**离散**的（状态0或1，邻居计数）
- ODE 是**连续**的（状态是实数，导数驱动）

虽然 `Super_ReactionDiffusion` 可以用连续值近似一些离散行为，但无法精确复现 GoL 的规则。

**替代方案：** 
- 用连续值近似离散规则（如 `1 if (c > 0.5 and 2 <= sum_n <= 3) or (c <= 0.5 and sum_n == 3) else 0`）
- 但这会失去 GoL 的一些精确特性（如滑翔机）

---

### 3. 将反应扩散（Gray-Scott）与 CA（Game of Life）统一

**原因：** 反应扩散是**连续偏微分方程**，CA 是**离散格点规则**。虽然都可以用 `c + f1*(avg_n - c) + f2*R(c, neighbors)` 形式近似，但：
- 反应项 `R` 对不同系统差异极大
- Gray-Scott 需要**两个场**（U 和 V），而 GoL 只需要一个场

**替代方案：** `Super_ReactionDiffusion` 提供了一个通用框架，但需要根据具体系统调整 `w1` 参数。

---

### 4. 将分形（如 Mandelbrot）与周期图案（如条纹）统一到 Init 超级公式

**原因：** 分形需要**迭代**（如 `z = z^2 + c`），而 `templates.py` 的 init 表达式只能是 `x, y` 的单次表达式，不能包含循环。

**替代方案：** 用近似方法（如 `sin(3*pi*x)*sin(9*pi*x)*...` 近似 Cantor 集），但无法精确生成 Mandelbrot 集。

---

### 5. 将湍流（Navier-Stokes）与简单扩散统一到 Evolution 超级公式

**原因：** 湍流是**非线性偏微分方程**，需要模拟速度场、压力场等。用简单的细胞自动机式更新规则无法精确模拟。

**替代方案：** 用耦合映射网格（CML）近似，但精度有限。

---

### 6. 将吸引子（Lorenz, Rossler）与 CA 统一到同一个 Color 超级公式

**原因：** 吸引子色板是基于**相位**的（如 `cos(2*pi*v)`），而 CA 可视化通常基于**状态值**（如 `v` 直接映射灰度）。虽然可以用 `Super_Phase` 统一一些相位类色板，但无法统一所有类型。

**替代方案：** 根据可视化需求手动选择色板。

---

## 🔶 部分实现（有局限）

### 1. Evolution 超级公式中的 `neighbors` 访问

**局限：** `Super_EvolutionFourier` 等公式只使用了 `avg_n`（平均邻居值），而没有使用个别邻居值 `neighbors[0]` 等。这限制了表达各向异性行为的能力。

**改进方向：** 在超级公式中加入 `neighbors[i]` 访问，但这会增加参数数量。

---

### 2. Init 超级公式中的 `random()` 控制

**局限：** `Super_PerlinLike` 等噪声公式使用了固定的随机种子（每次运行相同）。无法在超级公式中动态调整随机性。

**改进方向：** 加入 `random()` 调用，但这会使结果不可复现。

---

### 3. Color 超级公式中的 `clip()` 依赖

**局限：** `Super_Gradient` 等公式使用了 `clip()` 函数，这需要引擎支持。如果引擎不支持 `clip()`，这些公式会失败。

**改进方向：** 用 `min(max(...))` 替代 `clip()`，但需要确认引擎支持。

---

## 总结

| 类别 | 已实现 | 未实现 | 原因 |
|------|--------|--------|------|
| Init 超级公式 | 6个 | 分形精确生成 | 需要迭代，表达式不支持 |
| Evolution 超级公式 | 5个 | CA与ODE统一 | 离散vs连续本质不同 |
| Color 超级公式 | 7个 | 所有色板统一 | 色板设计目标不同 |
| 跨类别统一 | ❌ | Init+Evolution+Color | 数学本质不同 |

**建议：** 使用已实现的18个超级公式作为起点，根据具体问题调整参数。如需更精确的控制，使用专项模板（如 `GameOfLife`, `Mandelbrot` 等）。
