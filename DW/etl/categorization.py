"""The only product categorizer: name-only, shared by every sales source."""
import re
from dataclasses import dataclass
from functools import lru_cache
from .common import norm

CATEGORY_VERSION='2026-11-04-name-rules-v1'
BUSINESS_CATEGORIES=('Quà tặng','Bánh','Kẹo','Ngũ cốc')

@dataclass(frozen=True)
class CategoryResult:
    canonical_category: str | None
    rule: str
    keyword_conflict: bool=False
    mapping_method: str='rule_based_name'

    @property
    def status(self):return 'Mapped' if self.canonical_category else 'Unmapped'

@lru_cache(maxsize=8192)
def categorize_product(product_name):
    name=norm(product_name)
    word=lambda value:bool(re.search(r'(?<!\w)'+re.escape(value)+r'(?!\w)',name))
    cake,candy,cereal=word('bánh'),word('kẹo'),word('ngũ cốc')
    conflict=cake and candy
    gift=(bool(re.search(r'\[\s*quà\s+tặng(?:\s*\]|\s+không\s+bán\s*\])',name))
          or word('quà tặng ngẫu nhiên') or word('quà tặng không bán') or word('tặng kèm'))
    if gift:return CategoryResult('Quà tặng','gift_marker',False)
    if cake:return CategoryResult('Bánh','cake_keyword',conflict)
    if candy:return CategoryResult('Kẹo','candy_keyword',conflict)
    if cereal:return CategoryResult('Ngũ cốc','cereal_keyword',conflict)
    return CategoryResult(None,'empty_name' if not name else 'no_name_keyword',conflict)
