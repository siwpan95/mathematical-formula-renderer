"""
公式模板库 V2 — 含超级公式
==========================

包含所有 init / evolution / color 模板。
每个模板：
  - init:       {description, expression, notes}
  - evolution:  {description, expression, variables, notes}
  - color:      {description, red, green, blue, notes}
"""

FORMULA_TEMPLATES = {
    "init": {
        "PureRandom": {
            "description": "每个细胞随机初始值 [随机/噪声]",
            "expression": "random()",
            "notes": "完全随机的初始状态",
        },
        "HalfHalf": {
            "description": "约一半细胞为1 [随机/结构]",
            "expression": "1 if random() > 0.5 else 0",
            "notes": "经典二分初始",
        },
        "CenterDot": {
            "description": "中心单点激活 [结构/对称]",
            "expression": "1 if (abs(x-0.5) < 0.03 and abs(y-0.5) < 0.03) else 0",
            "notes": "单点种子",
        },
        "CenterCross": {
            "description": "中心十字 [结构/对称]",
            "expression": "1 if (abs(x-0.5) < 0.02 or abs(y-0.5) < 0.02) else 0",
            "notes": "十字种子",
        },
        "Diagonal": {
            "description": "对角线激活 [结构/对称]",
            "expression": "1 if (abs(x-y) < 0.03) else 0",
            "notes": "对角线渐变",
        },
        "Concentric": {
            "description": "同心圆 [结构/对称]",
            "expression": "1 if (abs(sqrt((x-0.5)**2 + (y-0.5)**2) - 0.3) < 0.02) else 0",
            "notes": "圆形波",
        },
        "Checkerboard": {
            "description": "棋盘格 [周期/结构]",
            "expression": "1 if ((int(x*20) + int(y*20)) % 2 == 0) else 0",
            "notes": "经典棋盘（用三角函数避免int）",
        },
        "StripesX": {
            "description": "竖直条纹 [周期/结构]",
            "expression": "1 if (sin(x*40) > 0) else 0",
            "notes": "竖直条纹",
        },
        "StripesY": {
            "description": "水平条纹 [周期/结构]",
            "expression": "1 if (sin(y*40) > 0) else 0",
            "notes": "水平条纹",
        },
        "Grid": {
            "description": "网格 [周期/结构]",
            "expression": "1 if (sin(x*30) * sin(y*30) > 0) else 0",
            "notes": "网格纹理",
        },
        "NoiseSmooth": {
            "description": "平滑噪声 [随机/噪声]",
            "expression": "0.5 + 0.5*random()",
            "notes": "平滑随机",
        },
        "GradientX": {
            "description": "水平渐变 [梯度/结构]",
            "expression": "x",
            "notes": "从左到右渐变",
        },
        "GradientY": {
            "description": "竖直渐变 [梯度/结构]",
            "expression": "y",
            "notes": "从上到下渐变",
        },
        "GradientRadial": {
            "description": "径向渐变 [梯度/对称]",
            "expression": "sqrt((x-0.5)**2 + (y-0.5)**2)",
            "notes": "从中心向外渐变",
        },
        "SineWave": {
            "description": "正弦波初始 [周期/波形]",
            "expression": "0.5 + 0.5*sin(x*20)",
            "notes": "正弦空间调制",
        },
        "CosineWave": {
            "description": "余弦波初始 [周期/波形]",
            "expression": "0.5 + 0.5*cos(y*20)",
            "notes": "余弦空间调制",
        },
        "SineRing": {
            "description": "正弦环 [周期/对称]",
            "expression": "0.5 + 0.5*sin(20*sqrt((x-0.5)**2 + (y-0.5)**2))",
            "notes": "环形正弦波",
        },
        "Spiral": {
            "description": "螺旋初始 [结构/对称]",
            "expression": "1 if ((atan2(y-0.5, x-0.5) / (2*pi) + sqrt((x-0.5)**2 + (y-0.5)**2) * 2) % 1 < 0.5) else 0",
            "notes": "螺旋相位近似",
        },
        "Diamond": {
            "description": "菱形 [结构/对称]",
            "expression": "1 if (abs(x-0.5) + abs(y-0.5) < 0.2) else 0",
            "notes": "菱形区域",
        },
        "FilledCircle": {
            "description": "实心圆 [结构/对称]",
            "expression": "1 if ((x-0.5)**2 + (y-0.5)**2 < 0.16) else 0",
            "notes": "圆形种子",
        },
        "Mandelbrot": {
            "description": "Mandelbrot集边界 [分形/复杂]",
            "expression": "1 if (abs(complex(x*3-1.5, y*3-1.5)) < 2) else 0",
            "notes": "Mandelbrot边界（需complex支持）",
        },
        "CantorDust": {
            "description": "Cantor尘埃近似 [分形/经典]",
            "expression": "1 if (cos(3*pi*x)*cos(9*pi*x)*cos(27*pi*x) > 0 and cos(3*pi*y)*cos(9*pi*y)*cos(27*pi*y) > 0) else 0",
            "notes": "Cantor集乘积近似（无int版本）",
        },
        "SierpinskiTrigger": {
            "description": "Sierpinski三角触发 [分形/经典]",
            "expression": "1 if (sin(x*511*pi)*sin(y*511*pi) > 0) else 0",
            "notes": "Sierpinski三角（三角函数近似）",
        },
        "DoubleSlit": {
            "description": "双缝干涉 [波动/物理]",
            "expression": "0.5 + 0.25*sin(30*sqrt((x-0.3)**2 + (y-0.5)**2)) + 0.25*sin(30*sqrt((x-0.7)**2 + (y-0.5)**2))",
            "notes": "双缝干涉图案",
        },
        "SingleSlit": {
            "description": "单缝衍射 [波动/物理]",
            "expression": "(sin(pi*10*sqrt((x-0.5)**2 + (y-0.5)**2)) / (pi*10*sqrt((x-0.5)**2 + (y-0.5)**2) + 0.001))**2",
            "notes": "单缝Airy盘近似",
        },
        "PlaneWave": {
            "description": "平面波 [波动/物理]",
            "expression": "0.5 + 0.5*sin(2*pi*(x*cos(0.3) + y*sin(0.3)))",
            "notes": "斜向平面波",
        },
        "StandingWave": {
            "description": "驻波 [波动/物理]",
            "expression": "(sin(2*pi*x*10))**2",
            "notes": "一维驻波",
        },
        "TuringSpot": {
            "description": "Turing斑点初始 [反应扩散/模式]",
            "expression": "0.5 + 0.5*sin(14*x)*sin(14*y) + 0.3*random()",
            "notes": "Turing斑点种子",
        },
        "TuringStripe": {
            "description": "Turing条纹初始 [反应扩散/模式]",
            "expression": "0.5 + 0.5*sin(14*x) + 0.3*random()",
            "notes": "Turing条纹种子",
        },
        "Percolation30": {
            "description": "30%渗流 [渗流/统计]",
            "expression": "1 if random() < 0.3 else 0",
            "notes": "30%渗流阈值附近",
        },
        "Percolation50": {
            "description": "50%渗流 [渗流/统计]",
            "expression": "1 if random() < 0.5 else 0",
            "notes": "50%渗流",
        },
        "Percolation60": {
            "description": "60%渗流 [渗流/统计]",
            "expression": "1 if random() < 0.6 else 0",
            "notes": "60%接近渗流阈值",
        },
        "CahnHilliard": {
            "description": "Cahn-Hilliard初始 [相分离/物理]",
            "expression": "0.5 + 0.5*random()",
            "notes": "白噪声初始（相分离用）",
        },
        "PointSource": {
            "description": "点源初始 [结构/对称]",
            "expression": "1 if ((x-0.5)**2 + (y-0.5)**2 < 0.001) else 0.01",
            "notes": "点源种子",
        },
        "RingSource": {
            "description": "环源初始 [结构/对称]",
            "expression": "1 if (abs(sqrt((x-0.5)**2 + (y-0.5)**2) - 0.3) < 0.02) else 0",
            "notes": "环形种子",
        },
        "FourSources": {
            "description": "四源初始 [结构/对称]",
            "expression": "1 if ((x-0.25)**2+(y-0.25)**2<0.01 or (x-0.75)**2+(y-0.25)**2<0.01 or (x-0.25)**2+(y-0.75)**2<0.01 or (x-0.75)**2+(y-0.75)**2<0.01) else 0",
            "notes": "四角种子",
        },
        "PinkNoise": {
            "description": "粉红噪声近似 [随机/噪声]",
            "expression": "0.5 + 0.5*sin(random()*100)*sin(random()*100)",
            "notes": "低频增强噪声",
        },
        "WhiteNoise": {
            "description": "白噪声 [随机/噪声]",
            "expression": "random()",
            "notes": "均匀白噪声",
        },
        "HexGrid": {
            "description": "六角网格 [周期/结构]",
            "expression": "1 if (sin(x*34.64) + sin(y*40) > 1.5) else 0",
            "notes": "六角密铺近似",
        },
        "BZSeed": {
            "description": "BZ反应种子 [反应扩散/模式]",
            "expression": "1 if (sin(10*x)*sin(10*y) > 0.5 and random() > 0.5) else 0",
            "notes": "BZ反应初始",
        },
        "Voronoi4": {
            "description": "4-cell Voronoi [镶嵌/结构]",
            "expression": "1 if (min(abs(x-0.2)+abs(y-0.2), abs(x-0.8)+abs(y-0.2), abs(x-0.2)+abs(y-0.8), abs(x-0.8)+abs(y-0.8)) < 0.1) else 0",
            "notes": "4-cell Voronoi近似",
        },
        "Gaussian": {
            "description": "高斯分布 [随机/结构]",
            "expression": "exp(-((x-0.5)**2 + (y-0.5)**2) / 0.04)",
            "notes": "二维高斯",
        },
        "MultiGaussian": {
            "description": "双高斯 [随机/结构]",
            "expression": "exp(-((x-0.3)**2 + (y-0.3)**2) / 0.02) + exp(-((x-0.7)**2 + (y-0.7)**2) / 0.02)",
            "notes": "双峰高斯",
        },
        "PerlinLike": {
            "description": "Perlin类噪声 [随机/噪声]",
            "expression": "0.5 + 0.5*sin(x*20)*cos(y*20) + 0.3*sin(x*40)*cos(y*40)",
            "notes": "多频叠加噪声",
        },
        "CircularWave": {
            "description": "圆形波 [波动/对称]",
            "expression": "0.5 + 0.5*sin(20*sqrt((x-0.5)**2 + (y-0.5)**2))",
            "notes": "从中心发出的圆形波",
        },
        "Spiral2": {
            "description": "双螺旋 [结构/对称]",
            "expression": "1 if (sin(10*atan2(y-0.5, x-0.5) + 5*sqrt((x-0.5)**2 + (y-0.5)**2)) > 0) else 0",
            "notes": "双螺旋近似",
        },
        "Checker3": {
            "description": "3x3棋盘 [周期/结构]",
            "expression": "1 if ((int(x*6) + int(y*6)) % 2 == 0) else 0",
            "notes": "3x3棋盘",
        },
        "StripesDiag": {
            "description": "对角条纹 [周期/结构]",
            "expression": "1 if (sin((x+y)*30) > 0) else 0",
            "notes": "对角条纹",
        },
        "NoiseFractal": {
            "description": "分形噪声近似 [随机/噪声]",
            "expression": "0.5 + 0.5*sin(x*10)*sin(y*10)*sin(x*20)*sin(y*20)",
            "notes": "分形噪声近似",
        },
        "DomainWall": {
            "description": "畴壁 [物理/结构]",
            "expression": "0.5 + 0.5*tanh(20*(x-0.5))",
            "notes": "畴壁近似",
        },
        "Vortex": {
            "description": "涡旋 [流体/对称]",
            "expression": "atan2(y-0.5, x-0.5) / (2*pi) % 1",
            "notes": "涡旋相位场",
        },
        "LogisticSpace": {
            "description": "Logistic空间图案 [混沌/复杂]",
            "expression": "3.8*x*(1-x)*3.8*y*(1-y)",
            "notes": "Logistic映射空间填充",
        },
        "CellularNoise": {
            "description": "细胞噪声 [随机/噪声]",
            "expression": "1 if random() > 0.9 else 0.1",
            "notes": "稀疏细胞噪声",
        },
        "GradientCorner": {
            "description": "角点渐变 [梯度/结构]",
            "expression": "abs(x-0.5) * abs(y-0.5)",
            "notes": "角点渐变",
        },
        "SineChecker": {
            "description": "正弦棋盘 [周期/结构]",
            "expression": "0.5 + 0.5*sin(x*20)*sin(y*20)",
            "notes": "连续棋盘波",
        },
        "Annulus": {
            "description": "圆环 [结构/对称]",
            "expression": "1 if (0.2 < (x-0.5)**2 + (y-0.5)**2 < 0.25) else 0",
            "notes": "圆环区域",
        },
        "CrossHair": {
            "description": "十字准线 [结构/对称]",
            "expression": "1 if (abs(x-0.5) < 0.01 or abs(y-0.5) < 0.01) else 0",
            "notes": "十字准线",
        },
        "GradRadialSQ": {
            "description": "径向平方根渐变 [梯度/对称]",
            "expression": "sqrt((x-0.5)**2 + (y-0.5)**2)",
            "notes": "径向距离",
        },
        "PolarAngle": {
            "description": "极角 [角度/对称]",
            "expression": "atan2(y-0.5, x-0.5) / (2*pi) % 1",
            "notes": "极角映射",
        },
        "Lissajous": {
            "description": "Lissajous初始 [周期/复杂]",
            "expression": "1 if (sin(3*x*20)*sin(2*y*20) > 0.5) else 0",
            "notes": "Lissajous图案",
        },
        "Cateye": {
            "description": "猫眼 [结构/对称]",
            "expression": "1 if ((x-0.5)**2/0.04 + (y-0.5)**2/0.01 < 1) else 0",
            "notes": "椭圆形",
        },
        "Super_SineField": {
            "description": "正弦场超级公式 [超级公式]",
            "expression": "0.5 + 0.5*sin(x*f1*20)*cos(y*f2*20)",
            "notes": "单参数正弦场；f1=1: 水平条纹，f1=2: 高频水平，f2=1: 竖直条纹，f1=f2=1: 棋盘格",
        },
        "Super_Gaussian": {
            "description": "高斯超级公式 [超级公式]",
            "expression": "exp(-((x-p1)**2 + (y-p2)**2) / (0.1*(1+w1)))",
            "notes": "可定位可调宽高斯；p1,p2控制位置，w1控制宽度",
        },
        "Super_PerlinLike": {
            "description": "Perlin类噪声超级公式 [超级公式]",
            "expression": "0.5 + 0.5*sin(x*f1*30)*cos(y*f2*30) + 0.3*sin(x*f1*60)*cos(y*f2*60)",
            "notes": "多频叠加噪声；f1,f2控制频率，可近似Perlin",
        },
        "Super_Checker": {
            "description": "棋盘超级公式 [超级公式]",
            "expression": "0.5 + 0.5*sin(x*f1*pi)*sin(y*f2*pi)",
            "notes": "连续棋盘；f1,f2控制格子数",
        },
        "Super_Spiral": {
            "description": "螺旋超级公式 [超级公式]",
            "expression": "0.5 + 0.5*sin(f1*atan2(y-0.5, x-0.5) + f2*10*sqrt((x-0.5)**2 + (y-0.5)**2))",
            "notes": "可调螺旋；f1控制臂数，f2控制密度",
        },
        "Super_WavePacket": {
            "description": "波包超级公式 [超级公式]",
            "expression": "exp(-((x-0.5)**2 + (y-0.5)**2)/(0.04+w1))*sin(f1*20*sqrt((x-0.5)**2 + (y-0.5)**2))",
            "notes": "高斯波包；f1控制振荡频率，w1控制宽度",
        },
        "SinCosMix": {
            "description": "正弦余弦混合 [周期/波形]",
            "expression": "0.5 + 0.5*sin(x*20)*cos(y*20)",
            "notes": "正弦余弦乘积",
        },
        "TanWave": {
            "description": "正切波 [周期/波形]",
            "expression": "0.5 + 0.5*tan(x*10)/(1+abs(tan(x*10)))",
            "notes": "正切波近似",
        },
        "ExpDecay": {
            "description": "指数衰减 [数学/渐变]",
            "expression": "exp(-10*x)",
            "notes": "指数衰减",
        },
        "LogSpira": {
            "description": "对数螺旋 [结构/对称]",
            "expression": "1 if (log(sqrt((x-0.5)**2 + (y-0.5)**2) + 0.001) * atan2(y-0.5, x-0.5)) % 1 < 0.5 else 0",
            "notes": "对数螺旋近似",
        },
        "CircularGradient": {
            "description": "圆形渐变 [渐变/对称]",
            "expression": "atan2(y-0.5, x-0.5) / (2*pi) % 1",
            "notes": "角度渐变",
        },
        "RadialGradient2": {
            "description": "径向渐变2 [渐变/对称]",
            "expression": "abs(x-0.5) + abs(y-0.5)",
            "notes": "Manhattan距离",
        },
        "Checker5": {
            "description": "5x5棋盘 [周期/结构]",
            "expression": "1 if ((int(x*10) + int(y*10)) % 2 == 0) else 0",
            "notes": "5x5棋盘",
        },
        "Stripes45": {
            "description": "45度条纹 [周期/结构]",
            "expression": "1 if (sin((x+y)*25) > 0) else 0",
            "notes": "45度条纹",
        },
        "NoiseSmooth2": {
            "description": "平滑噪声2 [随机/噪声]",
            "expression": "0.5 + 0.3*random()",
            "notes": "低对比度噪声",
        },
        "GaussianRing": {
            "description": "高斯环 [结构/对称]",
            "expression": "exp(-((sqrt((x-0.5)**2 + (y-0.5)**2) - 0.3)**2) / 0.01)",
            "notes": "高斯环形",
        }
    },
    "evolution": {
        "GameOfLife": {
            "description": "Game of Life [经典/CA]",
            "expression": "1 if (c > 0.5 and sum_n >= 2 and sum_n <= 3) or (c <= 0.5 and sum_n == 3) else 0",
            "variables": ["c", "sum_n"],
            "notes": "经典GoL（连续值近似）",
        },
        "HighLife": {
            "description": "HighLife [经典/CA]",
            "expression": "1 if (c > 0.5 and sum_n in [2, 3]) or (c <= 0.5 and sum_n in [3, 6]) else 0",
            "variables": ["c", "sum_n"],
            "notes": "HighLife",
        },
        "Seeds": {
            "description": "Seeds (仅出生) [经典/CA]",
            "expression": "1 if (c <= 0.5 and sum_n == 2) else 0",
            "variables": ["c", "sum_n"],
            "notes": "Seeds规则",
        },
        "LifeWithoutDeath": {
            "description": "Life without Death [经典/CA]",
            "expression": "c if c > 0.5 else (1 if sum_n >= 3 else 0)",
            "variables": ["c", "sum_n"],
            "notes": "不死生命",
        },
        "2x2": {
            "description": "2x2 [经典/CA]",
            "expression": "1 if (c > 0.5 and sum_n in [1, 2, 5]) or (c <= 0.5 and sum_n in [3, 6]) else 0",
            "variables": ["c", "sum_n"],
            "notes": "2x2规则",
        },
        "BS678_S": {
            "description": "678生存 [经典/CA]",
            "expression": "1 if sum_n >= 6 else 0",
            "variables": ["c", "sum_n"],
            "notes": "高阈值生存",
        },
        "BS12345_S": {
            "description": "12345生存 [经典/CA]",
            "expression": "1 if (sum_n >= 1 and sum_n <= 5) else 0",
            "variables": ["c", "sum_n"],
            "notes": "低阈值生存",
        },
        "Move116": {
            "description": "移动116 [经典/CA]",
            "expression": "1 if (c > 0.5 and sum_n in [1, 4, 5]) or (c <= 0.5 and sum_n in [3, 6]) else 0",
            "variables": ["c", "sum_n"],
            "notes": "移动规则",
        },
        "PureDiffusion": {
            "description": "经典热传导扩散 [扩散/热传导]",
            "expression": "c + 0.20*(avg_n - c)",
            "variables": ["c", "avg_n"],
            "notes": "最基础的扩散",
        },
        "AnisotropicDiffusion": {
            "description": "各向异性扩散 [扩散/物理]",
            "expression": "c + 0.15*((neighbors[0] if len(neighbors)>0 else avg_n) + (neighbors[1] if len(neighbors)>1 else avg_n) + (neighbors[2] if len(neighbors)>2 else avg_n) + (neighbors[3] if len(neighbors)>3 else avg_n) - 4*c)",
            "variables": ["c", "neighbors"],
            "notes": "仅4邻域扩散（neighbors[0-3]=上左下右）",
        },
        "DiffusionLimited": {
            "description": "扩散限制聚集DLA [扩散/聚集]",
            "expression": "c if c > 0.5 else (1 if (sum_n >= 0.5 and random() < 0.1) else 0)",
            "variables": ["c", "sum_n"],
            "notes": "DLA生长",
        },
        "Laplacian": {
            "description": "拉普拉斯锐化 [扩散/图像]",
            "expression": "c + 0.5*(avg_n - c)",
            "variables": ["c", "avg_n"],
            "notes": "拉普拉斯滤波",
        },
        "HeatEquation": {
            "description": "热方程 [扩散/物理]",
            "expression": "avg_n",
            "variables": ["avg_n"],
            "notes": "热方程（直接平均）",
        },
        "GrayScott_Diffusion": {
            "description": "Gray-Scott扩散步骤 [反应扩散/模式]",
            "expression": "c + 0.20*(avg_n - c)",
            "variables": ["c", "avg_n"],
            "notes": "Gray-Scott的扩散部分",
        },
        "FitzHughNagumo": {
            "description": "FitzHugh-Nagumo近似 [反应扩散/神经]",
            "expression": "c + 0.01*(c - c**3/3 + avg_n + 0.5)",
            "variables": ["c", "avg_n"],
            "notes": "FHN神经元模型近似",
        },
        "Oregonator": {
            "description": "Oregonator (BZ反应) [反应扩散/化学]",
            "expression": "c + 0.1*(avg_n - c) + 0.5*c*(1 - c)*(c - 0.3)",
            "variables": ["c", "avg_n"],
            "notes": "Oregonator近似",
        },
        "WavePropagate": {
            "description": "波传播 [波动/激发]",
            "expression": "1 if (c <= 0.5 and sum_n >= 1) else (c * 0.9)",
            "variables": ["c", "sum_n"],
            "notes": "简化波传播（含衰减）",
        },
        "BZReaction": {
            "description": "BZ反应近似 [波动/化学]",
            "expression": "1 if (c > 0.5) else (0.5 if sum_n > 1 else c)",
            "variables": ["c", "sum_n"],
            "notes": "BZ反应阈值近似",
        },
        "ExcitableThreshold": {
            "description": "阈值激发 [波动/神经]",
            "expression": "1 if (c <= 0.1 and sum_n > 0.5) else (c * 0.95)",
            "variables": ["c", "sum_n"],
            "notes": "激发+衰减",
        },
        "LogisticTrajectory": {
            "description": "Logistic轨迹 [动力系统/混沌]",
            "expression": "3.8*c*(1-c)",
            "variables": ["c"],
            "notes": "Logistic映射（逐格独立）",
        },
        "HenonTrajectory": {
            "description": "Henon轨迹近似 [动力系统/混沌]",
            "expression": "1 - 1.4*c**2 + 0.3*avg_n",
            "variables": ["c", "avg_n"],
            "notes": "Henon映射近似",
        },
        "DuffingTrajectory": {
            "description": "Duffing方程近似 [动力系统/混沌]",
            "expression": "c + 0.01*(avg_n - 0.2*c + c**3) + 0.5*sin(t*0.1)",
            "variables": ["c", "avg_n", "t"],
            "notes": "Duffing振子（弱混沌）",
        },
        "EdenGrowth": {
            "description": "Eden生长 [生长/统计]",
            "expression": "c if c > 0.5 else (1 if (sum_n >= 0.5 and random() < 0.3) else 0)",
            "variables": ["c", "sum_n"],
            "notes": "Eden生长模型",
        },
        "DPProcess": {
            "description": "有向渗流 [渗流/统计]",
            "expression": "1 if (c > 0.5 and random() < 0.8) or (c <= 0.5 and sum_n >= 0.5 and random() < 0.4) else 0",
            "variables": ["c", "sum_n"],
            "notes": "有向渗流",
        },
        "IsingGlauber": {
            "description": "Ising Glauber [统计物理/磁]",
            "expression": "1 if (sum_n > 2 and c <= 0.5) or (sum_n < 2 and c > 0.5) else c",
            "variables": ["c", "sum_n"],
            "notes": "Ising模型Glauber动力学",
        },
        "CahnHilliard_step": {
            "description": "Cahn-Hilliard演化 [相分离/物理]",
            "expression": "c + 0.1*(avg_n - c) - 0.01*(c**3 - c)",
            "variables": ["c", "avg_n"],
            "notes": "Cahn-Hilliard数值格式（简化）",
        },
        "PhaseSeparation": {
            "description": "相分离 [相分离/物理]",
            "expression": "c + 0.2*(avg_n - c) - 0.1*(c - 0.5)",
            "variables": ["c", "avg_n"],
            "notes": "简化相分离",
        },
        "TuringActivation": {
            "description": "Turing激活-抑制近似 [反应扩散/模式]",
            "expression": "c + 0.1*(avg_n - c) + 0.01*sin(c*20)",
            "variables": ["c", "avg_n"],
            "notes": "Turing模式近似",
        },
        "Meinhardt": {
            "description": "Meinhardt激活-抑制 [反应扩散/模式]",
            "expression": "c + 0.15*(avg_n - c) + 0.1*(c - c**2)",
            "variables": ["c", "avg_n"],
            "notes": "Meinhardt模型简化",
        },
        "CoupledMap": {
            "description": "耦合映射网格 [耦合系统/复杂]",
            "expression": "(1 - 0.1)*c + 0.1*avg_n",
            "variables": ["c", "avg_n"],
            "notes": "耦合映射（扩散耦合）",
        },
        "CMLChaotic": {
            "description": "混沌耦合映射 [耦合系统/复杂]",
            "expression": "(1 - 0.2)*3.8*c*(1-c) + 0.2*3.8*avg_n*(1-avg_n)",
            "variables": ["c", "avg_n"],
            "notes": "Logistic CML",
        },
        "Kuramoto": {
            "description": "Kuramoto同步近似 [耦合系统/同步]",
            "expression": "c + 0.01*sin(avg_n - c)",
            "variables": ["c", "avg_n"],
            "notes": "Kuramoto相位同步近似",
        },
        "ForestFire": {
            "description": "森林火灾模型 [随机/复杂]",
            "expression": "1 if (c <= 0.5 and sum_n >= 0.5) else (0 if c > 0.5 else c)",
            "variables": ["c", "sum_n"],
            "notes": "森林火灾（1=火，0=空，>0.5=树）",
        },
        "StochasticGrowth": {
            "description": "随机生长 [随机/生长]",
            "expression": "c if c > 0.5 else (1 if sum_n >= 1 and random() < 0.4 else 0)",
            "variables": ["c", "sum_n"],
            "notes": "概率性生长",
        },
        "SmoothLife": {
            "description": "SmoothLife近似 [混合/复杂]",
            "expression": "1/(1+exp(-10*(avg_n - 0.3)))",
            "variables": ["avg_n"],
            "notes": "SmoothLife激活函数",
        },
        "Lenia": {
            "description": "Lenia近似 [混合/复杂]",
            "expression": "c + 0.1*(1/(1+exp(-20*(avg_n - 0.15))) - c)",
            "variables": ["c", "avg_n"],
            "notes": "Lenia生长函数近似",
        },
        "ThresholdGrowth": {
            "description": "阈值生长 [混合/统计]",
            "expression": "1 if (sum_n > 0.4 and c < 0.5) else (c * 0.98)",
            "variables": ["c", "sum_n"],
            "notes": "连续阈值",
        },
        "Super_EvolutionFourier": {
            "description": "Fourier演化超级公式 [超级公式]",
            "expression": "c + f1*(avg_n - c) + f2*sin(c*20)/(1 + w1*abs(avg_n - c))",
            "variables": ["c", "avg_n"],
            "notes": "可调反应扩散；f1=扩散率，f2=反应振幅，w1=非线性抑制",
        },
        "Super_CoupledMap": {
            "description": "耦合映射超级公式 [超级公式]",
            "expression": "(1 - f1)*c + f1*avg_n + f2*sin(2*pi*c)",
            "variables": ["c", "avg_n"],
            "notes": "耦合映射超公式；f1=耦合强度，f2=混沌调制",
        },
        "Super_Threshold": {
            "description": "阈值超级公式 [超级公式]",
            "expression": "clip(c + f1*(avg_n - c) + f2*(0.5 - abs(c - 0.5)), 0, 1)",
            "variables": ["c", "avg_n"],
            "notes": "带阈值的扩散；f1=扩散，f2=阈值偏好",
        },
        "Super_Oscillation": {
            "description": "振荡超级公式 [超级公式]",
            "expression": "c + f1*(avg_n - c) + f2*sin(t*0.1)",
            "variables": ["c", "avg_n", "t"],
            "notes": "时间振荡扩散；f1=扩散，f2=振荡振幅",
        },
        "Super_ReactionDiffusion": {
            "description": "反应扩散超级公式 [超级公式]",
            "expression": "c + f1*(avg_n - c) + f2*c*(w1 - c)",
            "variables": ["c", "avg_n"],
            "notes": "广义反应扩散；f1=扩散，f2=反应速率，w1=偏好值",
        }
    },
    "color": {
        "Grayscale": {
            "description": "经典黑白灰度 [经典/渐变]",
            "red": "v",
            "green": "v",
            "blue": "v",
            "notes": "标准灰度",
        },
        "Inverted": {
            "description": "反色 [经典/渐变]",
            "red": "1-v",
            "green": "1-v",
            "blue": "1-v",
            "notes": "反色",
        },
        "Binary": {
            "description": "二值化 [经典/阈值]",
            "red": "1 if v > 0.5 else 0",
            "green": "1 if v > 0.5 else 0",
            "blue": "1 if v > 0.5 else 0",
            "notes": "阈值二值",
        },
        "Threshold3": {
            "description": "三值化 [经典/阈值]",
            "red": "1 if v > 0.66 else (0.5 if v > 0.33 else 0)",
            "green": "1 if v > 0.66 else (0.5 if v > 0.33 else 0)",
            "blue": "1 if v > 0.66 else (0.5 if v > 0.33 else 0)",
            "notes": "三值分割",
        },
        "Rainbow": {
            "description": "彩虹色 [经典/周期]",
            "red": "0.5+0.5*sin(2*pi*v)",
            "green": "0.5+0.5*sin(2*pi*v+2*pi/3)",
            "blue": "0.5+0.5*sin(2*pi*v+4*pi/3)",
            "notes": "HSV彩虹映射",
        },
        "Hot": {
            "description": "Hot热力图 [经典/热力]",
            "red": "v",
            "green": "v**2",
            "blue": "v**4",
            "notes": "Hot colormap",
        },
        "JetSimple": {
            "description": "Jet简化 [经典/热力]",
            "red": "clip(4*v-1.5, 0, 1)",
            "green": "clip(4*v-0.5, 0, 1)",
            "blue": "clip(-4*v+2.5, 0, 1)",
            "notes": "Jet简化版",
        },
        "Cool": {
            "description": "Cool冷色 [经典/渐变]",
            "red": "v",
            "green": "1-v",
            "blue": "1",
            "notes": "Cool colormap",
        },
        "Spring": {
            "description": "Spring暖色 [经典/渐变]",
            "red": "1",
            "green": "0.5+0.5*v",
            "blue": "v",
            "notes": "Spring colormap",
        },
        "Summer": {
            "description": "Summer [经典/渐变]",
            "red": "0.5+0.5*v",
            "green": "0.5+0.25*v",
            "blue": "0.5*v",
            "notes": "Summer colormap",
        },
        "Autumn": {
            "description": "Autumn [经典/渐变]",
            "red": "1",
            "green": "v",
            "blue": "0",
            "notes": "Autumn colormap",
        },
        "Winter": {
            "description": "Winter [经典/渐变]",
            "red": "0",
            "green": "0.5+0.5*v",
            "blue": "0.5+0.5*v",
            "notes": "Winter colormap",
        },
        "Phase": {
            "description": "相位色 [相位/周期]",
            "red": "0.5+0.5*cos(2*pi*v)",
            "green": "0.5+0.5*cos(2*pi*v+2*pi/3)",
            "blue": "0.5+0.5*cos(2*pi*v+4*pi/3)",
            "notes": "相位->RGB",
        },
        "Compass": {
            "description": "方向色 [相位/结构]",
            "red": "0.5+0.5*sin(2*pi*v)",
            "green": "0.5+0.5*sin(2*pi*v+pi/2)",
            "blue": "0.5+0.5*sin(2*pi*v+pi)",
            "notes": "方向编码",
        },
        "BlueWhiteRed": {
            "description": "蓝-白-红 [渐变/热力]",
            "red": "v",
            "green": "2*v*(1-v)",
            "blue": "1-v",
            "notes": "蓝白红渐变",
        },
        "CyanWhiteMagenta": {
            "description": "青-白-品红 [渐变/热力]",
            "red": "v",
            "green": "1-v",
            "blue": "0.5+0.5*v",
            "notes": "青白品红",
        },
        "GreenBlackRed": {
            "description": "绿-黑-红 [渐变/热力]",
            "red": "v",
            "green": "0",
            "blue": "1-v",
            "notes": "绿黑红",
        },
        "LorenzPalette": {
            "description": "Lorenz吸引子色板 [吸引子/复杂]",
            "red": "0.5+0.5*sin(2*pi*v)",
            "green": "0.5+0.5*sin(2*pi*v+pi/3)",
            "blue": "0.5+0.5*cos(2*pi*v)",
            "notes": "Lorenz风格",
        },
        "RosslerPalette": {
            "description": "Rossler吸引子色板 [吸引子/复杂]",
            "red": "v",
            "green": "0.5+0.5*sin(4*pi*v)",
            "blue": "0.5+0.5*cos(4*pi*v)",
            "notes": "Rossler风格",
        },
        "IQ_Palette": {
            "description": "IQ色板（连续） [分岔/复杂]",
            "red": "0.5+0.5*cos(2*pi*(v*0.9+0.1))",
            "green": "0.5+0.5*cos(2*pi*(v*0.7+0.3))",
            "blue": "0.5+0.5*cos(2*pi*(v*0.5+0.5))",
            "notes": "适合分岔图",
        },
        "IQ_Palette2": {
            "description": "IQ色板2 [分岔/复杂]",
            "red": "v*(1-v)*4",
            "green": "v*(1-v)*4*v*(1-v)*4",
            "blue": "v",
            "notes": "另一种分岔图配色",
        },
        "Emboss": {
            "description": "浮雕效果 [特效/图像]",
            "red": "v + 0.2*sin(20*v)",
            "green": "v + 0.1*sin(20*v)",
            "blue": "v - 0.1*sin(20*v)",
            "notes": "浮雕风格",
        },
        "Posterize": {
            "description": "海报化 [特效/艺术]",
            "red": "0.25*int(v*4)",
            "green": "0.25*int(v*4)",
            "blue": "0.25*int(v*4)",
            "notes": "4级海报化（需int支持）",
        },
        "Solarize": {
            "description": "曝光 [特效/艺术]",
            "red": "1-v if v > 0.5 else v",
            "green": "1-v if v > 0.5 else v",
            "blue": "1-v if v > 0.5 else v",
            "notes": "Solarization",
        },
        "Parabola": {
            "description": "抛物线渐变 [数学/渐变]",
            "red": "v**2",
            "green": "v**2",
            "blue": "v**2",
            "notes": "抛物线灰度",
        },
        "SinePalette": {
            "description": "正弦调色板 [数学/周期]",
            "red": "0.5+0.5*sin(2*pi*v)",
            "green": "0.5+0.5*sin(4*pi*v)",
            "blue": "0.5+0.5*sin(6*pi*v)",
            "notes": "多频正弦",
        },
        "LogPalette": {
            "description": "对数调色板 [数学/渐变]",
            "red": "log(1+v*9)/log(10)",
            "green": "log(1+v*9)/log(10)",
            "blue": "log(1+v*9)/log(10)",
            "notes": "对数映射",
        },
        "Super_IQPalette": {
            "description": "IQ色板超级公式 [超级公式]",
            "red": "0.5+0.5*cos(2*pi*(v*p1+d1))",
            "green": "0.5+0.5*cos(2*pi*(v*p2+d2))",
            "blue": "0.5+0.5*cos(2*pi*(v*p3+d3))",
            "notes": "IQ色板参数化；p1-p3控制频率，d1-d3控制相位",
        },
        "Super_WarmCool": {
            "description": "冷暖超级公式 [超级公式]",
            "red": "0.5+0.5*sin(v*pi*f1+d1)",
            "green": "v",
            "blue": "0.5+0.5*cos(v*pi*f2+d2)",
            "notes": "冷暖可调；f1,f2控制红蓝振荡",
        },
        "Super_Phase": {
            "description": "相位超级公式 [超级公式]",
            "red": "0.5+0.5*cos(2*pi*v*f1+p1)",
            "green": "0.5+0.5*cos(2*pi*v*f2+p2)",
            "blue": "0.5+0.5*cos(2*pi*v*f3+p3)",
            "notes": "三通道独立相位；f1-f3频率，p1-p3相位",
        },
        "Super_Contrast": {
            "description": "对比度超级公式 [超级公式]",
            "red": "clip((v-0.5)*c1+0.5, 0, 1)",
            "green": "clip((v-0.5)*c2+0.5, 0, 1)",
            "blue": "clip((v-0.5)*c3+0.5, 0, 1)",
            "notes": "对比度可调；c1-c3各通道对比度",
        },
        "Super_Gradient": {
            "description": "渐变超级公式 [超级公式]",
            "red": "clip(a1 + b1*v, 0, 1)",
            "green": "clip(a2 + b2*v, 0, 1)",
            "blue": "clip(a3 + b3*v, 0, 1)",
            "notes": "线性渐变超公式；a1-a3偏移，b1-b3斜率",
        },
        "Super_SinePalette": {
            "description": "正弦调色板超级公式 [超级公式]",
            "red": "0.5+0.5*sin(2*pi*v*f1)*g1",
            "green": "0.5+0.5*sin(2*pi*v*f2+pi/3)*g2",
            "blue": "0.5+0.5*sin(2*pi*v*f3+2*pi/3)*g3",
            "notes": "正弦调色板可调；f1-f3频率，g1-g3增益",
        },
        "Super_Thermal": {
            "description": "热力超级公式 [超级公式]",
            "red": "clip(v*f1, 0, 1)",
            "green": "clip(v*(1-v)*f2*4, 0, 1)",
            "blue": "clip((1-v)*f3, 0, 1)",
            "notes": "热力图可调；f1红标度，f2绿标度，f3蓝标度",
        }
    }
}


