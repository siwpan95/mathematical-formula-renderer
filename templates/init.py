"""INIT_TEMPLATES (由 templates.py 自动拆分生成)."""

INIT_TEMPLATES = {
"PureRandom": {
    "description": '每个细胞随机初始值 [随机/噪声]',
    "expression": 'random()',
    "notes": '完全随机的初始状态',
},
"HalfHalf": {
    "description": '约一半细胞为1 [随机/结构]',
    "expression": '1 if random() > 0.5 else 0',
    "notes": '经典二分初始',
},
"CenterDot": {
    "description": '中心单点激活 [结构/对称]',
    "expression": '1 if (abs(x-0.5) < 0.03 and abs(y-0.5) < 0.03) else 0',
    "notes": '单点种子',
},
"CenterCross": {
    "description": '中心十字 [结构/对称]',
    "expression": '1 if (abs(x-0.5) < 0.02 or abs(y-0.5) < 0.02) else 0',
    "notes": '十字种子',
},
"Diagonal": {
    "description": '对角线激活 [结构/对称]',
    "expression": '1 if (abs(x-y) < 0.03) else 0',
    "notes": '对角线渐变',
},
"Concentric": {
    "description": '同心圆 [结构/对称]',
    "expression": '1 if (abs(sqrt((x-0.5)**2 + (y-0.5)**2) - 0.3) < 0.02) else 0',
    "notes": '圆形波',
},
"Checkerboard": {
    "description": '棋盘格 [周期/结构]',
    "expression": '1 if ((int(x*20) + int(y*20)) % 2 == 0) else 0',
    "notes": '经典棋盘（用三角函数避免int）',
},
"StripesX": {
    "description": '竖直条纹 [周期/结构]',
    "expression": '1 if (sin(x*40) > 0) else 0',
    "notes": '竖直条纹',
},
"StripesY": {
    "description": '水平条纹 [周期/结构]',
    "expression": '1 if (sin(y*40) > 0) else 0',
    "notes": '水平条纹',
},
"Grid": {
    "description": '网格 [周期/结构]',
    "expression": '1 if (sin(x*30) * sin(y*30) > 0) else 0',
    "notes": '网格纹理',
},
"NoiseSmooth": {
    "description": '平滑噪声 [随机/噪声]',
    "expression": '0.5 + 0.5*random()',
    "notes": '平滑随机',
},
"GradientX": {
    "description": '水平渐变 [梯度/结构]',
    "expression": 'x',
    "notes": '从左到右渐变',
},
"GradientY": {
    "description": '竖直渐变 [梯度/结构]',
    "expression": 'y',
    "notes": '从上到下渐变',
},
"GradientRadial": {
    "description": '径向渐变 [梯度/对称]',
    "expression": 'sqrt((x-0.5)**2 + (y-0.5)**2)',
    "notes": '从中心向外渐变',
},
"SineWave": {
    "description": '正弦波初始 [周期/波形]',
    "expression": '0.5 + 0.5*sin(x*20)',
    "notes": '正弦空间调制',
},
"CosineWave": {
    "description": '余弦波初始 [周期/波形]',
    "expression": '0.5 + 0.5*cos(y*20)',
    "notes": '余弦空间调制',
},
"SineRing": {
    "description": '正弦环 [周期/对称]',
    "expression": '0.5 + 0.5*sin(20*sqrt((x-0.5)**2 + (y-0.5)**2))',
    "notes": '环形正弦波',
},
"Spiral": {
    "description": '螺旋初始 [结构/对称]',
    "expression": '1 if ((atan2(y-0.5, x-0.5) / (2*pi) + sqrt((x-0.5)**2 + (y-0.5)**2) * 2) % 1 < 0.5) else 0',
    "notes": '螺旋相位近似',
},
"Diamond": {
    "description": '菱形 [结构/对称]',
    "expression": '1 if (abs(x-0.5) + abs(y-0.5) < 0.2) else 0',
    "notes": '菱形区域',
},
"FilledCircle": {
    "description": '实心圆 [结构/对称]',
    "expression": '1 if ((x-0.5)**2 + (y-0.5)**2 < 0.16) else 0',
    "notes": '圆形种子',
},
"Mandelbrot": {
    "description": 'Mandelbrot集边界 [分形/复杂]',
    "expression": '1 if (abs(complex(x*3-1.5, y*3-1.5)) < 2) else 0',
    "notes": 'Mandelbrot边界（需complex支持）',
},
"CantorDust": {
    "description": 'Cantor尘埃近似 [分形/经典]',
    "expression": '1 if (cos(3*pi*x)*cos(9*pi*x)*cos(27*pi*x) > 0 and cos(3*pi*y)*cos(9*pi*y)*cos(27*pi*y) > 0) else 0',
    "notes": 'Cantor集乘积近似（无int版本）',
},
"SierpinskiTrigger": {
    "description": 'Sierpinski三角触发 [分形/经典]',
    "expression": '1 if (sin(x*511*pi)*sin(y*511*pi) > 0) else 0',
    "notes": 'Sierpinski三角（三角函数近似）',
},
"DoubleSlit": {
    "description": '双缝干涉 [波动/物理]',
    "expression": '0.5 + 0.25*sin(30*sqrt((x-0.3)**2 + (y-0.5)**2)) + 0.25*sin(30*sqrt((x-0.7)**2 + (y-0.5)**2))',
    "notes": '双缝干涉图案',
},
"SingleSlit": {
    "description": '单缝衍射 [波动/物理]',
    "expression": '(sin(pi*10*sqrt((x-0.5)**2 + (y-0.5)**2)) / (pi*10*sqrt((x-0.5)**2 + (y-0.5)**2) + 0.001))**2',
    "notes": '单缝Airy盘近似',
},
"PlaneWave": {
    "description": '平面波 [波动/物理]',
    "expression": '0.5 + 0.5*sin(2*pi*(x*cos(0.3) + y*sin(0.3)))',
    "notes": '斜向平面波',
},
"StandingWave": {
    "description": '驻波 [波动/物理]',
    "expression": '(sin(2*pi*x*10))**2',
    "notes": '一维驻波',
},
"TuringSpot": {
    "description": 'Turing斑点初始 [反应扩散/模式]',
    "expression": '0.5 + 0.5*sin(14*x)*sin(14*y) + 0.3*random()',
    "notes": 'Turing斑点种子',
},
"TuringStripe": {
    "description": 'Turing条纹初始 [反应扩散/模式]',
    "expression": '0.5 + 0.5*sin(14*x) + 0.3*random()',
    "notes": 'Turing条纹种子',
},
"Percolation30": {
    "description": '30%渗流 [渗流/统计]',
    "expression": '1 if random() < 0.3 else 0',
    "notes": '30%渗流阈值附近',
},
"Percolation50": {
    "description": '50%渗流 [渗流/统计]',
    "expression": '1 if random() < 0.5 else 0',
    "notes": '50%渗流',
},
"Percolation60": {
    "description": '60%渗流 [渗流/统计]',
    "expression": '1 if random() < 0.6 else 0',
    "notes": '60%接近渗流阈值',
},
"CahnHilliard": {
    "description": 'Cahn-Hilliard初始 [相分离/物理]',
    "expression": '0.5 + 0.5*random()',
    "notes": '白噪声初始（相分离用）',
},
"PointSource": {
    "description": '点源初始 [结构/对称]',
    "expression": '1 if ((x-0.5)**2 + (y-0.5)**2 < 0.001) else 0.01',
    "notes": '点源种子',
},
"RingSource": {
    "description": '环源初始 [结构/对称]',
    "expression": '1 if (abs(sqrt((x-0.5)**2 + (y-0.5)**2) - 0.3) < 0.02) else 0',
    "notes": '环形种子',
},
"FourSources": {
    "description": '四源初始 [结构/对称]',
    "expression": '1 if ((x-0.25)**2+(y-0.25)**2<0.01 or (x-0.75)**2+(y-0.25)**2<0.01 or (x-0.25)**2+(y-0.75)**2<0.01 or (x-0.75)**2+(y-0.75)**2<0.01) else 0',
    "notes": '四角种子',
},
"PinkNoise": {
    "description": '粉红噪声近似 [随机/噪声]',
    "expression": '0.5 + 0.5*sin(random()*100)*sin(random()*100)',
    "notes": '低频增强噪声',
},
"WhiteNoise": {
    "description": '白噪声 [随机/噪声]',
    "expression": 'random()',
    "notes": '均匀白噪声',
},
"HexGrid": {
    "description": '六角网格 [周期/结构]',
    "expression": '1 if (sin(x*34.64) + sin(y*40) > 1.5) else 0',
    "notes": '六角密铺近似',
},
"BZSeed": {
    "description": 'BZ反应种子 [反应扩散/模式]',
    "expression": '1 if (sin(10*x)*sin(10*y) > 0.5 and random() > 0.5) else 0',
    "notes": 'BZ反应初始',
},
"Voronoi4": {
    "description": '4-cell Voronoi [镶嵌/结构]',
    "expression": '1 if (min(abs(x-0.2)+abs(y-0.2), abs(x-0.8)+abs(y-0.2), abs(x-0.2)+abs(y-0.8), abs(x-0.8)+abs(y-0.8)) < 0.1) else 0',
    "notes": '4-cell Voronoi近似',
},
"Gaussian": {
    "description": '高斯分布 [随机/结构]',
    "expression": 'exp(-((x-0.5)**2 + (y-0.5)**2) / 0.04)',
    "notes": '二维高斯',
},
"MultiGaussian": {
    "description": '双高斯 [随机/结构]',
    "expression": 'exp(-((x-0.3)**2 + (y-0.3)**2) / 0.02) + exp(-((x-0.7)**2 + (y-0.7)**2) / 0.02)',
    "notes": '双峰高斯',
},
"PerlinLike": {
    "description": 'Perlin类噪声 [随机/噪声]',
    "expression": '0.5 + 0.5*sin(x*20)*cos(y*20) + 0.3*sin(x*40)*cos(y*40)',
    "notes": '多频叠加噪声',
},
"CircularWave": {
    "description": '圆形波 [波动/对称]',
    "expression": '0.5 + 0.5*sin(20*sqrt((x-0.5)**2 + (y-0.5)**2))',
    "notes": '从中心发出的圆形波',
},
"Spiral2": {
    "description": '双螺旋 [结构/对称]',
    "expression": '1 if (sin(10*atan2(y-0.5, x-0.5) + 5*sqrt((x-0.5)**2 + (y-0.5)**2)) > 0) else 0',
    "notes": '双螺旋近似',
},
"Checker3": {
    "description": '3x3棋盘 [周期/结构]',
    "expression": '1 if ((int(x*6) + int(y*6)) % 2 == 0) else 0',
    "notes": '3x3棋盘',
},
"StripesDiag": {
    "description": '对角条纹 [周期/结构]',
    "expression": '1 if (sin((x+y)*30) > 0) else 0',
    "notes": '对角条纹',
},
"NoiseFractal": {
    "description": '分形噪声近似 [随机/噪声]',
    "expression": '0.5 + 0.5*sin(x*10)*sin(y*10)*sin(x*20)*sin(y*20)',
    "notes": '分形噪声近似',
},
"DomainWall": {
    "description": '畴壁 [物理/结构]',
    "expression": '0.5 + 0.5*tanh(20*(x-0.5))',
    "notes": '畴壁近似',
},
"Vortex": {
    "description": '涡旋 [流体/对称]',
    "expression": 'atan2(y-0.5, x-0.5) / (2*pi) % 1',
    "notes": '涡旋相位场',
},
"LogisticSpace": {
    "description": 'Logistic空间图案 [混沌/复杂]',
    "expression": '3.8*x*(1-x)*3.8*y*(1-y)',
    "notes": 'Logistic映射空间填充',
},
"CellularNoise": {
    "description": '细胞噪声 [随机/噪声]',
    "expression": '1 if random() > 0.9 else 0.1',
    "notes": '稀疏细胞噪声',
},
"GradientCorner": {
    "description": '角点渐变 [梯度/结构]',
    "expression": 'abs(x-0.5) * abs(y-0.5)',
    "notes": '角点渐变',
},
"SineChecker": {
    "description": '正弦棋盘 [周期/结构]',
    "expression": '0.5 + 0.5*sin(x*20)*sin(y*20)',
    "notes": '连续棋盘波',
},
"Annulus": {
    "description": '圆环 [结构/对称]',
    "expression": '1 if (0.2 < (x-0.5)**2 + (y-0.5)**2 < 0.25) else 0',
    "notes": '圆环区域',
},
"CrossHair": {
    "description": '十字准线 [结构/对称]',
    "expression": '1 if (abs(x-0.5) < 0.01 or abs(y-0.5) < 0.01) else 0',
    "notes": '十字准线',
},
"GradRadialSQ": {
    "description": '径向平方根渐变 [梯度/对称]',
    "expression": 'sqrt((x-0.5)**2 + (y-0.5)**2)',
    "notes": '径向距离',
},
"PolarAngle": {
    "description": '极角 [角度/对称]',
    "expression": 'atan2(y-0.5, x-0.5) / (2*pi) % 1',
    "notes": '极角映射',
},
"Lissajous": {
    "description": 'Lissajous初始 [周期/复杂]',
    "expression": '1 if (sin(3*x*20)*sin(2*y*20) > 0.5) else 0',
    "notes": 'Lissajous图案',
},
"Cateye": {
    "description": '猫眼 [结构/对称]',
    "expression": '1 if ((x-0.5)**2/0.04 + (y-0.5)**2/0.01 < 1) else 0',
    "notes": '椭圆形',
},
"Super_SineField": {
    "description": '正弦场超级公式 [超级公式]',
    "expression": '0.5 + 0.5*sin(x*f1*20)*cos(y*f2*20)',
    "notes": '单参数正弦场；f1=1: 水平条纹，f1=2: 高频水平，f2=1: 竖直条纹，f1=f2=1: 棋盘格',
},
"Super_Gaussian": {
    "description": '高斯超级公式 [超级公式]',
    "expression": 'exp(-((x-p1)**2 + (y-p2)**2) / (0.1*(1+w1)))',
    "notes": '可定位可调宽高斯；p1,p2控制位置，w1控制宽度',
},
"Super_PerlinLike": {
    "description": 'Perlin类噪声超级公式 [超级公式]',
    "expression": '0.5 + 0.5*sin(x*f1*30)*cos(y*f2*30) + 0.3*sin(x*f1*60)*cos(y*f2*60)',
    "notes": '多频叠加噪声；f1,f2控制频率，可近似Perlin',
},
"Super_Checker": {
    "description": '棋盘超级公式 [超级公式]',
    "expression": '0.5 + 0.5*sin(x*f1*pi)*sin(y*f2*pi)',
    "notes": '连续棋盘；f1,f2控制格子数',
},
"Super_Spiral": {
    "description": '螺旋超级公式 [超级公式]',
    "expression": '0.5 + 0.5*sin(f1*atan2(y-0.5, x-0.5) + f2*10*sqrt((x-0.5)**2 + (y-0.5)**2))',
    "notes": '可调螺旋；f1控制臂数，f2控制密度',
},
"Super_WavePacket": {
    "description": '波包超级公式 [超级公式]',
    "expression": 'exp(-((x-0.5)**2 + (y-0.5)**2)/(0.04+w1))*sin(f1*20*sqrt((x-0.5)**2 + (y-0.5)**2))',
    "notes": '高斯波包；f1控制振荡频率，w1控制宽度',
},
"SinCosMix": {
    "description": '正弦余弦混合 [周期/波形]',
    "expression": '0.5 + 0.5*sin(x*20)*cos(y*20)',
    "notes": '正弦余弦乘积',
},
"TanWave": {
    "description": '正切波 [周期/波形]',
    "expression": '0.5 + 0.5*tan(x*10)/(1+abs(tan(x*10)))',
    "notes": '正切波近似',
},
"ExpDecay": {
    "description": '指数衰减 [数学/渐变]',
    "expression": 'exp(-10*x)',
    "notes": '指数衰减',
},
"LogSpira": {
    "description": '对数螺旋 [结构/对称]',
    "expression": '1 if (log(sqrt((x-0.5)**2 + (y-0.5)**2) + 0.001) * atan2(y-0.5, x-0.5)) % 1 < 0.5 else 0',
    "notes": '对数螺旋近似',
},
"CircularGradient": {
    "description": '圆形渐变 [渐变/对称]',
    "expression": 'atan2(y-0.5, x-0.5) / (2*pi) % 1',
    "notes": '角度渐变',
},
"RadialGradient2": {
    "description": '径向渐变2 [渐变/对称]',
    "expression": 'abs(x-0.5) + abs(y-0.5)',
    "notes": 'Manhattan距离',
},
"Checker5": {
    "description": '5x5棋盘 [周期/结构]',
    "expression": '1 if ((int(x*10) + int(y*10)) % 2 == 0) else 0',
    "notes": '5x5棋盘',
},
"Stripes45": {
    "description": '45度条纹 [周期/结构]',
    "expression": '1 if (sin((x+y)*25) > 0) else 0',
    "notes": '45度条纹',
},
"NoiseSmooth2": {
    "description": '平滑噪声2 [随机/噪声]',
    "expression": '0.5 + 0.3*random()',
    "notes": '低对比度噪声',
},
"GaussianRing": {
    "description": '高斯环 [结构/对称]',
    "expression": 'exp(-((sqrt((x-0.5)**2 + (y-0.5)**2) - 0.3)**2) / 0.01)',
    "notes": '高斯环形',
},
"Super_Noise": {
    "description": '噪声超级公式 [超级公式]',
    "expression": 'clip(w1*random() + p1, 0, 1)',
    "notes": '可调噪声；w1=强度(0-1)，p1=偏移；w1=1,p1=0:白噪声，w1=0.5,p1=0.25:平滑噪声',
},
"Super_Fractal": {
    "description": '分形超级公式 [超级公式]',
    "expression": '1 if (sin(f1*pi*x)*sin(f2*pi*x)*sin(f3*pi*x) * sin(f1*pi*y)*sin(f2*pi*y)*sin(f3*pi*y)) > w1 else 0',
    "notes": '可调分形（Cantor类）；f1,f2,f3=频率，w1=阈值；f1=3,f2=9,f3=27,w1=0: Cantor尘埃近似',
},
"Super_Wave": {
    "description": '波动超级公式 [超级公式]',
    "expression": '0.5 + 0.5*sin(f1*(x*cos(p1)+y*sin(p1))*20 + w1)*cos(f2*(x*sin(p1)-y*cos(p1))*20)',
    "notes": '可调波；f1,f2=频率，p1=方向角(rad)，w1=相位偏移；f1=1,f2=0:平面波，f1=1,f2=1:驻波',
},
"Super_Shape2D": {
    "description": '2D形状超级公式 [超级公式]',
    "expression": '(((x-p1)/w1)**2 + ((y-p2)/w2)**2 < 1) * 1.0',
    "notes": '可调椭圆/圆形（硬边界）；p1,p2=中心，w1,w2=半径；w1=w2:圆形，w1!=w2:椭圆；形状内=1，外=0',
},
"Super_Polygon": {
    "description": '多边形超级公式 [超级公式]',
    "expression": '((x-p1)**2 + (y-p2)**2 < w1**2) * 1.0',
    "notes": '可调圆形边界（硬边界）；p1,p2=中心，w1=半径；圆内=1，圆外=0',
},
"Super_Gradient2D": {
    "description": '2D渐变超级公式 [超级公式]',
    "expression": 'clip(p1 + w1*abs(x-p2) + w2*abs(y-p3), 0, 1)',
    "notes": '可调2D渐变；p1=基底，p2,p3=参考点，w1,w2=梯度强度',
},
"Super_Interference": {
    "description": '干涉超级公式 [超级公式]',
    "expression": '(sin(f1*pi*sqrt((x-p1)**2+(y-p2)**2)) * sin(f2*pi*sqrt((x-p3)**2+(y-p4)**2)))**2',
    "notes": '双缝/多缝干涉；p1-p4=缝位置，f1,f2=空间频率',
},
"Super_Voronoi": {
    "description": 'Voronoi超级公式 [超级公式]',
    "expression": '(amin([(x-p1)**2+(y-p2)**2, (x-p3)**2+(y-p4)**2, (x-p5)**2+(y-p6)**2, (x-p7)**2+(y-p8)**2], axis=0) < w1**2) * 1.0',
    "notes": '4-cell Voronoi硬边界；p1-p8=4个种子坐标(x1,y1,x2,y2,x3,y3,x4,y4)，w1=影响半径；离最近种子距离<w1的为1，否则为0',
},
# ===== 量子模式 =====
"QuantumWalk": {
    "description": '量子行走干涉图案 [量子/波动]',
    "expression": '0.5 + 0.5*cos(2*pi*(x*3 + y*2)) * cos(2*pi*(x*2 - y*3))',
    "notes": '量子随机行走干涉近似；周期性格点图案',
},
"QuantumRing": {
    "description": '量子环形干涉 [量子/波动]',
    "expression": '0.5 + 0.5*cos(2*pi*5*sqrt((x-0.5)**2 + (y-0.5)**2)) * sin(2*pi*10*atan2(y-0.5, x-0.5))',
    "notes": '环形量子干涉；径向振荡+角向量子数',
},
# ===== 准晶/非周期 =====
"Quasicrystal8": {
    "description": '八重对称准晶 [准晶/非周期]',
    "expression": '(cos(8*atan2(y-0.5, x-0.5)) > 0.3) * 1.0',
    "notes": '八重旋转对称准晶近似；八瓣花图案',
},
"Quasicrystal10": {
    "description": '十重对称准晶 [准晶/非周期]',
    "expression": '(cos(10*atan2(y-0.5, x-0.5)) > 0.2) * 1.0',
    "notes": '十重旋转对称准晶近似；十瓣花图案',
},
"PenroseApprox": {
    "description": 'Penrose镶嵌近似 [准晶/非周期]',
    "expression": '(sin(8*pi*x)*sin(8*pi*y) > 0) * 1.0',
    "notes": 'Penrose类准周期图案近似；用八重正弦乘积模拟',
},
# ===== 拓扑缺陷 =====
"VortexLattice": {
    "description": '涡旋晶格 [拓扑缺陷/流体]',
    "expression": 'atan2(sin(2*pi*4*y), sin(2*pi*4*x)) / (2*pi) % 1',
    "notes": '4x4涡旋晶格；相位场中嵌入整数拓扑电荷',
},
"Disclination": {
    "description": '向错缺陷 [拓扑缺陷/物理]',
    "expression": '(atan2(y-0.5, x-0.5) / (2*pi) % 1 + 0.2*(x-0.5)) % 1',
    "notes": '带向错的相位场；整数拓扑电荷+连续畸变',
},
"DomainWall2": {
    "description": '畴壁2 [拓扑缺陷/物理]',
    "expression": '0.5 + 0.5*tanh(20*(x-0.5)) * tanh(20*(y-0.5))',
    "notes": '十字畴壁；两个方向的一维畴壁乘积',
},
# ===== 多尺度分形 =====
"JuliaSet": {
    "description": 'Julia集近似 [分形/复杂]',
    "expression": '1 if ((x*3-1.5)**2 + (y*3-1.5)**2 < 4) else 0',
    "notes": 'Julia集(c=-0.8+0.156i)单次迭代近似；实际上为圆域，分形边界需多次迭代',
},
"JuliaSet2": {
    "description": 'Julia集二次近似 [分形/复杂]',
    "expression": '1 if ((x*3-1.5)**2 + (y*3-1.5)**2 < 4) else 0',
    "notes": 'Julia集二次迭代近似（简化版）',
},
"BurningShip": {
    "description": 'Burning Ship分形 [分形/复杂]',
    "expression": '1 if (abs(x*3-1.5) + abs(y*3-1.5) < 2) else 0',
    "notes": 'Burning Ship分形近似；曼德博变种，绝对值迭代',
},
# ===== 波动方程初值 =====
"WaveEquation2D": {
    "description": '2D波动方程初值-高斯波包 [波动/物理]',
    "expression": 'sin(2*pi*5*sqrt((x-0.5)**2 + (y-0.5)**2)) * exp(-((x-0.5)**2 + (y-0.5)**2)/0.01)',
    "notes": '高斯波包；适合作为波动方程初始条件',
},
"WaveEquation2D_Slit": {
    "description": '2D波动方程初值-单缝 [波动/物理]',
    "expression": 'sin(2*pi*10*(x-0.3)) * exp(-((y-0.5)**2)/0.01) * (abs(x-0.3) < 0.1)',
    "notes": '单缝波包；模拟单缝衍射初始波函数',
},
"WaveEquation2D_DoubleSlit": {
    "description": '2D波动方程初值-双缝 [波动/物理]',
    "expression": 'sin(2*pi*10*(x-0.3)) * (exp(-((y-0.3)**2)/0.01) + exp(-((y-0.7)**2)/0.01)) * (abs(x-0.3) < 0.1)',
    "notes": '双缝波包；模拟双缝衍射初始波函数',
},
# ===== 新增超级公式 =====
"Super_QuantumWalk": {
    "description": '量子行走超级公式 [超级公式]',
    "expression": '0.5 + 0.5*cos(2*pi*(x*f1 + y*f2) + p1) * sin(2*pi*(x*f3 - y*f4) + p2)',
    "notes": '可调量子干涉；f1,f2,f3,f4=波矢分量，p1,p2=相位偏移',
},
"Super_Quasicrystal": {
    "description": '准晶超级公式 [超级公式]',
    "expression": '(cos(f1*atan2(y-p2, x-p1)) > w1) * 1.0',
    "notes": '可调准晶；f1=旋转对称阶数(8=八重,10=十重)，p1,p2=中心，w1=阈值',
},
"Super_Defect": {
    "description": '拓扑缺陷超级公式 [超级公式]',
    "expression": '(atan2(y-p2, x-p1) / (2*pi) % 1 + w1*(x-p1) + w2*(y-p2)) % 1',
    "notes": '可调拓扑缺陷；p1,p2=中心，w1,w2=缺陷强度；w1=0:纯涡旋，w1>0:向错',
},
"Super_Julia": {
    "description": 'Julia集超级公式 [超级公式]',
    "expression": '1 if ((x*3-1.5)**2 + (y*3-1.5)**2 < 4) else 0',
    "notes": '可调Julia集近似；p1,p2暂未使用；完整版需多次迭代，单次迭代近似为圆域',
},
"Super_WaveEquation2D": {
    "description": '2D波动方程初值超级公式 [超级公式]',
    "expression": 'sin(2*pi*f1*sqrt((x-p1)**2 + (y-p2)**2)) * exp(-((x-p1)**2 + (y-p2)**2)/w1)',
    "notes": '可调高斯波包；p1,p2=波包中心，f1=空间频率，w1=波包宽度',
},
}
