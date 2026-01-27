from flask import Flask, render_template
import shared_state

app = Flask(__name__)

@app.route("/")
def index():
    return render_template(
        "index.html",
        state=shared_state.assistant_state,
        command=shared_state.current_command,
        intent=shared_state.current_intent,
        action=shared_state.current_action,
    )

def start_web():
    app.run(host="127.0.0.1", port=5000, debug=False)
