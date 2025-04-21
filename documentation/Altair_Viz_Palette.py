import altair as alt
import pandas as pd

# Define your color palette
palette = ["#EC3E3D", "#FEB809", "#FFF8FE"]

# Apply global Altair theme for minimalist design (Altair 5.5+)
@alt.theme.register('minimalist_theme', enable=True)
def minimalist_theme():
    return {
        'config': {
            'background': palette[2],  # Off-white
            'title': {'fontSize': 20, 'anchor': 'start', 'font': 'Arial', 'color': '#333333'},
            'axis': {
                'labelFontSize': 12,
                'titleFontSize': 14,
                'grid': False,
                'domainColor': '#333333',
                'tickColor': '#333333',
                'labelColor': '#333333',
                'titleColor': '#333333',
            },
            'legend': {
                'labelFontSize': 12,
                'titleFontSize': 14,
                'orient': 'right',
                'labelColor': '#333333',
                'titleColor': '#333333',
            },
            'view': {'stroke': 'transparent'},
        }
    }

# Example visualization functions

def minimalist_bar_chart(df, x_col, y_col, title=''):
    return alt.Chart(df).mark_bar(
        cornerRadiusTopLeft=3,
        cornerRadiusTopRight=3,
        color=palette[0]
    ).encode(
        x=alt.X(f'{x_col}:N', sort='-y'),
        y=alt.Y(f'{y_col}:Q'),
        tooltip=[x_col, y_col]
    ).properties(
        title=title,
        width=600,
        height=350
    )
def minimalist_line_chart(df, x_col, y_col, title=''):
    # Auto-detect x-axis type
    dtype = df[x_col].dtype
    if pd.api.types.is_numeric_dtype(dtype):
        x_type = 'Q'  # Quantitative
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        x_type = 'T'  # Temporal
    else:
        x_type = 'N'  # Nominal

    return alt.Chart(df).mark_line(
        point=alt.OverlayMarkDef(color=palette[1]),
        color=palette[0]
    ).encode(
        x=alt.X(f'{x_col}:{x_type}'),
        y=alt.Y(f'{y_col}:Q'),
        tooltip=[x_col, y_col]
    ).properties(
        title=title,
        width=600,
        height=350
    )

def minimalist_scatter_plot(df, x_col, y_col, color_col=None, title=''):
    base = alt.Chart(df).mark_circle(size=60, opacity=0.8)

    if color_col:
        base = base.encode(
            color=alt.Color(f'{color_col}:N', scale=alt.Scale(range=palette[:2]))
        )
    else:
        base = base.encode(
            color=alt.value(palette[0])
        )

    return base.encode(
        x=alt.X(f'{x_col}:Q'),
        y=alt.Y(f'{y_col}:Q'),
        tooltip=[x_col, y_col, color_col] if color_col else [x_col, y_col]
    ).properties(
        title=title,
        width=600,
        height=350
    )

def minimalist_histogram(
    df, col, title="Distribution of Transcript Segment Counts per Episode", bin_width=5
):
    """
    Plots a professional, minimalist histogram with an overlaid distribution curve using Altair.
    - Softer bar color, subtle line
    - Descriptive axis labels and title
    - Annotates the highest frequency bin
    """
    import numpy as np

    # Calculate bin edges
    min_val, max_val = df[col].min(), df[col].max()
    bins = np.arange(min_val, max_val + bin_width, bin_width)

    # Bin the data for the line
    hist_df = (
        df[[col]]
        .dropna()
        .assign(bin=lambda d: pd.cut(d[col], bins=bins, include_lowest=True))
        .groupby('bin')
        .size()
        .reset_index(name='frequency')
    )
    # Bin center for line
    hist_df['bin_center'] = hist_df['bin'].apply(lambda x: float(x.mid) if pd.notnull(x) else None)
    hist_df = hist_df.drop(columns=['bin'])

    # Find the highest frequency bin for annotation
    max_idx = hist_df['frequency'].idxmax()
    max_bin_center = hist_df.loc[max_idx, 'bin_center']
    max_freq = hist_df.loc[max_idx, 'frequency']

    # Histogram (bar chart)
    bars = alt.Chart(hist_df).mark_bar(
        color="#EC3E3D",  # Use plain string for color
        opacity=1,
        size=20
    ).encode(
        x=alt.X('bin_center:Q',
                title='Segment Count (per Episode)',
                axis=alt.Axis(format='d')),
        y=alt.Y('frequency:Q', title='Number of Episodes (Frequency)'),
        tooltip=[alt.Tooltip('bin_center:Q', title='Segment Count (bin center)'),
                 alt.Tooltip('frequency:Q', title='Episodes')]
    )

    # Line (distribution curve)
    line = alt.Chart(hist_df).mark_line(
        color="#FEB809",  # Use plain string for color
        strokeWidth=4,
        opacity=1
    ).encode(
        x='bin_center:Q',
        y='frequency:Q'
    )

    # Annotation for the highest frequency bin
    annotation = alt.Chart(pd.DataFrame({
        'bin_center': [max_bin_center],
        'frequency': [max_freq]
    })).mark_text(
        align='left',
        baseline='bottom',
        dx=7,
        dy=-7,
        fontSize=13,
        color='#333'
    ).encode(
        x='bin_center:Q',
        y='frequency:Q',
        text=alt.value(f"Peak: {int(max_freq)} episodes")
    )

    # Compose the chart
    chart = (bars + line + annotation).properties(
        title=title,
        width=800,
        height=350,
        background="#FFF8FE"
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=14,
        grid=False,
        domainColor='#333333',
        tickColor='#333333',
        labelColor='#333333',
        titleColor='#333333'
    ).configure_title(
        fontSize=20,
        anchor='start',
        font='Arial',
        color='#333333'
    )

    return chart

# Example usage
# df = pd.read_csv('your_data.csv')
# chart = minimalist_bar_chart(df, 'category', 'value', title='Minimalist Bar Chart')
# chart.display()