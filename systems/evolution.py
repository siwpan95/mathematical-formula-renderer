"""
EvolutionSystem — CA 演化系统
================================
源自：engine.CARenderEngine
    - _build_kernel()          → _build_kernel()（搬过来）
    - _build_coordinate_grids() → _init_grid_component()
    - _reset_grid()             → reset_grid()
    - step()                    → update()
    - _compile / _compile_*     → _compile()（搬过来，后续可分离为 FormulaCompilerSystem）

职责：
    每帧对 RecipeEntity 的 GridComponent 执行一次演化步骤。
    首次（dirty=True）时负责编译公式并初始化网格。

调用顺序（World 主循环）：
    EvolutionSystem.update(entity) → 演化一步，更新 grid.data
    ColorSystem.update(entity)     → 读取 grid.data，写入 grid.rgb_hw
    RenderSystem.draw(entity)      → 读取 grid.rgb_hw，blit 到屏幕
"""

from __future__ import annotations
import re
import numpy as np
from scipy.ndimage import convolve
from asteval import Interpreter

from entities.recipe import RecipeEntity
from components.grid import GridComponent
from components.formula import FormulaComponent
from components.config import ConfigComponent


class EvolutionSystem:
    """CA 演化系统（对应 engine.CARenderEngine 的计算核心）。

    使用方式：
        system = EvolutionSystem()
        system.update(entity)   # 每帧调用

    system 本身无状态，全部状态在 entity.grid / entity.formula 中。
    """

    # ================================================================
    #  对外接口（System 标准 API）
    # ================================================================

    def update(self, entity: RecipeEntity):
        """演化一帧（支持 steps_per_frame）"""
        if entity._dirty:
            self._initialize(entity)

        grid = entity.grid
        formula = entity.formula
        cfg = entity.config

        spf = cfg.steps_per_frame
        for _ in range(spf):
            self._step(grid, formula, cfg)

    def reset(self, entity: RecipeEntity):
        """强制重置网格和时间步"""
        self._reset_grid(entity.grid, entity.formula, entity.config)
        entity.grid.reset_t()

    # ================================================================
    #  初始化（dirty 时调用）
    # ================================================================

    def _initialize(self, entity: RecipeEntity):
        """编译公式 + 初始化网格（对应 engine.load_config 的后半段）"""
        cfg = entity.config
        grid = entity.grid
        formula = entity.formula

        # 更新网格尺寸（配方切换时可能变更）
        grid.w = cfg.grid_w
        grid.h = cfg.grid_h
        grid.wrap = cfg.wrap

        # 编译公式（共享 _cache）
        self._compile_all(cfg, formula)

        # 构建邻域核
        grid.build_kernel(cfg.topology, cfg.nb_type, cfg.nb_radius)

        # 构建坐标系
        self._build_coords(grid)

        # 预分配颜色缓冲（rgb_wh 为主，rgb_hw 由 ColorSystem 设为视图）
        grid.rgb_wh = np.zeros((grid.w, grid.h, 3), dtype=np.uint8)
        grid.rgb_hw = None  # 由 ColorSystem.update() 设为 rgb_wh 的转置视图

        # 初始化网格
        self._reset_grid(grid, formula, cfg)
        grid.reset_t()

        entity.mark_clean()
        print(f"[EvolutionSystem] 初始化完成: {cfg.name} ({grid.w}×{grid.h})")

    # ================================================================
    #  公式编译（对应 engine._compile / _compile_numeric / _compile_logic）
    # ================================================================

    def _compile_all(self, cfg: ConfigComponent, formula: FormulaComponent):
        """编译所有公式并写入 FormulaComponent"""
        formula.init_fn = self._compile(
            cfg.init_expr, ['x', 'y', 'i', 'j', 'random'], formula._cache)
        formula.rule_fn = self._compile(
            cfg.evolution_rule, cfg.evolution_vars, formula._cache)
        for ch in ['red', 'green', 'blue']:
            expr = getattr(cfg, f'color_{ch}')
            formula.color_fns[ch] = self._compile(
                expr, ['v', 'x', 'y'], formula._cache)

    _IF_ELSE_PAT = re.compile(r'\bif\b|\belse\b')

    @classmethod
    def _ifelse_to_where(cls, expr: str) -> str:
        """稳健地将 Python 三元表达式转换为 NumPy where()。

        逐层剥离：先找最内层（括号深度最大）的 if-else 替换为 where()，
        然后逐层向外，彻底解决嵌套 if-else 的误匹配问题。

        示例：
            c if c > 0 else (1 if n > 2 else 0)
            → where(c > 0, c, where(n > 2, 1, 0))
        """
        for _ in range(10):
            # 1. 扫描所有 if/else 及其深度
            tokens = []
            for m in cls._IF_ELSE_PAT.finditer(expr):
                pos = m.start()
                depth = expr[:pos].count('(') - expr[:pos].count(')')
                tokens.append((pos, m.group(), depth))

            # 2. 配对 if-else：找每个 if 后第一个同深度 else
            pairs = []
            i = 0
            while i < len(tokens):
                if tokens[i][1] == 'if':
                    if_depth = tokens[i][2]
                    j = i + 1
                    while j < len(tokens):
                        if tokens[j][1] == 'else' and tokens[j][2] == if_depth:
                            pairs.append((tokens[i][0], tokens[j][0], if_depth))
                            i = j + 1
                            break
                        j += 1
                    else:
                        i += 1
                else:
                    i += 1

            if not pairs:
                break

            # 3. 取最内层（深度最大）的 if-else，若有并列取最靠右的
            pairs.sort(key=lambda x: (x[2], x[0]), reverse=True)
            if_pos, else_pos, depth = pairs[0]

            # 4. 确定 if-else 所在子表达式的边界
            #    向左找深度下降点（即包裹这个 if-else 的 '(' )
            left = 0
            for k in range(if_pos - 1, -1, -1):
                d = expr[:k].count('(') - expr[:k].count(')')
                if d < depth:
                    left = k + 1
                    break

            #    向右找深度下降点（即包裹这个 if-else 的 ')' ）
            right = len(expr)
            for k in range(else_pos + 4, len(expr)):
                d = expr[:k].count('(') - expr[:k].count(')')
                if d < depth:
                    right = k
                    break

            # 5. 提取 true / condition / false
            sub = expr[left:right]
            # sub = " true_val if condition else false_val "
            inner_if = sub.index(' if ')
            inner_else = sub.index(' else ')
            true_val = sub[:inner_if].strip()
            condition = sub[inner_if + 4:inner_else].strip()
            false_val = sub[inner_else + 6:].strip()

            # 6. 替换
            replacement = f'where({condition}, {true_val}, {false_val})'
            expr = expr[:left] + replacement + expr[right:]

        return expr

    def _compile(self, expr: str, var_names: list[str], cache: dict):
        """编译单个表达式（对应 engine._compile）"""
        cache_key = (expr, tuple(var_names))
        if cache_key in cache:
            return cache[cache_key]

        # Python if-else → where() 转换（稳健版）
        processed = self._ifelse_to_where(expr)

        # min/max → minimum/maximum（engine 要求）
        processed = re.sub(r'\bmin\(', 'minimum(', processed)
        processed = re.sub(r'\bmax\(', 'maximum(', processed)

        # and/or/not → NumPy &/|/~ （添加括号保护优先级）
        processed = self._convert_logic_ops(processed)

        func = self._compile_numeric(processed)
        cache[cache_key] = func
        return func

    @staticmethod
    def _convert_logic_ops(expr: str) -> str:
        """将 Python 逻辑运算符 and/or/not 转换为 NumPy &/|/~。

        自动为操作数添加括号，解决 NumPy & 优先级高于 > < == 的问题。

        示例：
            sum_n >= 0.5 and random() < 0.1
            → (sum_n >= 0.5) & (random() < 0.1)

            n == 2 or n == 3
            → (n == 2) | (n == 3)

            not c and n > 2
            → ((~c) & (n > 2))
        """
        # ---- 第 1 步：处理 not ----
        # not<expr> → ~(<expr>)，扫描右操作数并自动包裹括号
        # 必须在检查 and/or 关键字边界，防止越界
        _KW_RE = re.compile(r'\band\b|\bor\b')
        while True:
            m = re.search(r'\bnot\b', expr)
            if not m:
                break
            start = m.start()
            end = m.end()

            # 构建当前关键字位置（用于边界检查）
            kw_positions = {kw.start() for kw in _KW_RE.finditer(expr)}

            # 扫描右操作数边界
            right_boundary = len(expr)
            depth = 0
            for i in range(end, len(expr)):
                ch = expr[i]
                if ch == '(':
                    depth += 1
                elif ch == ')':
                    if depth == 0:
                        right_boundary = i
                        break
                    depth -= 1
                elif ch == ',' and depth == 0:
                    right_boundary = i
                    break
                elif i in kw_positions and depth == 0:
                    # 遇到 and/or 关键字，停止
                    right_boundary = i
                    break
            operand = expr[end:right_boundary].strip()

            # 替换 not<operand> → logical_not(operand)
            expr = expr[:start] + f'logical_not({operand})' + expr[right_boundary:]

        # ---- 第 2 步：处理 and/or（左到右，每轮重新定位）----
        while True:
            m = re.search(r'\band\b|\bor\b', expr)
            if not m:
                break
            start, end = m.start(), m.end()
            op = m.group()

            # 构建当前字符串中所有关键字位置（用作边界）
            kw_positions = {kw.start()
                            for kw in re.finditer(r'\band\b|\bor\b', expr)}

            # --- 左操作数 ---
            left_boundary = 0
            depth = 0
            for i in range(start - 1, -1, -1):
                ch = expr[i]
                if ch == ')':
                    depth += 1
                elif ch == '(':
                    if depth == 0:
                        left_boundary = i + 1
                        break
                    depth -= 1
                elif ch == ',' and depth == 0:
                    left_boundary = i + 1
                    break
                elif i in kw_positions and depth == 0:
                    # 遇到另一个 and/or 关键字 — 找到其末尾作为边界
                    kw_m = re.match(r'\band\b|\bor\b', expr[i:])
                    left_boundary = i + (kw_m.end() if kw_m else 3)
                    break
            left = expr[left_boundary:start].strip()

            # --- 右操作数 ---
            right_boundary = len(expr)
            depth = 0
            for i in range(end, len(expr)):
                ch = expr[i]
                if ch == '(':
                    depth += 1
                elif ch == ')':
                    if depth == 0:
                        right_boundary = i
                        break
                    depth -= 1
                elif ch == ',' and depth == 0:
                    right_boundary = i
                    break
                elif i in kw_positions and depth == 0:
                    right_boundary = i
                    break
            right = expr[end:right_boundary].strip()

            # --- 替换 ---
            new_op = '&' if op == 'and' else '|'
            replacement = f'({left}) {new_op} ({right})'
            expr = expr[:left_boundary] + replacement + expr[right_boundary:]

        return expr

    def _compile_numeric(self, processed: str):
        """纯数值向量化路径（对应 engine._compile_numeric）"""
        ns = {
            'sin': np.sin, 'cos': np.cos, 'tan': np.tan,
            'exp': np.exp, 'log': np.log, 'sqrt': np.sqrt,
            'abs': np.abs, 'pi': np.pi, 'e': np.e,
            'minimum': np.minimum, 'maximum': np.maximum,
            'min': min, 'max': max,
            'amin': np.amin, 'amax': np.amax,
            'where': np.where, 'clip': np.clip,
            'logical_not': np.logical_not,
            'floor': np.floor, 'ceil': np.ceil, 'round': np.round,
            'random': lambda *a: np.random.random(a[0] if a else None),
        }

        def func(**kwargs):
            first_arr = next((v for v in kwargs.values()
                              if isinstance(v, np.ndarray) and v.ndim == 2), None)
            if first_arr is not None:
                ns['random'] = lambda *a: np.random.random(first_arr.shape)
            else:
                ns['random'] = lambda *a: np.random.random()
            try:
                result = eval(processed, {"__builtins__": {}}, {**ns, **kwargs})
                return np.asarray(result, dtype=np.float64)
            except KeyboardInterrupt:
                raise
            except Exception:
                return np.float64(0.0)
        return func

    def _compile_logic(self, processed: str, var_names: list[str]):
        """逻辑路径（含 and/or/not，逐像素）（对应 engine._compile_logic）"""
        ae = Interpreter()
        ae.symtable.update({
            'sin': np.sin, 'cos': np.cos, 'exp': np.exp,
            'abs': abs, 'sqrt': np.sqrt,
            'random': np.random.random,
            'clip': np.clip, 'min': min, 'max': max, 'where': np.where,
        })

        def func(**kwargs):
            first_val = next(iter(kwargs.values()), None)
            if isinstance(first_val, np.ndarray) and first_val.ndim == 2:
                h, w = first_val.shape
                result = np.zeros((h, w), dtype=np.float64)
                for i in range(h):
                    for j in range(w):
                        for k in var_names:
                            v = kwargs.get(k)
                            ae.symtable[k] = (v[i, j]
                                              if isinstance(v, np.ndarray) and v.ndim == 2
                                              else v)
                        ae.symtable['random'] = np.random.random
                        try:
                            result[i, j] = ae.eval(processed) or 0.0
                        except Exception:
                            result[i, j] = 0.0
                return result
            else:
                for k in var_names:
                    if k in kwargs:
                        ae.symtable[k] = kwargs[k]
                ae.symtable['random'] = np.random.random
                try:
                    return np.float64(ae.eval(processed) or 0.0)
                except Exception:
                    return np.float64(0.0)
        return func

    # ================================================================
    #  网格操作（对应 engine._build_kernel / _build_coordinate_grids / _reset_grid）
    # ================================================================

    def _build_kernel(self, nb_type: str, radius: int) -> np.ndarray:
        """构建邻域核（直接搬自 engine._build_kernel）"""
        size = 2 * radius + 1
        cx = cy = radius

        if nb_type in ('moore', 'square'):
            kernel = np.ones((size, size), dtype=np.float32)
            kernel[cx, cy] = 0.0
        elif nb_type in ('circle', 'circular'):
            y_idx, x_idx = np.ogrid[-radius:radius + 1, -radius:radius + 1]
            dist = np.sqrt(x_idx ** 2 + y_idx ** 2)
            kernel = (dist <= radius).astype(np.float32)
            kernel[cx, cy] = 0.0
        elif nb_type == 'ring':
            inner_r = radius * 0.4
            y_idx, x_idx = np.ogrid[-radius:radius + 1, -radius:radius + 1]
            dist = np.sqrt(x_idx ** 2 + y_idx ** 2)
            kernel = ((dist <= radius) & (dist >= inner_r)).astype(np.float32)
            kernel[cx, cy] = 0.0
        elif nb_type in ('cross', 'vonneumann', 'von_neumann'):
            kernel = np.zeros((size, size), dtype=np.float32)
            y_idx, x_idx = np.ogrid[-radius:radius + 1, -radius:radius + 1]
            dist_manhattan = np.abs(x_idx) + np.abs(y_idx)
            kernel[dist_manhattan <= radius] = 1.0
            kernel[cx, cy] = 0.0
        else:
            kernel = np.ones((size, size), dtype=np.float32)
            kernel[cx, cy] = 0.0

        return kernel

    def _build_coords(self, grid: GridComponent):
        """预计算归一化坐标网格（对应 engine._build_coordinate_grids）"""
        grid.x_coords = np.broadcast_to(
            np.linspace(0, 1, grid.w, endpoint=False,
                        dtype=np.float64).reshape(1, -1),
            (grid.h, grid.w)
        ).copy()
        grid.y_coords = np.broadcast_to(
            np.linspace(0, 1, grid.h, endpoint=False,
                        dtype=np.float64).reshape(-1, 1),
            (grid.h, grid.w)
        ).copy()

    def _reset_grid(self, grid: GridComponent, formula: FormulaComponent,
                    cfg: ConfigComponent):
        """用 init_fn 初始化网格（对应 engine._reset_grid）"""
        if grid.x_coords is None:
            self._build_coords(grid)

        i_grid = grid.y_coords * grid.h
        j_grid = grid.x_coords * grid.w

        try:
            val = formula.init_fn(
                x=grid.x_coords, y=grid.y_coords,
                i=i_grid, j=j_grid,
                random=np.random.random,
            )
            val = np.asarray(val, dtype=np.float32)
            if val.shape != (grid.h, grid.w):
                raise ValueError("shape mismatch")
            grid.data = np.clip(val, 0.0, 1.0).astype(np.float32)
        except Exception:
            grid.data = np.zeros((grid.h, grid.w), dtype=np.float32)
            for i in range(grid.h):
                for j in range(grid.w):
                    x = j / grid.w
                    y = i / grid.h
                    try:
                        val = formula.init_fn(x=x, y=y, i=float(i),
                                              j=float(j),
                                              random=np.random.random)
                        grid.data[i, j] = float(np.clip(val, 0.0, 1.0))
                    except Exception:
                        grid.data[i, j] = 0.0

    def _step(self, grid: GridComponent, formula: FormulaComponent,
              cfg: ConfigComponent):
        """执行一步演化（对应 engine.step）"""
        # 循环检测
        if cfg.cycle_steps > 0 and grid.t >= cfg.cycle_steps:
            self._reset_grid(grid, formula, cfg)
            grid.t = 0
            grid.total_cycles += 1
            return

        # 根据 boundary 配置选择卷积边界模式
        _boundary_map = {
            'periodic': 'wrap',
            'reflective': 'reflect',
            'absorbing': 'constant',
            'dirichlet': 'constant',
            'neumann': 'nearest',
        }
        mode = _boundary_map.get(cfg.boundary, 'wrap')
        cval = 0.0 if cfg.boundary != 'dirichlet' else cfg.get('boundary_value', 0.0)
        sum_n = convolve(grid.data, grid.kernel, mode=mode, cval=cval,
                         axes=(-2, -1))
        avg_n = sum_n / grid.kernel.sum()

        val = formula.rule_fn(
            c=grid.data, sum_n=sum_n, avg_n=avg_n,
            x=grid.x_coords, y=grid.y_coords,
            t=np.float64(grid.t),
            i=grid.y_coords * grid.h,
            j=grid.x_coords * grid.w,
        )
        val = np.asarray(val, dtype=np.float32)
        if val.shape != (grid.h, grid.w):
            val = np.broadcast_to(
                val.ravel()[0:1], (grid.h, grid.w)).astype(np.float32)
        grid.data = np.clip(val, 0.0, 1.0)
        grid.t += 1
