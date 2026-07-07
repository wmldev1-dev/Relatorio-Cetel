"""Componentes visuais reutilizaveis do frontend Streamlit."""

from __future__ import annotations

from contextlib import contextmanager
from html import escape
from typing import Iterator

import pandas as pd
import streamlit as st

from utils.table_formatters import build_column_config, prepare_dataframe_for_display, shape_table


def apply_global_styles() -> None:
    """Aplica a identidade visual light da aplicacao."""
    st.markdown(
        """
        <style>
            :root {
                --rf-primary: #2563EB;
                --rf-primary-dark: #1D4ED8;
                --rf-primary-soft: #DBEAFE;
                --rf-cyan: #06B6D4;
                --rf-success: #16A34A;
                --rf-danger: #DC2626;
                --rf-warning: #F59E0B;
                --rf-bg: #F8FAFC;
                --rf-card: #FFFFFF;
                --rf-border: #E2E8F0;
                --rf-text: #0F172A;
                --rf-muted: #64748B;
                --rf-shadow: rgba(15, 23, 42, 0.07);
                --rf-shadow-soft: 0 12px 30px rgba(15, 23, 42, 0.08);
                --rf-shadow-card: 0 16px 42px rgba(15, 23, 42, 0.10);
                --rf-radius: 16px;
                --rf-radius-lg: 20px;
            }
            .stApp,
            div[data-testid="stAppViewContainer"],
            div[data-testid="stAppViewContainer"] > .main {
                background: var(--rf-bg) !important;
                color: var(--rf-text) !important;
                font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            }
            header[data-testid="stHeader"] {
                background: rgba(248, 250, 252, 0.96) !important;
                border-bottom: 1px solid var(--rf-border) !important;
                box-shadow: none !important;
            }
            div[data-testid="stDecoration"] {
                display: none !important;
            }
            .block-container {
                max-width: 1440px;
                padding-top: 2.4rem;
                padding-bottom: 2.4rem;
            }
            div[data-testid="stVerticalBlock"] {
                gap: 0.8rem;
            }
            div[data-testid="column"] > div[data-testid="stVerticalBlock"] {
                gap: 0.75rem;
            }
            [data-testid="stSidebar"] {
                background: var(--rf-card) !important;
                border-right: 1px solid var(--rf-border);
                box-shadow: 6px 0 22px rgba(15, 23, 42, 0.04);
            }
            [data-testid="stSidebar"] > div:first-child {
                padding-top: 1.15rem;
            }
            [data-testid="stSidebarNav"] {
                padding-top: 0.85rem;
            }
            [data-testid="stSidebarNav"] ul {
                gap: 0.32rem;
            }
            [data-testid="stSidebarNav"] a {
                border-radius: 12px;
                color: var(--rf-text) !important;
                font-size: 0.88rem;
                font-weight: 720;
                margin: 0.06rem 0.55rem;
                min-height: 2.45rem;
                padding: 0.62rem 0.72rem;
            }
            [data-testid="stSidebarNav"] a:hover {
                background: #EFF6FF;
            }
            [data-testid="stSidebarNav"] a[aria-current="page"] {
                background: var(--rf-primary-soft);
                color: var(--rf-primary-dark) !important;
                box-shadow: inset 3px 0 0 var(--rf-primary);
            }
            [data-testid="stSidebarNav"] [data-testid="stMarkdownContainer"] p,
            [data-testid="stSidebarNav"] span {
                letter-spacing: 0.02em;
            }
            .rf-page-header {
                background: var(--rf-card);
                border: 1px solid var(--rf-border);
                border-radius: var(--rf-radius-lg);
                box-shadow: var(--rf-shadow-soft);
                margin-bottom: 1.15rem;
                padding: 1.2rem 1.35rem;
            }
            .rf-page-header-top {
                align-items: center;
                display: flex;
                gap: 0.75rem;
                justify-content: space-between;
            }
            .rf-page-title {
                color: var(--rf-text);
                font-size: clamp(1.35rem, 2vw, 1.85rem);
                font-weight: 800;
                letter-spacing: 0.018em;
                line-height: 1.15;
                margin: 0;
                text-transform: uppercase;
            }
            .rf-page-subtitle {
                color: var(--rf-muted);
                font-size: 0.94rem;
                line-height: 1.45;
                margin: 0.35rem 0 0;
                max-width: 780px;
            }
            .rf-badge,
            .rf-status-badge {
                align-items: center;
                border-radius: 999px;
                display: inline-flex;
                font-size: 0.72rem;
                font-weight: 750;
                letter-spacing: 0.025em;
                line-height: 1;
                padding: 0.42rem 0.62rem;
                text-transform: uppercase;
            }
            .rf-status-neutral { background: #F1F5F9; color: #334155; }
            .rf-status-success { background: #DCFCE7; color: #166534; }
            .rf-status-warning { background: #FEF3C7; color: #92400E; }
            .rf-status-danger { background: #FEE2E2; color: #991B1B; }
            .rf-section-head {
                margin: 1.15rem 0 0.55rem;
            }
            .rf-section-title {
                color: var(--rf-text);
                font-size: 0.92rem;
                font-weight: 800;
                letter-spacing: 0.05em;
                margin: 0;
                text-transform: uppercase;
            }
            .rf-section-description,
            .rf-muted {
                color: var(--rf-muted);
                font-size: 0.88rem;
                line-height: 1.45;
                margin: 0.25rem 0 0;
            }
            .rf-filter-panel,
            div[data-testid="stVerticalBlockBorderWrapper"],
            div[data-testid="stForm"] {
                background: var(--rf-card) !important;
                border: 1px solid var(--rf-border) !important;
                border-radius: var(--rf-radius) !important;
                box-shadow: var(--rf-shadow-soft);
            }
            div[data-testid="stForm"] {
                padding: 1.05rem !important;
            }
            div[data-testid="stDialog"] div[data-testid="stForm"] {
                box-shadow: none;
            }
            .rf-filter-panel {
                border-left: 4px solid var(--rf-primary) !important;
                margin: 0.15rem 0 0.8rem;
                padding: 1rem 1.05rem;
            }
            .rf-dashboard-block {
                margin-top: 0.35rem;
            }
            .rf-metric-grid,
            .rf-card-grid,
            .rf-card-row {
                align-items: stretch;
                box-sizing: border-box;
                display: grid;
                gap: 20px;
                margin-bottom: 24px;
                overflow: hidden;
                width: 100%;
            }
            .rf-metric-grid {
                grid-template-columns: repeat(4, minmax(0, 1fr));
            }
            .rf-card-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .rf-card-row {
                grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            }
            .rf-card,
            .rf-section-card,
            .rf-chart-card,
            .rf-table-card {
                background: var(--rf-card);
                border: 1px solid var(--rf-border);
                border-radius: var(--rf-radius);
                box-sizing: border-box;
                box-shadow: var(--rf-shadow-soft);
                margin-bottom: 24px;
                overflow: hidden;
                width: 100%;
            }
            .rf-card,
            .rf-section-card {
                height: 100%;
                padding: 20px;
            }
            .rf-chart-card {
                padding: 0.25rem 0.35rem 0;
            }
            .rf-table-card {
                margin-top: 4px;
            }
            .rf-grid {
                display: grid;
                gap: 20px;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                margin-bottom: 24px;
            }
            @media (max-width: 1180px) {
                .rf-grid,
                .rf-metric-grid,
                .rf-card-grid {
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }
            }
            @media (max-width: 760px) {
                .rf-grid,
                .rf-metric-grid,
                .rf-card-grid {
                    grid-template-columns: 1fr;
                }
                .block-container {
                    padding-left: 0.85rem;
                    padding-right: 0.85rem;
                }
            }
            .rf-filter-title {
                color: var(--rf-text);
                font-size: 0.82rem;
                font-weight: 800;
                letter-spacing: 0.05em;
                margin: 0;
                text-transform: uppercase;
            }
            .rf-filter-description {
                color: var(--rf-muted);
                font-size: 0.8rem;
                margin: 0.25rem 0 0;
            }
            label,
            div[data-testid="stSelectbox"] label,
            div[data-testid="stDateInput"] label,
            div[data-testid="stNumberInput"] label,
            div[data-testid="stTextInput"] label,
            div[data-testid="stTextArea"] label,
            div[data-testid="stFileUploader"] label,
            div[data-testid="stMultiSelect"] label {
                color: var(--rf-text) !important;
                font-size: 0.74rem !important;
                font-weight: 760 !important;
                letter-spacing: 0.04em;
                text-transform: uppercase;
            }
            div[data-baseweb="select"] > div,
            div[data-baseweb="input"] > div,
            div[data-baseweb="textarea"] > div,
            div[data-baseweb="tag"] {
                border-radius: 10px !important;
            }
            div[data-baseweb="input"] input::placeholder {
                color: #94A3B8 !important;
            }
            div[data-baseweb="select"] > div,
            div[data-baseweb="input"] > div,
            textarea,
            div[data-testid="stFileUploader"] section {
                background: #FFFFFF !important;
                border: 0 !important;
                border-radius: 12px !important;
                box-shadow: inset 0 0 0 1.5px #CBD5E1 !important;
                color: var(--rf-text) !important;
                box-sizing: border-box !important;
                min-height: 3.1rem;
                overflow: visible !important;
            }
            input {
                border: 0 !important;
                box-shadow: none !important;
                line-height: 1.4 !important;
                min-height: 2.85rem !important;
                padding: 0.72rem 0.9rem !important;
            }
            div[data-baseweb="input"] {
                min-height: 3.1rem !important;
            }
            div[data-baseweb="input"] > div {
                align-items: center !important;
                display: flex !important;
            }
            div[data-baseweb="select"] > div:focus-within,
            div[data-baseweb="input"] > div:focus-within,
            textarea:focus {
                box-shadow:
                    inset 0 0 0 1.5px var(--rf-primary),
                    0 0 0 3px rgba(37, 99, 235, 0.14) !important;
            }
            div[data-testid="stWidgetLabel"] p {
                color: var(--rf-text) !important;
                font-weight: 760 !important;
                letter-spacing: 0.04em;
                text-transform: uppercase;
            }
            div[data-testid="stCaptionContainer"],
            div[data-testid="stMarkdownContainer"] small {
                color: var(--rf-muted) !important;
            }
            .stButton > button {
                align-items: center !important;
                border-radius: 12px !important;
                display: inline-flex !important;
                font-weight: 760 !important;
                justify-content: center !important;
                letter-spacing: 0.025em;
                line-height: 1.2 !important;
                min-height: 2.9rem;
                min-width: 10.5rem;
                padding: 0.72rem 1rem !important;
                text-transform: uppercase;
            }
            div[data-testid="stFormSubmitButton"] > button {
                align-items: center !important;
                border-radius: 12px !important;
                display: inline-flex !important;
                font-weight: 760 !important;
                justify-content: center !important;
                letter-spacing: 0.025em;
                line-height: 1.2 !important;
                min-height: 3rem;
                min-width: 10.5rem;
                padding: 0.75rem 1rem !important;
                text-transform: uppercase;
            }
            div[data-testid="stFormSubmitButton"] {
                margin-top: 0.35rem;
            }
            .rf-button-row {
                margin-top: 0.85rem;
            }
            .rf-metric-card {
                background: var(--rf-card);
                border: 1px solid var(--rf-border);
                border-left: 4px solid var(--rf-primary);
                border-radius: var(--rf-radius);
                box-sizing: border-box;
                box-shadow: var(--rf-shadow-soft);
                display: flex;
                flex-direction: column;
                height: 100%;
                justify-content: space-between;
                margin-bottom: 20px;
                min-height: 152px;
                overflow: hidden;
                padding: 21px;
                width: 100%;
            }
            .rf-metric-row-spacer {
                height: 20px;
                width: 100%;
            }
            .rf-metric-card.rf-status-success { border-left-color: var(--rf-success); }
            .rf-metric-card.rf-status-warning { border-left-color: var(--rf-warning); }
            .rf-metric-card.rf-status-danger { border-left-color: var(--rf-danger); }
            .rf-metric-card.rf-metric-long .rf-metric-value {
                display: -webkit-box;
                font-size: 0.95rem;
                line-height: 1.28;
                -webkit-line-clamp: 3;
                -webkit-box-orient: vertical;
                min-height: 3.65rem;
                overflow: hidden;
            }
            .rf-metric-top {
                align-items: flex-start;
                display: flex;
                gap: 0.75rem;
                justify-content: space-between;
                min-height: 2.35rem;
            }
            .rf-metric-label {
                color: var(--rf-muted);
                font-size: 0.72rem;
                font-weight: 800;
                letter-spacing: 0.05em;
                line-height: 1.2;
                margin: 0;
                max-width: calc(100% - 3rem);
                text-transform: uppercase;
                word-break: normal;
            }
            .rf-metric-icon {
                align-items: center;
                background: #EFF6FF;
                border: 1px solid #BFDBFE;
                border-radius: 12px;
                color: var(--rf-primary-dark);
                display: inline-flex;
                flex: 0 0 2.25rem;
                font-size: 0.95rem;
                font-weight: 800;
                height: 2.25rem;
                justify-content: center;
                width: 2.25rem;
            }
            .rf-metric-value {
                color: var(--rf-text);
                font-size: clamp(1.08rem, 1.7vw, 1.48rem);
                font-weight: 800;
                line-height: 1.18;
                margin: 0.65rem 0 0;
                min-height: 2.1rem;
                overflow-wrap: anywhere;
                word-break: break-word;
                white-space: normal;
            }
            .rf-metric-description {
                color: var(--rf-muted);
                font-size: 0.78rem;
                line-height: 1.32;
                margin: 0.45rem 0 0.75rem;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
                overflow: hidden;
            }
            .rf-metric-trend {
                align-items: center;
                border-radius: 999px;
                display: inline-flex;
                font-size: 0.72rem;
                font-weight: 800;
                letter-spacing: 0.035em;
                line-height: 1;
                margin-top: 0.75rem;
                padding: 0.4rem 0.55rem;
                text-transform: uppercase;
                width: fit-content;
            }
            .rf-metric-card.rf-status-success .rf-metric-trend {
                background: #DCFCE7;
                color: #166534;
            }
            .rf-metric-card.rf-status-warning .rf-metric-trend {
                background: #FEF3C7;
                color: #92400E;
            }
            .rf-metric-card.rf-status-danger .rf-metric-trend {
                background: #FEE2E2;
                color: #991B1B;
            }
            .rf-metric-card.rf-status-neutral .rf-metric-trend,
            .rf-metric-trend {
                background: #F1F5F9;
                color: #334155;
            }
            .rf-empty-state {
                background: var(--rf-card);
                border: 1px dashed #CBD5E1;
                border-radius: var(--rf-radius);
                color: var(--rf-muted);
                padding: 1.45rem;
                text-align: center;
            }
            .rf-empty-title {
                color: var(--rf-text);
                font-weight: 800;
                margin: 0 0 0.25rem;
                text-transform: uppercase;
            }
            div[data-testid="stDataFrame"] {
                background: #FFFFFF !important;
                border: 1px solid var(--rf-border) !important;
                border-radius: var(--rf-radius) !important;
                color: var(--rf-text) !important;
                overflow: hidden;
            }
            div[data-testid="stDataFrame"] [role="columnheader"] {
                background: #EAF2FF !important;
                color: var(--rf-text) !important;
                font-size: 0.72rem;
                font-weight: 800;
                letter-spacing: 0.045em;
                text-transform: uppercase;
            }
            .rf-table-title {
                color: var(--rf-text);
                font-size: 0.9rem;
                font-weight: 800;
                letter-spacing: 0.045em;
                margin: 0 0 0.55rem;
                text-transform: uppercase;
            }
            .rf-table-caption {
                color: var(--rf-muted);
                font-size: 0.78rem;
                margin: -0.1rem 0 0.55rem;
            }
            .rf-footer {
                border-top: 1px solid var(--rf-border);
                color: var(--rf-muted);
                font-size: 0.78rem;
                margin-top: 2.2rem;
                padding-top: 1.05rem;
                text-align: right;
            }
            .rf-login-shell {
                margin: 0.75rem auto 0;
                max-width: 480px;
                padding: 0 0.5rem;
                width: 100%;
            }
            .rf-login-panel {
                width: 100%;
            }
            .rf-login-brand {
                align-items: center;
                display: flex;
                flex-direction: column;
                margin-bottom: 1.15rem;
                text-align: center !important;
                width: 100%;
            }
            .rf-login-brand * {
                text-align: center !important;
            }
            .rf-login-logo {
                align-items: center;
                background: #EFF6FF;
                border: 1px solid #BFDBFE;
                border-radius: 16px;
                box-shadow: 0 10px 24px rgba(37, 99, 235, 0.16);
                color: var(--rf-primary-dark);
                display: inline-flex;
                font-size: 1.2rem;
                font-weight: 850;
                height: 3.35rem;
                justify-content: center;
                letter-spacing: 0.04em;
                margin-bottom: 0.95rem;
                width: 5.4rem;
            }
            .rf-login-kicker {
                color: var(--rf-primary-dark);
                font-size: 0.72rem;
                font-weight: 850;
                letter-spacing: 0.08em;
                margin: 0 0 0.35rem;
                text-transform: uppercase;
            }
            .rf-login-title {
                color: var(--rf-text);
                font-size: 1.8rem;
                font-weight: 850;
                letter-spacing: 0.02em;
                line-height: 1.1;
                margin: 0;
                text-transform: uppercase;
            }
            .rf-login-subtitle {
                color: var(--rf-muted);
                display: block;
                font-size: 0.95rem;
                line-height: 1.45;
                margin: 0.5rem auto 0;
                max-width: 420px;
                text-align: center !important;
                width: 100%;
            }
            .rf-login-card {
                background: var(--rf-card);
                border: 1px solid var(--rf-border);
                border-radius: var(--rf-radius-lg);
                box-shadow: var(--rf-shadow-card);
                margin-top: 0.25rem;
                padding: 0;
            }
            .rf-login-form-title {
                color: var(--rf-text);
                font-size: 0.92rem;
                font-weight: 850;
                letter-spacing: 0.055em;
                margin: 0 0 0.25rem;
                text-transform: uppercase;
            }
            .rf-login-form-copy {
                color: var(--rf-muted);
                font-size: 0.86rem;
                line-height: 1.45;
                margin: 0 0 1rem;
            }
            .rf-login-footer {
                color: var(--rf-muted);
                font-size: 0.76rem;
                line-height: 1.45;
                margin-top: 1rem;
                text-align: center;
            }
            .rf-login-field-spacer {
                height: 0.15rem;
            }
            .rf-user-badge {
                align-items: center;
                background: #EFF6FF;
                border: 1px solid #BFDBFE;
                border-radius: 14px;
                color: var(--rf-primary-dark);
                display: flex;
                gap: 0.7rem;
                margin: 0.75rem 0 0.9rem;
                padding: 0.82rem 0.9rem;
            }
            .rf-user-avatar {
                align-items: center;
                background: var(--rf-primary);
                border-radius: 999px;
                color: #FFFFFF;
                display: inline-flex;
                flex: 0 0 2.15rem;
                font-size: 0.78rem;
                font-weight: 850;
                height: 2.15rem;
                justify-content: center;
                letter-spacing: 0.03em;
                width: 2.15rem;
            }
            .rf-user-content {
                min-width: 0;
            }
            .rf-user-name {
                color: var(--rf-text);
                font-size: 0.86rem;
                font-weight: 800;
                line-height: 1.2;
                margin: 0;
            }
            .rf-user-email {
                color: var(--rf-muted);
                font-size: 0.76rem;
                line-height: 1.25;
                margin: 0.18rem 0 0;
                overflow-wrap: anywhere;
            }
            .rf-app-brand {
                align-items: center;
                border-bottom: 1px solid var(--rf-border);
                display: flex;
                gap: 0.75rem;
                margin-bottom: 0.85rem;
                padding: 0.25rem 0 1rem;
            }
            .rf-app-mark {
                align-items: center;
                background: #EFF6FF;
                border: 1px solid #BFDBFE;
                border-radius: 14px;
                color: var(--rf-primary-dark);
                display: inline-flex;
                flex: 0 0 2.55rem;
                font-size: 0.9rem;
                font-weight: 850;
                height: 2.55rem;
                justify-content: center;
                width: 2.55rem;
            }
            .rf-app-brand-text {
                min-width: 0;
            }
            .rf-app-name {
                color: var(--rf-primary-dark);
                font-size: 1.14rem;
                font-weight: 850;
                letter-spacing: 0.045em;
                line-height: 1.1;
                margin: 0;
                text-transform: uppercase;
            }
            .rf-app-subtitle {
                color: var(--rf-muted);
                font-size: 0.78rem;
                font-weight: 700;
                margin: 0.2rem 0 0;
                text-transform: uppercase;
            }
            .rf-alert {
                border: 1px solid var(--rf-border);
                border-radius: 12px;
                font-size: 0.88rem;
                font-weight: 650;
                line-height: 1.35;
                margin: 0.65rem 0;
                padding: 0.82rem 0.95rem;
            }
            .rf-alert-info { background: #EFF6FF; border-color: #BFDBFE; color: #1E40AF; }
            .rf-alert-success { background: #F0FDF4; border-color: #BBF7D0; color: #166534; }
            .rf-alert-warning { background: #FFFBEB; border-color: #FDE68A; color: #92400E; }
            .rf-alert-error { background: #FEF2F2; border-color: #FECACA; color: #991B1B; }
            .rf-loading {
                align-items: center;
                background: var(--rf-card);
                border: 1px solid var(--rf-border);
                border-radius: var(--rf-radius);
                color: var(--rf-muted);
                display: flex;
                font-size: 0.9rem;
                font-weight: 750;
                gap: 0.6rem;
                padding: 1rem;
                text-transform: uppercase;
            }
            .rf-form-actions {
                display: grid;
                gap: 0.75rem;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                margin-top: 0.8rem;
            }
            .rf-danger-button-hint .stButton > button {
                border-color: #FECACA !important;
                color: var(--rf-danger) !important;
            }
            @media (max-width: 640px) {
                .rf-form-actions {
                    grid-template-columns: 1fr;
                }
                .rf-login-shell {
                    margin-top: 0.25rem;
                    padding-left: 0.4rem;
                    padding-right: 0.4rem;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str | None = None, badge: str | None = None) -> None:
    """Renderiza cabecalho de pagina."""
    badge_markup = status_badge(badge, "neutral", render=False) if badge else ""
    subtitle_markup = f'<p class="rf-page-subtitle">{escape(subtitle)}</p>' if subtitle else ""
    _html(
        (
            '<div class="rf-page-header">'
            '<div class="rf-page-header-top">'
            f'<h1 class="rf-page-title">{escape(title.upper())}</h1>'
            f"{badge_markup}"
            "</div>"
            f"{subtitle_markup}"
            "</div>"
        ),
    )


def app_header(user: dict[str, object] | None = None) -> None:
    """Renderiza marca e usuario na sidebar autenticada."""
    st.markdown(
        """
        <div class="rf-app-brand">
            <div class="rf-app-mark">BI</div>
            <div class="rf-app-brand-text">
                <p class="rf-app-name">CETEL</p>
                <p class="rf-app-subtitle">Relatórios Financeiros</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if user:
        user_badge(user)


def login_layout() -> None:
    """Renderiza base visual da tela de login."""
    st.empty()


def login_header() -> None:
    """Renderiza marca e contexto da tela de login."""
    _html(
        """
        <div class="rf-login-brand">
            <h1 class="rf-login-title">CETEL</h1>
            <p class="rf-login-subtitle">Relatórios Financeiros para acompanhamento seguro de indicadores e lançamentos.</p>
        </div>
        """,
    )


def login_form(error_message: str | None = None) -> tuple[str, str, bool]:
    """Renderiza formulario de login."""
    with st.container(border=True):
        st.markdown(
            """
            <p class="rf-login-form-title">Acesso ao dashboard</p>
            <p class="rf-login-form-copy">Entre com suas credenciais para acessar o ambiente financeiro.</p>
            """,
            unsafe_allow_html=True,
        )
        if error_message:
            alert_box(error_message, status="error")
        st.markdown('<div class="rf-login-field-spacer"></div>', unsafe_allow_html=True)
        email = st.text_input("Email", key="login_email", placeholder="seu.email@cetel.local")
        password = password_input("Senha", key="login_password", placeholder="Digite sua senha")
        submitted = primary_button("Entrar", key="login_submit_button")
    return email, password, submitted


def login_footer() -> None:
    """Renderiza rodape discreto do login."""
    st.markdown(
        '<p class="rf-login-footer">Acesso restrito ao sistema financeiro CETEL. Use uma conta autorizada.</p>',
        unsafe_allow_html=True,
    )


def login_card(error_message: str | None = None) -> tuple[str, str, bool]:
    """Renderiza card central de login e retorna credenciais submetidas."""
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"],
            [data-testid="collapsedControl"] {
                display: none !important;
            }
            .block-container {
                align-items: center !important;
                display: flex !important;
                justify-content: center !important;
                max-width: 100% !important;
                min-height: 100vh !important;
                padding: 0 1rem !important;
            }
            .block-container > div {
                width: 100% !important;
            }
            div[data-testid="column"] {
                max-width: 560px !important;
            }
            div[data-testid="stVerticalBlockBorderWrapper"] {
                border-radius: 20px !important;
                box-shadow: 0 16px 42px rgba(15, 23, 42, 0.10) !important;
                overflow: visible !important;
            }
            div[data-testid="stVerticalBlockBorderWrapper"] > div {
                overflow: visible !important;
            }
            div[data-testid="stTextInput"] {
                box-sizing: border-box !important;
                margin-bottom: 1.05rem !important;
                overflow: visible !important;
                padding: 0 !important;
                width: 100% !important;
            }
            div[data-testid="stTextInput"] > div {
                box-sizing: border-box !important;
                overflow: visible !important;
                width: 100% !important;
            }
            div[data-baseweb="input"] {
                box-sizing: border-box !important;
                height: 52px !important;
                min-height: 52px !important;
                overflow: visible !important;
                width: 100% !important;
            }
            div[data-baseweb="input"] > div {
                align-items: center !important;
                background: #FFFFFF !important;
                border: 1.5px solid #CBD5E1 !important;
                border-radius: 13px !important;
                box-shadow: none !important;
                box-sizing: border-box !important;
                display: flex !important;
                height: 52px !important;
                min-height: 52px !important;
                overflow: visible !important;
                padding: 0 !important;
                width: 100% !important;
            }
            div[data-baseweb="input"] > div:focus-within {
                border-color: #2563EB !important;
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.14) !important;
            }
            div[data-baseweb="input"] input {
                border: 0 !important;
                box-shadow: none !important;
                box-sizing: border-box !important;
                height: 50px !important;
                line-height: 24px !important;
                min-height: 50px !important;
                outline: 0 !important;
                overflow: visible !important;
                padding: 12px 14px !important;
                width: 100% !important;
            }
            .stButton {
                margin-top: 0.15rem !important;
                width: 100% !important;
            }
            .stButton > button {
                align-items: center !important;
                border-radius: 13px !important;
                display: inline-flex !important;
                justify-content: center !important;
                min-height: 52px !important;
                padding: 12px 14px !important;
                width: 100% !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    _, center, _ = st.columns([1, 1.05, 1], gap="large")
    with center:
        login_layout()
        login_header()
        email, password, submitted = login_form(error_message)
        login_footer()
    return email, password, submitted


def user_badge(user: dict[str, object]) -> None:
    """Renderiza dados resumidos do usuario logado."""
    name = str(user.get("name") or "Usuário")
    email = str(user.get("email") or "")
    initials = _initials(name)
    st.markdown(
        f"""
        <div class="rf-user-badge">
            <div class="rf-user-avatar">{escape(initials)}</div>
            <div class="rf-user-content">
                <p class="rf-user-name">{escape(name)}</p>
                <p class="rf-user-email">{escape(email)}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def alert_box(message: str, status: str = "info") -> None:
    """Renderiza alerta padronizado."""
    normalized_status = status if status in {"info", "success", "warning", "error"} else "info"
    st.markdown(
        f'<div class="rf-alert rf-alert-{normalized_status}">{escape(message)}</div>',
        unsafe_allow_html=True,
    )


def loading_state(message: str = "Carregando") -> None:
    """Renderiza estado de carregamento padronizado."""
    st.markdown(
        f'<div class="rf-loading">↻ {escape(message)}</div>',
        unsafe_allow_html=True,
    )


def confirm_action(label: str, key: str, help_text: str | None = None) -> bool:
    """Renderiza checkbox de confirmacao para acoes sensiveis."""
    return st.checkbox(label.upper(), key=key, help=help_text)


def password_input(
    label: str = "Senha",
    key: str | None = None,
    placeholder: str | None = None,
) -> str:
    """Campo padrao de senha."""
    return st.text_input(
        label,
        type="password",
        key=key,
        placeholder=placeholder,
    )


def form_actions(
    primary_label: str,
    secondary_label: str | None = None,
    primary_key: str | None = None,
    secondary_key: str | None = None,
) -> tuple[bool, bool]:
    """Renderiza botoes de acao para formularios."""
    cols = st.columns(2 if secondary_label else 1, gap="medium")
    with cols[0]:
        primary_clicked = primary_button(primary_label, key=primary_key)
    secondary_clicked = False
    if secondary_label:
        with cols[1]:
            secondary_clicked = secondary_button(secondary_label, key=secondary_key)
    return primary_clicked, secondary_clicked


@contextmanager
def section_card(title: str | None = None, description: str | None = None) -> Iterator[None]:
    """Container visual para secoes."""
    if title:
        section_title(title, description)
    st.markdown('<div class="rf-section-card">', unsafe_allow_html=True)
    with st.container(border=True):
        yield
    st.markdown("</div>", unsafe_allow_html=True)


@contextmanager
def section_container(title: str | None = None, description: str | None = None) -> Iterator[None]:
    """Container padronizado para blocos de conteudo."""
    if title:
        section_title(title, description)
    st.markdown('<div class="rf-section-card">', unsafe_allow_html=True)
    with st.container(border=True):
        yield
    st.markdown("</div>", unsafe_allow_html=True)


@contextmanager
def filter_panel(title: str = "FILTROS", description: str | None = None) -> Iterator[None]:
    """Container visual para filtros."""
    description_markup = f'<p class="rf-filter-description">{escape(description)}</p>' if description else ""
    st.markdown(
        f"""
        <div class="rf-filter-panel">
            <p class="rf-filter-title">{escape(title.upper())}</p>
            {description_markup}
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        yield


def metric_grid(columns: int = 4) -> list[object]:
    """Cria grade padronizada para cards de metricas."""
    return list(st.columns(columns, gap="large"))


def card_grid(columns: int = 2) -> list[object]:
    """Cria grade padronizada para cards e graficos menores."""
    return list(st.columns(columns, gap="large"))


def render_metric_cards(cards: list[dict[str, object]], columns: int = 4) -> None:
    """Renderiza cards de metrica com grade e espaçamento padronizados."""
    st.markdown('<div class="rf-metric-grid">', unsafe_allow_html=True)
    chunks = list(range(0, len(cards), columns))
    for chunk_index, chunk_start in enumerate(chunks):
        row = cards[chunk_start:chunk_start + columns]
        cols = metric_grid(columns)
        for column, card in zip(cols, row, strict=False):
            with column:
                metric_card(
                    str(card.get("label") or ""),
                    card.get("value", ""),
                    str(card.get("icon") or ""),
                    str(card.get("description") or ""),
                    status=str(card.get("status")) if card.get("status") else None,
                )
        if chunk_index < len(chunks) - 1:
            st.markdown('<div class="rf-metric-row-spacer"></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def primary_button(
    label: str,
    key: str | None = None,
    icon: str | None = None,
    disabled: bool = False,
) -> bool:
    """Botao primario padronizado."""
    return st.button(
        _button_label(label, icon),
        type="primary",
        key=key,
        width="stretch",
        disabled=disabled,
    )


def secondary_button(
    label: str,
    key: str | None = None,
    icon: str | None = None,
    disabled: bool = False,
) -> bool:
    """Botao secundario padronizado."""
    return st.button(
        _button_label(label, icon),
        type="secondary",
        key=key,
        width="stretch",
        disabled=disabled,
    )


def danger_button(
    label: str,
    key: str | None = None,
    icon: str | None = None,
    disabled: bool = False,
) -> bool:
    """Botao destrutivo padronizado."""
    st.markdown('<div class="rf-danger-button-hint">', unsafe_allow_html=True)
    clicked = secondary_button(label, key=key, icon=icon or "!", disabled=disabled)
    st.markdown("</div>", unsafe_allow_html=True)
    return clicked


def action_buttons(
    primary_label: str = "ATUALIZAR",
    secondary_label: str = "LIMPAR FILTROS",
    primary_key: str | None = None,
    secondary_key: str | None = None,
) -> tuple[bool, bool]:
    """Renderiza botoes de filtro alinhados a direita."""
    st.markdown('<div class="rf-button-row">', unsafe_allow_html=True)
    spacer, primary_col, secondary_col = st.columns([3.2, 1.15, 1.15], gap="medium")
    with spacer:
        st.empty()
    with primary_col:
        primary_clicked = primary_button(primary_label, key=primary_key, icon="↻")
    with secondary_col:
        secondary_clicked = secondary_button(secondary_label, key=secondary_key, icon="×")
    st.markdown("</div>", unsafe_allow_html=True)
    return primary_clicked, secondary_clicked


def metric_card(
    label: str,
    value: object,
    icon: str | None = None,
    description: str | None = None,
    status: str | None = None,
) -> None:
    """Renderiza card de indicador."""
    if description is not None and icon is not None and len(str(icon)) > 3 and len(str(description)) <= 3:
        icon, description = description, icon
    long_class = " rf-metric-long" if len(str(value)) > 48 else ""
    status_class = f" rf-status-{status}" if status else " rf-status-neutral"
    description_text, trend_text = _split_metric_description(description)
    description_markup = (
        f'<p class="rf-metric-description">{escape(description_text)}</p>'
        if description_text else ""
    )
    trend_markup = (
        f'<span class="rf-metric-trend">{escape(trend_text)}</span>'
        if trend_text else ""
    )
    icon_markup = f'<span class="rf-metric-icon">{escape(icon or "•")}</span>'
    st.markdown(
        f"""
        <div class="rf-metric-card{status_class}{long_class}">
            <div class="rf-metric-top">
                <p class="rf-metric-label">{escape(label.upper())}</p>
                {icon_markup}
            </div>
            <p class="rf-metric-value">{escape(str(value))}</p>
            {description_markup}
            {trend_markup}
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_badge(text: str, status: str = "neutral", render: bool = True) -> str | None:
    """Renderiza badge de status."""
    markup = f'<span class="rf-status-badge rf-status-{escape(status)}">{escape(text.upper())}</span>'
    if render:
        st.markdown(markup, unsafe_allow_html=True)
        return None
    return markup


def empty_state(title: str, message: str, icon: str | None = None) -> None:
    """Renderiza estado vazio amigavel."""
    icon_markup = f"<div>{escape(icon)}</div>" if icon else ""
    st.markdown(
        f"""
        <div class="rf-empty-state">
            {icon_markup}
            <p class="rf-empty-title">{escape(title)}</p>
            <p>{escape(message)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_table(
    df: pd.DataFrame,
    title: str | None = None,
    height: int = 520,
    key: str | None = None,
    caption: str | None = None,
    column_order: list[str] | tuple[str, ...] | None = None,
    hidden_columns: list[str] | tuple[str, ...] | None = None,
) -> None:
    """Renderiza tabela padronizada com st.dataframe e column_config."""
    prepared_df = prepare_dataframe_for_display(
        shape_table(df, column_order, hidden_columns),
    )
    st.markdown('<div class="rf-table-card">', unsafe_allow_html=True)
    with st.container(border=True):
        if title:
            st.markdown(f'<p class="rf-table-title">{escape(title.upper())}</p>', unsafe_allow_html=True)
        if caption:
            st.markdown(f'<p class="rf-table-caption">{escape(caption)}</p>', unsafe_allow_html=True)
        if prepared_df.empty:
            empty_state("Sem registros", "Nenhum dado disponível para exibição.")
        else:
            st.dataframe(
                prepared_df,
                column_config=build_column_config(prepared_df),
                height=height,
                hide_index=True,
                key=key,
                width="stretch",
            )
    st.markdown("</div>", unsafe_allow_html=True)


def page_footer(text: str = "UI CETEL LIGHT BI v3") -> None:
    """Renderiza rodape padrao."""
    st.markdown(f'<div class="rf-footer">{escape(text)}</div>', unsafe_allow_html=True)


def section_title(title: str, description: str | None = None) -> None:
    """Renderiza titulo de secao."""
    description_markup = f'<p class="rf-section-description">{escape(description)}</p>' if description else ""
    st.markdown(
        f"""
        <div class="rf-section-head">
            <h2 class="rf-section-title">{escape(title.upper())}</h2>
            {description_markup}
        </div>
        """,
        unsafe_allow_html=True,
    )


def info_box(message: str) -> None:
    st.info(message)


def warning_box(message: str) -> None:
    st.warning(message)


def error_box(message: str) -> None:
    st.error(message)


def success_box(message: str) -> None:
    st.success(message)


def filter_header(title: str, description: str | None = None) -> None:
    """Compatibilidade com filtros no sidebar do dashboard."""
    description_markup = f'<p class="rf-filter-description">{escape(description)}</p>' if description else ""
    st.markdown(
        f'<div class="rf-filter-panel"><p class="rf-filter-title">{escape(title.upper())}</p>{description_markup}</div>',
        unsafe_allow_html=True,
    )


def filter_group_title(title: str) -> None:
    st.markdown(f'<p class="rf-section-title">{escape(title.upper())}</p>', unsafe_allow_html=True)


# Compatibilidade com chamadas antigas.
page_title = page_header


def _html(markup: str) -> None:
    """Renderiza HTML sem deixar o parser Markdown expor tags como texto."""
    if hasattr(st, "html"):
        st.html(markup)
    else:
        st.markdown(markup, unsafe_allow_html=True)


def _split_metric_description(description: str | None) -> tuple[str | None, str | None]:
    """Separa descricao e tendencia quando o texto usa o padrao 'descricao | tendencia'."""
    if not description:
        return None, None
    if "|" not in description:
        return description, None
    description_text, trend_text = description.rsplit("|", 1)
    return description_text.strip() or None, trend_text.strip() or None


def _button_label(label: str, icon: str | None = None) -> str:
    text = label.upper()
    return f"{icon} {text}" if icon else text


def _initials(name: str) -> str:
    parts = [part for part in name.strip().split() if part]
    if not parts:
        return "U"
    return "".join(part[0].upper() for part in parts[:2])
