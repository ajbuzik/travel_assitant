import json
import datetime as dt
import streamlit as st
import pandas as pd
from auth import check_authorization
import db

METRICS_COLS = ['faithfulness', 'groundedness', 'relevance', 'completeness', 'coherence', 'conciseness']

def _load_db_tables():
    """Load conversation and feedback data from DB (defensive)."""
    try:
        conversation_history = db.get_conversation_data() or []
    except Exception:
        conversation_history = []
    try:
        feedback_data = db.get_feedback_data() or []
    except Exception:
        feedback_data = []
    return pd.DataFrame(conversation_history), pd.DataFrame(feedback_data)

def _normalize_conversation_df(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce types, expand metrics JSON, and compute totals / derived columns."""
    if df.empty:
        # create expected columns to simplify downstream code
        empty = pd.DataFrame(columns=['timestamp'] + METRICS_COLS + ['estimated_cost_usd','eval_estimated_cost_usd','tokens_used','eval_tokens_used','quality_score'])
        return empty

    df = df.copy()
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    # normalize nested metrics if present
    if 'metrics' in df.columns:
        try:
            metrics_df = pd.json_normalize(df['metrics']).add_prefix('metric_')
            df = pd.concat([df.reset_index(drop=True), metrics_df.reset_index(drop=True)], axis=1)
            for m in METRICS_COLS:
                pref = f"metric_{m}"
                if pref in df.columns:
                    df[m] = pd.to_numeric(df[pref], errors='coerce')
        except Exception:
            pass

    # ensure numeric cost/token columns exist
    for col in ['estimated_cost_usd', 'eval_estimated_cost_usd', 'tokens_used', 'eval_tokens_used']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        else:
            df[col] = 0.0

    df['total_cost'] = df['estimated_cost_usd'].fillna(0.0) + df['eval_estimated_cost_usd'].fillna(0.0)
    df['total_tokens'] = df['tokens_used'].fillna(0.0) + df['eval_tokens_used'].fillna(0.0)

    return df

def _render_top_level_metrics(conv_df: pd.DataFrame, fb_df: pd.DataFrame):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Questions Asked", len(conv_df))
    with col2:
        st.metric("Total Feedback Responses", len(fb_df))
    with col3:
        positive = 0
        total_feedback = 0
        if not fb_df.empty and 'feedback_type' in fb_df.columns:
            positive = fb_df[fb_df['feedback_type'] == 'positive'].shape[0]
            total_feedback = len(fb_df)
        if total_feedback > 0:
            satisfaction = (positive / total_feedback) * 100
            st.metric("User Satisfaction", f"{satisfaction:.1f}%")
        else:
            st.metric("User Satisfaction", "N/A")

def _render_feedback_distribution(fb_df: pd.DataFrame):
    st.markdown("### 📈 Feedback Distribution")
    if not fb_df.empty and 'feedback_type' in fb_df.columns:
        positive = fb_df[fb_df['feedback_type'] == 'positive'].shape[0]
        negative = fb_df[fb_df['feedback_type'] == 'negative'].shape[0]
        chart_df = pd.DataFrame({'Feedback Type': ['Positive 👍', 'Negative 👎'], 'Count': [positive, negative]})
        st.bar_chart(chart_df.set_index('Feedback Type'))
    else:
        st.info("No feedback data yet")

def _render_costs_and_tokens(conv_df: pd.DataFrame):
    st.subheader("💰 Cost & Token Summary")
    c1, c2, c3, c4 = st.columns(4)
    total_cost = conv_df['total_cost'].sum() if not conv_df.empty else 0.0
    avg_cost = conv_df['total_cost'].mean() if not conv_df.empty else 0.0
    median_cost = conv_df['total_cost'].median() if not conv_df.empty else 0.0
    total_tokens = conv_df['total_tokens'].sum() if not conv_df.empty else 0.0

    with c1:
        st.metric("Total Estimated Cost (USD)", f"${total_cost:.4f}")
    with c2:
        st.metric("Avg Cost / Query (USD)", f"${avg_cost:.4f}")
    with c3:
        st.metric("Median Cost / Query (USD)", f"${median_cost:.4f}")
    with c4:
        st.metric("Total Tokens Used", f"{int(total_tokens)}")

    st.markdown("#### Cost Over Time")
    if not conv_df.empty and 'timestamp' in conv_df.columns:
        cost_time = (conv_df.dropna(subset=['timestamp']).set_index('timestamp').resample('D').sum()[['total_cost']])
        if not cost_time.empty:
            st.line_chart(cost_time['total_cost'])
        else:
            st.info("No timestamped cost data to display.")
    else:
        st.info("No timestamped conversation data to display cost over time.")

def _render_tokens_usage_and_top_queries(conv_df: pd.DataFrame):
    st.subheader("Tokens Usage")
    if conv_df.empty:
        st.info("No conversation records available for token charts.")
        return

    if 'timestamp' in conv_df.columns and conv_df['timestamp'].notna().any():
        tokens_time = (conv_df.dropna(subset=['timestamp']).set_index('timestamp').resample('D').sum()[['tokens_used', 'eval_tokens_used', 'total_tokens']])
        if not tokens_time.empty:
            st.line_chart(tokens_time)

    top_by_cost = conv_df.sort_values('total_cost', ascending=False).head(10)
    if not top_by_cost.empty:
        display_cols = [c for c in ['question', 'total_cost', 'tokens_used', 'eval_tokens_used', 'total_tokens', 'timestamp'] if c in top_by_cost.columns]
        st.markdown("Top queries by total cost/tokens")
        st.dataframe(top_by_cost[display_cols].reset_index(drop=True))
    else:
        st.info("No conversational records to show.")

def _render_tokens_vs_cost_scatter(conv_df: pd.DataFrame):
    st.subheader("Tokens vs Cost")
    if conv_df.empty:
        st.info("No conversation data for Tokens vs Cost.")
        return
    scatter_df = conv_df[['total_tokens', 'total_cost']].dropna()
    if scatter_df.empty:
        st.info("Not enough data for scatter.")
        return
    try:
        import altair as alt
        chart = alt.Chart(scatter_df.reset_index()).mark_circle(size=60).encode(
            x='total_tokens',
            y='total_cost',
            tooltip=['total_tokens', 'total_cost']
        ).interactive()
        st.altair_chart(chart, use_container_width=True)
    except Exception:
        bucketed = scatter_df.copy()
        bucketed['tokens_bucket'] = (bucketed['total_tokens'] // 50) * 50
        agg = bucketed.groupby('tokens_bucket').sum().reset_index()
        st.bar_chart(agg.set_index('tokens_bucket')['total_cost'])

def _map_label_to_score(v):
    if pd.isna(v):
        return None
    if isinstance(v, str):
        if v.startswith("NON_"):
            return 0.0
        if v.startswith("PARTLY_"):
            return 0.5
        return 1.0
    try:
        return float(v)
    except Exception:
        return None

def _render_quality_metrics(conv_df: pd.DataFrame):
    st.subheader("Evaluation / Quality Metrics")
    if conv_df.empty:
        st.info("No conversation data for evaluation metrics.")
        return

    if 'quality_score' in conv_df.columns:
        conv_df['quality_score'] = pd.to_numeric(conv_df['quality_score'], errors='coerce')
        avg_q = conv_df['quality_score'].mean()
        median_q = conv_df['quality_score'].median()
        count_q = conv_df['quality_score'].count()
        q1, q2, q3 = st.columns(3)
        with q1:
            st.metric("Avg Quality Score", f"{avg_q:.2f}" if not pd.isna(avg_q) else "N/A")
        with q2:
            st.metric("Median Quality Score", f"{median_q:.2f}" if not pd.isna(median_q) else "N/A")
        with q3:
            st.metric("Quality-rated Responses", f"{int(count_q)}")

        q_dist = conv_df['quality_score'].dropna()
        if not q_dist.empty:
            st.markdown("#### Quality Score distribution")
            st.bar_chart(q_dist.value_counts().sort_index())

            top_q = conv_df.sort_values('quality_score', ascending=False).head(5)
            bottom_q = conv_df.sort_values('quality_score', ascending=True).head(5)
            display_cols = [c for c in ['question', 'quality_score', 'total_cost', 'total_tokens', 'timestamp'] if c in conv_df.columns]
            if not top_q.empty:
                st.markdown("**Top answers by Quality Score**")
                st.dataframe(top_q[display_cols].reset_index(drop=True))
            if not bottom_q.empty:
                st.markdown("**Lowest scoring answers**")
                st.dataframe(bottom_q[display_cols].reset_index(drop=True))
        else:
            st.info("Quality score column present but no values to display.")
    else:
        st.info("No numeric quality_score column found.")

    # per-criterion label distributions and aggregated numeric mapping
    existing_metric_cols = [m for m in METRICS_COLS if m in conv_df.columns]
    if existing_metric_cols:
        st.markdown("#### Per-criterion label distributions")
        for m in existing_metric_cols:
            counts = conv_df[m].fillna("MISSING").value_counts()
            st.markdown(f"**{m.capitalize()}**")
            st.bar_chart(counts)

        numeric_metrics = conv_df[existing_metric_cols].applymap(_map_label_to_score)
        avg_metrics = numeric_metrics.mean().dropna()
        if not avg_metrics.empty:
            st.markdown("#### Average (mapped) scores — NON_=0, PARTLY_=0.5, *_=1.0")
            st.bar_chart(avg_metrics)
            st.table(avg_metrics.rename("Average Score").to_frame())
        else:
            st.info("Evaluation metrics present but no parsable values found for aggregation.")
    else:
        st.info("No evaluation metric columns found (faithfulness, groundedness, relevance, completeness, coherence, conciseness).")

def _render_recent_conversations(conv_df: pd.DataFrame):
    st.subheader("💬 Recent Conversations")
    if conv_df.empty:
        st.info("No conversations yet")
        return
    recent = conv_df.tail(10).to_dict(orient='records')
    for entry in reversed(recent):
        ts_raw = entry.get('timestamp')
        # coerce to pandas Timestamp if possible, else fallback to string
        ts_parsed = pd.to_datetime(ts_raw, errors='coerce')
        if not pd.isna(ts_parsed):
            try:
                ts_str = ts_parsed.strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                ts_str = str(ts_parsed)
        else:
            ts_str = str(ts_raw)
        st.write(f"**Q:** {entry.get('question', '')}")
        st.write(f"*Timestamp: {ts_str}*")
        st.divider()

def _render_exports(conv_df: pd.DataFrame, fb_df: pd.DataFrame):
    st.subheader("💾 Data Export")
    if st.button("Export Feedback Data"):
        feedback_json = json.dumps(fb_df.to_dict(orient='records'), indent=2, default=str)
        st.download_button(label="Download Feedback JSON", data=feedback_json, file_name="feedback_data.json", mime="application/json")
    if st.button("Export Conversation Data"):
        conversation_json = json.dumps(conv_df.to_dict(orient='records'), indent=2, default=str)
        st.download_button(label="Download Conversation JSON", data=conversation_json, file_name="conversation_data.json", mime="application/json")
    if st.button("Export Conversation Data (with costs & tokens)"):
        export_df = conv_df.copy()
        st.download_button(label="Download Conversations (CSV)", data=export_df.to_csv(index=False), file_name="conversations_with_costs_tokens.csv", mime="text/csv")
    if st.button("Export Evaluation Metrics"):
        existing_metric_cols = [m for m in METRICS_COLS if m in conv_df.columns]
        if existing_metric_cols:
            metrics_export = conv_df[existing_metric_cols].to_csv(index=False)
            st.download_button(label="Download Metrics (CSV)", data=metrics_export, file_name="evaluation_metrics.csv", mime="text/csv")
        else:
            st.info("No evaluation metrics to export.")

def monitoring_page():
    """Refactored monitoring page that delegates to small rendering helpers."""
    if not check_authorization():
        st.warning("Please login to access the Monitoring page.")
        return

    st.title("📊 Monitoring Dashboard")
    st.markdown("System performance and analytics")

    # lightweight import/DB actions preserved as buttons
    if st.button("Import conversations from file"):
        try:
            res = db.import_conversations_from_file()
            st.success(f"Conversations import result: {res}")
        except Exception as e:
            st.error(f"Import conversations failed: {e}")

    if st.button("Import feedback from file"):
        try:
            res = db.import_feedback_from_file()
            st.success(f"Feedback import result: {res}")
        except Exception as e:
            st.error(f"Import feedback failed: {e}")

    conv_df, fb_df = _load_db_tables()
    conv_df = _normalize_conversation_df(conv_df)

    _render_top_level_metrics(conv_df, fb_df)
    st.markdown("---")
    _render_feedback_distribution(fb_df)
    st.markdown("---")
    _render_costs_and_tokens(conv_df)
    st.markdown("---")
    _render_tokens_usage_and_top_queries(conv_df)
    st.markdown("---")
    _render_tokens_vs_cost_scatter(conv_df)
    st.markdown("---")
    _render_quality_metrics(conv_df)
    st.markdown("---")
    _render_recent_conversations(conv_df)
    st.markdown("---")
    _render_exports(conv_df, fb_df)

    if st.button("Logout"):
        st.session_state.user = None
        st.rerun()
