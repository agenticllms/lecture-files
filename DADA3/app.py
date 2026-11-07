"""The deployable app: your bug-fixing team behind bugteam_ui.py.

    python app.py            # http://localhost:7860

Nothing to implement here; it works once notebooks 01 and 02 are done.
"""
import os

from bugteam_ui import interface

demo = interface()

if __name__ == "__main__":
    # Render sets PORT and needs 0.0.0.0. Locally this is http://localhost:7860.
    # show_error puts the exception text in the app, so a bad key or an exhausted quota reads as
    # what it is instead of a bare "Error".
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", 7860)), show_error=True)
