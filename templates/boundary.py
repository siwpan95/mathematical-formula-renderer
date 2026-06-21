"""BOUNDARY_TEMPLATES - 边界条件模板.
边界条件影响邻域计算，通过修改 avg_n 和 sum_n 的计算方式实现。
"""

BOUNDARY_TEMPLATES = {
    "Periodic": {
        "description": "周期边界（环面） [经典/拓扑]",
        "notes": "网格上下左右相连，形成环面。邻域计算自动环绕。",
    },
    "Reflective": {
        "description": "反射边界 [经典/对称]",
        "notes": "边界处反射，邻域计算时超出边界的索引被反射回内部。",
    },
    "Absorbing": {
        "description": "吸收边界（开放） [物理/开放]",
        "notes": "边界处值为0，超出边界的邻域贡献为0。",
    },
    "Dirichlet": {
        "description": "Dirichlet边界（固定值） [数学/PDE]",
        "notes": "边界处固定为指定值（通常为0或1）。",
    },
    "Neumann": {
        "description": "Neumann边界（零梯度） [数学/PDE]",
        "notes": "边界处梯度为0，值等于最近内点的值。",
    },
    "Super_Boundary": {
        "description": "边界条件超级公式 [超级公式]",
        "notes": "可调边界条件；p1=边界类型(0=周期,1=反射,2=吸收,3=Dirichlet,4=Neumann)，w1=边界固定值",
    },
}
