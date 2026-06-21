"""NEIGHBORHOOD_TEMPLATES - 邻域模式模板."""

NEIGHBORHOOD_TEMPLATES = {
    "Moore": {
        "description": "Moore邻域（8邻域） [经典/CA]",
        "notes": "包括对角线邻域",
        "neighbors": "[(i+di, j+dj) for di in [-1,0,1] for dj in [-1,0,1] if not (di==0 and dj==0)]",
    },
    "VonNeumann": {
        "description": "von Neumann邻域（4邻域） [经典/CA]",
        "notes": "仅上下左右邻域",
        "neighbors": "[(i+1,j), (i-1,j), (i,j+1), (i,j-1)]",
    },
    "Hexagonal": {
        "description": "六边形邻域（6邻域） [生物/空间]",
        "notes": "六边形网格的邻域",
        "neighbors": "[(i+1,j), (i-1,j), (i,j+1), (i,j-1), (i+1,j+1), (i-1,j-1)]",
    },
    "Radius2": {
        "description": "半径2邻域 [扩展/CA]",
        "notes": "扩展邻域，半径2",
        "neighbors": "[(i+di, j+dj) for di in range(-2,3) for dj in range(-2,3) if not (di==0 and dj==0)]",
    },
    "Weighted": {
        "description": "加权邻域 [物理/连续]",
        "notes": "根据距离加权的邻域",
        "neighbors": "[(i+di, j+dj, weight) for di, dj, weight in weights]",
    },
    "Super_Neighborhood": {
        "description": "邻域超级公式 [超级公式]",
        "notes": "可调邻域；f1=半径，f2=形状(0=方形,1=圆形)，w1=权重衰减",
        "formula": "sum(grid[i+di, j+dj] * exp(-w1*(di**2+dj**2)) for di in range(-f1,f1+1) for dj in range(-f1,f1+1) if (di**2+dj**2 <= f1**2 or f2==0))",
    },
}
