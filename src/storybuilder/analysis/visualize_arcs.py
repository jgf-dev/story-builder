import argparse
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go


def fetch_story(conn, story_query=None):
    if story_query:
        df_story = pd.read_sql_query(
            "SELECT id, story_dir FROM stories WHERE story_dir LIKE ?",
            conn,
            params=(f"%{story_query}%",),
        )
    else:
        df_story = pd.read_sql_query("SELECT id, story_dir FROM stories LIMIT 1", conn)

    if df_story.empty:
        return None, None

    return int(df_story.iloc[0]["id"]), df_story.iloc[0]["story_dir"]


def get_overall_sentiment(conn, story_id, window):
    df_sentences = pd.read_sql_query(
        """
        SELECT id, chapter_index, sentence_index, sentiment_score
        FROM sentences
        WHERE story_id = ?
        ORDER BY chapter_index, sentence_index
    """,
        conn,
        params=(story_id,),
    )

    df_sentences["global_index"] = range(len(df_sentences))
    df_sentences["smoothed_sentiment"] = (
        df_sentences["sentiment_score"]
        .rolling(window=window, center=True, min_periods=max(1, window // 10))
        .mean()
    )
    return df_sentences


def get_top_characters(conn, story_id, limit=5):
    df_chars = pd.read_sql_query(
        """
        SELECT entity_text, COUNT(*) as freq
        FROM sentence_entities
        JOIN sentences ON sentences.id = sentence_entities.sentence_id
        WHERE sentences.story_id = ? AND entity_label = 'PERSON'
        GROUP BY entity_text
        ORDER BY freq DESC
        LIMIT ?
    """,
        conn,
        params=(story_id, limit),
    )
    return df_chars["entity_text"].tolist()


def get_character_sentiment(conn, story_id, char, df_sentences, window):
    char_sentences = pd.read_sql_query(
        """
        SELECT sentences.id, sentiment_score
        FROM sentences
        JOIN sentence_entities ON sentences.id = sentence_entities.sentence_id
        WHERE sentences.story_id = ? AND entity_text = ?
        ORDER BY chapter_index, sentences.id
    """,
        conn,
        params=(story_id, char),
    )

    char_sentences = char_sentences.merge(df_sentences[["id", "global_index"]], on="id")
    char_sentences = char_sentences.sort_values("global_index")

    char_window = max(5, window // 4)
    char_sentences["smoothed_sentiment"] = (
        char_sentences["sentiment_score"]
        .rolling(window=char_window, center=True, min_periods=1)
        .mean()
    )
    return char_sentences


def plot_narrative_arcs(story_dir, df_sentences, char_arcs):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df_sentences["global_index"],
            y=df_sentences["smoothed_sentiment"],
            mode="lines",
            name="Overall Narrative Arc",
            line=dict(width=4, color="white"),
        )
    )

    for char, char_sentences in char_arcs.items():
        fig.add_trace(
            go.Scatter(
                x=char_sentences["global_index"],
                y=char_sentences["smoothed_sentiment"],
                mode="lines",
                name=f"{char}'s Emotional Arc",
                opacity=0.7,
                line=dict(width=2),
            )
        )

    story_name = Path(story_dir).name
    fig.update_layout(
        title=f"Emotional Trajectories: {story_name}",
        xaxis_title="Narrative Timeline (Sentence Index)",
        yaxis_title="Sentiment Score (-1.0 to 1.0)",
        template="plotly_dark",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig, story_name


def main():
    parser = argparse.ArgumentParser(
        description="Visualize narrative arcs from sentiment_analysis.db"
    )
    parser.add_argument("--db-path", default="stories/db/sentiment_analysis.db")
    parser.add_argument("--story", help="Substring of story_dir to visualize")
    parser.add_argument(
        "--window", type=int, default=100, help="Moving average window size (sentences)"
    )
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)

    story_id, story_dir = fetch_story(conn, args.story)

    if story_id is None:
        print("No processed stories found in DB.")
        return

    print(f"Visualizing narrative arc for: {story_dir}")

    df_sentences = get_overall_sentiment(conn, story_id, args.window)

    top_chars = get_top_characters(conn, story_id)
    print(f"Found top characters: {', '.join(top_chars)}")

    char_arcs = {}
    for char in top_chars:
        char_arcs[char] = get_character_sentiment(
            conn, story_id, char, df_sentences, args.window
        )

    fig, story_name = plot_narrative_arcs(story_dir, df_sentences, char_arcs)

    out_file = f"arc_{story_name}.html"
    fig.write_html(out_file)
    print(f"Saved interactive visualization to {out_file}")


if __name__ == "__main__":
    main()
