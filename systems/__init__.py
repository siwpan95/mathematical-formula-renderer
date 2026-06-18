"""System 层 — 操作 Component 的逻辑单元，每帧被 World 依次调用"""
from systems.evolution import EvolutionSystem
from systems.colormap import ColorSystem
from systems.render import RenderSystem
from systems.ui import UISystem

__all__ = ['EvolutionSystem', 'ColorSystem', 'RenderSystem', 'UISystem']
