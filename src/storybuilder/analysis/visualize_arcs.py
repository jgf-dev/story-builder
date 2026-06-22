import argparse
import sqlite3

import pandas as pd
import plotly.graph_objects as go
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Visualize narrative arcs from sentiment_analysis.db")
    parser.add_argument("--db-path", default="sentiment_analysis.db")
    parser.add_argument("--story", help="Substring of story_dir to visualize")
    parser.add_argument("--window", type=int, default=100, help="Moving average window size (sentences)")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)

    if args.story:
        df_story = pd.read_sql_query("SELECT id, story_dir FROM stories WHERE story_dir LIKE ?", conn, params=(f"%{args.story}%",))
    else:
        df_story = pd.read_sql_query("SELECT id, story_dir FROM stories LIMIT 1", conn)

    if df_story.empty:
        print("No processed stories found in DB.")
        return

    story_id = int(df_story.iloc[0]["id"])
    story_dir = df_story.iloc[0]["story_dir"]

    print(f"Visualizing narrative arc for: {story_dir}")

    df_sentences = pd.read_sql_query("""
        SELECT id, chapter_index, sentence_index, sentiment_score
        FROM sentences
        WHERE story_id = ?
        ORDER BY chapter_index, sentence_index
    """, conn, params=(story_id,))

    df_sentences["global_index"] = range(len(df_sentences))
    df_sentences["smoothed_sentiment"] = df_sentences["sentiment_score"].rolling(
        window=args.window, center=True, min_periods=max(1, args.window // 10)
    ).mean()

    df_chars = pd.read_sql_query("""
        SELECT entity_text, COUNT(*) as freq
        FROM sentence_entities
        JOIN sentences ON sentences.id = sentence_entities.sentence_id
        WHERE sentences.story_id = ? AND entity_label = 'PERSON'
        GROUP BY entity_text
        ORDER BY freq DESC
        LIMIT 5
    """, conn, params=(story_id,))

    top_chars = df_chars["entity_text"].tolist()
    print(f"Found top characters: {', '.join(top_chars)}")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_sentences["global_index"],
        y=df_sentences["smoothed_sentiment"],
        mode="lines",
        name="Overall Narrative Arc",
        line=dict(width=4, color="white")
    ))

    for char in top_chars:
        char_sentences = pd.read_sql_query("""
            SELECT sentences.id, sentiment_score
            FROM sentences
            JOIN sentence_entities ON sentences.id = sentence_entities.sentence_id
            WHERE sentences.story_id = ? AND entity_text = ?
            ORDER BY chapter_index, sentences.id
        """, conn, params=(story_id, char))

        char_sentences = char_sentences.merge(df_sentences[["id", "global_index"]], on="id")
        char_sentences = char_sentences.sort_values("global_index")

        char_window = max(5, args.window // 4)
        char_sentences["smoothed_sentiment"] = char_sentences["sentiment_score"].rolling(
            window=char_window, center=True, min_periods=1
        ).mean()

        fig.add_trace(go.Scatter(
            x=char_sentences["global_index"],
            y=char_sentences["smoothed_sentiment"],
            mode="lines",
            name=f"{char}'s Emotional Arc",
            opacity=0.7,
            line=dict(width=2)
        ))

    story_name = Path(story_dir).name
    fig.update_layout(
        title=f"Emotional Trajectories: {story_name}",
        xaxis_title="Narrative Timeline (Sentence Index)",
        yaxis_title="Sentiment Score (-1.0 to 1.0)",
        template="plotly_dark",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    out_file = f"arc_{story_name}.html"
    fig.write_html(out_file)
    print(f"Saved interactive visualization to {out_file}")


if __name__ == "__main__":
    main()
