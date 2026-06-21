"""TOPOLOGY_TEMPLATES - 网格拓扑模板."""

TOPOLOGY_TEMPLATES = {
    "Square": {
        "description": "正方形网格 [经典/标准]",
        "notes": "标准正方形网格，4邻域或8邻域",
        "neighbors": "[(i+1,j), (i-1,j), (i,j+1), (i,j-1)]  # 4邻域",
    },
    "Hexagonal": {
        "description": "六边形网格 [生物/空间]",
        "notes": "六边形网格，更自然的邻近关系",
        "neighbors": "[(i+1,j), (i-1,j), (i,j+1), (i,j-1), (i+1,j+1), (i-1,j-1)]  # 奇偶行不同",
    },
    "Triangular": {
        "description": "三角形网格 [数学/镶嵌]",
        "notes": "三角形镶嵌网格",
        "neighbors": "6个邻域（取决于方向）",
    },
    "Torus": {
        "description": "环面网格 [数学/拓扑]",
        "notes": "周期边界的正方形网格",
        "neighbors": "同Square，但边界相连",
    },
    "KleinBottle": {
        "description": "Klein瓶网格 [数学/拓扑]",
        "notes": "非定向曲面，一边周期一边反射",
        "neighbors": "复杂边界条件",
    },
    "Super_Topology": {
        "description": "拓扑超级公式 [超级公式]",
        "notes": "可调拓扑；p1=拓扑类型(0=方形,1=六边形,2=三角形)，f1=曲率",
        "formula": "adjust_neighbors_by_topology(i, j, p1, f1)",
    },
}
