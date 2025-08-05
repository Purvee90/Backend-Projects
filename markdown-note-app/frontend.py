import dash
from dash import dcc, html, Input, Output, State
from markdown_app import app, db
from utils import create_snippet, remove_markdown_formatting
from services.markdown_render import calculate_note_stats
import requests
import json

# Initialize Dash app
app = dash.Dash(__name__)
server = app.server

# Layout of the app
app.layout = html.Div(
    [
        html.H1("Markdown Note-taking App"),
        html.H2("Register"),
        dcc.Input(id="reg-username", type="text", placeholder="Username"),
        dcc.Input(id="reg-email", type="email", placeholder="Email"),
        dcc.Input(id="reg-password", type="password", placeholder="Password"),
        html.Button("Register", id="register-btn"),
        html.Div(id="register-output"),
        html.H2("Login"),
        dcc.Input(
            id="login-username-email", type="text", placeholder="Username or Email"
        ),
        dcc.Input(id="login-password", type="password", placeholder="Password"),
        html.Button("Login", id="login-btn"),
        html.Div(id="login-output"),
        html.H2("Create Note"),
        dcc.Input(id="note-title", type="text", placeholder="Note Title"),
        dcc.Textarea(
            id="note-content",
            placeholder="Enter markdown content",
            style={"width": "100%", "height": "200px"},
        ),
        html.Button("Save Note", id="save-note-btn"),
        html.Div(id="save-note-output"),
        html.H2("Search Notes"),
        dcc.Input(id="search-query", type="text", placeholder="Search query"),
        html.Button("Search", id="search-btn"),
        html.Div(id="search-results"),
        html.H2("Render Note"),
        dcc.Input(id="render-note-id", type="number", placeholder="Note ID"),
        html.Button("Render", id="render-btn"),
        html.Div(
            id="render-output", style={"border": "1px solid #ccc", "padding": "10px"}
        ),
        html.H2("Note Statistics"),
        dcc.Input(id="stats-note-id", type="number", placeholder="Note ID"),
        html.Button("Get Stats", id="stats-btn"),
        html.Div(id="stats-output"),
        html.H2("Dashboard Statistics"),
        html.Button("Get Dashboard Stats", id="dashboard-btn"),
        html.Div(id="dashboard-output"),
    ]
)


# Callbacks
@app.callback(
    Output("register-output", "children"),
    Input("register-btn", "n_clicks"),
    State("reg-username", "value"),
    State("reg-email", "value"),
    State("reg-password", "value"),
)
def register_user(n_clicks, username, email, password):
    if n_clicks:
        payload = {"username": username, "email": email, "password": password}
        response = requests.post("http://localhost:5000/register", json=payload)
        return response.text


@app.callback(
    Output("login-output", "children"),
    Input("login-btn", "n_clicks"),
    State("login-username-email", "value"),
    State("login-password", "value"),
)
def login_user(n_clicks, username_or_email, password):
    if n_clicks:
        payload = {"username_or_email": username_or_email, "password": password}
        response = requests.post("http://localhost:5000/login", json=payload)
        if response.status_code == 200:
            user_id = response.json().get("user_id")
            return f"Login successful. User ID: {user_id}"
        else:
            return response.text


@app.callback(
    Output("save-note-output", "children"),
    Input("save-note-btn", "n_clicks"),
    State("note-title", "value"),
    State("note-content", "value"),
    State("login-output", "children"),
)
def save_note(n_clicks, title, markdown_text, login_output):
    if n_clicks and "User ID:" in login_output:
        user_id = int(login_output.split("User ID:")[1].strip())
        payload = {"title": title, "markdown_text": markdown_text, "user_id": user_id}
        response = requests.post("http://localhost:5000/save-note", json=payload)
        return response.text


@app.callback(
    Output("search-results", "children"),
    Input("search-btn", "n_clicks"),
    State("search-query", "value"),
)
def search_notes(n_clicks, query):
    if n_clicks:
        response = requests.get(f"http://localhost:5000/search-notes?q={query}")
        results = response.json().get("results", [])
        return html.Ul([html.Li(f"{r['title']}: {r['snippet']}") for r in results])


@app.callback(
    Output("render-output", "children"),
    Input("render-btn", "n_clicks"),
    State("render-note-id", "value"),
)
def render_note(n_clicks, note_id):
    if n_clicks:
        response = requests.get(f"http://localhost:5000/render-note/{note_id}")
        return html.Div(dcc.Markdown(response.text))


@app.callback(
    Output("stats-output", "children"),
    Input("stats-btn", "n_clicks"),
    State("stats-note-id", "value"),
)
def note_stats(n_clicks, note_id):
    if n_clicks:
        response = requests.get(f"http://localhost:5000/note-stats/{note_id}")
        stats = response.json()
        return html.Pre(json.dumps(stats, indent=2))


@app.callback(
    Output("dashboard-output", "children"),
    Input("dashboard-btn", "n_clicks"),
)
def dashboard_stats(n_clicks):
    if n_clicks:
        response = requests.get("http://localhost:5000/dashboard-stats")
        stats = response.json()
        return html.Pre(json.dumps(stats, indent=2))


# Run the Dash app
if __name__ == "__main__":
    app.run(debug=True)
