from flask import Flask, g

from flask_rlmt import Limiter

app = Flask(__name__)

limiter = Limiter(
    app=app
)

def redirect_source():
    logs = g.logs
    return f"""
        <head>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
        </head>
        <body>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                    font-family: 'Inter', sans-serif;
                }}

                body {{
                    background: #F4F1EA;
                    color: #3A3835;
                    overflow: hidden;
                }}

                .wrapper {{
                    display: flex;
                    flex-direction: column;
                    width: 100vw;
                    height: 100vh;
                    position: relative;
                }}

                .wrapper::before {{
                    position: fixed;
                    color: rgba(229, 224, 216, 0.7);
                    top: 55%;
                    left: 62%;
                    transform: translate(-50%, -50%);
                    font-size: 35vw;
                    font-weight: 800;
                    content: "429";
                    user-select: none;
                    pointer-events: none;
                    z-index: 0;
                    line-height: 1;
                }}

                header {{
                    background: #121212;
                    padding: 1.25rem 2.5rem;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    position: relative;
                    z-index: 10;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
                }}

                header h1 {{
                    color: #F4F1EA;
                    font-size: 1.35rem;
                    font-weight: 600;
                    letter-spacing: -0.02em;
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                }}

                header h1::before {{
                    content: "";
                    display: inline-block;
                    width: 10px;
                    height: 10px;
                    background-color: #FF3B30;
                    border-radius: 50%;
                    box-shadow: 0 0 10px rgba(255, 59, 48, 0.8);
                }}

                header ul {{
                    display: flex;
                    gap: 1.5rem;
                    list-style: none;
                }}

                header a {{
                    color: #A0A0A0;
                    font-size: 0.95rem;
                    font-weight: 500;
                    text-decoration: none;
                    transition: color 0.2s ease;
                }}

                header a:hover {{
                    color: #F4F1EA;
                }}

                .content-area {{
                    display: flex;
                    flex: 1;
                    position: relative;
                    z-index: 5;
                    height: calc(100vh - 70px);
                }}

                .sidebar {{
                    width: 380px;
                    max-width: 90vw;
                    height: 100%;
                    background: rgba(244, 241, 234, 0.85);
                    backdrop-filter: blur(12px);
                    border-right: 1px solid rgba(229, 224, 216, 0.9);
                    display: flex;
                    flex-direction: column;
                    padding: 1.75rem 1.5rem;
                    box-shadow: 10px 0 30px rgba(0, 0, 0, 0.03);
                    gap: 1rem;
                }}

                .info-card {{
                    background: #FFFFFF;
                    border: 1px solid #E5E0D8;
                    border-radius: 8px;
                    padding: 0.85rem 1rem;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}

                .info-card h3 {{
                    font-size: 0.75rem;
                    font-weight: 700;
                    color: #7A7773;
                    text-transform: uppercase;
                    letter-spacing: 0.04em;
                }}

                .info-card p {{
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 0.85rem;
                    color: #121212;
                    font-weight: 600;
                }}

                .logs-div {{
                    display: flex;
                    flex-direction: column;
                    flex: 1;
                    overflow: hidden;
                }}

                .logs-div h2 {{
                    font-size: 0.9rem;
                    font-weight: 600;
                    color: #121212;
                    margin-bottom: 1rem;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                }}

                .logs-list {{
                    list-style: none;
                    display: flex;
                    flex-direction: column;
                    gap: 0.5rem;
                    overflow-y: auto;
                    padding-right: 0.5rem;
                    flex: 1;
                }}

                .logs-list::-webkit-scrollbar {{
                    width: 5px;
                }}

                .logs-list::-webkit-scrollbar-thumb {{
                    background: #E5E0D8;
                    border-radius: 3px;
                }}

                .logs-list li {{
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 0.825rem;
                    background: #FFFFFF;
                    color: #2B2A28;
                    padding: 0.75rem 1rem;
                    border-radius: 6px;
                    border-left: 3px solid #121212;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
                    word-break: break-word;
                }}

                .no-logs {{
                    font-size: 0.95rem;
                    color: #7A7773;
                    font-style: italic;
                }}

                .limit-warning-div {{
                    background: #FFFFFF;
                    border: 1px solid #E5E0D8;
                    border-radius: 8px;
                    padding: 1rem 1.25rem;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
                }}

                .limit-warning-div h2 {{
                    font-size: 0.8rem;
                    font-weight: 600;
                    color: #7A7773;
                    text-transform: uppercase;
                    letter-spacing: 0.04em;
                    margin-bottom: 0.35rem;
                }}

                .limit-warning-p {{
                    font-size: 0.95rem;
                    color: #3A3835;
                    font-weight: 500;
                }}

                .limit-warning {{
                    font-weight: 700;
                    font-size: 1.1rem;
                    color: #FF3B30;
                }}

                .limit-list {{
                    list-style: none;
                    margin: 0.5rem 0 0.75rem;
                    padding: 0;
                }}

                .limit-list {{
                    list-style: none;
                    margin: 0.5rem 0 0.75rem;
                    padding: 0;
                }}

                .limit-list li {{
                    display: flex;
                    justify-content: space-between;
                    padding: 0.3rem 0;
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 0.85rem;
                    color: #3A3835;
                }}

                .enforced-limit {{
                    margin: 0.75rem 0;
                    font-size: 0.9rem;
                    color: #3A3835;
                }}

                .enforced-limit strong {{
                    color: #121212;
                }}
            </style>

            <div class="wrapper">
                <header>
                    <h1>/{logs.endpoint}</h1>
                    <ul>
                        <li><a href="/example">Example</a></li>
                        <li><a href="/example">Example</a></li>
                        <li><a href="/example">Example</a></li>
                    </ul>
                </header>

                <div class="content-area">
                    <aside class="sidebar">
                        <div class="info-card">
                            <h3>Identity</h3>
                            <p>{logs.identity}</p>
                        </div>

                        <div class="logs-div">
                            <h2>Logs:</h2>
                            {'<ul class="logs-list">' + ''.join(f"<li>{log}</li>" for log in reversed(logs.logs)) + '</ul>' if logs.logs else '<p class="no-logs">No available logs</p>'}
                        </div>

                        <div class="info-card">
                            <h3>Reset At</h3>
                            <p>{logs.reset_at}</p>
                        </div>

                        <div class="info-card">
                            <h3>Retry After</h3>
                            <p>{str(logs.retry_after) + "s" if logs.retry_after is not None else "None"}</p>
                        </div>

                       <div class="limit-warning-div">
                           <h2>Limits</h2>

                           <ul class="limit-list">
                               {''.join(f'<li>{stat.limit} req / {stat.window}s</li>' for stat in logs.limit_statistics)}
                           </ul>

                           {f'<p class="enforced-limit"><strong>Enforced Limit:</strong> {logs.enforced_limit[0]} req / {logs.enforced_limit[1]}s</p>' if logs.enforced_limit else 'No enforced limit'}

                           <p class="limit-warning-p">
                               <span class="limit-warning">{logs.remaining}</span> requests remaining
                           </p>
                       </div>
                    </aside>
                </div>
            </div>
        </body>
        """

