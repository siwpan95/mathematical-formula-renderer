"""Entity 层 — 只有 ID + 附属 Component 集合，不含业务逻辑"""
from entities.recipe import RecipeEntity
from entities.registry import TemplateRegistry

__all__ = ['RecipeEntity', 'TemplateRegistry']
