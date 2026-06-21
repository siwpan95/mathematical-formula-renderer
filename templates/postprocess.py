"""POSTPROCESS_TEMPLATES - 后处理特效模板."""

POSTPROCESS_TEMPLATES = {
    "GaussianBlur": {
        "description": "高斯模糊 [图像/平滑]",
        "notes": "使用高斯核模糊图像",
        "formula": "sum(grid[i+di, j+dj] * exp(-(di**2+dj**2)/sigma**2) for di, dj in neighbors) / sum(exp(-(di**2+dj**2)/sigma**2))",
    },
    "EdgeDetect": {
        "description": "边缘检测 [图像/特征]",
        "notes": "使用Sobel算子检测边缘",
        "formula": "sqrt((grid[i+1, j] - grid[i-1, j])**2 + (grid[i, j+1] - grid[i, j-1])**2)",
    },
    "Sharpen": {
        "description": "锐化 [图像/增强]",
        "notes": "增强边缘对比度",
        "formula": "grid[i, j] + alpha * (grid[i, j] - avg_n)",
    },
    "Bloom": {
        "description": "泛光效果 [渲染/特效]",
        "notes": "高亮区域向外扩散",
        "formula": "grid[i, j] + intensity * max(0, grid[i, j] - threshold)",
    },
    "MotionTrail": {
        "description": "运动轨迹 [渲染/特效]",
        "notes": "保留前一帧的残影",
        "formula": "alpha * grid[i, j] + (1-alpha) * prev_grid[i, j]",
    },
    "Invert": {
        "description": "反色 [图像/调整]",
        "notes": "反转颜色值",
        "formula": "1 - grid[i, j]",
    },
    "Vignette": {
        "description": "暗角效果 [渲染/特效]",
        "notes": "边缘变暗，中心保持不变",
        "formula": "grid[i, j] * (1 - vignette_strength * ((i/N-0.5)**2 + (j/N-0.5)**2))",
    },
    "Super_Blur": {
        "description": "模糊超级公式 [超级公式]",
        "notes": "可调模糊；f1=模糊半径，f2=模糊强度",
        "formula": "sum(grid[i+di, j+dj] for di in range(-f1, f1+1) for dj in range(-f1, f1+1)) / ((2*f1+1)**2)",
    },
}
