#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ranking Engine - Core "Run Colors" Algorithm
Implements parent-child hierarchy based on DATE > RANK > PX
"""
from typing import List, Dict
from collections import defaultdict
from models.color import ColorRaw, ColorProcessed
import logging

logger = logging.getLogger(__name__)


class RankingEngine:
    """
    Implements parent-child hierarchy for color data
    
    Algorithm:
    1. Group by CUSIP
    2. Sort by: DATE (desc) > RANK (asc) > PX (asc)
    3. First = Parent, rest = Children
    """
    
    def run_colors(self, raw_colors: List[ColorRaw]) -> List[ColorProcessed]:
        """
        Main algorithm entry point
        
        Args:
            raw_colors: List of raw color data from database
            
        Returns:
            List of processed colors with parent-child hierarchy
        """
        if not raw_colors:
            logger.warning("Empty color list provided to ranking engine")
            return []
        
        logger.info(f"Processing {len(raw_colors)} colors")
        
        # Group by CUSIP
        grouped = self._group_by_cusip(raw_colors)
        logger.info(f"Grouped into {len(grouped)} unique CUSIPs")
        
        # Process each group
        result = []
        for cusip, colors in grouped.items():
            processed = self._process_group(colors)
            result.extend(processed)
        
        # Count parents and children
        parents = sum(1 for c in result if c.is_parent)
        children = sum(1 for c in result if not c.is_parent)
        logger.info(f"Processed: {parents} parents, {children} children")
        
        return result
    
    def _group_by_cusip(self, colors: List[ColorRaw]) -> Dict[str, List[ColorRaw]]:
        """Group colors by CUSIP identifier"""
        grouped = defaultdict(list)
        for color in colors:
            grouped[color.cusip].append(color)
        return dict(grouped)
    
    def _process_group(self, colors: List[ColorRaw]) -> List[ColorProcessed]:
        """
        Process a single CUSIP group
        
        Sorting hierarchy:
        1. DATE (descending) - More recent = higher priority
        2. RANK (ascending) - Lower rank = higher priority
        3. PX (ascending) - Lower price = higher priority
        """
        # Sort colors by priority
        sorted_colors = sorted(colors, key=lambda c: (
            -c.date.timestamp(),                         # More recent = higher priority
            c.rank,                                      # Lower rank = higher priority
            c.px if c.px else float('inf')              # Lower price = higher priority
        ))
        
        if len(sorted_colors) == 1:
            # Single color = always parent with no children
            return [self._create_parent(sorted_colors[0], 0)]
        
        # First = parent, rest = children
        parent = sorted_colors[0]
        children = sorted_colors[1:]
        
        result = []
        
        # Create parent
        parent_processed = self._create_parent(parent, len(children))
        result.append(parent_processed)
        
        # Create children
        for child in children:
            child_processed = self._create_child(child, parent.message_id)
            result.append(child_processed)
        
        return result
    
    def _create_parent(self, color: ColorRaw, children_count: int) -> ColorProcessed:
        """Create parent color with metadata"""
        return ColorProcessed(
            **color.model_dump(),
            is_parent=True,
            parent_message_id=None,
            children_count=children_count
        )
    
    def _create_child(self, color: ColorRaw, parent_id: int) -> ColorProcessed:
        """Create child color with parent reference"""
        return ColorProcessed(
            **color.model_dump(),
            is_parent=False,
            parent_message_id=parent_id,
            children_count=0
        )