# ============================================================
# 超级公式参数默认值（用于替换表达式中的未绑定变量）
# ============================================================
SUPER_PARAM_DEFAULTS = {
    # 位置 / 频率 / 宽度
    'p1': 0.5, 'p2': 0.5, 'p3': 0.5,
    'w1': 0.5,
    'f1': 1.0, 'f2': 1.0, 'f3': 1.0,
    # 相位偏移
    'd1': 0.0, 'd2': 0.0, 'd3': 0.0,
    # 对比度
    'c1': 2.0, 'c2': 2.0, 'c3': 2.0,
    # 增益
    'g1': 1.0, 'g2': 1.0, 'g3': 1.0,
    # 渐变偏移 / 斜率
    'a1': 0.0, 'a2': 0.0, 'a3': 0.0,
    'b1': 1.0, 'b2': 1.0, 'b3': 1.0,
}


def resolve_super_params(expr: str) -> str:
    """将超级公式参数名替换为默认数值，使表达式可以独立编译执行。"""
    import re
    for name, value in SUPER_PARAM_DEFAULTS.items():
        expr = re.sub(r'\b' + re.escape(name) + r'\b', str(value), expr)
    return expr


def print_template(ttype, name=None):
    """Print template(s) by category or single template.
    
    ttype: category name ('init', 'evolution', 'color') or 'all'
    name: if given, print that specific template
    """
    if name is not None:
        # Single template mode
        t = FORMULA_TEMPLATES[ttype][name]
        print(f"\n{'='*60}")
        print(f"  [{ttype.upper()}] {name}")
        print(f"{'='*60}")
        print(f"  描述: {t['description']}")
        if ttype == 'init':
            print(f"  表达式: {t['expression']}")
        elif ttype == 'evolution':
            print(f"  表达式: {t['expression']}")
            print(f"  变量: {t['variables']}")
        else:
            print(f"  红(R): {t['red']}")
            print(f"  绿(G): {t['green']}")
            print(f"  蓝(B): {t['blue']}")
        print(f"  备注: {t['notes']}")
    else:
        # Category mode: print all templates in that category
        categories = ['init', 'evolution', 'color'] if ttype == 'all' else [ttype]
        for cat in categories:
            if cat not in FORMULA_TEMPLATES:
                print(f"[!] 未知类别: {cat}")
                continue
            templates = FORMULA_TEMPLATES[cat]
            print(f"\n{'='*60}")
            print(f"  [{cat.upper()}] 共 {len(templates)} 个模板")
            print(f"{'='*60}")
            for name, t in templates.items():
                print(f"\n  --- {name} ---")
                print(f"  描述: {t['description']}")
                if cat == 'init':
                    print(f"  表达式: {t['expression']}")
                elif cat == 'evolution':
                    print(f"  表达式: {t['expression']}")
                    print(f"  变量: {t['variables']}")
                else:
                    print(f"  红(R): {t['red']}")
                    print(f"  绿(G): {t['green']}")
                    print(f"  蓝(B): {t['blue']}")
                print(f"  备注: {t['notes']}")


def list_all_templates():
    """列出所有模板名称，按类别分组。"""
    print(f"\n{'='*60}")
    print(f"  公式模板库 — 共 {sum(len(FORMULA_TEMPLATES[c]) for c in FORMULA_TEMPLATES)} 个模板")
    print(f"{'='*60}")
    for cat in ['init', 'evolution', 'color']:
        templates = FORMULA_TEMPLATES[cat]
        print(f"\n  [{cat.upper()}] {len(templates)} 个:")
        for i, (name, t) in enumerate(templates.items()):
            print(f"    {i+1:3d}. {name:<35s} {t['description']}")


if __name__ == '__main__':
    print(f"Total templates: {sum(len(FORMULA_TEMPLATES[c]) for c in FORMULA_TEMPLATES)}")
    for cat in FORMULA_TEMPLATES:
        print(f"  {cat}: {len(FORMULA_TEMPLATES[cat])}")
    print_template("init", "PureRandom")
