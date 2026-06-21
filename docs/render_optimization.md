"""
渲染管线性能分析与优化方案
==============================

## 当前渲染管线（world.py + render.py）

数据流：
  grid.data (numpy) 
    → ColorSystem.update() → grid.rgb_hw (h,w,3) + grid.rgb_wh (w,h,3)
    → pygame.surfarray.blit_array(_ca_surface, rgb_wh.transpose)   # CPU 写入 Surface
    → pygame.transform.scale(_ca_surface, (dw,dh), _ca_scaled)   # CPU 软件缩放
    → screen.blit(_ca_scaled, (x,y))                                # CPU→GPU 上传
    → pygame.display.flip()                                        # 双缓冲交换

性能瓶颈（按严重程度排序）：
  1. ★★★ surfarray.blit_array + transform.scale：纯 CPU 操作，大网格（512+）时很慢
  2. ★★  ColorSystem.update() 中三次 astype(np.uint8) 转置写回
  3. ★★  postprocessing（gaussian_filter / sobel）每帧执行，scipy 开销大
  4. ★◇  screen.blit() 每帧执行，有 CPU→GPU 上传开销
  5. ★◇  grid.rgb_wh / rgb_hw 双缓冲，内存占用翻倍

---

## 优化方案

### 方案A：启用 pygame-ce SDL2 Renderer 硬件加速（推荐，改动中等）

原理：用 pygame._sdl2.video.Renderer + Texture 替代 Surface blit
- Renderer 使用 GPU 加速，缩放由 GPU 完成
- Texture.update() 仍然需要 CPU→GPU 上传，但只需一次
- 缩放和质量由 Renderer 在 GPU 上完成

改动点（render.py / world.py）：
  1. 在 RenderSystem.__init__() 中创建 Renderer：
     renderer = pygame._sdl2.video.Renderer(screen, flags=pygame._sdl2.video.RENDERER_ACCELERATED)
  2. 创建 Streaming Texture（频繁更新）：
     texture = pygame._sdl2.video.Texture(renderer, pygame.PIXELFORMAT_RGB24, grid.w, grid.h)
  3. 每帧：numpy → texture.update(rgb_hw) → renderer.clear() → renderer.blit(texture) → renderer.present()

优点：GPU 缩放，大幅降低 CPU 开销
缺点：需要 pygame-ce 2.3+，改动较大

---

### 方案B：优化 ColorSystem（小改动，立竿见影）

当前瓶颈：
  grid.rgb_wh[:,:,0] = (r.T * 255).astype(np.uint8)  # 三次转置+赋值

优化：一次性计算 (h,w,3) 数组，避免三次切片赋值
"""