@app.route("/")
@limiter.guard(limits=[(15, 60), "100 per hour", "1000/d"], on_limited=redirect_source)
def test():
    logs = g.logs
    return f"""
        <head>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
        </head>
        <body>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                    font-family: 'Inter', sans-serif;
                }}

                body {{
                    background: #F4F1EA;
                    color: #3A3835;
                    overflow: hidden;
                }}

                .wrapper {{
                    display: flex;
                    flex-direction: column;
                    width: 100vw;
                    height: 100vh;
                    position: relative;
                }}

                .wrapper::before {{
                    position: fixed;
                    color: rgba(229, 224, 216, 0.7);
                    top: 55%;
                    left: 62%;
                    transform: translate(-50%, -50%);
                    font-size: 35vw;
                    font-weight: 800;
                    content: "200";
                    user-select: none;
                    pointer-events: none;
                    z-index: 0;
                    line-height: 1;
                }}

                header {{
                    background: #121212;
                    padding: 1.25rem 2.5rem;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    position: relative;
                    z-index: 10;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
                }}

                header h1 {{
                    color: #F4F1EA;
                    font-size: 1.35rem;
                    font-weight: 600;
                    letter-spacing: -0.02em;
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                }}

                header h1::before {{
                    content: "";
                    display: inline-block;
                    width: 10px;
                    height: 10px;
                    background-color: #34C759;
                    border-radius: 50%;
                    box-shadow: 0 0 10px rgba(52, 199, 89, 0.8);
                }}

                header ul {{
                    display: flex;
                    gap: 1.5rem;
                    list-style: none;
                }}

                header a {{
                    color: #A0A0A0;
                    font-size: 0.95rem;
                    font-weight: 500;
                    text-decoration: none;
                    transition: color 0.2s ease;
                }}

                header a:hover {{
                    color: #F4F1EA;
                }}

                .content-area {{
                    display: flex;
                    flex: 1;
                    position: relative;
                    z-index: 5;
                    height: calc(100vh - 70px);
                }}

                .sidebar {{
                    width: 380px;
                    max-width: 90vw;
                    height: 100%;
                    background: rgba(244, 241, 234, 0.85);
                    border-right: 1px solid rgba(229, 224, 216, 0.9);
                    display: flex;
                    flex-direction: column;
                    padding: 1.75rem 1.5rem;
                    box-shadow: 10px 0 30px rgba(0, 0, 0, 0.03);
                    gap: 1rem;
                }}

                .info-card {{
                    background: #FFFFFF;
                    border: 1px solid #E5E0D8;
                    border-radius: 8px;
                    padding: 0.85rem 1rem;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}

                .info-card h3 {{
                    font-size: 0.75rem;
                    font-weight: 700;
                    color: #7A7773;
                    text-transform: uppercase;
                    letter-spacing: 0.04em;
                }}

                .info-card p {{
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 0.85rem;
                    color: #121212;
                    font-weight: 600;
                }}

                .logs-div {{
                    display: flex;
                    flex-direction: column;
                    flex: 1;
                    overflow: hidden;
                }}

                .logs-div h2 {{
                    font-size: 0.9rem;
                    font-weight: 600;
                    color: #121212;
                    margin-bottom: 1rem;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                }}

                .logs-list {{
                    list-style: none;
                    display: flex;
                    flex-direction: column;
                    gap: 0.5rem;
                    overflow-y: auto;
                    padding-right: 0.5rem;
                    flex: 1;
                }}

                .logs-list::-webkit-scrollbar {{
                    width: 5px;
                }}

                .logs-list::-webkit-scrollbar-thumb {{
                    background: #E5E0D8;
                    border-radius: 3px;
                }}

                .logs-list li {{
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 0.825rem;
                    background: #FFFFFF;
                    color: #2B2A28;
                    padding: 0.75rem 1rem;
                    border-radius: 6px;
                    border-left: 3px solid #121212;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
                    word-break: break-word;
                    border-right: 1px solid #E5E0D8;
                    border-bottom: 1px solid #E5E0D8;
                    border-top: 1px solid #E5E0D8;
                }}

                .no-logs {{
                    font-size: 0.95rem;
                    color: #7A7773;
                    font-style: italic;
                }}

                .limit-warning-div {{
                    background: #FFFFFF;
                    border: 1px solid #E5E0D8;
                    border-radius: 8px;
                    padding: 1rem 1.25rem;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
                }}

                .limit-warning-div h2 {{
                    font-size: 0.8rem;
                    font-weight: 600;
                    color: #7A7773;
                    text-transform: uppercase;
                    letter-spacing: 0.04em;
                    margin-bottom: 0.35rem;
                }}

                .limit-warning-p {{
                    font-size: 0.95rem;
                    color: #3A3835;
                    font-weight: 500;
                }}

                .limit-warning {{
                    font-weight: 700;
                    font-size: 1.1rem;
                    color: #121212;
                }}
                .limit-list {{
                    list-style: none;
                    margin: 0.5rem 0 0.75rem;
                    padding: 0;
                }}

                .limit-list li {{
                    display: flex;
                    justify-content: space-between;
                    padding: 0.3rem 0;
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 0.85rem;
                    color: #3A3835;
                }}

                .enforced-limit {{
                    margin: 0.75rem 0;
                    font-size: 0.9rem;
                    color: #3A3835;
                }}

                .enforced-limit strong {{
                    color: #121212;
                }}
            </style>

            <div class="wrapper">
                <header>
                    <h1>/{logs.endpoint}</h1>
                    <ul>
                        <li><a href="/example">Example</a></li>
                        <li><a href="/example">Example</a></li>
                        <li><a href="/example">Example</a></li>
                    </ul>
                </header>

                <div class="content-area">
                    <aside class="sidebar">
                        <div class="info-card">
                            <h3>Identity</h3>
                            <p>{logs.identity}</p>
                        </div>

                        <div class="logs-div">
                            <h2>Logs:</h2>
                            {'<ul class="logs-list">' + ''.join(f"<li>{log}</li>" for log in logs.logs) + '</ul>' if logs.logs else '<p class="no-logs">No available logs</p>'}
                        </div>

                        <div class="info-card">
                            <h3>Reset At</h3>
                            <p>{logs.reset_at}</p>
                        </div>

                        <div class="info-card">
                            <h3>Retry After</h3>
                            <p>{str(logs.retry_after) + "s" if logs.retry_after is not None else "None"}</p>
                        </div>

                        <div class="limit-warning-div">
                            <h2>Limits</h2>

                            <ul class="limit-list">
                                {''.join(f'<li>{stat.limit} req / {stat.window}s</li>' for stat in logs.limit_statistics)}
                            </ul>

                            {f'<p class="enforced-limit"><strong>Enforced Limit:</strong> {logs.enforced_limit[0]} req / {logs.enforced_limit[1]}s</p>' if logs.enforced_limit else '<p class="enforced-limit"><strong>No enforced limit</strong></p>'}

                            <p class="limit-warning-p">
                                <span class="limit-warning">{logs.remaining}</span> requests remaining
                            </p>
                        </div>
                    </aside>
                </div>
            </div>
        </body>
        """

if __name__ == "__main__":
    app.run(debug=True)
