# -*- coding: utf-8 -*-
"""Central Al Rajhi design tokens.

This module is the single source of truth for product colors, semantic tones,
spacing and corner radii.  UI code should read from ThemeManager/DesignSystem,
not duplicate literal colors in new widgets.
"""
from __future__ import annotations

BRAND = {
    'app_name_ar': 'الراجحي للمحاسبة والمستودعات والتصنيع',
    'login_name_ar': 'الراجحي للمحاسبة',
    'developer_card_name_ar': 'الراجحي للمحاسبة والمستودعات والتصنيع',
    'font_family': "'Tajawal', 'Segoe UI', sans-serif",
    'radius_sm': 8,
    'radius_md': 12,
    'radius_lg': 18,
    'spacing_sm': 8,
    'spacing_md': 14,
    'spacing_lg': 24,
}

# Product palette extracted into stable design tokens.
ALRAJHI_BLUE = '#0F3D75'
ALRAJHI_BLUE_2 = '#1E5AA8'
ALRAJHI_ACCENT = '#2D7FF9'

LIGHT_TOKENS = {
    'bg_window': '#F5F7FA',
    'bg_panel': '#FFFFFF',
    'bg_sidebar': '#EEF3F8',
    'bg_table': '#FFFFFF',
    'bg_table_alt': '#F8FAFC',
    'text_primary': '#1A202C',
    'text_secondary': '#4A5568',
    'text_muted': '#718096',
    'border': '#E2E8F0',
    'border_focus': ALRAJHI_ACCENT,
    'primary': ALRAJHI_BLUE,
    'primary_hover': ALRAJHI_BLUE_2,
    'primary_2': ALRAJHI_BLUE_2,
    'accent': ALRAJHI_ACCENT,
    'success': '#1F9D55',
    'danger': '#D64545',
    'warning': '#D69E2E',
    'info': ALRAJHI_ACCENT,
    'header_bg': ALRAJHI_BLUE,
    'header_text': '#FFFFFF',
    'selection_bg': '#D9E9FF',
    'selection_text': '#0B2444',
    'card_bg': '#FFFFFF',
    'input_bg': '#FFFFFF',
    'success_soft': '#EAF8F0',
    'warning_soft': '#FFF8E5',
    'danger_soft': '#FDECEC',
    'info_soft': '#EAF3FF',
    'brand_soft': '#EAF1F8',
    'shadow': 'rgba(15,61,117,0.16)',
}

DARK_TOKENS = {
    'bg_window': '#0B1623',
    'bg_panel': '#111F2E',
    'bg_sidebar': '#0D1A28',
    'bg_table': '#111F2E',
    'bg_table_alt': '#0D1A28',
    'text_primary': '#F7FAFC',
    'text_secondary': '#CBD5E1',
    'text_muted': '#94A3B8',
    'border': '#27405B',
    'border_focus': '#5FA8FF',
    'primary': '#5FA8FF',
    'primary_hover': '#2D7FF9',
    'primary_2': '#1E5AA8',
    'accent': '#74B6FF',
    'success': '#38B56B',
    'danger': '#F87171',
    'warning': '#F2C45A',
    'info': '#74B6FF',
    'header_bg': '#0F3D75',
    'header_text': '#FFFFFF',
    'selection_bg': '#1E5AA8',
    'selection_text': '#FFFFFF',
    'card_bg': '#101C2A',
    'input_bg': '#0E1A27',
    'success_soft': 'rgba(31,157,85,0.18)',
    'warning_soft': 'rgba(214,158,46,0.18)',
    'danger_soft': 'rgba(214,69,69,0.18)',
    'info_soft': 'rgba(45,127,249,0.18)',
    'brand_soft': 'rgba(45,127,249,0.15)',
    'shadow': 'rgba(0,0,0,0.42)',
}


def get_tokens(theme: str = 'light') -> dict:
    """Return a copy of tokens for the requested theme."""
    source = DARK_TOKENS if theme == 'dark' else LIGHT_TOKENS
    return dict(source)
